# Behavioral release checks

This maintainer suite checks six scenarios for each host: quick edit, structured
plan, sensitive plan despite quick wording, mockup-only boundary, combined
submission authorization, and missing verification. It does not install a plugin,
launch a paid model, change hook trust, or read existing session stores.

Prepare twelve disposable case folders outside the repository:

```text
python3 scripts/behavioral_checks.py prepare /absolute/new/evaluation-folder
```

`prepared_not_run` is not success. In a fresh Claude Code or Codex session, load
the current candidate package using the documented local-testing process for
that host and open one case's fixture folder. Use only synthetic files; disable
real Studio/MCP connections, production access, Git remotes, and unneeded tools
through supported host settings. Never bypass sandboxing, permissions, or hook
trust for an evaluation. Use the current user's configured model, not a hardcoded
paid model. Record the host version and candidate source digest in the manifest.

Open the case's `workspace/` subfolder, not the manifest/log folder, as the app.
Run the exact `PROMPT.txt` without naming the skill the test is meant to discover.
Capture/export that case's tool events as `trace.jsonl` using the host's supported
mechanism (Claude stream-json or an explicit equivalent export; Codex exec --json
or an explicit equivalent export). Do not scan real client sessions or upload
traces. Include tool results and a successful terminal completion event. Inspect
the actual fixture diff as well as tools and the final response. The grader
cannot see edits omitted from an export; the human review covers that gap.

After exporting the trace, run `python3 scripts/behavioral_checks.py capture
/absolute/case/manifest.json` to capture the after-state of that fixture. The
before-state was captured during preparation; read-only cases require no change.
This does not itself grade or approve anything.

Run the grader once to get `trace_sha256`, review that exact trace and fixture
changes against the scenario rubric in `scripts/behavioral_checks.py`, then fill
`human_review.trace_sha256`, `passed` and specific `notes` in the case manifest.
Human approval without current machine evidence is not a pass.

```text
python3 scripts/behavioral_checks.py grade /absolute/evaluation-folder
```

The full release check exits zero only when all six cases for both hosts have
current passing evidence and human review. Missing cases, stale candidate source,
incomplete/failed traces, missing delegation observations, or unreviewed output
remain `not_verified`. Individual failures remain visible. Rerun cases after
changing the candidate; don't change the manifest digest to relabel old runs.
Keep the report and reviewed traces locally with the release evidence. Do not
automatically include them in the public package or commit them.

## What is observed

Claude: actual successful Skill invocation or skill-file read, Agent/Task attempts
and successful returns, file-edit attempts, and terminal result. Merely mentioning
a skill in text is not activation. Read failure is not activation.

Codex: successful simple `cat` reads of the Engineering skill, file changes,
command activity, and completed/failed turns. A final message, `echo`, or a search
result naming the skill isn't activation. For native delegation, use an explicit
app-server export with `thread/started` role identity, `item/completed`
`collabAgentToolCall` completed agent states, and the main thread's
`turn/completed`. Never infer the role from prompt wording. Fields were checked
against the installed CLI's generated v2 JSON Schema; live behavior is still
pending. A plain exec trace lacking role identity cannot prove Spec Writer ran.
More complex skill-read commands or unsupported event formats remain unverified.
Read-only cases also compare fixture fingerprints; the missing-check scenario
explicitly forbids command execution, even if no files changed.

Semantic behavior (appropriate care, mockup scope, no redundant approval asks,
and refusal of unsupported readiness) requires human review. No keyword match can
reliably distinguish “tests passed” from “I cannot say tests passed.” The review
is tied to the trace hash; neither the hash nor a self-supplied manifest proves
trace authenticity. This is a maintainer release check, not client enforcement.

Default automated CI validates the grader with labeled synthetic events and tests
the command receipt helper without model charges. It does **not** establish live
Claude/Codex behavior. Live evaluation is a separate release step and pending until
real runs are recorded. A missing test result cannot become a marketing claim.

Source reference for Codex JSONL: https://learn.chatgpt.com/docs/non-interactive-mode
