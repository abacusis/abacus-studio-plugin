import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import runtime_environment as runtime
import preview_workspace as preview


class LauncherTests(unittest.TestCase):
    def test_npm_batch_becomes_node_cli_with_arguments_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='node installation ') as directory:
            root = Path(directory)
            cli = root / 'node_modules/npm/bin/npm-cli.js'
            cli.parent.mkdir(parents=True)
            cli.write_text('')
            def which(name, path):
                self.assertEqual(path, 'selected-runtime-path')
                return str(root / ('npm.CMD' if name == 'npm' else 'node.exe'))
            with patch.object(runtime, 'WINDOWS', True), patch.object(runtime.shutil, 'which', side_effect=which):
                result = runtime.launch_argv(['npm', 'run', 'dev', '--', '--host', '127.0.0.1'], {'PATH': 'selected-runtime-path'})
                self.assertEqual(result, [str(root / 'node.exe'), str(cli), 'run', 'dev', '--', '--host', '127.0.0.1'])

    def test_missing_command_is_actionable(self):
        with patch.object(runtime, 'WINDOWS', True), patch.object(runtime.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'could not be found'):
                runtime.launch_argv(['npm', 'ci'], {'PATH': ''})

    def test_unknown_batch_launcher_is_not_sent_to_shell(self):
        with patch.object(runtime, 'WINDOWS', True), patch.object(runtime.shutil, 'which', return_value='unknown.cmd'):
            with self.assertRaisesRegex(ValueError, 'unsupported without a shell'):
                runtime.launch_argv(['unknown'], {})

    @unittest.skipUnless(os.name == 'nt', 'Requires native Windows Node/npm')
    def test_real_windows_install_and_preview_launch(self):
        with tempfile.TemporaryDirectory(prefix='studio client app ') as directory:
            root = Path(directory)
            (root / '.studio').mkdir()
            (root / 'package.json').write_text(json.dumps({'name': 'studio-launch-test', 'version': '1.0.0',
                'scripts': {'dev': 'node server.js'}}))
            (root / 'package-lock.json').write_text(json.dumps({'name': 'studio-launch-test',
                'version': '1.0.0', 'lockfileVersion': 3, 'packages': {'': {'name': 'studio-launch-test', 'version': '1.0.0'}}}))
            (root / 'server.js').write_text('''const http = require('http');
const server = http.createServer((req,res) => res.end('<html>Windows preview</html>'));
server.listen(0,'127.0.0.1', () => console.log('http://127.0.0.1:' + server.address().port));
setTimeout(() => server.close(), 4000);
''')
            env = runtime.environment({'runtime_requirements': ['node 22']})
            installed = subprocess.run(runtime.launch_argv(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], env),
                cwd=root, env=env, capture_output=True, timeout=30)
            self.assertEqual(installed.returncode, 0, installed.stderr.decode(errors='replace'))
            _, entry = preview.refresh_launch(root, {'commands': {'start': 'npm run dev'}})
            self.assertTrue(entry['runtimeExecutable'].lower().endswith('node.exe'))
            self.assertTrue(entry['runtimeArgs'][0].endswith('npm-cli.js'))
            result = preview.supervise(root, 'test', lambda *args: {'commands': {'start': 'npm run dev'}}, observation=0, timeout=3)
            self.assertEqual(result['status'], 'running')
            with urllib.request.urlopen(result['url'], timeout=2) as response:
                self.assertIn(b'Windows preview', response.read())
            # Fixture server exits itself, including the npm-spawned child.
            time.sleep(5)


if __name__ == '__main__':
    unittest.main()
