"""Explicit, read-only local diagnostics. No credentials, network or repairs."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil


def report(workspace=None, plugin=None):
    plugin = Path(plugin or Path(__file__).resolve().parents[1])
    checks = []

    def add(code, ok, action):
        checks.append({'code': code, 'status': 'ok' if ok else 'needs_attention',
                       'next_step': None if ok else action})

    manifest = next((plugin / name for name in ('.codex-plugin/plugin.json',
                    '.claude-plugin/plugin.json') if (plugin / name).is_file()), None)
    version = None
    try:
        version = json.loads(manifest.read_text()).get('version') if manifest else None
    except (OSError, ValueError):
        pass
    add('package_manifest', bool(version), 'Update the plugin through your host plugin manager.')
    for executable in ('git', 'node'):
        add(executable, bool(shutil.which(executable)), 'Install the required runtime under Setup approval.')
    add('keyring_module', importlib.util.find_spec('keyring') is not None,
        'Use the approved Studio Python environment; do not install globally or paste credentials.')
    if workspace:
        root = Path(workspace).absolute()
        safe = root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents))
        studio = root / '.studio'
        marker = studio / 'workspace.json'
        add('workspace_path', safe, 'Select the actual local workspace, without symlinked folders.')
        if safe:
            add('workspace_marker', studio.is_dir() and not studio.is_symlink()
                and marker.is_file() and not marker.is_symlink(),
                'Resume Setup for this folder. Preserve existing files; do not delete or adopt an unknown .studio folder.')
            add('git_checkout', (root / '.git').exists(),
                'Use the authorized client Git checkout; a source snapshot cannot be submitted.')
            if (root / 'package.json').is_file():
                add('dependencies', (root / 'node_modules').is_dir(),
                'For a Node app, run the configured install through approved Setup; other runtimes may not need node_modules.')
    return {'status': 'needs_attention' if any(c['status'] != 'ok' for c in checks) else 'ok',
            'package_version_on_disk': version, 'loaded_session_version': 'not_verified',
            'connection': 'not_checked', 'preview': 'not_checked',
            'checks': checks, 'changes_made': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace')
    args = parser.parse_args()
    print(json.dumps(report(args.workspace)))
