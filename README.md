# Abacus Studio

## Build your software with AI, without doing it alone.

“I wish our software could do this.”

Abacus Studio helps you turn that idea into a change you can see and test—using
Claude Code or Codex, connected to your application and backed by Abacus's engineering
guidance and review process.

Keep using the AI tool you know. Describe what you want, preview the results,
and work with Abacus to bring reviewed changes into your live application.

[Get started](https://studio.abacusis.ca/install/claude) ·
[Explore Abacus Studio](https://studio.abacusis.ca)

New in 0.32.1: safer setup diagnostics distinguish network,
branch, local execution and repository-access failures, and report whether Studio
credential retrieval was observed—without exposing keys or raw Git logs.

New in 0.32.0: combine your work with incoming team updates
locally before submitting. Claude and Codex explain conflicting behavior, propose
a combined result and ask about meaningful choices. Local checkpoints preserve
your work; combining changes locally never grants permission to push or publish.

New in 0.31.0: say “get the latest app changes” or use
`/abacus-studio:update` (Codex: `$abacus-update`) to safely download updates through
Studio, without a separate GitHub login. Local unfinished work is never silently
stashed, committed or overwritten, and Update never pushes or publishes.

Version 0.30.1: Windows app installation and preview now launch npm through
Node directly, avoiding batch-launcher lookup failures and misleading sign-in errors.

Clearer local setup diagnostics and preview
failure guidance help identify missing tools and avoid repeating an unchanged,
failed startup. Successful setups keep the same simple flow.
Windows workspace validation now accepts Git's forward-slash
paths, allowing valid existing clones to continue setup without recloning.

## Your idea. An AI engineering team behind it.

Don't just ask AI to write code. Give it a process for understanding your app,
planning the change, building it, and checking the result from different angles.

Your AI tool coordinates the work in your local session, bringing in the relevant
specialists for substantial changes. Small improvements stay small—you don't
need to manage a team of agents or remember a command for each one.

| Specialist | What it brings to your change |
| --- | --- |
| Spec Writer | Turns your request into clear requirements and acceptance criteria. |
| Builder | Implements the agreed change and adds relevant tests. |
| Verification Specialist | Checks requirements against actual results and identifies what remains untested. |
| Code Reviewer | Looks for bugs, regressions, and code that will be difficult to maintain. |
| Security Reviewer | Examines relevant access and data boundaries through focused source review. |
| UI Reviewer | Inspects real screenshots for clipping, layout issues, and visual inconsistency. |
| UX Reviewer | Examines actual interaction evidence for confusing steps, missing feedback, and recovery problems. |
| Readiness Reviewer | Brings requirements, checks and reviews together to identify what is ready and what still needs attention. |

For example, a form might look right but silently lose your work after a failed
save. Visual review checks the screen; UX review examines the recorded flow and
flags the lost input and missing explanation. Passing tests, good-looking screens,
and a usable workflow are different questions—the plugin helps Claude consider
each one instead of treating “the code is written” as “the work is finished.”

Relevant findings go back for corrections, with at most two correction rounds
before unresolved issues are brought to you. You get a plain-language summary of
what changed, what was checked, and what still needs attention.

These are AI specialists, not a replacement for the Abacus team. They run through
your local Claude session and depend on available tools, approved access, and
actual evidence. No screenshot means no visual pass; no executed check means no
claim that it passed. Readiness to preview is never approval to publish.

### What's new in 0.32.1

**Clearer setup failure reports.** Failed Git downloads now include a safe failure
category, exit status and credential-helper observations, rather than assuming
GitHub access is the problem. Credentials and raw Git output stay out of reports.

**Combine changes without submitting yet.** When your work overlaps team updates,
ask to combine them locally. The workflow preserves a local checkpoint, explains
conflicting behavior and asks about meaningful choices. Checks follow the combined
result; a later Submit request is still required before anything is pushed.

**Get the latest app changes safely.** Update workspace downloads newer code
through Studio authorization, without a separate GitHub sign-in. Clean workspaces
fast-forward; unfinished work and diverged histories stop for review. Nothing is
pushed or published, and downloaded install scripts do not run automatically.

**Smoother Windows setup.** npm installation and preview use the selected Node
runtime directly, including paths with spaces. Missing-command errors give a
runtime-related next step instead of incorrectly suggesting a sign-in problem.

**Clearer proof behind “done.”** Approved checks
can leave a private local record of what ran and which code it checked, helping
identify results made stale by later edits. New release-test tooling checks
observed Claude/Codex activity rather than trusting an agent's summary. Live
cross-tool behavioral acceptance remains pending; small changes stay lightweight.

**Simpler saving and review requests.**
Say “submit and publish” to authorize saving to sandbox and opening Abacus’s
review request in one flow, without approving every intermediate step again.
Checks, sensitive-file protection and conflict decisions remain. This never
authorizes an automatic merge or deployment; host permission prompts still apply.

Codex menu labels are clearer: skills use simple titles such as **Setup**,
**Design**, and **Request Publish** under **Abacus Studio**, without repeating
the brand. Version 0.28.2 includes this naming cleanup;
existing skill identifiers and Claude commands are unchanged.

Refresh the Codex marketplace with `codex plugin marketplace upgrade abacus-studio-codex`,
then run `codex plugin add abacus-studio@abacus-studio-codex` and restart Codex.

### Shared packages on main

**One repository, consistent packages for each tool.** Claude's package is
generated in `plugins/claude` and Codex's in `plugins/codex`, both from shared
source. Each marketplace selects the right package—no tool-specific branch flag.
A freshness check keeps both distributions synchronized with the playbooks and
helpers. The same adapter pattern can support more tools after compatibility work;
no other tool integration is included yet.

Version 0.32.1 is available from `main` for both tools. Existing Codex installs
pinned to the old `codex` branch need a one-time marketplace re-registration;
see the [Codex installation instructions](adapters/codex/INSTALL.md).

### Recent improvements

**One workflow, in your preferred AI tool.** The Codex adapter shares Abacus's
playbooks, project knowledge, setup, verification, Submit and Request publish
workflows. See [Codex setup](adapters/codex/INSTALL.md).

**Named Codex specialists.** Version 0.29.0 adds eight native,
project-scoped specialist profiles during approved setup. Their recorded activity
can appear in the same local team dashboard, using trusted Codex hooks. Small
changes still stay focused. Live client acceptance remains tracked in
[Codex testing](adapters/codex/TESTING.md); successful packaging is not a claim
that every live integration has been verified.

**Try the idea before connecting the backend.** Ask for a mockup first, or let
Claude suggest a clickable sample-data preview when the layout or flow is still
uncertain. Say “mockup only” to stop at the preview, or “build directly” to skip
it. Small fixes stay small; design approval is never a claim that backend behavior
has been implemented or tested. No extra command or mandatory design stage.

The mockup-first guidance is included in 0.28.0 for both tools.

**Small changes stay small.** Say “keep it quick” or “go deeper”—Claude uses your
intent and the actual risk to choose an appropriate workflow. Simple messages and
copy edits stay with the main conversation and focused checks, rather than a full
agent team. Sensitive work still gets the checks it needs. No new commands.

**Watch Claude coordinate the team.** A live map connects the Orchestrator to
invoked specialists. One-shot handoff signals show tasks starting and returning,
while parallel work stays visible together. Reduced motion keeps the same state
without moving signals. These connections represent recorded session activity,
not private agent conversations.

Compact agent panels appear as specialists join,
show their task and latest action, and become muted when finished. Unused agents
stay out of the way. Meaningful file activity replaces repetitive event labels;
finished tasks remain distinct from passing checks.

Version 0.26.0 is available from the Abacus Studio marketplace.

Publish requests open a development-to-release review PR without requiring paid
GitHub branch protection. Review, merging and deployment remain separate steps.

**See your AI team working locally.** Ask Claude to open the team dashboard to see
the Orchestrator and eight specialists, select an agent's activity and findings,
and see changes still on your computer. Submit and Request publish buttons queue
the existing Claude workflows; they never bypass review or publish directly.
Tracking is optional and local. Returned agents are not automatically marked as
passed, and stale activity is clearly labeled.

Ask Claude to
“Open the local team dashboard” and approve workspace tracking to get started.

The **Readiness Reviewer** adds a final evidence check before Claude calls a
substantial change ready to preview. It brings together the agreed requirements,
actual test results, and relevant specialist findings—so a missing test or an
unresolved problem does not get lost behind a reassuring “done.”

You get one clear outcome: **Ready to preview**, **Needs changes**, or **Needs human
input**, with the reason and next step. This builds on the recent UX, UI, Security
and Code reviewers; it does not replace Abacus's review or approve publishing.

See the
[installation and update guide](INSTALL.md) to get the latest release.

## More than a connection to your code

Claude Code provides the AI. The Abacus Studio plugin adds project context,
engineering playbooks, and a guided path from local development to review.

**Knowledge of your application.** Claude can retrieve relevant decisions,
agreements, and prior reasoning explicitly shared through Studio. You don't have
to explain the same background every time. Previous decisions inform the
conversation; they don't permanently prevent changes.

**Engineering guidance built in.** Abacus Engineering provides playbooks for
clarifying requirements, planning features, testing, debugging, and reviewing
code. Larger changes get a structured approach; small improvements stay simple.
For substantial features, a read-only Spec Writer agent can help clarify the
requirements before implementation, while Claude coordinates the work.
An implementation Builder agent can then work from those requirements, with
a Verification Specialist checking the result against agreed requirements.
It reports what passed, what failed, and what still needs checking. A read-only
Code Reviewer examines the engineering quality and potential regressions.
Abacus technical review and publishing approval remain separate.

**Design and security support.** Improve layouts and usability with the optional
Studio-managed Impeccable design package. Focused source reviews help identify
potential security issues and explain what still needs verification. They are
not a substitute for a complete security audit.
For sensitive changes, a read-only Security Reviewer traces relevant access and
data boundaries and reports concerns without probing your live application.
A UI Reviewer inspects actual desktop/mobile screenshots for layout problems
and visual consistency, keeping visual review separate from workflow testing.
A separate UX Reviewer examines actual flow evidence for confusing actions,
missing feedback, and recovery problems, without mistaking screenshots for a
successfully tested workflow.

**A clearer view of the code.** When enabled for your application, a local code
map helps Claude locate related components before making substantial changes.

**Plain-language communication.** The plugin guides Claude to explain results
and next steps simply, with technical detail when you need it.

**See the result, not just the code.** Approved local browser checks can exercise
the changed flow and capture desktop and mobile-sized screenshots for inspection.
The plugin can reuse available browser tools or offer a managed Playwright setup.
Screenshots alone do not prove the feature works or replace your review.

These capabilities guide Claude's work; they don't guarantee correct code or
replace testing and professional review. Availability depends on your app's
Studio configuration.

## From your idea to your live application

1. **Set up your app.** Sign in to Studio, choose your application, and let guided
   setup prepare its code and local preview with your approval.
2. **Describe your change.** Ask Claude what you want to improve. Work through
   the plan, try the result, and refine it together.
3. **Save your progress.** Submit reviewed changes to your sandbox repository,
   so they aren't stored only on your computer. You don't have to be ready to
   publish.
4. **Request publishing review.** When you're ready, send the changes for review.
   Abacus can review them with you and coordinate the publishing process.

**Saving is not publishing.** Submitting saves changes to the sandbox repository.
Requesting publish opens a separate review request. Neither command automatically
merges changes or deploys your application.

## Get started

You'll need Claude Code and access to an application configured for local
development in Abacus Studio. The public plugin does not grant access to any
client's application, code, or data.

Follow the [Claude installation guide](adapters/claude/INSTALL.md), which includes the full
`claude plugin` installation and update commands for `abacusis/abacus-studio-plugin`.
Then run this in Claude Code:

```text
/abacus-studio:setup
```

Setup guides you through sign-in, app selection, and approval of the local setup.
After that, just describe what you'd like to change.

Both the [Claude guide](adapters/claude/INSTALL.md) and [Codex guide](adapters/codex/INSTALL.md)
walk through the same simple steps: install, connect, set up, build, save your
progress, and request Abacus’s publishing review. No developer setup instructions
are required to follow either guide.

Installation guides live in matching `adapters/<tool>/INSTALL.md` locations.
The [installation overview](INSTALL.md) helps you choose your tool.

> “Help me add a sales dashboard showing monthly revenue and recent orders.”

## Useful commands

You can describe your development goals naturally. These commands are shortcuts
for specific Studio actions:

| Command | When to use it |
| --- | --- |
| `/abacus-studio:setup` | Prepare your app and open a local preview. |
| `/abacus-studio:connect` | Sign in or renew your Studio connection. |
| `/abacus-studio:status` | Check your connection, role, and access. |
| `/abacus-studio:engineering` | Get help planning, building, debugging, or reviewing. |
| `/abacus-studio:design` | Improve a screen's design or usability. |
| `/abacus-studio:security` | Request a focused source-code security review. |
| `/abacus-studio:submit` | Review and save changes to the sandbox repository. |
| `/abacus-studio:update` | Download the latest app code when your workspace can update safely. |
| `/abacus-studio:request-publish` | Send your changes for publishing review. |
| `/abacus-studio:disconnect` | Revoke the plugin's Studio connection. |

## Your project stays yours

Studio checks your access to the assigned private client repository. Sign-in
credentials use your computer's secure credential store. If your app needs
sandbox keys, authorized setup can place them in a local, Git-ignored environment
file; local users and coding tools can read that copy. Never use production keys
for this workflow or paste credentials into chat.

See [security and access details](SECURITY.md) for boundaries and limitations.

## Behind the plugin

**An optional local team dashboard** makes the work visible without exposing
private AI reasoning or conversation transcripts. Local changes and cached Git
comparisons are shown separately; the dashboard does not verify GitHub freshness.
After queuing an action, return to Claude and send “Continue.” Normal checks and
approvals still apply.

Abacus maintains the engineering guidance and Studio workflows. Skills provide
specialized playbooks, while Studio's MCP services supply authorized project
information and workflow access. Optional project tools add design guidance and
local code mapping without requiring clients to learn another set of commands.
A small local routing hook helps Claude choose the development workflow from a
normal request. It does not upload data, edit your project, or grant permissions.
Automatic selection is guidance, not a guarantee for every request or model.

For installation help, updates, or project access, contact your Abacus team.

[Installation and updates](INSTALL.md) ·
[Maintainer guide](references/maintainer-guide.md) ·
[Third-party acknowledgements](THIRD_PARTY_NOTICES.md)

By Abacus Internet Solutions Inc. See [LICENSE](LICENSE) for the current licensing
document, which is marked as a draft, not effective terms. Third-party components
retain their own applicable licenses.
