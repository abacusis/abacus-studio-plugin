"""Select an installed Studio-required Node runtime without changing global settings."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

WINDOWS = os.name == 'nt'


def launch_argv(argv, env):
    """Resolve Windows launchers without cmd.exe or shell interpretation."""
    if not argv:
        raise ValueError('The configured command is empty.')
    if not WINDOWS:
        return list(argv)
    executable = shutil.which(argv[0], path=env.get('PATH', ''))
    if not executable:
        raise ValueError('The configured command could not be found in the selected runtime PATH. Check the installed runtime and Studio command.')
    path = Path(executable)
    if path.suffix.lower() in ('.cmd', '.bat'):
        name = path.stem.lower()
        if name not in ('npm', 'npx'):
            raise ValueError('This Windows batch launcher is unsupported without a shell. Configure a direct executable command in Studio.')
        cli = path.parent / 'node_modules' / 'npm' / 'bin' / (name + '-cli.js')
        node = shutil.which('node', path=env.get('PATH', ''))
        if not node or not cli.is_file():
            raise ValueError('The Windows npm runtime is incomplete. Check Node and npm installation before retrying Setup.')
        return [node, str(cli), *argv[1:]]
    return [executable, *argv[1:]]


def environment(config):
    env = os.environ.copy()
    requirements = config.get('runtime_requirements', [])
    if isinstance(requirements, str):
        requirements = requirements.splitlines()
    node = next((str(value) for value in requirements if re.match(r'^node\b', str(value), re.I)), None)
    if not node:
        return env
    match = re.fullmatch(r'node\s+(\d+)(?:\.\d+(?:\.\d+)?)?', node.strip(), re.I)
    if not match:
        raise ValueError('Studio must specify a Node requirement such as node 22.')
    major = int(match.group(1))
    home = Path.home()
    candidates = [shutil.which('node')]
    candidates += list((home / '.nvm/versions/node').glob('v*/bin/node'))
    candidates += list((home / '.local/share/fnm/node-versions').glob('v*/installation/bin/node'))
    if os.environ.get('NVM_HOME'):
        candidates += list(Path(os.environ['NVM_HOME']).glob('v*/node.exe'))
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        try:
            version = subprocess.run([str(candidate), '--version'], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            continue
        if re.match(r'^v' + str(major) + r'\.', version):
            env['PATH'] = str(Path(candidate).parent) + os.pathsep + env.get('PATH', '')
            return env
    raise ValueError(f'Node {major} is required but not installed. Ask permission to install it; do not start with another version.')


if __name__ == '__main__':
    # Managed launches use this wrapper so child processes inherit the selected
    # runtime even when the desktop app was opened with a different shell PATH.
    major, executable, *arguments = sys.argv[1:]
    env = environment({'runtime_requirements': ['node ' + major]})
    try:
        raise SystemExit(subprocess.call(launch_argv([executable, *arguments], env), env=env))
    except (FileNotFoundError, ValueError):
        print('The configured preview command could not start. Check the selected runtime and command.', file=sys.stderr)
        raise SystemExit(1)
