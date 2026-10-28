"""Render the Codex adapter from allowlisted shared sources; no installation."""
import json
import re

ROLES = ('spec-writer', 'builder', 'verifier', 'code-reviewer', 'security-reviewer',
         'ui-reviewer', 'ux-reviewer', 'readiness-reviewer')
SKILLS = ('connect', 'disconnect', 'setup', 'status', 'update', 'submit', 'request-publish',
          'engineering', 'design', 'security', 'project-knowledge', 'sandbox-database')
SKILL_DESCRIPTIONS = {
    'connect': 'Sign in to Studio and choose your application',
    'disconnect': 'Disconnect your Studio authorization',
    'setup': 'Set up your application and local preview',
    'status': 'Show your Studio connection and access role',
    'update': 'Download the latest app code without pushing local work',
    'submit': 'Review and save your changes to the client repository',
    'request-publish': 'Request Abacus review before publishing',
    'engineering': 'Plan, build and verify application changes',
    'design': 'Improve your application interface and usability',
    'security': 'Review application code for security concerns',
    'project-knowledge': 'Find application decisions and project context',
    'sandbox-database': 'Review and apply authorized sandbox database changes',
}


def translate(value):
    """Translate host references, not business rules, script code or licenses."""
    value = value.replace('${CLAUDE_PLUGIN_ROOT}', '<plugin-root>')
    for role in ROLES:
        value = value.replace('abacus-studio:' + role, role)
    for name in SKILLS:
        value = value.replace('/abacus-studio:' + name, '$abacus-' + name)
        value = value.replace('abacus-studio:' + name, 'abacus-' + name)
    value = value.replace('.claude/skills/', '.agents/skills/')
    value = value.replace('/abacus-studio:', '$abacus-')
    value = value.replace('.claude/launch.json', '.studio/codex-preview.json')
    value = value.replace('Claude Code', 'Codex').replace('Claude', 'Codex')
    value = value.replace('Agent/Task', 'native delegation').replace('Task or Agent', 'a native delegation tool')
    value = value.replace('installed specialist agents', 'specialist role procedures')
    value = value.replace('installed `', 'packaged role `')
    value = value.replace('the installed\n', 'the packaged role\n')
    value = value.replace('and installed\n', 'and packaged role\n')
    value = value.replace('installed agent', 'specialist role')
    value = value.replace('installed namespaced', 'packaged')
    value = value.replace('invoke the Skill tool', 'read the packaged skill')
    return value


def strip_frontmatter(value):
    if not value.startswith('---\n') or '\n---\n' not in value[4:]:
        raise ValueError('Expected skill/role frontmatter')
    return value.split('\n---\n', 1)[1].lstrip()


def render(root, sources):
    sources = {p.relative_to(root).as_posix(): p for p in sources}
    output = {}
    for name, path in sources.items():
        if (name.startswith(('.claude-plugin/', 'adapters/', 'agents/', 'skills/', 'hooks/', 'tests/'))
                or name in ('.mcp.json', 'INSTALL.md', 'README.md')
                or name in ('scripts/route_development.py', 'scripts/build_release.py',
                            'scripts/build_codex.py', 'scripts/build_claude.py', 'scripts/generate_packages.py', 'scripts/check_readme.py')
                or name == 'references/engineering/orchestration-testing.md'):
            continue
        content = path.read_text()
        # Immutable third-party notices/licenses and Python code remain byte-identical.
        if name.startswith('references/') and not name.endswith('/upstream.md'):
            content = translate(content)
        if name.startswith('dashboard/'):
            content = content.replace('Claude', 'Codex')
        output[name] = content.encode()
    for name in SKILLS:
        raw = sources[f'skills/{name}/SKILL.md'].read_text()
        description = re.search(r'^description: (.+)$', raw, re.M).group(1)
        body = translate(strip_frontmatter(raw))
        header = ('Resolve `<plugin-root>` from the absolute source path of this loaded skill: '
                  'two directories above its directory. Substitute that real path in commands; '
                  'it is not an environment variable. Skill references name packaged workflows, '
                  'not a Claude Skill tool. Read references/codex/delegation.md before any '
                  'specialist handoff; use approved project-scoped Abacus profiles when available.\n\n')
        body = body.replace('The request is: $ARGUMENTS', 'Use the current user request as the input.')
        value = f'---\nname: abacus-{name}\ndescription: {translate(description)}\n---\n\n' + header + body
        if name == 'engineering':
            value = sources['adapters/codex/engineering.md'].read_text()
        if name == 'setup':
            value += ('\n## Codex project specialists\n\n'
                      'Include eight project-scoped Abacus agent profiles in the local setup approval. '
                      'After the workspace is created, run `python3 -I "<plugin-root>/scripts/codex_agents.py" '
                      '--workspace "<absolute workspace>" --approved`. This installs only owned '
                      '`.codex/agents/abacus-*.toml` files and a local receipt; no global configuration, '
                      'model changes, or hook-trust changes. Existing conflicting profiles are preserved. '
                      'Open a new Codex session in the workspace to discover the profiles. Existing '
                      'workspaces can use this same approved refresh without recloning.\n')
        output[f'skills/abacus-{name}/SKILL.md'] = value.encode()
        # Codex supplies the plugin label; do not repeat the brand in skill titles.
        interface = ('interface:\n'
                     f'  display_name: {json.dumps(name.replace("-", " ").title())}\n'
                     f'  short_description: {json.dumps(SKILL_DESCRIPTIONS[name])}\n'
                     f'  default_prompt: {json.dumps("Use $abacus-" + name + " for my application.")}\n')
        if 'disable-model-invocation: true' in raw:
            interface += 'policy:\n  allow_implicit_invocation: false\n'
        output[f'skills/abacus-{name}/agents/openai.yaml'] = interface.encode()
    for role in ROLES:
        body = translate(strip_frontmatter(sources[f'agents/{role}.md'].read_text()))
        prefix = ('Codex specialist instructions, also used by approved project-scoped profiles.\n'
                  'Read references/codex/delegation.md. Map allowed operations to host tools '
                  'without expanding permissions; these instructions are not a tool sandbox.\n\n')
        output[f'roles/{role}.md'] = (prefix + body).encode()
    output['references/codex/delegation.md'] = sources['adapters/codex/delegation.md'].read_bytes()
    output['references/engineering/local-dashboard-shared.md'] = output['references/engineering/local-dashboard.md']
    output['references/engineering/local-dashboard.md'] = sources['adapters/codex/local-dashboard.md'].read_bytes()
    workflow = output['references/engineering/orchestration.md'].decode()
    start = workflow.index('## Current capability boundary')
    end = workflow.index('### Spec Writer handoff', start)
    workflow = workflow[:start] + (
        '## Current capability boundary\n\nRead [Codex delegation](../codex/delegation.md) first. '
        'Eight specialist procedures are bundled in roles/. Approved Setup installs project-scoped '
        'abacus-<role> profiles. Use those exact names only when available in the current session; '
        'otherwise use authorized native delegation with complete role instructions. '
        'If unavailable or forbidden, disclose a main-conversation fallback; do not pretend '
        'a separate agent ran. Read-only scopes are behavioral constraints, not enforced tool '
        'allowlists. Local execution depends on this session. Optional trusted hooks provide '
        'routing and partial local observation, not an execution engine or recovery service.\n\n'
    ) + workflow[end:]
    output['references/engineering/orchestration.md'] = workflow.encode()
    version = json.loads(sources['.claude-plugin/plugin.json'].read_text())['version']
    manifest = {'name': 'abacus-studio', 'version': version,
                'description': 'Build and improve your application in Codex with Abacus engineering guidance, project knowledge and reviewed submission workflows.',
                'skills': './skills/', 'hooks': './hooks/hooks.json',
                'interface': {'displayName': 'Abacus Studio', 'shortDescription': 'Build with AI, backed by Abacus engineering',
                              'developerName': 'Abacus', 'category': 'Productivity'}}
    output['.codex-plugin/plugin.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    marketplace = {'name': 'abacus-studio-codex', 'interface': {'displayName': 'Abacus Studio for Codex'},
                   'plugins': [{'name': 'abacus-studio', 'source': {'source': 'local', 'path': './'},
                                'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_USE'},
                                'category': 'Productivity'}]}
    output['.agents/plugins/marketplace.json'] = (json.dumps(marketplace, indent=2) + '\n').encode()
    events = ('SessionStart', 'UserPromptSubmit', 'SubagentStart', 'SubagentStop',
              'PreToolUse', 'PostToolUse', 'Interrupt', 'Stop', 'SessionEnd')
    hooks = {event: [{'hooks': [{'type': 'command',
             'command': 'python3 -I "${PLUGIN_ROOT}/scripts/codex_hook.py"', 'timeout': 1 if event == 'Interrupt' else 5}]}] for event in events}
    output['hooks/hooks.json'] = (json.dumps({'hooks': hooks}, indent=2) + '\n').encode()
    install = sources['adapters/codex/INSTALL.md'].read_bytes()
    output['INSTALL.md'] = install
    output['TESTING.md'] = sources['adapters/codex/TESTING.md'].read_bytes()
    output['RELEASE.md'] = (f'# Codex adapter {version}\n\nDistribution generated from the shared Abacus Studio source. '
        'See INSTALL.md for installation and capabilities; TESTING.md separates '
        'executed checks from pending live acceptance. No remote publication, '
        'account installation or hook-trust approval is performed by this build.\n').encode()
    output['README.md'] = (f'# Abacus Studio for Codex\n\nVersion {version}.\n\n'
        'Build your software with AI, without doing it alone. Abacus Studio brings '
        'engineering playbooks, curated project decisions, optional mockups, security '
        'guidance and reviewed submission to your Codex workflow.\n\n'
        'Small changes stay focused. Substantial changes can use eight specialist '
        'profiles installed locally during approved Setup. Named profiles use Codex '
        'native delegation; trusted lifecycle hooks connect their recorded activity '
        'to the local dashboard. Existing profiles and global settings are preserved. '
        'See TESTING.md for executed checks and remaining live acceptance.\n\n'
        'See [Installation and testing](INSTALL.md). No automatic commits, pushes, '
        'merges or deployments. Readiness is not Abacus approval.\n').encode()
    # Fail closed on missed executable host references in model instructions.
    for name, value in output.items():
        if name.startswith(('skills/', 'roles/', 'references/')) and name.endswith('.md') and not name.endswith('/upstream.md'):
            if any(token in value.decode() for token in ('${CLAUDE_PLUGIN_ROOT}', '/abacus-studio:', '$ARGUMENTS', 'abacus-studio:spec-writer')):
                raise ValueError('Unadapted host reference: ' + name)
    return output
