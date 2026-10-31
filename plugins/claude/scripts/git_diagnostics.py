"""Allowlisted Git failure summaries; never return raw process output."""
import re


class GitOperationError(ValueError):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__('Git operation failed: ' + diagnostic['category'] + '. ' + diagnostic['next_step'])


def failure(stderr, exit_code=None, nonce=None, operation='git'):
    text = (stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else str(stderr or ''))[-65536:]
    stages = set()
    if nonce and re.fullmatch(r'[a-f0-9]{32}', nonce):
        stages = set(re.findall(r'\[studio-git:' + nonce + r':(invoked|retrieval_attempted|issued|failed)\]', text))
    category, step = 'unclassified', 'Inspect local execution permissions and connectivity; request a sanitized diagnostic, not GitHub credentials.'
    lower = text.lower()
    if 'failed' in stages:
        category, step = 'studio_credential_helper', 'Check Studio authorization, secure credential storage and repository access. Do not request GitHub sign-in.'
    elif 'could not resolve host' in lower or 'could not resolve proxy' in lower:
        category, step = 'network_dns', 'Check DNS, proxy and allowed network access to GitHub.'
    elif any(value in lower for value in ('certificate verify failed', 'ssl certificate problem', 'server certificate verification failed')):
        category, step = 'network_tls', 'Check certificate and proxy configuration; do not disable certificate verification.'
    elif any(value in lower for value in ('failed to connect', 'connection timed out', 'network is unreachable', 'connection refused')):
        category, step = 'network_connection', 'Check connectivity and host network permissions before one controlled retry.'
    elif 'remote branch' in lower and 'not found' in lower:
        category, step = 'branch_unavailable', 'Have the administrator verify the configured development branch exists.'
    elif 'repository not found' in lower or 'requested url returned error: 404' in lower:
        category, step = 'repository_or_access', 'Verify repository identity and Studio GitHub App access; a private repository can return not found when access is denied.'
    elif any(value in lower for value in ('authentication failed', 'could not read username', 'terminal prompts disabled', 'requested url returned error: 403', 'requested url returned error: 401')):
        category, step = 'authentication_or_access', 'Check the Studio credential-helper evidence and app access; do not request a personal token or GitHub login.'
    elif any(value in lower for value in ('permission denied', 'operation not permitted', 'read-only file system', 'could not create work tree')):
        category, step = 'local_permissions', 'Check destination and host execution permissions without bypassing security controls.'
    return {'operation': operation if operation in ('git', 'clone') else 'git',
            'exit_code': exit_code if isinstance(exit_code, int) else None,
            'category': category, 'next_step': step,
            'credential_helper': 'observed' if 'invoked' in stages else 'not_observed',
            'credential_helper_result': 'failed' if 'failed' in stages else 'completed' if 'issued' in stages else 'unconfirmed',
            'credential_retrieval': ('issued' if 'issued' in stages else 'failed' if 'failed' in stages and 'retrieval_attempted' in stages
                                      else 'attempted' if 'retrieval_attempted' in stages else 'not_observed'),
            'raw_output_retained': False}
