import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from setup_health import report


class HealthTests(unittest.TestCase):
    def test_no_workspace_is_created_and_session_version_not_inferred(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / '.claude-plugin').mkdir()
            (root / '.claude-plugin/plugin.json').write_text(json.dumps({'version': '1.0'}))
            before = sorted(str(p) for p in root.rglob('*'))
            result = report(root / 'missing', root)
            self.assertEqual(before, sorted(str(p) for p in root.rglob('*')))
            self.assertEqual(result['package_version_on_disk'], '1.0')
            self.assertEqual(result['loaded_session_version'], 'not_verified')
            self.assertFalse(result['changes_made'])
            self.assertEqual(result['preview'], 'not_checked')

    def test_symlinked_studio_is_not_adopted_or_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / '.studio').symlink_to(root.parent, target_is_directory=True)
            result = report(root, root)
            marker = next(c for c in result['checks'] if c['code'] == 'workspace_marker')
            self.assertEqual(marker['status'], 'needs_attention')
            self.assertNotIn('dependencies', [c['code'] for c in result['checks']])


if __name__ == '__main__':
    unittest.main()
