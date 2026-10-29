# Update workspace

Use this workflow to download current code into an existing authorized client Git
workspace. Do not use Submit just to download changes. A clear “get the latest
changes” request covers this local update; no redundant confirmation is required.

Read the selected workspace's Studio metadata to identify its app, without printing
credentials. Use the setup-approved Python interpreter and packaged helper:

`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/studio_git.py" update --project-id "<Studio ID>" --workspace "<absolute workspace>" --approved`

Only the helper may fetch/update: it validates current Studio authorization,
repository and configured branch, uses private repository-scoped credentials and
holds the existing Git-operation lock. Never call its credential action directly,
run plain git pull/gh auth, ask for GitHub login or tokens, or change remotes.
If Studio authorization expired, use Connect; do not substitute GitHub credentials.

Handle the actual result:

- `already_current`: no newer remote commits; disclose any local commits ahead.
- `updated`: report a concise summary of downloaded changes. A changed dependency
  manifest means installation may be needed; inspect scripts and obtain applicable
  execution approval first. Do not automatically execute downloaded code, run checks,
  restart previews, or install packages as part of this command.
- `local_changes` or `diverged`: preserve all work. Offer to combine the updates
  locally without pushing, or use Submit only if the user actually wants to submit.
  Do not automatically stash or commit under an ordinary Update request.
- Locked, interrupted operation, unfinished submission, fetch failure or unsafe
  fast-forward: stop. Do not delete locks, reset, force checkout or retry blindly.

Ordinary Update never pushes, creates commits, opens PRs, migrates databases or deploys.
It retrieves the configured client development branch, not production's repository
or live deployed build. “Up to date” never proves that sandbox matches the live app.
If a live feature is missing, trace its deployment/source rather than claiming a
successful fetch must contain it. Report preview/testing status honestly.

## Explicit local integration

When the user asks to combine updates with unfinished work without submitting,
explain that the helper will save reviewed local changes in a local checkpoint
commit and merge the incoming sandbox revision. It will not push. Obtain that
permission unless the user already clearly authorized these local actions.
Review ALL local changes first, including untracked files; do not checkpoint
unrelated work without resolving scope. Secret/exclusion checks still apply.

Read [Conflict resolution](conflicts.md). Run the helper's `integrate` action with
the same project-id/workspace, `--approved`, and JSON description on stdin, just
as Prepare uses. It fetches before checkpointing, preserves the saved commit,
and records local-only intent. A normal Update request alone does not cover this.

For conflicts, follow the shared playbook, then `resolve ... --approved` after
the resolution is approved. For auto-merges, still review combined behavior.
Inspect and run authorized configured checks with `check ... --approved`; local
integration permission includes normal relevant project checks, not arbitrary
new service access or dependency installation. `integration_checked_local`
reports only configured checks; an empty checks_run list means no checks ran.
Failed checks remain failures. Finish locally, never invoke submit or publish.
The helper rejects a push from local-integration state; a later explicit Submit
request must start a fresh Prepare/review/check cycle.
