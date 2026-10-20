---
name: abacus-engineering
description: Plan, build, fix, test or review application changes with Abacus engineering playbooks, prior project decisions and proportionate verification. Includes optional mockups and the local team dashboard. Not general conversation, connection status or plugin installation help.
---

# Abacus Engineering for Codex

Read [Client communication](../../references/client-communication.md). Keep client
updates brief and explain outcomes, not every internal step. The installed plugin
root is two directories above this skill's directory. Resolve real absolute paths
from this loaded source; never execute literal `<plugin-root>` placeholders or
assume a Claude environment variable exists.

Read [Workflow depth](../../references/engineering/workflow-depth.md) first.
Infer quick/deep intent and consequences. Ordinary copy, spacing and confirmation
messages stay in the main conversation with focused checks. No automatic team,
spec document, map or dashboard just for a small change.

For requested mockups or meaningful visual uncertainty, apply
[Mockup-first](../../references/engineering/mockup-first.md). Keep sample data
isolated. Respect mockup-only and build-directly; visual approval is not backend
authorization. Planning-only never authorizes edits.

For structured/sensitive work read [Coordinator workflow](../../references/engineering/orchestration.md)
and [Codex delegation](../../references/codex/delegation.md). The main Codex
conversation coordinates. Approved Setup installs eight project-scoped native
profiles named `abacus-spec-writer`, `abacus-builder`, `abacus-verifier`,
`abacus-code-reviewer`, `abacus-security-reviewer`, `abacus-ui-reviewer`,
`abacus-ux-reviewer`, and `abacus-readiness-reviewer`. Prefer these when the current
session lists them. The source instructions are in `roles/`; they are not Claude
agents. Use only the host's actually available, authorized
delegation tools. Supply the relevant role file completely and the scoped handoff.
Never invent an agent type, change configuration, bypass a host restriction or
launch a separate headless coding session to obtain delegation.

Use Spec Writer for structured planning; Builder only for authorized implementation;
Verifier for actual approved checks; Code/Security/UI/UX reviewers when relevant;
Readiness Reviewer for substantial implemented work. Read their role procedures
and the corresponding playbook before handoff. Read-only procedures are behavioral
limits, not a claim that plugin files enforce a tool sandbox. Do not give reviewers
extra privileges. If separate delegation is unavailable or forbidden, disclose it
and do permitted work in the main conversation; never label this independent review.
An explicit request for separate review remains unmet until it actually runs.
Keep the shared maximum of two correction rounds. Evidence must match current code.

For required command checks on structured implementation, read
[Command evidence](../../references/engineering/verification-records.md). The
shared helper records approved checks and source freshness; it does not grant
execution approval or certify readiness. Focused edits may use direct checks.

For a Studio-linked app, use the packaged `abacus-project-knowledge` skill before
consequential behavior decisions. Missing knowledge is unavailable, not empty.
Load only relevant shared planning/testing/debugging/architecture/review playbooks.
Source mapping is optional for unfamiliar substantial work, not every edit.
Visible changes use [Browser verification](../../references/engineering/browser-verification.md):
actual image inspection for visual claims; screenshots alone do not prove a flow.
For relevant security boundaries use `abacus-security`, not a live penetration test.

When asked to open the team dashboard, read
[Local dashboard](../../references/engineering/local-dashboard.md). It is opt-in,
local and dependent on trusted supported hooks. Missing observation is not a
working agent. Do not read transcripts to fill gaps or promise background recovery.

Submit and Request publish remain separate authorized workflows through their
packaged skills. An explicit “submit and publish” request covers both in sequence
without repeated confirmations; read references/changes/authorization.md.
Submit alone does not open a PR. Never automatically commit, push, open PRs, merge, deploy, run
migrations, or expand access. Reviewed sandbox changes use `abacus-sandbox-database`.
Readiness is not human approval, a security certification or publishing permission.
