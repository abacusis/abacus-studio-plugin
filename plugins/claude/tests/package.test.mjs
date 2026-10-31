import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { test } from 'node:test';
import assert from 'node:assert/strict';
const read = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
test('mockup-first is optional, isolated and preserves implementation authority', () => {
  const guide=read('references/engineering/mockup-first.md');
  for(const phrase of ['No new command','mockup only','build directly','No preference','Do not suggest mockups for ordinary success messages','Quick','synthetic sample data','Localhost is not','No backend edits','No new command','Planning-only','Mockup-only request: stop','already authorized','publishing approval','screenshots','No preference'])assert.ok(guide.toLowerCase().includes(phrase.toLowerCase()),phrase);
  assert.match(read('references/engineering/workflow-depth.md'),/\[Mockup-first\]\(mockup-first.md\)/);
  assert.match(read('skills/engineering/SKILL.md'),/optional visual-only route/);
  assert.match(read('skills/design/SKILL.md'),/mockup-first.md/);
  assert.match(read('scripts/route_development.py'),/mockup-first.md before full feature orchestration/);
  assert.match(guide,/static image.*appearance/);
  assert.match(guide,/cannot establish click behavior/);
});
test('workflow depth honors user intent without turning every change into a team job', () => {
  const skill=read('skills/engineering/SKILL.md');
  const guide=read('references/engineering/workflow-depth.md');
  const hook=read('scripts/route_development.py');
  assert.ok(skill.indexOf('[Workflow depth]')<skill.indexOf('[Coordinator workflow]'));
  for(const phrase of ['Quick','Deep','Automatic','keywords alone','Planning-only stays planning-only','review-only does not authorize fixes','Classify by consequences, not file count','Quick Change — complete here','Main conversation','No automatic specialists','screenshots must be inspected','do not start it','No extra command']) assert.ok(guide.toLowerCase().includes(phrase.toLowerCase()),phrase);
  assert.match(guide,/Saved successfully/);
  assert.match(guide,/Quickly let all users read invoices/);
  assert.match(guide,/STOP/);
  assert.match(hook,/shortest adequate path/);
  assert.match(hook,/Never add agents to populate the dashboard/);
});
test('Engineering loads coordination with honest limits and complete responsibilities', () => {
  assert.match(read('skills/engineering/SKILL.md'), /\[Coordinator workflow\]\(\.\.\/\.\.\/references\/engineering\/orchestration\.md\)/);
  const guide = read('references/engineering/orchestration.md');
  for (const role of ['Orchestrator', 'Spec Writer', 'Builder', 'Verification Specialist', 'Code Reviewer', 'Security Reviewer', 'UI Reviewer', 'UX Reviewer', 'Readiness Reviewer']) assert.ok(guide.includes(role), role);
  for (const phrase of ['Classify by consequences, not file count', 'no mandatory classification questionnaire', 'Do not spawn specialist', 'two correction rounds', 'Needs human input', 'Source inspection does not', 'HEAD', 'not another installed agent', 'not a publishing Approver']) assert.ok(guide.toLowerCase().includes(phrase.toLowerCase()), phrase);
  assert.match(guide, /Execution depends on the local Claude session/);
  assert.match(guide, /summarize the scope and proceed/);
  assert.match(guide, /Saving and publishing/);
  assert.match(read('references/engineering/specification.md'), /do not add a mandatory approval pause/);
  assert.match(read('references/engineering/orchestration-testing.md'), /not model compliance/);
});
test('Spec Writer has a read-only handoff and installed specialists are explicit', () => {
  assert.deepEqual(readdirSync(new URL('../agents/', import.meta.url)).sort(), ['builder.md', 'code-reviewer.md', 'readiness-reviewer.md', 'security-reviewer.md', 'spec-writer.md', 'ui-reviewer.md', 'ux-reviewer.md', 'verifier.md']);
  const agent = read('agents/spec-writer.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^name: spec-writer$/m);
  assert.match(frontmatter, /^tools: Read, Grep, Glob$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 20$/m);
  assert.match(agent, /If a required instruction file is inaccessible, return blocked/);
  assert.doesNotMatch(frontmatter, /permissionMode|hooks|mcpServers|memory|skills/);
  for (const phrase of ['Do not write even specification files', 'Do not assume you inherit', 'unavailable knowledge', 'UI considerations and UX considerations', 'explicitly planned, not run', 'Never read .env']) {
    assert.ok(agent.includes(phrase), phrase);
  }
  const coordinator = read('references/engineering/orchestration.md');
  assert.match(coordinator, /Invoke the installed namespaced `abacus-studio:spec-writer`/);
  assert.match(coordinator, /If unavailable or denied/);
  assert.match(coordinator, /Wait for its result/);
  assert.match(coordinator, /UX Reviewer, and Readiness Reviewer are installed specialist agents/);
  assert.match(read('skills/engineering/SKILL.md'), /you MUST delegate the specification/);
  assert.match(read('skills/project-knowledge/SKILL.md'), /do not invoke Engineering again/);
  assert.match(coordinator, /Do not paste the agent's full draft into chat by default/);
  assert.match(read('references/client-communication.md'), /aim for 2–4 sentences/);
  assert.match(coordinator, /never collapse them into a single/);
});
test('every bundled skill loads the shared client communication standard', () => {
  const root = new URL('../skills/', import.meta.url);
  const skills = readdirSync(root).filter(name => existsSync(new URL(`${name}/SKILL.md`, root)));
  assert.ok(skills.length > 0);
  for (const name of skills) {
    assert.match(read(`skills/${name}/SKILL.md`), /Read and apply \[Client communication\]\(\.\.\/\.\.\/references\/client-communication\.md\) completely\./, name);
  }
  const standard = read('references/client-communication.md');
  assert.match(standard, /Lead with the outcome/);
  assert.match(standard, /usually be under 100 words, not a rigid limit/);
  assert.match(standard, /user asks for technical details/);
  assert.match(standard, /never overrides permissions, approval requirements/);
  assert.match(standard, /exact commands, SQL, diffs/);
  assert.match(standard, /Never print credentials/);
  assert.match(standard, /short answer is not permission to skip verification/);
  assert.match(standard, /review requested, not approved or live/);
});
test('Builder is scoped to implementation and browser capture is not a visual pass', () => {
  const agent = read('agents/builder.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^tools: Read, Grep, Glob, Edit, Write, Bash$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 40$/m);
  assert.doesNotMatch(frontmatter, /permissionMode|hooks|mcpServers|memory/);
  for (const phrase of ['A plan alone', 'Do not commit', 'subject to host permissions', 'Read captured images', 'not independent verification']) assert.ok(agent.includes(phrase), phrase);
  const engineering = read('skills/engineering/SKILL.md');
  assert.match(engineering, /you MUST then delegate to/);
  assert.match(engineering, /Planning-only work must never invoke Builder/);
  const browser = read('references/engineering/browser-verification.md');
  for (const phrase of ['Capture never auto-installs', 'captured is NOT a visual pass', 'no automatic redaction', 'No personal browser profile', 'do not sandbox the server']) assert.ok(browser.includes(phrase), phrase);
});
test('Verifier checks evidence without application edits or publishing authority', () => {
  const agent = read('agents/verifier.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^tools: Read, Grep, Glob, Bash$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 30$/m);
  assert.doesNotMatch(frontmatter, /Edit|Write|permissionMode|hooks|mcpServers/);
  for (const phrase of ['Do not fix defects', 'not a read-only', 'Builder-only evidence cannot', 'mark affected evidence stale', 'not verified', 'source state', 'publishing approval', 'image-capable tool']) assert.ok(agent.includes(phrase), phrase);
  assert.match(read('skills/engineering/SKILL.md'), /MUST delegate to\n`abacus-studio:verifier`/);
  assert.match(read('references/engineering/orchestration.md'), /Do not edit relevant files concurrently/);
});
test('Code Reviewer is read-only, evidence-based, and wired into substantial work', () => {
  const agent = read('agents/code-reviewer.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^tools: Read, Grep, Glob$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 25$/m);
  assert.doesNotMatch(frontmatter, /Bash|Edit|Write|permissionMode|hooks|mcpServers/);
  for (const phrase of ['Do not edit any files', 'Do not assume you', 'comparison baseline', 'file and line', 'optional suggestions', 'source inspection', 'publishing', 'two-round limit']) assert.ok(agent.includes(phrase), phrase);
  assert.match(read('skills/engineering/SKILL.md'), /MUST also delegate\nsource review to `abacus-studio:code-reviewer`/);
  assert.match(read('references/engineering/orchestration.md'), /wait for both before readiness/);
  assert.match(read('scripts/route_development.py'), /abacus-studio:code-reviewer/);
});
test('Security Reviewer is source-only with conservative evidence labels', () => {
  const agent = read('agents/security-reviewer.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^tools: Read, Grep, Glob$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 25$/m);
  assert.doesNotMatch(frontmatter, /Bash|Edit|Write|permissionMode|mcpServers|hooks/);
  for (const phrase of ['references/security/review.md', 'Do not edit files', 'Never read .env', 'no severity', 'not an observed runtime result', 'try to disprove', 'two-round', 'readiness/publishing approval']) assert.ok(agent.includes(phrase), phrase);
  assert.match(read('skills/security/SKILL.md'), /installed `abacus-studio:security-reviewer`/);
  assert.match(read('skills/security/SKILL.md'), /do not delegate recursively/);
  assert.match(read('references/engineering/orchestration.md'), /Material unresolved security validation prevents claiming ready/);
  assert.match(read('scripts/route_development.py'), /abacus-studio:security-reviewer/);
});
test('UI Reviewer requires actual image inspection and preserves scope', () => {
  const agent = read('agents/ui-reviewer.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^tools: Read, Grep, Glob$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 25$/m);
  assert.doesNotMatch(frontmatter, /Bash|Edit|Write|permissionMode|hooks|mcpServers/);
  for (const phrase of ['references/engineering/ui-review.md', 'Read EACH supplied screenshot', 'not visually verified', 'Do not edit files', 'Do not invent exact', 'replace the UX Reviewer', 'two-round', 'readiness/publishing approval']) assert.ok(agent.includes(phrase), phrase);
  assert.match(read('skills/engineering/SKILL.md'), /MUST also delegate to\n`abacus-studio:ui-reviewer`/);
  assert.match(read('references/engineering/ui-review.md'), /Capture success is not visual inspection/);
  assert.match(read('scripts/route_development.py'), /abacus-studio:ui-reviewer/);
});
test('UX Reviewer separates actual flow evidence from static screenshots', () => {
  const agent = read('agents/ux-reviewer.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^tools: Read, Grep, Glob$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 25$/m);
  assert.doesNotMatch(frontmatter, /Bash|Edit|Write|permissionMode|hooks|mcpServers/);
  for (const phrase of ['references/engineering/ux-review.md', 'Do not edit files', 'not an independently executed browser test', 'not flow-verified', 'two-round limit', 'readiness/publishing approval', 'Open supplied screenshots']) assert.ok(agent.includes(phrase), phrase);
  assert.match(read('skills/engineering/SKILL.md'), /MUST also delegate to `abacus-studio:ux-reviewer`/);
  assert.match(read('references/engineering/ux-review.md'), /A test plan is not an executed check/);
  assert.match(read('scripts/route_development.py'), /abacus-studio:ux-reviewer/);
});
test('Readiness Reviewer cannot waive checks or approve publication', () => {
  const agent = read('agents/readiness-reviewer.md');
  const frontmatter = agent.split('---')[1];
  assert.match(frontmatter, /^tools: Read, Grep, Glob$/m);
  assert.match(frontmatter, /^model: inherit$/m);
  assert.match(frontmatter, /^maxTurns: 25$/m);
  assert.doesNotMatch(frontmatter, /Bash|Edit|Write|permissionMode|mcpServers|hooks/);
  for (const phrase of ['references/engineering/readiness.md', 'Do not edit files', 'Ready to preview / Needs changes / Needs human', 'Stale, failed, blocked, missing', 'Agent agreement is not proof', 'not an independently executed test', 'same existing two-round limit', 'approved to publish']) assert.ok(agent.includes(phrase), phrase);
  assert.match(read('skills/engineering/SKILL.md'), /MUST delegate\nthe final assessment to `abacus-studio:readiness-reviewer`/);
  assert.match(read('scripts/route_development.py'), /abacus-studio:readiness-reviewer/);
  assert.match(agent, /0 used\nmeans 2 left/);
});
test('Claude marketplace selects its generated package with shared identity', () => {
  const marketplace = JSON.parse(read('.claude-plugin/marketplace.json'));
  const plugin = JSON.parse(read('.claude-plugin/plugin.json'));
  assert.equal(marketplace.name, 'abacus-studio-marketplace');
  assert.equal(marketplace.owner.name, 'Abacus');
  assert.equal(marketplace.plugins.length, 1);
  assert.equal(marketplace.plugins[0].name, plugin.name);
  assert.equal(marketplace.plugins[0].version, plugin.version);
  assert.equal(marketplace.plugins[0].description, plugin.description);
  assert.equal(marketplace.plugins[0].source, './plugins/claude');
  assert.match(read('adapters/claude/INSTALL.md'), /https:\/\/github.com\/abacusis\/abacus-studio-plugin/);
  assert.match(read('adapters/claude/INSTALL.md'), /claude plugin marketplace add abacusis\/abacus-studio-plugin/);
  assert.match(read('adapters/claude/INSTALL.md'), /abacus-studio@abacus-studio-marketplace/);
});
test('client installation guides share a simple journey without maintainer build steps', () => {
  for (const [path, prefix] of [['adapters/claude/INSTALL.md', '/abacus-studio:'], ['adapters/codex/INSTALL.md', '$abacus-']]) {
    const guide = read(path);
    for (const action of ['connect', 'setup', 'submit', 'request-publish']) assert.ok(guide.includes(prefix + action), action);
    assert.match(guide, /Submit my changes/);
    assert.match(guide, /Request publishing review/);
    assert.match(guide, /does not make the changes live/);
    assert.match(guide, /does\s+not automatically publish/);
    assert.doesNotMatch(guide, /build_release\.py|generate_packages\.py|Publisher checklist|Build a local test package/);
  }
  assert.match(read('adapters/codex/INSTALL.md'), /codex plugin add abacus-studio@abacus-studio-codex/);
  assert.match(read('adapters/claude/README.md'), /\]\(INSTALL\.md\)/);
  for (const tool of ['claude', 'codex']) assert.ok(read('INSTALL.md').includes(`adapters/${tool}/INSTALL.md`));
});
test('submission authorization is shared, scoped, and does not repeat stage confirmations', () => {
  const authorization = read('references/changes/authorization.md').replace(/\s+/g, ' ');
  for (const phrase of ['Submit and publish', 'Submit alone', 'failed/missing required checks', 'sensitive or blocked files', 'conflicts', 'one synchronization retry', 'Host-required permission', 'never merging']) assert.ok(authorization.includes(phrase), phrase);
  for (const action of ['submit', 'request-publish']) assert.match(read(`references/changes/${action}.md`), /\[Submission authorization\]\(authorization\.md\)/);
  assert.doesNotMatch(read('references/changes/submit.md'), /ask for explicit confirmation to push|Ask the client to approve the description/);
  assert.doesNotMatch(read('references/changes/request-publish.md'), /own confirmations|obtain approval again|ask the client to confirm the publish request/);
  assert.match(read('adapters/codex/engineering.md'), /references\/changes\/authorization\.md/);
});
test('migrations require per-file approval and never deliver management credentials', () => {
  const skill = read('references/changes/migrate.md');
  assert.match(skill, /disable-model-invocation: true/);
  assert.match(skill, /migration-preview/);
  assert.match(skill, /migration-apply/);
  assert.match(skill, /setup\/install approval is NOT migration approval/);
  assert.match(skill, /Never retry uncertain outcomes/);
  assert.match(skill, /token.*server-side/);
});
test('Claude package uses one helper authorization without an extra connector', () => {
  const manifest = JSON.parse(read('.claude-plugin/plugin.json'));
  assert.equal(manifest.name, 'abacus-studio');
  assert.equal(manifest.version, '0.32.1');
  const config = JSON.parse(read('.mcp.json'));
  assert.deepEqual(config.mcpServers, {});
  assert.equal(config.mcpServers['studio-local'], undefined);
  assert.equal(config.mcpServers['studio-sync'], undefined);
});
test('autosync is opt-in, independent, and does not claim deployment or review submission',()=>{
  const skill=read('references/legacy-sync.md');
  assert.match(skill,/disable-model-invocation: true/);
  assert.match(skill,/enable_local_sync/);
  assert.match(skill,/only after approval/i);
  assert.match(skill,/sync_workspace.py/);
  assert.match(skill,/does not create a PR/);
  assert.match(skill,/token out of chat, logs and files/);
});
test('setup clones with the secure Git helper and never falls back to snapshots', () => {
  const skill = read('references/workspace/setup.md');
  assert.match(skill, /studio_git.py/);
  assert.match(skill, /NEW folder/);
  assert.match(skill, /Do not fall back to a ZIP/);
  assert.match(skill, /Setup never commits/);
});
test('skill is explicitly invoked, generic, and honest about its limited scope', () => {
  const skill = read('references/workspace/connect.md');
  assert.match(skill, /disable-model-invocation: true/);
  assert.match(skill, /list-apps/);
  assert.match(skill, /workspace-config/);
  assert.match(skill, /needs_configuration/);
  assert.match(skill, /schema_version/);
  assert.match(skill, /does not authorize/);
  for (const fixture of ['private-client-app', 'abacusis/private-client', 'Bearer ', 'service_role_key']) assert.equal(skill.includes(fixture), false);
});
test('menu exposes direct actions and engineering with valid workflow links', () => {
  const root = new URL('../skills/', import.meta.url);
  const commands = readdirSync(root).filter(name => existsSync(new URL(`${name}/SKILL.md`, root))).sort();
  const visible = commands.filter(name => !read(`skills/${name}/SKILL.md`).includes('user-invocable: false'));
  assert.deepEqual(visible, ['connect', 'design', 'disconnect', 'engineering', 'request-publish', 'security', 'setup', 'status', 'submit', 'update']);
  assert.match(read('skills/sandbox-database/SKILL.md'), /user-invocable: false/);
  for (const command of commands) {
    const skill = read(`skills/${command}/SKILL.md`);
    if (!['design', 'engineering', 'security', 'project-knowledge', 'sandbox-database', 'update'].includes(command)) assert.match(skill, /disable-model-invocation: true/);
    for (const match of skill.matchAll(/\]\((\.\.\/\.\.\/references\/[^)]+)\)/g)) {
      assert.equal(existsSync(new URL(`../skills/${command}/${match[1]}`, import.meta.url)), true);
    }
  }
});
test('Setup works directly and Status stays limited to connection access', () => {
  const skill = read('skills/setup/SKILL.md');
  assert.match(skill, /no separate Connect command is required/);
  const setup = read('references/workspace/setup.md');
  assert.match(setup, /list-apps/);
  assert.match(setup, /workspace-config/);
  assert.match(setup, /Browser consent and host-required execution prompts still apply/);
  assert.match(read('references/workspace/status.md'), /get_connection_status/);
});

test('local dashboard ships semantic assets and queues existing workflows only', () => {
  const html=read('dashboard/index.html');
  const js=read('dashboard/app.js');
  assert.match(html,/Your AI team/);
  assert.match(html,/role="tablist"/);
  assert.match(html,/Return to Claude/);
  assert.match(js,/requestError/);
  assert.match(js,/Finished task/);
  assert.match(js,/seenHandoffs/);
  assert.match(js,/renderHandoffs/);
  assert.match(js,/a.invoked/);
  assert.match(js,/prefers-reduced-motion:reduce/);
  assert.match(js,/!agent.participated/);
  assert.equal(js.includes('Observed hook event'),false);
  assert.ok(JSON.parse(read('hooks/hooks.json')).hooks.PreToolUse);
  assert.match(js,/scrollIntoView/);
  assert.match(read('scripts/build_release.py'),/dashboard\/\*\.html/);
  assert.match(read('skills/engineering/SKILL.md'),/local-dashboard.md/);
  assert.match(read('scripts/route_development.py'),/local team dashboard/);
  for(const role of ['orchestrator','spec-writer','builder','verifier','code-reviewer','security-reviewer','ui-reviewer','ux-reviewer','readiness-reviewer'])assert.ok(js.includes(role));
});
