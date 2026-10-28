import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import studio_git as module


class LocalGit:
    def __init__(self, root):
        self.root = root
        self.calls = []
        self.fail_fetch = False
    def run(self, *args, check=True, input=None):
        self.calls.append(args)
        if self.fail_fetch and args[0] == 'fetch':
            raise ValueError('Offline')
        result = subprocess.run(['git', '-C', str(self.root), *args], input=input, capture_output=True)
        if check and result.returncode:
            raise ValueError('Git failed')
        return result
    def text(self, *args):
        return self.run(*args).stdout.decode().strip()
    def close(self):
        pass


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.seed, self.remote, self.root = [self.base / name for name in ('seed', 'remote.git', 'client')]
        self.seed.mkdir()
        self.command('init', '-b', 'sandbox', root=self.seed)
        self.identity(self.seed)
        (self.seed / 'app.txt').write_text('Original title\n')
        self.command('add', '.', root=self.seed)
        self.command('commit', '-m', 'Initial', root=self.seed)
        self.command('clone', '--bare', str(self.seed), str(self.remote), root=self.base)
        self.command('clone', str(self.remote), str(self.root), root=self.base)
        self.identity(self.root)
        (self.root / '.studio').mkdir()
        with (self.root / '.git/info/exclude').open('a') as output:
            output.write('\n/.studio/\n')
        self.git = LocalGit(self.root)
        self.config = {'repository': 'example/client', 'base_branch': 'sandbox',
                       'commands': {'test': None, 'build': None}}
        self.patch_workspace = patch.object(module, 'workspace', return_value=(self.root, self.config, self.git))
        self.patch_workspace.start()
        self.addCleanup(self.patch_workspace.stop)
        self.patch_record = patch.object(module, 'operation', return_value={'status': 'recorded'})
        self.patch_record.start()
        self.addCleanup(self.patch_record.stop)
    def command(self, *args, root):
        return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout.decode().strip()
    def identity(self, root):
        self.command('config', 'user.name', 'Test', root=root)
        self.command('config', 'user.email', 'test@example.com', root=root)
    def run_action(self, action, **kwargs):
        return module.execute(action, self.root, 'test-app', **kwargs)
    def remote_edit(self):
        self.command('remote', 'add', 'origin', str(self.remote), root=self.seed)
        (self.seed / 'app.txt').write_text('Team title\n')
        self.command('add', '.', root=self.seed)
        self.command('commit', '-m', 'Team update', root=self.seed)
        self.command('push', 'origin', 'sandbox', root=self.seed)

    def test_fetch_failure_never_stages_or_commits(self):
        (self.root / 'app.txt').write_text('Client title\n')
        before = self.git.text('rev-parse', 'HEAD')
        self.git.calls.clear()
        self.git.fail_fetch = True
        with self.assertRaises(ValueError):
            self.run_action('prepare', description='Update title', approved=True)
        self.assertEqual(self.git.calls[0][0], 'fetch')
        self.assertFalse(any(call[0] in ('add', 'commit', 'merge') for call in self.git.calls))
        self.assertEqual(self.git.text('rev-parse', 'HEAD'), before)
        self.assertEqual((self.root / 'app.txt').read_text(), 'Client title\n')

    def test_update_fast_forwards_without_push_or_new_commit(self):
        self.remote_edit()
        result = self.run_action('update', approved=True)
        self.assertEqual(result['status'], 'updated')
        self.assertEqual((self.root / 'app.txt').read_text(), 'Team title\n')
        self.assertFalse(result['dependencies_changed'])
        self.assertFalse(result['pushed'])
        self.assertFalse(any(c[0] in ('push', 'add', 'commit', 'stash', 'reset') for c in self.git.calls))
        self.assertFalse((self.root / '.studio/git-operation.lock').exists())

    def test_update_dirty_workspace_is_preserved(self):
        self.remote_edit()
        (self.root / 'app.txt').write_text('Unfinished client work')
        before = self.git.text('rev-parse', 'HEAD')
        result = self.run_action('update', approved=True)
        self.assertEqual(result['status'], 'local_changes')
        self.assertEqual(self.git.text('rev-parse', 'HEAD'), before)
        self.assertEqual((self.root / 'app.txt').read_text(), 'Unfinished client work')

    def test_update_untracked_draft_is_preserved(self):
        (self.root / 'draft.md').write_text('Draft specification')
        self.assertEqual(self.run_action('update', approved=True)['status'], 'local_changes')
        self.assertEqual((self.root / 'draft.md').read_text(), 'Draft specification')

    def test_update_already_current_and_local_commits_ahead(self):
        self.assertEqual(self.run_action('update', approved=True)['status'], 'already_current')
        (self.root / 'local.txt').write_text('Local commit')
        self.command('add', 'local.txt', root=self.root)
        self.command('commit', '-m', 'Local only', root=self.root)
        result = self.run_action('update', approved=True)
        self.assertEqual(result['status'], 'already_current')
        self.assertEqual(result['ahead'], 1)

    def test_update_divergence_stops_without_merge(self):
        self.remote_edit()
        (self.root / 'local.txt').write_text('Local commit')
        self.command('add', 'local.txt', root=self.root)
        self.command('commit', '-m', 'Local only', root=self.root)
        before = self.git.text('rev-parse', 'HEAD')
        self.assertEqual(self.run_action('update', approved=True)['status'], 'diverged')
        self.assertEqual(self.git.text('rev-parse', 'HEAD'), before)
        self.assertFalse(any(c[0] == 'merge' for c in self.git.calls))

    def test_update_does_not_delete_existing_lock(self):
        lock = self.root / '.studio/git-operation.lock'
        lock.mkdir()
        with self.assertRaisesRegex(ValueError, 'Another Git operation'):
            self.run_action('update', approved=True)
        self.assertTrue(lock.is_dir())

    def test_update_requires_authorization_and_fetch_failure_preserves_head(self):
        with self.assertRaisesRegex(ValueError, 'explicit Update'):
            self.run_action('update')
        before = self.git.text('rev-parse', 'HEAD')
        self.git.fail_fetch = True
        with self.assertRaises(ValueError):
            self.run_action('update', approved=True)
        self.assertEqual(self.git.text('rev-parse', 'HEAD'), before)

    def test_update_protects_ignored_files_from_remote_collision(self):
        with (self.root / '.git/info/exclude').open('a') as output:
            output.write('\nlocal-only.txt\n')
        (self.root / 'local-only.txt').write_text('Private local file')
        self.command('remote', 'add', 'origin', str(self.remote), root=self.seed)
        (self.seed / 'local-only.txt').write_text('Remote version')
        self.command('add', '.', root=self.seed)
        self.command('commit', '-m', 'Add file', root=self.seed)
        self.command('push', 'origin', 'sandbox', root=self.seed)
        with self.assertRaisesRegex(ValueError, 'could not complete safely'):
            self.run_action('update', approved=True)
        self.assertEqual((self.root / 'local-only.txt').read_text(), 'Private local file')

    def test_update_blocks_unfinished_submission(self):
        self.remote_edit()
        module.save_state(self.root, {'phase': 'ready'})
        with self.assertRaisesRegex(ValueError, 'unfinished submission'):
            self.run_action('update', approved=True)

    def test_update_blocks_interrupted_rebase(self):
        (self.root / '.git/rebase-merge').mkdir()
        with self.assertRaisesRegex(ValueError, 'existing Git operation'):
            self.run_action('update', approved=True)

    def test_update_reports_dependency_changes_without_running_install(self):
        self.command('remote', 'add', 'origin', str(self.remote), root=self.seed)
        (self.seed / 'package.json').write_text('{"scripts":{"install":"exit 99"}}')
        self.command('add', '.', root=self.seed)
        self.command('commit', '-m', 'Manifest', root=self.seed)
        self.command('push', 'origin', 'sandbox', root=self.seed)
        result = self.run_action('update', approved=True)
        self.assertTrue(result['dependencies_changed'])

    def test_conflicts_pause_and_cancel_preserves_client_commit(self):
        self.remote_edit()
        (self.root / 'app.txt').write_text('Client title\n')
        result = self.run_action('prepare', description='Update title', approved=True)
        self.assertEqual(result['status'], 'conflicts')
        self.assertEqual(result['conflicts'], ['app.txt'])
        with self.assertRaises(ValueError):
            self.run_action('resolve', approved=True)
        self.run_action('cancel', approved=True)
        self.assertEqual(self.git.text('rev-parse', 'HEAD'), result['saved_commit'])
        self.assertEqual((self.root / 'app.txt').read_text(), 'Client title\n')

    def test_remote_changes_block_push_after_review(self):
        (self.root / 'app.txt').write_text('Client title\n')
        self.run_action('prepare', description='Update title', approved=True)
        self.run_action('check', approved=True)
        self.remote_edit()
        result = self.run_action('submit', approved=True)
        self.assertEqual(result['status'], 'remote_changed')
        self.assertFalse(any(call[0] == 'push' for call in self.git.calls))

    def test_submit_requires_checks_and_verifies_pushed_commit(self):
        (self.root / 'app.txt').write_text('Client title\n')
        self.run_action('prepare', description='Update title', approved=True)
        with self.assertRaises(ValueError):
            self.run_action('submit', approved=True)
        self.run_action('check', approved=True)
        result = self.run_action('submit', approved=True)
        self.assertEqual(result['commit'], self.command('rev-parse', 'sandbox', root=self.remote))

    def test_secret_files_block_before_commit(self):
        (self.root / '.env').write_text('TOKEN=example\n')
        before = self.git.text('rev-parse', 'HEAD')
        with self.assertRaises(ValueError):
            self.run_action('prepare', description='Update config', approved=True)
        self.assertEqual(self.git.text('rev-parse', 'HEAD'), before)

    def test_request_authorization_can_cover_prepare_check_and_push(self):
        (self.root / 'app.txt').write_text('Client title\n')
        self.run_action('status')
        self.run_action('prepare', description='Update title', approved=True)
        self.run_action('check', approved=True)
        result = self.run_action('submit', approved=True)
        self.assertEqual(result['commit'], self.command('rev-parse', 'sandbox', root=self.remote))
        self.assertEqual(len([call for call in self.git.calls if call[0] == 'push']), 1)

    def test_failed_configured_check_still_blocks_an_authorized_push(self):
        (self.root / 'app.txt').write_text('Client title\n')
        self.config['commands']['build'] = 'false'
        self.run_action('prepare', description='Update title', approved=True)
        with self.assertRaisesRegex(ValueError, 'configured build check failed'):
            self.run_action('check', approved=True)
        with self.assertRaises(ValueError):
            self.run_action('submit', approved=True)
        self.assertFalse(any(call[0] == 'push' for call in self.git.calls))

    def test_workflow_still_requires_authorization(self):
        (self.root / 'app.txt').write_text('Client title\n')
        before = self.git.text('rev-parse', 'HEAD')
        with self.assertRaises(ValueError):
            self.run_action('prepare', description='Update title', approved=False)
        self.assertEqual(self.git.text('rev-parse', 'HEAD'), before)


if __name__ == '__main__':
    unittest.main()
