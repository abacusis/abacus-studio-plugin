"""Native filesystem checks; Windows CI exercises Git-style slash/case variants."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import studio_git


class WorkspaceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'Client App'
        self.root.mkdir()
        (self.root / '.git').mkdir()
        (self.root / '.studio').mkdir()
        (self.root / '.studio/workspace.json').write_text(json.dumps({
            'source_type': 'git_clone', 'project_id': 'test', 'repository': 'example/client'}))
        self.reported = self.root.as_posix()
        self.remote = 'https://github.com/example/client.git'
        self.branch = 'sandbox'
        owner = self
        class Git:
            closed = False
            def __init__(self, *args): owner.git = self
            def text(self, *args):
                if args[0] == 'rev-parse': return owner.reported
                if args[0] == 'remote': return owner.remote
                return owner.branch
            def close(self): self.closed = True
        self.enterContext(patch.object(studio_git, 'Git', Git))
        self.enterContext(patch.object(studio_git, 'operation', return_value={
            'repository': 'example/client', 'base_branch': 'sandbox'}))

    def test_native_and_git_forward_slash_paths_match(self):
        for value in (str(self.root), self.root.as_posix(), str(self.root / '.')):
            self.reported = value
            root, _, git = studio_git.workspace(self.root, 'test')
            self.assertEqual(root, self.root)
            git.close()

    @unittest.skipUnless(os.name == 'nt', 'Requires native Windows path semantics')
    def test_windows_slashes_drive_case_and_directory_case_match(self):
        self.reported = self.root.as_posix().swapcase()
        root, _, git = studio_git.workspace(self.root, 'test')
        self.assertEqual(root, self.root)
        git.close()

    def test_other_root_is_rejected_and_git_closed(self):
        self.reported = str(self.root.parent)
        with self.assertRaisesRegex(ValueError, 'Workspace root mismatch'):
            studio_git.workspace(self.root, 'test')
        self.assertTrue(self.git.closed)

    def test_relative_root_is_rejected(self):
        self.reported = '.'
        with self.assertRaisesRegex(ValueError, 'Workspace root mismatch'):
            studio_git.workspace(self.root, 'test')

    def test_remote_and_branch_checks_are_preserved(self):
        self.remote = 'https://github.com/example/other.git'
        with self.assertRaisesRegex(ValueError, 'Remote differs'):
            studio_git.workspace(self.root, 'test')
        self.remote = 'https://github.com/example/client.git'
        self.branch = 'main'
        with self.assertRaisesRegex(ValueError, 'Wrong remote or working branch'):
            studio_git.workspace(self.root, 'test')
