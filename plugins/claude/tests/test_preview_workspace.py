import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import preview_workspace as preview


class PreviewTests(unittest.TestCase):
    def test_npm_separator_before_generated_port_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'package.json').write_text(json.dumps({'scripts': {'dev': 'vite'}}))
            result = preview.isolate_vite_port(root, {'commands': {'start': 'npm run dev'}})
            self.assertTrue(result['commands']['start'].startswith('npm run dev -- --port'))

    def test_unchanged_failure_does_not_spawn_twice_or_expose_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.studio').mkdir()
            def spawn(argv, **kwargs):
                kwargs['stdout'].write('Missing script: dev; PRIVATE_VALUE\n')
                kwargs['stdout'].flush()
                return type('Process', (), {'poll': lambda self: 1})()
            with patch.object(preview.subprocess, 'Popen', side_effect=spawn) as popen:
                with self.assertRaisesRegex(ValueError, 'start script is missing') as error:
                    preview.supervise(root, 'app', lambda *args: {'commands': {'start': 'npm run dev'}})
                self.assertEqual(popen.call_count, 1)
                self.assertNotIn('PRIVATE_VALUE', str(error.exception))
                self.assertFalse((root / '.studio/preview-start.lock').exists())

    def test_vite_uses_fresh_strict_port_without_changing_studio_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'package.json').write_text(json.dumps({'scripts': {'dev': 'vite dev'}}))
            original = {'commands': {'start': 'bun run dev --host 127.0.0.1'}}
            selected = preview.isolate_vite_port(root, original)
            self.assertIn('--strictPort', selected['commands']['start'])
            self.assertIn('--port', selected['commands']['start'])
            self.assertNotIn('--port', original['commands']['start'])

    def test_stale_launch_is_updated_from_fresh_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.claude').mkdir()
            path = root / '.claude/launch.json'
            path.write_text(json.dumps({'version': '0.0.1', 'configurations': [
                {'name': 'Old preview', 'runtimeExecutable': 'bun', 'runtimeArgs': ['run', 'dev'], 'port': 5174}]}))
            argv, entry = preview.refresh_launch(root, {'commands': {'start': 'bun run dev:local'}})
            self.assertEqual(argv, ['bun', 'run', 'dev:local'])
            self.assertEqual(entry['port'], 5174)
            self.assertEqual(json.loads(path.read_text())['configurations'][0]['runtimeArgs'], ['run', 'dev:local'])

    def test_unrelated_launches_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.claude').mkdir()
            path = root / '.claude/launch.json'
            original = [{'name': 'API'}, {'name': 'Docs'}]
            path.write_text(json.dumps({'configurations': original}))
            preview.refresh_launch(root, {'commands': {'start': 'bun run dev:local'}})
            self.assertEqual(json.loads(path.read_text())['configurations'][:2], original)

    def test_shell_syntax_is_not_guessed_or_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                preview.refresh_launch(Path(directory), {'commands': {'start': 'bun run dev; other'}})

    def test_failure_refreshes_configuration_once_without_editing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.studio').mkdir()
            source = root / 'app.txt'
            source.write_text('untouched')
            commands = iter(['bun run dev', 'bun run dev:local'])
            loader_calls, started = [], []
            def loader(project, action):
                loader_calls.append((project, action))
                return {'commands': {'start': next(commands)}}
            def spawn(argv, **kwargs):
                started.append(argv)
                kwargs['stdout'].write('Local: http://127.0.0.1:5174/\n')
                kwargs['stdout'].flush()
                return type('Process', (), {'pid': 123, 'poll': lambda self: 1 if len(started) == 1 else None})()
            class Response:
                status = 200
                def read(self, size): return b'<html>Preview</html>'
                def __enter__(self): return self
                def __exit__(self, *args): pass
            opener = type('Opener', (), {'open': lambda self, *args, **kwargs: Response()})()
            with patch.object(preview.subprocess, 'Popen', side_effect=spawn), patch.object(preview.urllib.request, 'build_opener', return_value=opener):
                result = preview.supervise(root, 'app', loader, observation=0)
            self.assertEqual(started, [['bun', 'run', 'dev'], ['bun', 'run', 'dev:local']])
            self.assertEqual(len(loader_calls), 2)
            self.assertEqual(result['url'], 'http://127.0.0.1:5174/')
            self.assertEqual(source.read_text(), 'untouched')


if __name__ == '__main__':
    unittest.main()
