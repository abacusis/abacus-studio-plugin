import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from behavioral_checks import CASES, fixture_digest, grade, observations, prepare, source_digest


class BehavioralCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / 'README.md').write_text('source')
        self.trace = self.root / 'trace.jsonl'
        self.fixture = self.root / 'workspace'
        self.fixture.mkdir()
        (self.fixture / 'app.html').write_text('<button>Save</button>')

    def tearDown(self): self.temp.cleanup()

    def manifest(self, events, case='quick', host='claude', review=True):
        self.trace.write_text(''.join(json.dumps(e) + '\n' for e in events))
        return {'case': case, 'host': host, 'host_version': 'synthetic-fixture',
                'plugin_sha256': source_digest(self.root), 'trace': str(self.trace),
                'fixture': {'path': str(self.fixture), 'before': fixture_digest(self.fixture), 'after': fixture_digest(self.fixture), 'trace_sha256': hashlib.sha256(self.trace.read_bytes()).hexdigest()},
                'human_review': {'trace_sha256': hashlib.sha256(self.trace.read_bytes()).hexdigest(),
                                 'passed': review, 'notes': 'Synthetic grader fixture only; not a live session.'}}

    def claude(self, name='Skill', args=None):
        return [{'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'tool-1', 'name': name,
                   'input': args or {'skill': 'abacus-studio:engineering'}}]}},
                {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'tool-1', 'content': 'ok'}]}},
                {'type': 'result', 'subtype': 'success'}]

    def test_skill_mentions_are_not_activation_and_missing_trace_completion_is_unverified(self):
        events = [{'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'I used abacus-studio:engineering'}]}}, {'type': 'result', 'subtype': 'success'}]
        self.assertEqual(grade(self.root, self.manifest(events))['status'], 'not_verified')
        self.assertEqual(grade(self.root, self.manifest(self.claude()[:-1]))['status'], 'not_verified')

    def test_failed_skill_calls_are_not_activation(self):
        events = self.claude(); events[1]['message']['content'][0]['is_error'] = True
        self.assertEqual(grade(self.root, self.manifest(events))['status'], 'not_verified')

    def test_real_call_shape_plus_review_is_required(self):
        manifest = self.manifest(self.claude(), review=None)
        self.assertEqual(grade(self.root, manifest)['status'], 'not_verified')
        manifest['human_review']['passed'] = True
        self.assertEqual(grade(self.root, manifest)['status'], 'passed')
        manifest['human_review']['passed'] = False
        self.assertEqual(grade(self.root, manifest)['status'], 'failed')

    def test_early_edits_and_unnecessary_delegation_fail(self):
        edit = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'edit', 'name': 'Edit', 'input': {}}]}}
        events = [edit] + self.claude()
        self.assertEqual(grade(self.root, self.manifest(events))['status'], 'failed')
        events = self.claude() + self.claude('Agent', {'subagent_type': 'abacus-studio:builder'})
        self.assertEqual(grade(self.root, self.manifest(events))['status'], 'failed')

    def test_plan_only_mutations_fail_and_spec_delegation_must_be_observed(self):
        events = self.claude()
        self.assertEqual(grade(self.root, self.manifest(events, 'structured'))['status'], 'not_verified')
        events += self.claude('Agent', {'subagent_type': 'abacus-studio:spec-writer'})
        self.assertEqual(grade(self.root, self.manifest(events, 'structured'))['status'], 'passed')
        events += self.claude('Write', {'file_path': 'app.txt'})
        self.assertEqual(grade(self.root, self.manifest(events, 'structured'))['status'], 'failed')

    def test_codex_reads_are_observed_not_echoes_or_final_prose(self):
        item = {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': "cat '/plugin/skills/abacus-engineering/SKILL.md'", 'exit_code': 0}}
        events = [item, {'type': 'turn.completed'}]
        self.assertEqual(grade(self.root, self.manifest(events, host='codex'))['status'], 'passed')
        item['item']['command'] = 'echo /plugin/skills/abacus-engineering/SKILL.md'
        self.assertEqual(grade(self.root, self.manifest(events, host='codex'))['status'], 'not_verified')
        item['item']['command'] = 'cat /plugin/skills/abacus-engineering/SKILL.md; false'
        self.assertEqual(grade(self.root, self.manifest(events, host='codex'))['status'], 'not_verified')

    def test_stale_source_and_changed_reviewed_trace_are_unverified(self):
        manifest = self.manifest(self.claude())
        (self.root / 'README.md').write_text('changed')
        self.assertEqual(grade(self.root, manifest)['status'], 'not_verified')
        manifest['plugin_sha256'] = source_digest(self.root)
        self.trace.write_text(self.trace.read_text() + '\n')
        self.assertEqual(grade(self.root, manifest)['status'], 'not_verified')

    def test_preparation_is_not_execution_and_contains_both_hosts_and_all_cases(self):
        result = prepare(self.root, self.root.parent / (self.root.name + '-evals'))
        output = Path(result['folder'])
        self.addCleanup(__import__('shutil').rmtree, output)
        self.assertEqual(result['status'], 'prepared_not_run')
        self.assertFalse(result['model_inference_performed'])
        self.assertEqual(len(list(output.rglob('manifest.json'))), len(CASES) * 2)
        with self.assertRaises(ValueError): prepare(self.root, self.root / 'inside')

    def test_codex_native_notifications_link_role_to_completed_agent(self):
        events = [
            {'method': 'thread/started', 'params': {'thread': {'id': 'parent', 'agentRole': None}}},
            {'method': 'thread/started', 'params': {'thread': {'id': 'child', 'agentRole': 'abacus-spec-writer'}}},
            {'method': 'item/completed', 'params': {'item': {'type': 'commandExecution', 'command': 'cat /plugin/skills/abacus-engineering/SKILL.md', 'exitCode': 0}}},
            {'method': 'item/completed', 'params': {'item': {'type': 'collabAgentToolCall', 'status': 'completed', 'agentsStates': {'child': {'status': 'completed'}}}}},
            {'method': 'turn/completed', 'params': {'threadId': 'parent', 'turn': {'status': 'completed'}}},
        ]
        self.assertEqual(grade(self.root, self.manifest(events, 'structured', 'codex'))['status'], 'passed')
        events[3]['params']['item']['agentsStates']['child']['status'] = 'running'
        self.assertEqual(grade(self.root, self.manifest(events, 'structured', 'codex'))['status'], 'not_verified')

    def test_no_command_prompt_and_readonly_fixture_changes_are_enforced(self):
        events = self.claude('Bash', {'command': 'echo hello'})
        self.assertEqual(grade(self.root, self.manifest(events, 'missing-check'))['status'], 'failed')
        manifest = self.manifest(self.claude(), 'mockup')
        (self.fixture / 'app.html').write_text('changed')
        manifest['fixture']['after'] = fixture_digest(self.fixture)
        self.assertEqual(grade(self.root, manifest)['status'], 'failed')
