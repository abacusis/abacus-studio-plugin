"""Explicit Studio Git workflow. OAuth stays in OS keyring, never in chat/files.

Run connect/setup/status/prepare/resolve/submit/cancel. No background uploads.
"""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.error
import urllib.request
import webbrowser

from clone_workspace import clone
from sync_workspace import excluded, SECRET
from preview_workspace import refresh_launch, supervise
from sandbox_environment import provision
from install_skills import install as install_skills
from plugin_runtime import skills_directory
from helper_runtime import ensure_helper_runtime
from code_map import code_map
import browser_verification

FUNCTIONS = 'https://aseymhsdlzcwquwcbxzc.supabase.co/functions/v1'
SERVICE = 'Abacus Studio Git'
ACCOUNT = 'studio-account-v1'


def keyring_store():
    import keyring
    backend = keyring.get_keyring()
    # No plaintext fallback, environment-variable token, or project token file.
    if not backend.__class__.__module__.startswith(('keyring.backends.macOS', 'keyring.backends.Windows', 'keyring.backends.SecretService')):
        raise ValueError('A supported OS credential store is required (Keychain, Windows Credential Manager, or Secret Service).')
    return keyring


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Unexpected service redirect')


def post(path, body, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(FUNCTIONS + '/' + path, data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            return json.loads(response.read(300_000))
    except urllib.error.HTTPError as error:
        if path == 'local-git':
            try:
                message = json.loads(error.read(4096)).get('error')
            except Exception:
                message = None
            if isinstance(message, str) and len(message) <= 300:
                raise ValueError(message) from None
        raise


def access(project, isolated=False):
    store = keyring_store()
    key = project
    raw = None if isolated else store.get_password(SERVICE, ACCOUNT)
    if raw:
        key = ACCOUNT
    else:
        raw = store.get_password(SERVICE, key)
    if not raw:
        raise ValueError('Run connect to sign into Studio first.')
    saved = json.loads(raw)
    if saved['expires_at'] <= time.time() + 120:
        tokens = post('mcp-oauth/token', {'grant_type': 'refresh_token', 'client_id': saved['client_id'],
                                        'refresh_token': saved['refresh_token']})
        saved.update(tokens, expires_at=time.time() + tokens['expires_in'])
        store.set_password(SERVICE, key, json.dumps(saved))
    return saved['access_token']


def operation(project, action, **kwargs):
    return post('local-git', {'project_id': project, 'action': action, **kwargs}, access(project))


def disconnect(project=None):
    """Revoke this app's OAuth consent, then forget its local tokens."""
    store = keyring_store()
    project = project or ACCOUNT
    if store.get_password(SERVICE, project) is None:
        return {'status': 'disconnected', 'scope': 'local_git', 'server_revoked': True}
    failure = None
    try:
        response = post('mcp-oauth/revoke', {}, access(project, isolated=True))
        if response.get('revoked') is not True:
            failure = True
    except urllib.error.HTTPError as error:
        # Expired/revoked refresh or access grants are already unusable.
        failure = error.code != 401
    except Exception:
        failure = True
    finally:
        store.delete_password(SERVICE, project)
    if failure:
        raise ValueError('Local tokens were cleared, but Studio revocation could not be verified. '
                         'Revoke the connection in Studio Connections before reporting full disconnect.')
    return {'status': 'disconnected', 'scope': 'local_git', 'server_revoked': True}


def connect(project=None):
    store = keyring_store()  # Verify secure storage before starting authorization.
    project = project or ACCOUNT
    disconnect(project)  # An explicit Connect always starts fresh, never refreshes an old account.
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    result = {}
    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(url.query)
            if url.path != '/callback' or params.get('state') != [state]:
                self.send_error(400)
                return
            result.update(code=params.get('code', [None])[0], error=params.get('error', [None])[0])
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(b'Return to your coding tool. You can close this browser tab.')
    with HTTPServer(('127.0.0.1', 0), Callback) as server:
        server.timeout = 1
        redirect = f'http://127.0.0.1:{server.server_port}/callback'
        registration = post('mcp-oauth/register', {'client_name': 'Abacus Studio local Git',
            'redirect_uris': [redirect], 'token_endpoint_auth_method': 'none',
            'grant_types': ['authorization_code', 'refresh_token'], 'scope': 'projects:read local:write'})
        query = urllib.parse.urlencode({'client_id': registration['client_id'], 'redirect_uri': redirect,
            'response_type': 'code', 'scope': 'projects:read local:write', 'state': state,
            'code_challenge': base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('='),
            'code_challenge_method': 'S256', 'resource': 'https://studio.abacusis.ca/mcp'})
        url = 'https://studio.abacusis.ca/oauth/authorize?' + query
        print(json.dumps({'status': 'sign_in_required', 'authorization_url': url}), flush=True)
        webbrowser.open(url)
        deadline = time.time() + 300
        while not result and time.time() < deadline:
            server.handle_request()
        if result.get('error') or not result.get('code'):
            raise ValueError('Studio sign-in was cancelled or timed out.')
        tokens = post('mcp-oauth/token', {'grant_type': 'authorization_code', 'client_id': registration['client_id'],
            'redirect_uri': redirect, 'code': result['code'], 'code_verifier': verifier})
    store.set_password(SERVICE, project, json.dumps(tokens | {'client_id': registration['client_id'],
                                                              'expires_at': time.time() + tokens['expires_in']}))
    if project == ACCOUNT:
        return {'status': 'connected', **mcp_call('get_connection_status', {})}
    config = operation(project, 'config')
    return {'status': 'connected', 'repository': config['repository']}


def mcp_call(name, arguments):
    response = post('mcp', {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                          'params': {'name': name, 'arguments': arguments}}, access(ACCOUNT))
    result = response.get('result', {})
    if response.get('error') or result.get('isError') or not isinstance(result.get('structuredContent'), dict):
        raise ValueError('Studio could not complete this request. Check connection and app access.')
    return result['structuredContent']


def connection_status():
    if keyring_store().get_password(SERVICE, ACCOUNT) is None:
        return {'connected': False, 'roles': [], 'granted_scopes': []}
    try:
        return mcp_call('get_connection_status', {})
    except urllib.error.HTTPError as error:
        if error.code in (400, 401):
            return {'connected': False, 'roles': [], 'granted_scopes': []}
        raise ValueError('Studio connection could not be verified.') from None


def credential(project):
    fields = dict(line.split('=', 1) for line in sys.stdin.read(8192).splitlines() if '=' in line)
    config = operation(project, 'config')
    if fields.get('protocol') != 'https' or fields.get('host') != 'github.com' or fields.get('path') not in (
            config['repository'], config['repository'] + '.git'):
        raise ValueError('Credential request is not for the authorized client repository.')
    grant = operation(project, 'credential')
    if grant['repository'] != config['repository']:
        raise ValueError('Repository authorization changed.')
    # This stdout is consumed privately by Git's credential pipe. Never run this
    # command as a user-facing diagnostic or capture its output in Claude tools.
    sys.stdout.write('username=x-access-token\npassword=' + grant['token'] + '\n\n')


def helper(project):
    return '!' + ' '.join(shlex.quote(value) for value in
        [sys.executable, str(Path(__file__).resolve()), 'credential', '--project-id', project])


class Git:
    def __init__(self, root, project):
        self.root, self.project = Path(root).resolve(), project
        self.hooks = tempfile.TemporaryDirectory(prefix='studio-git-hooks-')
    def run(self, *args, check=True, input=None):
        environment = dict(os.environ)
        for name in list(environment):
            if name.startswith('GIT_'):
                del environment[name]
        environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
        command = ['git', '-c', f'core.hooksPath={self.hooks.name}', '-c', 'credential.helper=',
            '-c', 'credential.helper=' + helper(self.project), '-c', 'credential.useHttpPath=true',
            '-c', 'status.renames=false',
            '-c', 'protocol.file.allow=never', '-C', str(self.root), *args]
        result = subprocess.run(command, capture_output=True, env=environment, timeout=600, input=input)
        if check and result.returncode:
            raise ValueError('Git operation failed; changes remain local. Check authentication, conflicts, or remote updates.')
        return result
    def text(self, *args):
        return self.run(*args).stdout.decode('utf-8').strip()
    def close(self):
        self.hooks.cleanup()


def setup(project, destination):
    config = operation(project, 'config')
    # Adapt the safe clone helper; no credentials enter the manifest.
    target = Path(destination).expanduser().absolute()
    git = Git(target.parent, project)
    def run(args, **kwargs):
        # clone_workspace adds safe hooks settings; our wrapper provides the
        # credential helper and disables ambient Git config.
        result = git.run(*args[1:])
        return type('Result', (), {'returncode': result.returncode, 'stdout': result.stdout.decode()})()
    try:
        output = clone(config, target, run)
    finally:
        git.close()
    # Reserve setup metadata locally; do not modify tracked .gitignore.
    with (target / '.git/info/exclude').open('a') as output_file:
        output_file.write(f'\n/.studio/\n/{skills_directory()}/\n/.impeccable/\n')
    local_git = Git(target, project)
    try:
        provision(target, project, config, operation, local_git)
    finally:
        local_git.close()
    skills = install_skills(target, config)
    local_git = Git(target, project)
    try:
        mapping = code_map(target, config, local_git, install=True)
    finally:
        local_git.close()
    return output | {'commands': config['commands'], 'runtime_requirements': config['runtime_requirements'], 'skills': skills, 'code_map': mapping}


def workspace(root, project):
    root = Path(root).resolve()
    config = operation(project, 'config')
    metadata = json.loads((root / '.studio/workspace.json').read_text())
    if metadata.get('source_type') != 'git_clone' or metadata.get('project_id') != project or metadata.get('repository') != config['repository']:
        raise ValueError('Not the authorized Git workspace. Clone into a new folder.')
    if not (root / '.git').is_dir() or (root / '.git').is_symlink():
        raise ValueError('Only a standalone Git clone is supported.')
    if (root / '.studio').is_symlink():
        raise ValueError('Studio metadata must stay inside the workspace.')
    git = Git(root, project)
    try:
        # Git for Windows prints forward slashes; pathlib uses native separators.
        # Resolve real absolute paths rather than weakening this identity check
        # with string replacement, prefix matching or unconditional case folding.
        reported_root = Path(git.text('rev-parse', '--show-toplevel'))
        if not reported_root.is_absolute() or reported_root.resolve(strict=True) != root:
            raise ValueError('Workspace root mismatch.')
        if git.text('remote', 'get-url', 'origin') != f'https://github.com/{config["repository"]}.git':
            raise ValueError('Remote differs from Studio configuration.')
        push_url = git.text('remote', 'get-url', '--push', 'origin')
        if push_url != f'https://github.com/{config["repository"]}.git' or git.text('branch', '--show-current') != config['base_branch']:
            raise ValueError('Wrong remote or working branch.')
        return root, config, git
    except Exception:
        git.close()
        raise


def state_path(root):
    return root / '.studio/submission.json'


def save_state(root, value):
    path = state_path(root)
    if path.is_symlink():
        raise ValueError('Unsafe submission metadata.')
    temporary = path.with_suffix('.tmp')
    with temporary.open('x') as output:
        json.dump(value, output)
    temporary.chmod(0o600)
    os.replace(temporary, path)


def load_state(root):
    path = state_path(root)
    return json.loads(path.read_text()) if path.exists() else None


def fetch(git, config):
    git.run('fetch', '--no-tags', '--no-recurse-submodules', 'origin',
            f'refs/heads/{config["base_branch"]}:refs/remotes/origin/{config["base_branch"]}')
    return git.text('rev-parse', f'refs/remotes/origin/{config["base_branch"]}')


def conflicts(git):
    return git.text('diff', '--name-only', '--diff-filter=U').splitlines()


def changed_paths(git):
    result = git.run('status', '--porcelain=v1', '-z', '--untracked-files=all').stdout
    # Renames are disabled for deterministic staging and review of both paths.
    if any(record[:1] in (b'R', b'C') or record[1:2] in (b'R', b'C') for record in result.split(b'\0') if record):
        raise ValueError('Stage renames as separate additions and deletions before retrying.')
    return [record[3:].decode('utf-8') for record in result.split(b'\0') if record]


def verify_files(root, paths):
    for name in paths:
        path = root / name
        if excluded(name) or name.startswith('.github/'):
            raise ValueError('Submission contains a secret, local-only, workflow, or generated path. Review excluded files.')
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root and root in parent.parents):
            raise ValueError('Links are not supported for submission.')
        if path.exists():
            # Binary assets are supported; scan text files for known secret forms.
            with path.open('rb') as content:
                while chunk := content.read(1024 * 1024):
                    if SECRET.search(chunk.decode('utf-8', errors='ignore')):
                        raise ValueError('Possible secret found. Submission stopped.')


def stage(git, paths):
    git.run('add', '--pathspec-from-file=-', '--pathspec-file-nul',
            input=b''.join(name.encode('utf-8') + b'\0' for name in paths))


def execute(action, root, project, description=None, approved=False, checks_passed=False):
    root, config, git = workspace(root, project)
    lock = root / '.studio/git-operation.lock'
    locked = False
    try:
        try:
            lock.mkdir(mode=0o700)
        except FileExistsError:
            raise ValueError('Another Git operation is running, or a previous process left a lock. Inspect it before recovery.') from None
        locked = True
        if action == 'update' and not approved:
            raise ValueError('Updating local files requires an explicit Update workspace request.')
        merge = (root / '.git/MERGE_HEAD').exists()
        state = load_state(root)
        if action == 'cancel':
            if not approved or not state or not merge or not state.get('saved_commit'):
                raise ValueError('No plugin-owned merge to cancel.')
            if git.text('rev-parse', 'HEAD') != state['saved_commit']:
                raise ValueError('Merge ownership changed; manual review required.')
            git.run('merge', '--abort')
            save_state(root, state | {'phase': 'cancelled'})
            return {'status': 'cancelled', 'saved_commit': state['saved_commit']}
        if action == 'resolve':
            if not approved or not state or not merge or git.text('rev-parse', 'HEAD') != state.get('saved_commit'):
                raise ValueError('An approved plugin-owned conflict resolution is required.')
            paths = changed_paths(git)
            verify_files(root, paths)
            for name in conflicts(git):
                path = root / name
                if path.exists() and re.search(r'(?m)^(<<<<<<< |=======\s*$|>>>>>>> )', path.read_text(errors='replace')):
                    raise ValueError('Conflict markers remain; review both versions before resolving.')
            if paths:
                stage(git, paths)
            if conflicts(git):
                raise ValueError('Unresolved conflicts remain.')
            git.run('-c', 'user.name=Studio client', '-c', 'user.email=client@studio.abacusis.ca', 'commit', '--no-edit')
            save_state(root, state | {'phase': 'ready', 'review_commit': git.text('rev-parse', 'HEAD')})
            return {'status': 'ready_for_review', 'commit': git.text('rev-parse', 'HEAD')}
        # Fetch is always the first Git mutation, including every prepare/submit.
        remote = fetch(git, config)
        if action == 'update':
            if merge or any((root / '.git' / name).exists() for name in
                            ('rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'sequencer')):
                raise ValueError('Finish the existing Git operation before updating. No local files were updated.')
            if changed_paths(git):
                return {'status': 'local_changes', 'message': 'Local changes are preserved. Review and submit them, or choose how to preserve them before updating. Nothing was pushed.'}
            head = git.text('rev-parse', 'HEAD')
            ahead, behind = map(int, git.text('rev-list', '--left-right', '--count', 'HEAD...' + remote).split())
            if not behind:
                return {'status': 'already_current', 'ahead': ahead, 'behind': 0, 'commit': head,
                        'message': 'No newer commits on the configured client development branch. This does not verify parity with the live app.'}
            if ahead:
                return {'status': 'diverged', 'ahead': ahead, 'behind': behind,
                        'message': 'Local and remote commits differ. Use the reviewed Submit workflow to integrate them; Update made no local changes.'}
            if state and state.get('phase') not in ('submitted', 'cancelled'):
                raise ValueError('An unfinished submission needs review before updating. Local files were preserved.')
            paths = git.text('diff', '--name-only', head, remote).splitlines()
            # Recheck immediately before checkout; Git itself rejects clobbering
            # tracked/untracked work. Protect ignored local files too.
            if changed_paths(git) or git.text('rev-parse', 'HEAD') != head:
                raise ValueError('Workspace changed during Update. Stop and review before retrying.')
            result = git.run('merge', '--ff-only', '--no-autostash', '--no-overwrite-ignore', remote, check=False)
            if result.returncode:
                raise ValueError('Fast-forward update could not complete safely. Inspect the workspace; do not reset, stash or retry blindly.')
            if git.text('rev-parse', 'HEAD') != remote:
                raise ValueError('Update result changed unexpectedly. Inspect the workspace before continuing.')
            dependencies = {'package.json', 'package-lock.json', 'npm-shrinkwrap.json',
                            'pnpm-lock.yaml', 'yarn.lock', 'bun.lock', 'bun.lockb', 'requirements.txt', 'pyproject.toml'}
            return {'status': 'updated', 'previous_commit': head, 'commit': remote,
                    'changed_files': paths, 'dependencies_changed': any(Path(p).name in dependencies for p in paths),
                    'preview_restart_recommended': True, 'pushed': False,
                    'message': 'Updated from the client development branch. No dependencies installed, checks run, pushes or publishing performed.'}
        if action == 'record':
            if not state or not state.get('pushed_commit'):
                raise ValueError('No verified push awaiting Studio recording.')
            record = operation(project, 'record', commit=state['pushed_commit'])
            save_state(root, state | {'phase': 'submitted'})
            return {**record, 'status': 'submitted', 'commit': state['pushed_commit']}
        if action == 'status':
            counts = git.text('rev-list', '--left-right', '--count', 'HEAD...' + remote).split()
            return {'status': 'conflicts' if merge else 'ready', 'changed_files': changed_paths(git),
                    'ahead': int(counts[0]), 'behind': int(counts[1]), 'conflicts': conflicts(git)}
        if merge:
            return {'status': 'conflicts', 'conflicts': conflicts(git)}
        if action == 'check':
            if not approved or not state or state.get('phase') != 'ready' or changed_paths(git):
                raise ValueError('Prepare a clean reviewed submission before running checks.')
            current = git.text('rev-parse', 'HEAD')
            if current != state.get('review_commit'):
                raise ValueError('Workspace changed after review.')
            for name in ('test', 'build'):
                command = config['commands'].get(name)
                if command:
                    result = subprocess.run(command, shell=True, cwd=root, capture_output=True, timeout=600)
                    if result.returncode:
                        raise ValueError(f'The configured {name} check failed. Submission is blocked.')
            if changed_paths(git) or git.text('rev-parse', 'HEAD') != current:
                raise ValueError('Checks changed source files. Prepare and review again.')
            save_state(root, state | {'checked_commit': current, 'checked_commands': config['commands']})
            return {'status': 'checks_passed', 'commit': current}
        if action == 'prepare':
            if not approved or not description or not description.strip() or len(description) > 8000:
                raise ValueError('An approved change description is required.')
            paths = changed_paths(git)
            verify_files(root, paths)
            if paths:
                stage(git, paths)
                git.run('-c', 'user.name=Studio client', '-c', 'user.email=client@studio.abacusis.ca',
                        'commit', '-m', description.strip())
            saved = git.text('rev-parse', 'HEAD')
            state = {'saved_commit': saved, 'remote_commit': remote, 'description': description.strip(), 'phase': 'merging'}
            save_state(root, state)
            result = git.run('-c', 'user.name=Studio client', '-c', 'user.email=client@studio.abacusis.ca',
                             'merge', '--no-edit', '-m', description.strip(), remote, check=False)
            if result.returncode:
                return {'status': 'conflicts' if conflicts(git) else 'merge_failed', 'conflicts': conflicts(git), 'saved_commit': saved}
            review = git.text('rev-parse', 'HEAD')
            save_state(root, state | {'phase': 'ready', 'review_commit': review})
            return {'status': 'ready_for_review', 'commit': review,
                    'changed_files': git.text('diff', '--name-only', remote + '..HEAD').splitlines(), 'commands': config['commands']}
        if action != 'submit' or not approved or not state or state.get('phase') != 'ready':
            raise ValueError('Prepare, review, and run checks before confirming submission.')
        if state.get('checked_commit') != state.get('review_commit') or state.get('checked_commands') != config['commands']:
            raise ValueError('Run the configured checks for this exact reviewed commit first.')
        if remote != state['remote_commit']:
            return {'status': 'remote_changed', 'message': 'Prepare again, synchronize, and review before pushing.'}
        if changed_paths(git) or git.text('rev-parse', 'HEAD') != state['review_commit']:
            raise ValueError('Workspace changed after review. Prepare again.')
        if remote == state['review_commit']:
            return {'status': 'already_synced', 'message': 'No outgoing changes to submit.'}
        # Scan all outgoing commits, not only the final working tree.
        for sha in git.text('rev-list', remote + '..HEAD').splitlines():
            paths = git.text('diff-tree', '--no-commit-id', '--name-only', '-r', '--root', sha).splitlines()
            verify_files(root, paths)
            for name in paths:
                content = git.run('show', sha + ':' + name, check=False)
                if content.returncode == 0 and SECRET.search(content.stdout.decode('utf-8', errors='ignore')):
                    raise ValueError('Possible secret in outgoing history. Push stopped.')
        git.run('push', '--no-follow-tags', 'origin', 'HEAD:refs/heads/' + config['base_branch'])
        head = git.text('rev-parse', 'HEAD')
        if fetch(git, config) != head:
            raise ValueError('Remote changed after push; verify the submission before retrying.')
        state = state | {'pushed_commit': head, 'phase': 'pushed'}
        save_state(root, state)
        try:
            record = operation(project, 'record', commit=head)
        except Exception:
            return {'status': 'pushed_tracking_failed', 'commit': head,
                    'commit_url': f'https://github.com/{config["repository"]}/commit/{head}'}
        save_state(root, state | {'phase': 'submitted'})
        return {**record, 'status': 'submitted', 'commit': head}
    finally:
        git.close()
        if locked:
            lock.rmdir()


def migrate(action, directory, project, review_id=None, approved=False):
    if action == 'migration-apply' and (not approved or not review_id or not re.fullmatch(r'[a-f0-9-]{36}', review_id)):
        raise ValueError('Review the exact migration and approve it first.')
    root, config, git = workspace(directory, project)
    try:
        remote = fetch(git, config)
        if git.text('rev-parse', 'HEAD') != remote or any(path.startswith('supabase/migrations/') for path in changed_paths(git)):
            raise ValueError('Synchronize and submit migration changes before requesting sandbox migrations. Studio runs committed sandbox files only.')
        result = operation(project, 'migration_apply', review_id=review_id, approved=True) if action == 'migration-apply' else operation(project, 'migration_preview')
        if result.get('commit') != remote:
            raise ValueError('The sandbox branch changed. Refresh and review the migration again.')
        return result
    finally:
        git.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['browser-install', 'browser-verify', 'code-map', 'knowledge-search', 'knowledge-get', 'connection-status', 'list-apps', 'workspace-config', 'install', 'connect', 'disconnect', 'setup', 'migration-preview', 'migration-apply', 'publish-preview', 'publish', 'preview-config', 'preview', 'credential', 'status', 'update', 'prepare', 'resolve', 'check', 'submit', 'record', 'cancel'])
    parser.add_argument('credential_operation', nargs='?', choices=['get', 'store', 'erase'])
    parser.add_argument('--project-id')
    parser.add_argument('--query')
    parser.add_argument('--knowledge-id')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--workspace')
    parser.add_argument('--url')
    parser.add_argument('--destination')
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--review-id')
    args = parser.parse_args()
    try:
        if args.project_id and not re.fullmatch(r'[0-9a-f-]{36}', args.project_id):
            raise ValueError('Invalid Studio app ID.')
        if not args.project_id and args.action not in ('connect', 'disconnect', 'connection-status', 'list-apps'):
            raise ValueError('A Studio app ID is required.')
        ensure_helper_runtime(Path(__file__).resolve(), sys.argv[1:])
        # Git appends get/store/erase to the configured helper command.
        if args.action == 'credential':
            if args.credential_operation in ('store', 'erase'):
                return 0 # Never store the temporary GitHub token locally.
            credential(args.project_id)
            return 0
        if args.action in ('browser-install', 'browser-verify'):
            if not args.approved or not args.workspace:
                raise ValueError('Browser installation/capture requires an authorized workspace and explicit approval.')
            root, config, local_git = workspace(args.workspace, args.project_id)
            try:
                if args.action == 'browser-install':
                    browser_verification.runtime(install=True)
                    result = {'status': 'installed', 'runtime_version': browser_verification.VERSION}
                else:
                    raw = sys.stdin.read(20001)
                    if len(raw) > 20000: raise ValueError('Browser plan is too large.')
                    result = browser_verification.verify(root, args.url, json.loads(raw), local_git, approved=True, sandbox_services=config.get('sandbox_services', []))
            finally:
                local_git.close()
        elif args.action == 'code-map':
            if not args.workspace:
                raise ValueError('An authorized workspace is required.')
            root, config, local_git = workspace(args.workspace, args.project_id)
            try:
                result = code_map(root, config, local_git, query=args.query, install=args.approved)
            finally:
                local_git.close()
        elif args.action == 'connection-status':
            result = connection_status()
        elif args.action == 'list-apps':
            if args.query and len(args.query) > 160:
                raise ValueError('App search must be under 161 characters.')
            result = mcp_call('list_projects', {'query': args.query} if args.query else {})
        elif args.action == 'knowledge-search':
            if (args.query and len(args.query) > 300) or not 0 <= args.offset <= 10000:
                raise ValueError('Use a query up to 300 characters and offset from 0 to 10000.')
            result = mcp_call('search_app_knowledge', {'project_id': args.project_id, 'query': args.query or '', 'offset': args.offset})
        elif args.action == 'knowledge-get':
            if not args.knowledge_id or not re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', args.knowledge_id):
                raise ValueError('A knowledge record ID returned by Studio is required.')
            result = mcp_call('get_app_knowledge', {'project_id': args.project_id, 'knowledge_id': args.knowledge_id})
        elif args.action == 'workspace-config':
            result = mcp_call('get_workspace_config', {'project_id': args.project_id})
        elif args.action == 'connect':
            result = connect(args.project_id)
        elif args.action == 'disconnect':
            result = disconnect(args.project_id)
        elif args.action == 'setup':
            if not args.approved or not args.destination:
                raise ValueError('A confirmed new destination is required.')
            result = setup(args.project_id, args.destination)
        elif args.action in ('migration-preview', 'migration-apply') and args.workspace:
            result = migrate(args.action, args.workspace, args.project_id, args.review_id, args.approved)
        elif args.action in ('publish-preview', 'publish') and args.workspace:
            root, config, git = workspace(args.workspace, args.project_id)
            try:
                remote = fetch(git, config)
                if changed_paths(git) or git.text('rev-parse', 'HEAD') != remote:
                    raise ValueError('Submit and synchronize local changes before requesting publish.')
                if args.action == 'publish':
                    if not args.approved:
                        raise ValueError('Review and confirm the publish request first.')
                    body = json.loads(sys.stdin.read(20000))
                    if not isinstance(body, dict) or set(body) != {'title', 'description', 'expected_head', 'expected_base'}:
                        raise ValueError('Invalid publish approval payload.')
                    result = operation(args.project_id, 'publish', approved=True, **body)
                else:
                    result = operation(args.project_id, 'publish_preview')
            finally:
                git.close()
        elif args.action == 'install' and args.workspace:
            if not args.approved:
                raise ValueError('Dependency installation must be approved after manifest review.')
            from runtime_environment import environment, launch_argv
            import shlex
            root, config, git = workspace(args.workspace, args.project_id)
            git.close()
            command = config.get('commands', {}).get('install', '')
            if not command or re.search(r'[;&|<>`\n\r\x00]', command) or '$(' in command:
                raise ValueError('Configure a direct install command in Studio.')
            runtime_env = environment(config)
            completed = subprocess.run(launch_argv(shlex.split(command), runtime_env), cwd=root, env=runtime_env, stdout=sys.stderr, stderr=sys.stderr)
            if completed.returncode:
                raise ValueError('The approved dependency installation failed.')
            result = {'status': 'installed'}
        elif args.action in ('preview-config', 'preview') and args.workspace:
            root, config, git = workspace(args.workspace, args.project_id)
            try:
                provision(root, args.project_id, config, operation, git)
            finally:
                git.close()
            if args.action == 'preview':
                install_skills(root, config)
                if not args.approved:
                    raise ValueError('Local preview execution must be approved.')
                def fresh_config(project, action):
                    current = operation(project, action)
                    local_git = Git(root, project)
                    try:
                        provision(root, project, current, operation, local_git)
                    finally:
                        local_git.close()
                    return current
                result = supervise(root, args.project_id, fresh_config)
            else:
                installed_skills = install_skills(root, config)
                argv, entry = refresh_launch(root, config)
                result = {'status': 'launch_updated', 'configuration': entry, 'command': config['commands']['start'], 'skills': installed_skills}
        elif args.workspace:
            description = json.loads(sys.stdin.read(20000)).get('description') if args.action == 'prepare' else None
            result = execute(args.action, args.workspace, args.project_id, description, args.approved)
        else:
            raise ValueError('A Studio workspace is required.')
        print(json.dumps(result))
        return 0
    except Exception as error:
        # Never serialize HTTP/subprocess exceptions, which may contain credentials.
        message = str(error) if type(error) is ValueError else ('A required command or file could not be found. Check the selected runtime, configured command and workspace files.' if isinstance(error, FileNotFoundError) else 'Operation failed. Check Studio sign-in, Git, OS credential storage, and repository access.')
        print(json.dumps({'status': 'blocked', 'message': message}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
