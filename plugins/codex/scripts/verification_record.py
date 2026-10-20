"""Record one approved command against current source; never certify readiness."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
import uuid

LIMIT = 256 * 1024 * 1024
PRIVATE = re.compile(r'(^|/)(\.env(?:\..*)?|\.git|\.studio|node_modules|vendor|venv|__pycache__|secrets|credentials)(/|$)|\.(?:pem|key)$', re.I)
SECRET = re.compile(r'\b(?:sb_secret_|sbp_|ghp_|github_pat_)[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY|(?:password|api[_-]?key|access[_-]?token)\s*=', re.I)


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, timeout=20)
    if result.returncode:
        raise ValueError('Git inspection failed; use an existing application checkout.')
    return result.stdout


def workspace(value):
    raw = Path(value).absolute()
    if any(p.is_symlink() for p in (raw, *raw.parents)):
        raise ValueError('Workspace symlinks need review.')
    root = raw.resolve(strict=True)
    if Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != root:
        raise ValueError('Use the application Git root.')
    return root


def fingerprint(root):
    names = git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').decode().split('\0')
    digest, size = hashlib.sha256(), 0
    for name in sorted(set(filter(None, names))):
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe source path.')
        if PRIVATE.search(name):
            continue
        source = root / path
        if any(p.is_symlink() for p in (source, *source.parents)):
            raise ValueError('Source symlinks need review.')
        digest.update(name.encode() + b'\0')
        if not source.exists():
            digest.update(b'deleted\0')
            continue
        if not source.is_file():
            raise ValueError('Source must be a regular file.')
        digest.update(str(source.stat().st_mode & 0o111).encode() + b'\0')
        with source.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                size += len(chunk)
                if size > LIMIT:
                    raise ValueError('Source fingerprint size limit exceeded.')
                digest.update(chunk)
        digest.update(b'\0')
    return digest.hexdigest()


def evidence_dir(root):
    folder = root / '.studio' / 'verification'
    for path in (folder.parent, folder):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError('Verification folder must be a real directory.')
    ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '--quiet', '--no-index', '.studio/verification/probe.json'], capture_output=True)
    tracked = git(root, 'ls-files', '--', '.studio').strip()
    if ignored.returncode != 0 or tracked:
        raise ValueError('Exclude .studio/ from Git and remove tracked setup files before recording checks; no Git settings changed.')
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    return folder


def run_check(root, criteria, command, approved=False, timeout=300):
    if not approved:
        raise ValueError('Command execution requires existing approval and --approved.')
    if not criteria or len(criteria) > 20 or any(not re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}', c) for c in criteria):
        raise ValueError('Provide up to twenty criterion IDs.')
    if not command or len(command) > 100 or any(not isinstance(c, str) or not c or len(c) > 4000 or SECRET.search(c) for c in command) or sum(map(len, command)) > 16000:
        raise ValueError('Use an exact argument list without literal credentials.')
    if not 1 <= timeout <= 600:
        raise ValueError('Use a timeout between one and 600 seconds.')
    root = workspace(root)
    before = fingerprint(root)
    folder = evidence_dir(root)
    identities = [(p.stat().st_dev, p.stat().st_ino) for p in (root, folder.parent, folder)]
    started = time.time()
    # Only ordinary runtime variables. No ambient Studio/cloud token variables.
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'USERPROFILE', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'TMPDIR', 'LANG', 'LC_ALL', 'PATHEXT')}
    status, code = 'failed', None
    with tempfile.TemporaryFile() as output:
        try:
            process = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT, start_new_session=os.name != 'nt')
            try:
                code = process.wait(timeout=timeout)
                status = 'passed' if code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait()
                status = 'timed_out'
        except OSError:
            status = 'not_run'
        output.seek(0)
        output_digest = hashlib.sha256()
        for chunk in iter(lambda: output.read(1024 * 1024), b''):
            output_digest.update(chunk)
    try:
        after = fingerprint(root)
    except ValueError:
        after = None
    record = {'schema_version': 1, 'id': str(uuid.uuid4()), 'workspace': str(root),
              'criteria': list(criteria), 'command': command, 'exit_code': code,
              'execution_status': status, 'status': 'stale' if before != after else status,
              'source_before': before, 'source_after': after, 'started_at': started,
              'finished_at': time.time(), 'output_sha256': output_digest.hexdigest(),
              'scope': 'command_only', 'ready_to_preview': False}
    target = folder / (record['id'] + '.json')
    # New private receipt only; raw command output is deliberately not retained.
    evidence_dir(root)  # The approved child may have changed setup paths/ignores.
    if identities != [(p.stat().st_dev, p.stat().st_ino) for p in (root, folder.parent, folder)]:
        raise ValueError('Evidence directories changed during the check; no receipt written.')
    if os.name != 'nt':
        handles = []
        try:
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            handles.append(os.open(root, flags))
            handles.append(os.open('.studio', flags, dir_fd=handles[-1]))
            handles.append(os.open('verification', flags, dir_fd=handles[-1]))
            if identities != [(os.fstat(h).st_dev, os.fstat(h).st_ino) for h in handles]:
                raise ValueError('Evidence directories changed; no receipt written.')
            fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=handles[-1])
        finally:
            for handle in reversed(handles): os.close(handle)
    else:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    return {**record, 'record_path': str(target)}


def inspect_record(root, path):
    root = workspace(root)
    path = Path(path).absolute()
    if path.parent != root / '.studio' / 'verification' or path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Read only a local verification receipt in this workspace.')
    if path.stat().st_size > 100_000:
        raise ValueError('Invalid verification receipt size.')
    record = json.loads(path.read_text())
    if record.get('schema_version') != 1 or record.get('workspace') != str(root):
        raise ValueError('Receipt belongs to another workspace or schema.')
    current = fingerprint(root)
    valid = record.get('source_before') == record.get('source_after') == current
    status = record['execution_status'] if valid else 'stale'
    return {'status': status, 'criteria': record['criteria'], 'command': record['command'],
            'record_path': str(path), 'scope': 'command_only', 'ready_to_preview': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('run', 'inspect'))
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--criterion', action='append', default=[])
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--record')
    # Split the command explicitly so helper options never become child options.
    import sys
    args_list = sys.argv[1:]
    split = args_list.index('--') if '--' in args_list else len(args_list)
    args = parser.parse_args(args_list[:split])
    try:
        result = run_check(args.workspace, args.criterion, args_list[split + 1:], args.approved, args.timeout) if args.action == 'run' else inspect_record(args.workspace, args.record or '')
        print(json.dumps(result))
        sys.exit(0 if result['status'] == 'passed' else 1)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({'status': 'not_verified', 'message': str(error)}))
        sys.exit(2)
