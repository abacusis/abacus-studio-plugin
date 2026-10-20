import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from verification_record import run_check, inspect_record, fingerprint, workspace


class VerificationRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.studio/\n.env*\n')
        (self.root / 'app.txt').write_text('initial')

    def tearDown(self):
        self.temp.cleanup()

    def check(self, script='print("ok")', **kwargs):
        return run_check(self.root, ['R1'], [sys.executable, '-c', script], approved=True, **kwargs)

    def test_approval_required_before_any_command_or_receipt(self):
        with self.assertRaises(ValueError):
            run_check(self.root, ['R1'], [sys.executable, '-c', 'raise Exception()'])
        self.assertFalse((self.root / '.studio').exists())

    def test_pass_and_fresh_inspection_not_whole_feature_readiness(self):
        result = self.check()
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['exit_code'], 0)
        self.assertFalse(result['ready_to_preview'])
        receipt = Path(result['record_path'])
        self.assertNotIn('output', json.loads(receipt.read_text()))
        self.assertEqual(inspect_record(self.root, receipt)['status'], 'passed')
        self.assertNotIn('.studio', subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain']).decode())

    def test_failure_and_missing_command_are_not_passes(self):
        self.assertEqual(self.check('raise SystemExit(3)')['status'], 'failed')
        result = run_check(self.root, ['R1'], ['abacus-nonexistent-executable'], True)
        self.assertEqual(result['status'], 'not_run')

    def test_timeout_does_not_pass(self):
        self.assertEqual(self.check('import time; time.sleep(10)', timeout=1)['status'], 'timed_out')

    def test_changed_untracked_or_tracked_source_invalidates_evidence(self):
        result = self.check()
        (self.root / 'app.txt').write_text('changed')
        self.assertEqual(inspect_record(self.root, result['record_path'])['status'], 'stale')
        (self.root / 'app.txt').write_text('initial')
        subprocess.run(['git', '-C', str(self.root), 'add', 'app.txt'], check=True)
        result = self.check()
        (self.root / 'app.txt').unlink()
        self.assertEqual(inspect_record(self.root, result['record_path'])['status'], 'stale')

    def test_source_changes_during_command_and_hidden_config_are_detected(self):
        result = self.check('from pathlib import Path; Path("app.txt").write_text("new")')
        self.assertEqual(result['execution_status'], 'passed')
        self.assertEqual(result['status'], 'stale')
        result = self.check()
        (self.root / '.config.json').write_text('{}')
        self.assertEqual(inspect_record(self.root, result['record_path'])['status'], 'stale')

    def test_ignored_environment_and_receipts_do_not_change_fingerprint(self):
        before = fingerprint(self.root)
        (self.root / '.env.local').write_text('secret')
        self.check()
        self.assertEqual(before, fingerprint(self.root))

    def test_symlink_paths_and_other_workspace_records_are_refused(self):
        (self.root / 'link').symlink_to(self.root / 'app.txt')
        with self.assertRaises(ValueError): self.check()
        (self.root / 'link').unlink()
        (self.root / '.studio').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): self.check()
        with self.assertRaises(ValueError): inspect_record(self.root, self.root / 'outside.json')

    def test_refuses_tracked_or_nonignored_evidence_and_literal_credentials(self):
        (self.root / '.gitignore').write_text('')
        with self.assertRaises(ValueError): self.check()
        (self.root / '.gitignore').write_text('.studio/\n')
        with self.assertRaises(ValueError):
            run_check(self.root, ['R1'], ['echo', 'api_key=private'], True)

    def test_cli_run_and_inspect(self):
        helper = Path(__file__).parents[1] / 'scripts/verification_record.py'
        result = subprocess.run([sys.executable, '-I', str(helper), 'run', '--workspace', str(self.root), '--criterion', 'R1', '--approved', '--', sys.executable, '-c', 'print("ok")'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)['record_path']
        result = subprocess.run([sys.executable, '-I', str(helper), 'inspect', '--workspace', str(self.root), '--record', receipt], capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)['status'], 'passed')

    def test_secret_named_application_source_is_not_silently_excluded(self):
        (self.root / 'secretary.py').write_text('initial')
        result = self.check()
        (self.root / 'secretary.py').write_text('changed')
        self.assertEqual(inspect_record(self.root, result['record_path'])['status'], 'stale')

    def test_child_cannot_redirect_receipts_with_a_symlink(self):
        (self.root / 'outside').mkdir()
        script = 'from pathlib import Path; p=Path(".studio/verification"); p.rename(".studio/old"); p.symlink_to(Path("outside").resolve(), target_is_directory=True)'
        with self.assertRaises(ValueError): self.check(script)
        self.assertEqual(list((self.root / 'outside').iterdir()), [])
