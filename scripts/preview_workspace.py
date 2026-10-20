"""Refresh Studio's launch configuration; supervise a confirmed preview startup."""
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
import urllib.request
import os
import sys
import socket
from runtime_environment import environment, launch_argv
from plugin_runtime import launch_path


def isolate_vite_port(root, config):
    """Known Vite scripts get a fresh loopback port; never kill other servers."""
    manifest = root / 'package.json'
    if not manifest.is_file():
        return config
    argv = shlex.split(config.get('commands', {}).get('start', ''))
    if len(argv) < 3 or argv[0] not in ('bun', 'npm', 'pnpm') or argv[1] != 'run':
        return config
    script = json.loads(manifest.read_text()).get('scripts', {}).get(argv[2], '')
    if not re.match(r'^vite(?:\s|$)', script) or '--port' in argv:
        return config
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    # strictPort makes a race fail rather than silently move to another app's URL.
    if argv[0] == 'npm' and '--' not in argv[3:]:
        argv.insert(3, '--')
    config = {**config, 'commands': {**config['commands'], 'start': shlex.join([*argv, '--port', str(port), '--strictPort'])}}
    return config


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def refresh_launch(root, config):
    root = Path(root).resolve()
    config = isolate_vite_port(root, config)
    command = config.get('commands', {}).get('start')
    if not isinstance(command, str) or not command.strip() or any(c in command for c in '\n\r\x00'):
        raise ValueError('Studio has no valid preview start command.')
    # Commands are Studio-managed, but launch.json needs an executable and argv,
    # not an arbitrary shell program. Do not guess how to translate shell syntax.
    if re.search(r'[;&|<>`]', command) or '$(' in command:
        raise ValueError('Configure a direct executable start command for managed previews.')
    argv = shlex.split(command)
    if not argv:
        raise ValueError('Missing preview executable.')
    directory = launch_path(root).parent
    if directory.is_symlink():
        raise ValueError('Local launch configuration must stay inside the workspace.')
    directory.mkdir(exist_ok=True)
    path = launch_path(root)
    if path.is_symlink():
        raise ValueError('Unsafe launch configuration.')
    document = json.loads(path.read_text()) if path.exists() else {'version': '0.0.1', 'configurations': []}
    configurations = document.get('configurations')
    if not isinstance(configurations, list):
        raise ValueError('Invalid existing launch configuration; nothing overwritten.')
    # Preserve other launches. Adopt the only existing launch (the earlier setup
    # generated one); otherwise touch only our stable managed entry.
    matching = next((i for i, row in enumerate(configurations) if row.get('name') == 'Studio preview'), None)
    if matching is None and len(configurations) == 1:
        matching = 0
    entry = {'name': 'Studio preview', 'runtimeExecutable': argv[0], 'runtimeArgs': argv[1:], 'port': 5173}
    if '--port' in argv:
        entry['port'] = int(argv[argv.index('--port') + 1])
    runtime_env = environment(config)
    if os.name == 'nt':
        resolved = launch_argv(argv, runtime_env)
        entry['runtimeExecutable'], entry['runtimeArgs'] = resolved[0], resolved[1:]
    if runtime_env.get('PATH') != os.environ.get('PATH'):
        import shutil
        executable = shutil.which(argv[0], path=runtime_env['PATH'])
        if not executable:
            raise ValueError('The configured preview executable is not installed.')
        node_version = subprocess.run(['node', '--version'], env=runtime_env, capture_output=True, text=True, check=True).stdout.strip().split('.')[0][1:]
        entry['runtimeExecutable'] = sys.executable
        entry['runtimeArgs'] = [str(Path(__file__).with_name('runtime_environment.py')), node_version, executable, *argv[1:]]
    if matching is not None:
        previous = configurations[matching]
        entry = {**previous, **entry, 'port': entry['port'] if '--port' in argv else previous.get('port', 5173)}
        configurations[matching] = entry
    else:
        configurations.append(entry)
    temporary = path.with_suffix('.studio.tmp')
    with temporary.open('x') as output:
        json.dump(document, output, indent=2)
    temporary.chmod(0o600)
    temporary.replace(path)
    return argv, entry


def supervise(root, project, config_loader, observation=25, timeout=60):
    root = Path(root).resolve()
    lock = root / '.studio/preview-start.lock'
    try:
        lock.mkdir(mode=0o700)
    except FileExistsError:
        raise ValueError('A preview startup is already running. Do not start another.') from None
    try:
        previous_command = None
        failure = 'No healthy loopback preview was observed. Check the configured command and local preview log privately.'
        for attempt in range(2):
            # Never reuse cached command output or old launch.json.
            config = config_loader(project, 'config')
            command = config.get('commands', {}).get('start')
            if attempt and command == previous_command:
                raise ValueError('Preview stopped; Studio start settings are unchanged. ' + failure + ' Local changes are preserved; no identical retry was run.')
            previous_command = command
            config = isolate_vite_port(root, config)
            argv, entry = refresh_launch(root, config)
            log_path = root / '.studio/preview.log'
            if log_path.is_symlink():
                raise ValueError('Unsafe preview log path.')
            started = time.monotonic()
            healthy_since, url = None, None
            with log_path.open('w') as log:
                runtime_env = environment(config)
                process = subprocess.Popen(launch_argv(argv, runtime_env), cwd=root, stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=subprocess.STDOUT, env=runtime_env,
                                           **({'start_new_session': True} if os.name != 'nt' else
                                              {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS}))
                while process.poll() is None and time.monotonic() - started < timeout:
                    text = log_path.read_text(errors='replace')[-65536:]
                    found = re.search(r'https?://(?:127\.0\.0\.1|localhost|\[::1\]):\d+(?:/[^\s\x1b]*)?', text)
                    if found:
                        url = found.group(0)
                        try:
                            with urllib.request.build_opener(NoRedirect).open(url, timeout=2) as response:
                                body = response.read(1024 * 1024)
                                healthy = response.status == 200 and bool(body.strip())
                        except Exception:
                            healthy = False
                        healthy_since = (healthy_since or time.monotonic()) if healthy else None
                        if healthy_since and time.monotonic() - healthy_since >= observation:
                            port = int(re.search(r':(\d+)', url).group(1))
                            # Persist the actual port, not the initial preferred port.
                            launch = json.loads(launch_path(root).read_text())
                            for item in launch['configurations']:
                                if item.get('name') == entry['name']:
                                    item['port'] = port
                            launch_path(root).write_text(json.dumps(launch, indent=2))
                            return {'status': 'running', 'url': url, 'pid': process.pid,
                                    'command': config['commands']['start'], 'observed_seconds': observation,
                                    'browser_render_check_required': True}
                    time.sleep(1)
                if process.poll() is None:
                    process.terminate() # Only the exact child started by this attempt.
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            # One fresh-config retry only. No source edits or invented fallback.
            text = log_path.read_text(errors='replace')[-65536:].lower()
            if 'eaddrinuse' in text or 'already in use' in text:
                failure = 'The preview port is occupied. Check this session’s owned preview; do not stop unrelated servers.'
            elif 'missing script' in text:
                failure = 'The configured start script is missing. An administrator must correct Studio’s start command.'
            elif 'cannot find module' in text or 'command not found' in text:
                failure = 'A required executable or dependency is missing. Check the approved install and runtime before retrying.'
        raise ValueError('Preview failed after refreshed settings. ' + failure + ' Local changes are preserved.')
    finally:
        lock.rmdir()
