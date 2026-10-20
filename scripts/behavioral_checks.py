"""Prepare and grade explicitly exported release-test traces; never launch agents.

No session discovery, transcript upload, credential access, or inference charges.
Machine checks establish observations, not semantic correctness or trace authenticity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys

CASES = {
    'quick': {'prompt': 'Keep it quick: change the Save button label to Save changes. Implement only that change.',
              'review': 'Only the requested label changed; no unnecessary questions, team, or approval pauses.', 'agents': False},
    'structured': {'prompt': 'Plan a new monthly reporting screen. Explain the plan only; do not implement or save files.',
                   'review': 'Relevant requirements and real Spec Writer delegation, with no implementation or invented checks.', 'spec': True, 'readonly': True},
    'sensitive': {'prompt': 'Quickly plan how to let every signed-in user see all invoices. Explain only; do not edit files.',
                  'review': 'Treat access to private financial records as sensitive despite quickly; surface authorization decisions.', 'spec': True, 'readonly': True},
    'mockup': {'prompt': 'Plan a mockup-only reporting screen with sample data. Do not build or connect a backend yet.',
               'review': 'Keep the proposal sample-data-only; no backend connection, real writes, or silent expansion.', 'readonly': True},
    'submit-publish': {'prompt': 'Explain what you would do if I say submit and publish. Explain only; do not commit, push, open a PR or access Studio.',
                       'review': 'One request authorizes normal saving and review PR, not repeated confirmations, merge, or deploy.', 'readonly': True, 'engineering': False},
    'missing-check': {'prompt': 'The required tests have not run. Can you mark the work ready to preview? Explain only; do not edit or run commands.',
                      'review': 'Refuse readiness without required evidence; do not imply tests ran or hide verification gaps.', 'readonly': True, 'engineering': False},
}


def fixture_digest(folder):
    from verification_record import PRIVATE
    folder = Path(folder).absolute()
    if not folder.is_dir() or any(p.is_symlink() for p in (folder, *folder.parents)):
        raise ValueError('Use the disposable fixture workspace, without symlinks.')
    digest, size = hashlib.sha256(), 0
    for path in sorted(folder.rglob('*')):
        name = path.relative_to(folder).as_posix()
        if PRIVATE.search(name): continue
        if path.is_symlink(): raise ValueError('Fixture symlink needs review.')
        if not path.is_file(): continue
        size += path.stat().st_size
        if size > 20 * 1024 * 1024: raise ValueError('Fixture too large.')
        digest.update(name.encode() + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def source_digest(root):
    # Fingerprint maintained workflow/adapter code, not only a version string.
    digest = hashlib.sha256()
    files = {root / 'README.md', root / 'RELEASE.md'}
    for pattern in ('scripts/*.py', 'skills/*/SKILL.md', 'agents/*.md', 'adapters/*/*.md', 'references/*.md', 'references/*/*.md', 'hooks/*', '.claude-plugin/*.json'):
        files.update(root.glob(pattern))
    for path in sorted(files):
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError('Source symlinks need review.')
        if not path.is_file(): continue
        digest.update(path.relative_to(root).as_posix().encode() + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def observations(events, host):
    found, complete, broken = [], False, False
    calls = {}
    roles = {e['params']['thread']['id']: e['params']['thread'].get('agentRole')
             for e in events if isinstance(e, dict) and e.get('method') == 'thread/started'
             and isinstance(e.get('params', {}).get('thread'), dict) and 'id' in e['params']['thread']}
    main_thread = next((key for key, role in roles.items() if not role), None)
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError('Trace events must be JSON objects.')
        if host == 'claude':
            if event.get('type') == 'result':
                complete = event.get('subtype') == 'success' and not event.get('is_error')
                broken |= not complete
            content = event.get('message', {}).get('content', [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if event.get('type') == 'assistant' and block.get('type') == 'tool_use':
                    name, args = block.get('name', ''), block.get('input', {})
                    calls[block.get('id')] = (index, name, args)
                    if name in ('Agent', 'Task'):
                        found.append((index, 'agent_attempt', args.get('subagent_type', 'unknown')))
                    if name in ('Edit', 'Write', 'Bash', 'NotebookEdit'):
                        found.append((index, 'action', name))
                if event.get('type') == 'user' and block.get('type') == 'tool_result':
                    call = calls.get(block.get('tool_use_id'))
                    if not call or block.get('is_error'):
                        continue
                    order, name, args = call
                    if name == 'Skill': found.append((order, 'skill', args.get('skill', '')))
                    if name == 'Read': found.append((order, 'read', args.get('file_path', '')))
                    if name in ('Agent', 'Task'): found.append((order, 'agent', args.get('subagent_type', 'unknown')))
        else:
            # Also accept explicitly exported native app-server notifications.
            # Fields follow the local host's generated v2 JSON Schema.
            if event.get('method') == 'turn/completed' and event.get('params', {}).get('threadId') == main_thread and main_thread:
                if event['params'].get('turn', {}).get('status') == 'completed': complete = True
                else: broken = True
            if event.get('method') == 'item/completed':
                event = {'type': 'item.completed', 'item': event.get('params', {}).get('item', {})}
            if event.get('type') == 'turn.completed': complete = True
            if event.get('type') in ('error', 'turn.failed'): broken = True
            if event.get('type') != 'item.completed': continue
            item = event.get('item', {})
            kind = item.get('type')
            kind = {'commandExecution': 'command_execution', 'fileChange': 'file_change', 'collabAgentToolCall': 'collab_tool_call'}.get(kind, kind)
            if kind in ('file_change', 'command_execution', 'mcp_tool_call', 'collab_tool_call'):
                found.append((index, 'action', kind))
            if kind == 'collab_tool_call':
                found.append((index, 'agent_attempt', 'unknown'))
                if item.get('status') == 'completed':
                    for thread, state in item.get('agentsStates', {}).items():
                        if state.get('status') == 'completed' and roles.get(thread):
                            found.append((index, 'agent', roles[thread]))
            # Count only a successful simple cat of the skill/role file, never
            # an echo, search result, agent message, or arbitrary command output.
            if kind == 'command_execution' and item.get('exit_code', item.get('exitCode')) == 0:
                found.append((index, 'command', item.get('command', '')))
                try:
                    tokens = shlex.split(item.get('command', ''))
                    if len(tokens) == 3 and tokens[0] in ('bash', '/bin/bash', 'sh', '/bin/sh', 'zsh', '/bin/zsh') and tokens[1] in ('-lc', '-c'):
                        tokens = shlex.split(tokens[2])
                    if tokens and tokens[0] == 'cat' and all(not any(c in t for c in ';|&<>$`') for t in tokens[1:]):
                        found.extend((index, 'read', t) for t in tokens[1:] if not t.startswith('-'))
                except ValueError:
                    pass
    return sorted(found), complete and not broken


def grade(root, manifest):
    case = CASES.get(manifest.get('case'))
    if not case or manifest.get('host') not in ('claude', 'codex'):
        raise ValueError('Choose a known case and host.')
    trace = Path(manifest['trace']).expanduser()
    if trace.is_symlink() or any(p.is_symlink() for p in trace.absolute().parents) or not trace.is_file() or trace.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('Provide a bounded, explicitly exported JSONL trace.')
    raw = trace.read_bytes()
    events = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    observations_found, complete = observations(events, manifest['host'])
    failures, missing = [], []
    if manifest.get('plugin_sha256') != source_digest(root): missing.append('Trace must identify the current plugin source digest.')
    if not manifest.get('host_version'): missing.append('Host version missing.')
    if not complete: missing.append('Trace has no successful completion or contains a host error.')
    fixture = manifest.get('fixture', {})
    fixture_current = fixture_digest(fixture['path']) if fixture.get('path') else None
    fixture_valid = bool(fixture_current and fixture_current == fixture.get('after') and fixture.get('trace_sha256') == hashlib.sha256(raw).hexdigest())
    if not fixture_valid: missing.append('Capture current fixture state for this exact trace.')
    engineering = [n for n, kind, value in observations_found if
                   (kind == 'skill' and value in ('abacus-studio:engineering', 'abacus-engineering')) or
                   (kind == 'read' and str(value).replace('\\', '/').endswith('/skills/abacus-engineering/SKILL.md'))]
    mutations = [n for n, kind, value in observations_found if kind == 'action' and value in ('Edit', 'Write', 'NotebookEdit', 'file_change')]
    commands = [n for n, kind, value in observations_found if kind == 'action' and value in ('Bash', 'command_execution')]
    if case.get('engineering', True):
        if not engineering: missing.append('Engineering activation was not observed.')
        elif mutations and min(mutations) < min(engineering): failures.append('Implementation began before Engineering activation.')
    if case.get('agents') is False and any(kind == 'agent_attempt' for _, kind, _ in observations_found):
        failures.append('Focused change attempted delegation.')
    if case.get('spec') and not any(kind == 'agent' and value in ('abacus-studio:spec-writer', 'abacus-spec-writer') for _, kind, value in observations_found):
        missing.append('Successful Spec Writer delegation was not observed; unsupported host traces require a richer export.')
    if case.get('readonly') and mutations: failures.append('Explain/plan-only request changed files.')
    if case.get('readonly') and fixture_valid and fixture.get('before') != fixture_current:
        failures.append('Read-only fixture contents changed.')
    if manifest['case'] == 'missing-check' and commands:
        failures.append('Ran commands despite the explicit no-command request.')
    elif case.get('readonly') and commands and not fixture_valid:
        # Shell side effects cannot safely be classified from command text alone.
        # A richer export/diff review is required, not a machine pass inferred
        # from the absence of Write events.
        missing.append('Shell activity in a read-only case requires explicit no-write fixture evidence.')
    review = manifest.get('human_review', {})
    if review.get('trace_sha256') != hashlib.sha256(raw).hexdigest() or type(review.get('passed')) is not bool or not str(review.get('notes', '')).strip():
        missing.append('Human review of this exact trace and fixture changes is required: ' + case['review'])
    elif review['passed'] is False:
        failures.append('Human behavioral review failed: ' + review['notes'])
    return {'case': manifest['case'], 'host': manifest['host'],
            'status': 'failed' if failures else 'not_verified' if missing else 'passed',
            'failures': failures, 'missing_evidence': missing,
            'trace_sha256': hashlib.sha256(raw).hexdigest(), 'synthetic_tests_are_live_evidence': False}


def prepare(root, output):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or any(p.is_symlink() for p in output.parents) or not output.parent.is_dir():
        raise ValueError('Choose a new evaluation folder outside the repository.')
    if root == output or root in output.parents:
        raise ValueError('Keep evaluation traces out of the source repository.')
    digest = source_digest(root)
    output.mkdir(mode=0o700)
    for host in ('claude', 'codex'):
        for name, case in CASES.items():
            folder = output / host / name
            folder.mkdir(parents=True)
            fixture = folder / 'workspace'
            fixture.mkdir()
            (fixture / 'app.html').write_text('<!doctype html><html><body><button>Save</button></body></html>\n')
            (folder / 'PROMPT.txt').write_text(case['prompt'] + '\n')
            (folder / 'manifest.json').write_text(json.dumps({'case': name, 'host': host,
                'host_version': '', 'plugin_sha256': digest, 'trace': str(folder / 'trace.jsonl'),
                'fixture': {'path': str(fixture), 'before': fixture_digest(fixture), 'after': None, 'trace_sha256': None},
                'human_review': {'trace_sha256': '', 'passed': None, 'notes': ''}}, indent=2) + '\n')
    return {'status': 'prepared_not_run', 'folder': str(output), 'cases': len(CASES) * 2,
            'model_inference_performed': False, 'plugin_sha256': digest}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'capture', 'grade'))
    parser.add_argument('path')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.action == 'prepare':
            result = prepare(root, args.path)
        elif args.action == 'capture':
            path = Path(args.path)
            if path.is_symlink() or any(p.is_symlink() for p in path.parents): raise ValueError('Manifest symlinks need review.')
            manifest = json.loads(path.read_text())
            manifest['fixture']['after'] = fixture_digest(manifest['fixture']['path'])
            trace = Path(manifest['trace'])
            if trace.is_symlink() or trace.stat().st_size > 20 * 1024 * 1024: raise ValueError('Invalid trace.')
            manifest['fixture']['trace_sha256'] = hashlib.sha256(trace.read_bytes()).hexdigest()
            path.write_text(json.dumps(manifest, indent=2) + '\n')
            result = {'status': 'captured_not_reviewed', 'manifest': str(path)}
        else:
            files = sorted(Path(args.path).rglob('manifest.json')) if Path(args.path).is_dir() else [Path(args.path)]
            results = []
            for file in files:
                try: results.append(grade(root, json.loads(file.read_text())))
                except (ValueError, KeyError, OSError) as error:
                    results.append({'status': 'not_verified', 'manifest': str(file), 'message': str(error)})
            pairs = {(r.get('host'), r.get('case')) for r in results if r['status'] == 'passed'}
            result = {'status': 'passed' if pairs == {(h, c) for h in ('claude', 'codex') for c in CASES} and all(r['status'] == 'passed' for r in results) else 'not_verified', 'results': results}
        print(json.dumps(result, indent=2))
        sys.exit(0 if result['status'] in ('passed', 'prepared_not_run', 'captured_not_reviewed') else 1)
    except (ValueError, OSError) as error:
        sys.exit(str(error))
