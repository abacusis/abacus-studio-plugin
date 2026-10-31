import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from git_diagnostics import failure, GitOperationError
import studio_git as module


class DiagnosticTests(unittest.TestCase):
    def test_categories_never_echo_process_output(self):
        cases = [('Could not resolve host: private.example', 'network_dns'),
                 ('SSL certificate problem', 'network_tls'),
                 ('Failed to connect to github.com', 'network_connection'),
                 ('Remote branch sandbox not found', 'branch_unavailable'),
                 ('Repository not found', 'repository_or_access'),
                 ('Authentication failed', 'authentication_or_access'),
                 ('Permission denied', 'local_permissions'), ('Other failure', 'unclassified')]
        for message, category in cases:
            result = failure(message + ' password=PRIVATE_SENTINEL Authorization: PRIVATE_SENTINEL', 128)
            self.assertEqual(result['category'], category)
            self.assertEqual(result['exit_code'], 128)
            self.assertNotIn('PRIVATE_SENTINEL', json.dumps(result))
            self.assertNotIn('private.example', json.dumps(result))

    def test_only_matching_nonce_markers_count_as_evidence(self):
        nonce = 'a' * 32
        self.assertEqual(failure('[studio-git:' + 'b' * 32 + ':issued]', nonce=nonce)['credential_retrieval'], 'not_observed')
        text = ''.join('[studio-git:' + nonce + ':' + stage + ']' for stage in
                       ('invoked', 'retrieval_attempted', 'issued'))
        result = failure(text + ' Authentication failed', 128, nonce)
        self.assertEqual(result['credential_helper'], 'observed')
        self.assertEqual(result['credential_retrieval'], 'issued')
        self.assertEqual(result['category'], 'authentication_or_access')
        self.assertNotIn(nonce, json.dumps(result))

    def test_git_wrapper_retains_sanitized_clone_failure(self):
        def run(command, **kwargs):
            nonce = kwargs['env']['ABACUS_GIT_DIAGNOSTIC_NONCE']
            return subprocess.CompletedProcess(command, 128, b'',
                ('[studio-git:' + nonce + ':invoked][studio-git:' + nonce + ':retrieval_attempted][studio-git:' + nonce + ':failed] PRIVATE_SENTINEL').encode())
        with tempfile.TemporaryDirectory() as root:
            git = module.Git(root, 'test')
            self.addCleanup(git.close)
            with patch.object(module.subprocess, 'run', side_effect=run):
                with self.assertRaises(GitOperationError) as error:
                    git.run('clone', 'https://github.com/example/client.git')
            self.assertEqual(error.exception.diagnostic['operation'], 'clone')
            self.assertEqual(error.exception.diagnostic['category'], 'studio_credential_helper')
            self.assertEqual(error.exception.diagnostic['credential_retrieval'], 'failed')
            self.assertNotIn('PRIVATE_SENTINEL', str(error.exception))

    def test_missing_git_and_timeout_do_not_leak_exception(self):
        with tempfile.TemporaryDirectory() as root:
            git = module.Git(root, 'test')
            self.addCleanup(git.close)
            for source, expected in ((FileNotFoundError('PRIVATE_SENTINEL'), 'executable_missing'),
                    (subprocess.TimeoutExpired('PRIVATE_SENTINEL', 10, stderr=b'password=PRIVATE_SENTINEL'), 'timeout')):
                with patch.object(module.subprocess, 'run', side_effect=source):
                    with self.assertRaises(GitOperationError) as error:
                        git.run('clone', 'https://github.com/example/client.git')
                self.assertEqual(error.exception.diagnostic['category'], expected)
                self.assertNotIn('PRIVATE_SENTINEL', json.dumps(error.exception.diagnostic))

    def test_credential_markers_are_on_stderr_not_credential_stdout(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.dict(module.os.environ, {'ABACUS_GIT_DIAGNOSTIC_NONCE': 'a' * 32}), \
                patch.object(module.sys, 'stdin', io.StringIO('protocol=https\nhost=github.com\npath=example/client.git\n')), \
                patch.object(module, 'operation', side_effect=[{'repository': 'example/client'},
                    {'repository': 'example/client', 'token': 'PRIVATE_SENTINEL'}]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            module.credential('test')
        self.assertIn('password=PRIVATE_SENTINEL', stdout.getvalue())
        self.assertNotIn('studio-git', stdout.getvalue())
        self.assertNotIn('PRIVATE_SENTINEL', stderr.getvalue())
        result = failure(stderr.getvalue(), 128, 'a' * 32)
        self.assertEqual(result['credential_retrieval'], 'issued')

    def test_helper_failure_before_retrieval_does_not_claim_retrieval_attempt(self):
        nonce = 'a' * 32
        result = failure('[studio-git:' + nonce + ':invoked][studio-git:' + nonce + ':failed]', 128, nonce)
        self.assertEqual(result['credential_helper_result'], 'failed')
        self.assertEqual(result['credential_retrieval'], 'not_observed')


if __name__ == '__main__':
    unittest.main()
