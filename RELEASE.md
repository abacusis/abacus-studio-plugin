# Publishing Abacus Studio for Claude Code

## 0.32.0 — local integration and conflict guidance

- Shared conflict playbook routes Update and Submit through plain-language intent
  comparison, grouped resolution approval, both-side/interaction checks and bounded
  escalation. Clean merges are not treated as semantic verification.
- Explicit integrate action checkpoints reviewed local changes, merges sandbox and
  records local-only intent. Resolve/cancel preserve that intent and saved work;
  check records configured results without authorizing a push. Submit rejects
  local-integration state until a separately requested fresh Prepare workflow.
- Ordinary Update remains fast-forward-only. No auto-stash, reset, force-push,
  automatic ticket, GitHub login or silent resolution. Existing submission behavior
  retains fetch-first and checked normal pushes; ignored files remain protected.

## 0.31.0 — safe Update workspace

- Shared helper update action and Claude Update/Codex abacus-update skills fetch
  through existing Studio authorization and fast-forward clean, behind workspaces.
- Dirty workspaces, divergence, active Git operations and unfinished submissions
  stop without auto-stash, commits, pushes, resets or lock deletion. Ignored local
  files are protected by no-overwrite-ignore. Existing workspace validation remains.
- Reports dependency changes and preview restart recommendation without executing
  downloaded code. Natural-language app-update requests route to Update, not gh
  login or Submit. Matching client sandbox does not imply matching the live build.

## 0.30.1 — Windows npm launch fix

- Installation, supervised previews, managed preview configuration and runtime
  wrappers resolve Windows npm/npx launchers through the selected PATH and run
  node with npm-cli.js/npx-cli.js. No shell=True, cmd.exe or batch evaluation.
  Unknown batch launchers fail explicitly rather than enabling a shell.
- Missing-command/file errors no longer suggest an authentication failure.
- CI adds Node 22 and real Windows npm ci plus npm-run preview launch coverage.
  Native Windows results remain pending until the workflow executes.

## 0.30.0 — Windows workspace identity fix

- Compare Git's absolute top-level path using native resolved filesystem paths,
  not raw strings. This handles Git for Windows forward slashes without skipping
  workspace identity, repository, branch or metadata authorization checks.
- Regression tests cover matching roots, different roots, relative paths, remote
  and branch rejection. Native Windows case/separator coverage runs in the new
  Windows/macOS/Linux CI matrix; local macOS tests are not Windows execution.
- Existing authorized client clones can be reused after updating the plugin and
  restarting the host session. No client source or Studio settings migration.

### Setup diagnostics and bounded preview recovery

- Shared read-only setup_health.py reports package version on disk, local tools
  and explicitly selected workspace prerequisites. It never reads credentials,
  repairs files, signs in or claims the running session loaded that version.
- Setup uses local preflight; Status adds diagnostics only when explicitly asked.
- Failed previews refresh configuration but do not rerun an unchanged command.
  Safe failure categories replace raw-log output; local changes are preserved.
- Known npm Vite scripts receive the npm argument separator before generated
  port flags. Host-managed guidance also requires a corrected cause before retry.

### Evidence-backed checks and behavioral release tooling

- Shared `verification_record.py` runs an approved exact command, associates
  criterion IDs, captures status/exit/times/output digest and local source hashes,
  and writes a private ignored receipt. Failures, missing commands, timeouts and
  changed source cannot become passing receipts. Readiness remains a separate
  whole-change assessment; external state and meaningful coverage need review.
- Shared Claude/Codex guidance routes structured verification to these receipts;
  focused edits keep direct checks. No mandatory extra agents, automatic Git
  operations, dependency installation, dashboard or recovery system is added.
- `behavioral_checks.py` prepares and grades six scenarios per host from explicit
  tool-trace exports plus human review, tied to current candidate source. Default
  tests validate the grader with synthetic traces only. Live sessions have not
  been run for this change. Codex native delegation uses explicitly exported
  app-server role identities and completed agent states; plain exec traces lacking
  those fields remain unverified rather than being waived.
- Before publishing a behavioral release, follow
  `references/engineering/behavioral-release-tests.md`. Keep unresolved acceptance
  gaps visible; package/unit success is not live model compliance.

## 0.29.0 — Codex native specialists and simpler submission

- Approved Codex Setup can install eight project-scoped `.codex/agents/abacus-*.toml`
  profiles using the same shared role instructions. No global configuration,
  model selection, permission changes or automatic hook trust. Existing or edited
  profiles are preserved; ownership receipts permit safe refreshes.
- Normalize exact native profile names for local lifecycle attribution. Handle
  canonical Bash/Edit/Write/Agent events; private tool arguments remain discarded.
- Correct the Interrupt handler timeout to the documented one-second default.
- Keep all normal Studio workflows and the focused small-change path. Restart
  Codex in the workspace after approved profile setup. Live delegation and Studio
  acceptance are still pending, not silently promoted to proven parity.

### Request-scoped submission authorization

- Explicit Submit covers the normal reviewed commit/check/push workflow;
  explicit “submit and publish” covers submission and a publishing-review PR.
- Remove redundant wording, commit, check, push and PR confirmation gates from
  shared workflows, Claude entrypoints and the Codex Engineering adapter.
- Keep helper --approved requirements, exact-commit checks, fetch-first behavior,
  secret scanning, conflict decisions, bounded synchronization retry and exact
  expected-head/base PR validation. No helper safety gate is removed.
- Submit alone does not open a PR; Request publish alone does not save dirty
  local work. Quoted text and dashboard intents are not execution authorization.
- Never merge, deploy or authorize database changes through this combined flow.

## 0.28.2 — clearer Codex skill labels

- Give all eleven Codex skills explicit interface metadata with short display
  titles: Setup, Design, Engineering and the other actions. Codex supplies the
  Abacus Studio namespace; skill labels no longer repeat the brand.
- Preserve skill identifiers, invocation policy, authorization and Claude commands.
- Regenerate both packages and test metadata, packaging and shared workflows.
- Update: `codex plugin marketplace upgrade abacus-studio-codex`, then
  `codex plugin add abacus-studio@abacus-studio-codex`; restart Codex afterward.

## 0.28.1 — one branch, consistent tool packages

- Shared source remains on main; both distributions are generated at
  plugins/claude and plugins/codex. Root tool-specific marketplaces select the
  appropriate folder. Existing plugin identities and authorization stay unchanged.
- Codex's new install path needs no --ref codex. Existing branch-pinned installs
  require one explicit marketplace re-registration; the old branch is preserved.
- Both package adapters feed the same release builder and generation command.
  CI checks exact generated content, not only version numbers. Local edits and
  symlinks in generated folders block regeneration rather than being overwritten.
- This structure permits future tool adapters but does not implement Grok or
  promise compatibility with tools that have not been tested.
- No commit, remote publication, marketplace migration or branch deletion is
  performed by generation. Both packages are released together as 0.28.1.

Before an approved publication: update availability wording, run tests and
`python3 scripts/generate_packages.py`, then `--check`. Include both generated
folders and root marketplace catalogs in the release commit. ZIPs remain standalone
packages with their own local-root catalogs. Do not publish stale generated files.

Local layout validation on 2026-10-16: 110 Python and 21 JavaScript tests passed.
Native Claude and Codex CLI installs from the same local repository marketplace
both selected their own generated folder and installed version 0.28.1 in isolated
profiles. Claude manifest validation and both package freshness checks passed.
These checks do not constitute new live Studio or trusted-hook acceptance tests.

## 0.28.0 — Claude release and Codex testing preview

- One source repository, separate Claude and Codex release targets. Existing
  Claude packaging remains the default. Shared source and Claude distribution stay
  on main; a generated Codex-only distribution is published on the codex branch.
  No repository rename or client installation is performed by release builds.
- Codex package includes eleven adapted skills, shared Python helpers and eight
  specialist role procedures, with explicit native-delegation/tool-scope limits.
- Shared Studio browser authorization and OS credential storage; no separate
  connector consent, keys in chat or hard-coded client configuration.
- Package-selected skill installation into ignored `.agents/skills/`, isolated
  host installation receipts and private Codex preview metadata under `.studio/`.
- Optional Codex hook adapter filters raw inputs and uses supported lifecycle
  events. Hook trust is separate; generic workers remain unattributed. No full
  dashboard parity, enforced role tool sandbox or unattended recovery claim.
- Includes the previously unpublished 0.27.0 mockup-first work. Live service integration
  requires authorized testing; package/unit tests are not that evidence.

Both ZIPs accompany tag v0.28.0. The codex branch is generated output, not a second
source of truth: make changes on main and regenerate it. First publication creates
that branch without replacing an existing remote branch. Future updates must
preserve distribution history and never force-push over unknown changes.

Target repository: `abacusis/abacus-studio-claude-plugin`.
Internal plugin: `abacus-studio`; marketplace: `abacus-studio-marketplace`.
Only the plugin distribution belongs in this repository.

## Prepare a release

1. Bump both plugin/marketplace manifests and the version assertion. Update
   README.md in every change set: highlight meaningful new client value, keep its
   latest-feature heading and specialist roster current, and distinguish locally
   prepared features from published releases. Add the release notes here. See
   AGENTS.md for the ongoing documentation rule. Do not invent benefits for
   internal-only changes; use a short maintenance note instead.
   Run `python3 scripts/check_readme.py --base <starting commit SHA>` to check the
   whole change set. CI requires a README change for every push/PR with changes.
   The release builder also checks README version and specialist coverage.
2. Run the Python tests and `node --test tests/package.test.mjs`.
3. Run `claude plugin validate .`.
4. Use `scripts/build_release.py --output <NEW absolute release folder>`.
   It copies only allowlisted distribution files, rejects symlinks and concrete
   credential patterns, and writes file hashes and a verified ZIP beside the
   clean folder. It never initializes Git, pushes, or changes repository visibility.
5. Review the audit manifest. Do not upload the development folder wholesale:
   local `.claude` settings, caches, `.env`, and application workspaces are excluded.

## Before publishing

- Review README marketing claims against actual implementation and evidence.
  Once publication is authorized, replace the current local/unpublished notice
  with accurate release availability before including README in the release commit.
  Do not promise working interactions from screenshots or certified security.

- LICENSE currently contains a proprietary review draft, not adopted terms.
  Do not publish it as effective until legal review and owner approval confirm
  the licensor, ownership, acceptance process, client agreement consistency and
  governing terms. Preserve THIRD_PARTY_NOTICES.md and all upstream MIT notices.
  Public visibility alone does not grant an open-source license.
- Create a NEW dedicated repository from the clean folder, not another project's
  history. Check the initial commit for secrets before making it public.
- Test marketplace installation in a separate Claude profile and a clean app
  workspace, including Studio sign-in, setup, and a manual plugin update.
- Test Windows and Linux separately; current automated tests are not those tests.
- Publish a matching version tag after approval. Protect the distribution branch
  and review updates: clients enabling auto-update trust code released here.

## 0.27.0 — local preparation, unpublished

- Adds optional mockup-first routing for explicit preview requests and meaningful
  visual uncertainty, without new commands, agents or compulsory design reviews.
- Preserves quick-change routing and explicit build-directly intent; visual-only
  slices avoid automatic full-team orchestration and use labeled sample data.
- Separates mockup-only authority from already-authorized implementation and keeps
  real services, writes, migrations and publishing outside preview authorization.
- Updates Engineering, Design and routing guidance plus acceptance coverage.

## 0.26.0

- Adds quick/deep/automatic intent guidance and an early focused Quick Change
  path for ordinary success feedback, copy and isolated layout changes.
- Focused work avoids automatic specialists, full orchestration, broad mapping
  and reporting ceremony. Actual risk and explicit requirements still govern.
- Corrects broad role-table wording that could trigger UI/UX or Builder delegation
  for every small interaction. Routing remains model guidance, not enforcement.

- Adds a responsive coordination map with a central Orchestrator, recorded
  invocation connections and once-only assignment/return signals. No animated
  replay on initial load, unchanged polls, stale events, offline or ended sessions.
- Supports reduced motion and narrow-screen gutter connections; details and Git
  actions retain their existing behavior. Reopening replaces an identified older
  dashboard server rather than silently reusing an incompatible observer.

- Compact active-team panels hide unused specialists and retain muted participants.
- Adds pre-action observation and filtered Read paths without capturing commands,
  prompts, search patterns, outputs, transcripts or private reasoning.
- Shows task summaries and latest action on each visible agent; removes repetitive
  hook labels and generic lifecycle noise from the activity list.
- Requires concise coordinator task/result reporting when local tracking is enabled.
- "Finished task" is not a passing review. Stale/offline signals remain explicit.

## 0.25.0

- Removes obsolete plugin guidance requiring branch protection or Administration
  Read before requesting a client-repository review PR; no merge/deploy permission.

- Adds an opt-in loopback dashboard with Orchestrator and eight specialist cards,
  activity, safe file-path metadata, and coordinator-reported checks/findings.
- Lifecycle hooks record bounded metadata only after workspace approval. Returned
  agents are distinct from passed checks; stale sessions do not appear working.
- Shows local changes and cached upstream counts without fetching or reading diffs.
- Submit and Request publish queue allowlisted intents for the next Claude prompt;
  they cannot execute Git, start Claude, or authorize publishing themselves.
- No transcripts, private reasoning, remote telemetry, or new dependencies.

## 0.24.0

- Adds a read-only Readiness Reviewer to reconcile current requirements, checks
  and relevant specialist findings before declaring substantial work ready.
- Missing/stale evidence and material unresolved validation cannot become passes;
  actual defects take priority while evidence gaps stay visible.
- Preserves the shared two-round correction limit and separate publishing approval.
- Updates the public README with the client benefit and current specialist team.

## 0.23.0

- Adds a read-only UX Reviewer to assess actual flow evidence, feedback and recovery.
- Keeps UI presentation review distinct from task completion and executed checks.
- Refreshes the public README to explain the specialist team and its client value.
- Adds a standing README maintenance rule, CI change-set check, and release-time
  version/specialist coverage checks. These are structural checks, not editorial QA.
- No automatic publication, extra credentials, or new runtime access.

## 0.15.0

- Adds read-only application knowledge search/retrieval through the helper.
- Engineering and Design retrieve relevant records before consequential changes.
- Preserves explicit sharing, approval/lifecycle distinctions and app permissions.
- Requires Studio's application knowledge migration and matching MCP deployment.

## 0.14.1

- Publishes a clearly labeled proprietary license draft naming Abacus Internet
  Solutions Inc.; it is not effective terms and does not alter prior releases.
- Includes third-party notices and full upstream MIT attribution in packaging.
- No runtime, permission, or command changes.

## 0.14.0

- Adds specification-driven planning to Engineering for substantial features.
- Links requirements, implementation tasks, and actual acceptance evidence.
- Includes Spec Kit attribution and MIT notice; no extra installer or commands.
- Preserves existing standards, branch handling, migration and release approvals.

## 0.13.0

- Adds Abacus Security for focused source-only reviews and optional direct use.
- Routes materially security-sensitive Engineering changes to the security skill.
- Includes Cloudflare attribution and MIT notice; preserves Studio approvals.
- No full audit harness, target execution, live probes, or dashboard upload.

## 0.12.0

- Adds Abacus Engineering: one automatically discoverable skill and an optional
  `/abacus-studio:engineering` command for planning, testing, debugging,
  architecture, and review.
- Bundles curated Abacus playbooks with upstream attribution and the MIT notice.
- Preserves Studio's submission, sandbox approval, and publishing boundaries;
  adds no credentials, hooks, or automatic commits or deployments.
- Verifies the engineering references are included in release archives.

## 0.11.3

- Refreshes the client-facing plugin description in both manifests.
- Keeps marketplace version and description synchronized with the plugin manifest.
- No permissions, commands, authentication, or application behavior changes.

## 0.11.2

- Public-release packaging uses an explicit allowlist and hashes every included file.
- Excludes local permissions, credential files, Python caches, and Git history.
- Installation and update instructions use the dedicated Claude plugin repository.
- Removes client-name references from a package test fixture.
- Adds Supabase management-token detection to the submission secret guard.
- Documents credential boundaries, execution risks, and platform test limitations.
