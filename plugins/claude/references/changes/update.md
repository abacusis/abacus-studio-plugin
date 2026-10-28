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
- `local_changes`: preserve all work and explain the blocker; Submit commits/pushes
  and needs the user's separate request. Do not automatically stash or commit.
- `diverged`: preserve both histories and offer the reviewed Submit workflow.
- Locked, interrupted operation, unfinished submission, fetch failure or unsafe
  fast-forward: stop. Do not delete locks, reset, force checkout or retry blindly.

Update never pushes, creates commits, opens PRs, migrates databases or deploys.
It retrieves the configured client development branch, not production's repository
or live deployed build. “Up to date” never proves that sandbox matches the live app.
If a live feature is missing, trace its deployment/source rather than claiming a
successful fetch must contain it. Report preview/testing status honestly.
