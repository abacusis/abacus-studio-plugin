# Combine changes without losing intent

Use this playbook when Submit or an explicitly approved local integration reports
conflicts, or when overlapping behavior could be broken by an automatic merge.
No new agent or client GitHub login is needed. Use only the Studio Git helper for
Git mutations; source edits use the host's authorized editing tools.

## Understand and explain

Inspect the common ancestor, client's saved commit and incoming sandbox revision,
not just conflict markers. Read the relevant surrounding handlers, tests and
approved requirements. Use read-only local Git inspection without credentials;
do not fetch, checkout, stage or resolve with raw Git commands.

Explain each meaningful disagreement as behavior: “You and the Abacus team both
changed this filter. Your version includes inactive animals; theirs excludes them.”
Recommend a combined result and explain what it preserves. Do not ask clients to
choose “ours/theirs,” dump raw patches as the only explanation, or silently prefer
the newest version. Ask a short business question when intended behavior is unclear.

Obtain approval of the proposed resolution before editing conflicting files.
One clear approval can cover the described group of resolutions; do not request
approval per line or repeat authorization to run already-covered checks.
Permissions, payments, private data, deletion, schema changes and unclear behavior
need a relevant decision/review; do not guess because the merge is technically easy.

## Resolve and verify

Apply the agreed edits, preserving both intended changes wherever compatible.
For binary assets, delete/modify conflicts, excluded paths or secrets, stop and
explain a concrete choice or ask for Abacus review; do not blindly pick a side.
Run `resolve ... --approved` only for the helper-owned merge. It refuses remaining
conflict markers; a clean Git merge is not proof of correct application behavior.

Review the combined diff even if Git merged automatically. Identify the intended
behavior from each side and check both, plus their interaction. A focused regression
or browser flow should cover the combined behavior when feasible. Inspect configured
test/build commands before `check ... --approved`. Never waive failed or unavailable
checks. No configured checks means none ran, not a verified application.

## Finish or stop safely

For Submit, continue the existing checked push path only under the actual Submit
request. For local integration, stop locally after review/checks: do not call Submit
or publish. Say “Combined locally; not submitted,” and list any verification gap.

If intent remains unclear or checks fail after two bounded correction rounds,
stop and offer Abacus review with a sanitized summary of the competing behavior,
affected files, saved and incoming revisions, decisions and actual checks. Do not
create a ticket or send source externally without the user's request.

For an active helper-owned conflict, explain that `cancel ... --approved` abandons
merge-resolution edits but retains the saved pre-merge client commit. Ask before
cancelling. Do not reset hard, force-push, stash automatically, delete locks or
promise cancellation of an already-completed merge; completed merges need review.
