# Start implementation from current team code

For an existing Studio-linked client workspace, before editing for a new authorized
implementation task (including Design), read and apply
[Update workspace](../changes/update.md). The implementation request includes this
bounded safe update; do not ask the client to repeat an Update command or approve
the same action. Respect an explicit instruction not to update or to stay offline.
This is agent guidance when the skill runs, not a background synchronization service.

Use the setup-approved interpreter and loaded package's `studio_git.py update`
with the existing workspace/app ID and `--approved`. For Codex resolve the loaded
plugin root directly; do not assume CLAUDE_PLUGIN_ROOT. Only that helper may fetch
and fast-forward, through Studio authorization. No GitHub login, plain git pull,
credential output, remote changes or substitute authentication.

Do this once before the first edits of a new task, not for every message, agent,
correction, test, or follow-up in the same task. Do not run it for general questions,
planning-only, review-only, unlinked repositories, or plugin maintenance. Do not
create Studio metadata or start Setup merely to perform this check. An explicit
Update request still uses its normal workflow. Submit retains its own fetch-first
safety check; this check is not permission to submit or publish.

- `already_current`: continue; local commits ahead are not an error or published work.
- `updated`: briefly say team changes were downloaded, inspect their effect on the
  task, and refresh affected context before editing. Do not automatically install
  dependencies, execute downloaded scripts, run checks or restart a preview under
  update authority; apply the implementation workflow's normal execution approval.
- `local_changes` or `diverged`: preserve everything. Do not stash, checkpoint,
  merge, reset or resolve automatically. Explain that newer-code integration has
  not completed (local_changes alone does not establish remote freshness). Offer
  to combine work locally through the existing conflict workflow, or continue on
  the current revision if the client explicitly chooses that. Wait for that choice
  before new implementation edits; do not silently build on uncertain code.
- Lock, interrupted submission/merge, authorization, network or other failure:
  stop before new edits, report the safe diagnostic and next step. No blind retry,
  deleting locks or claims that the workspace is current.

This updates the configured client development branch, not production. Never say
it synchronizes sandbox with the live app, updates the plugin, or deploys changes.
