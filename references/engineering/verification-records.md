# Command evidence, not a completion badge

For structured changes with required command checks, use the shared
`scripts/verification_record.py` helper when the approved workspace has its
Git-ignored `.studio/` setup folder. Focused edits may keep using a direct focused
check; do not add a specification or evidence ceremony just for a label change.

Run the exact approved check, linking it to the accepted criterion IDs:

```text
python3 -I "<plugin-root>/scripts/verification_record.py" run --workspace "<absolute app root>" --criterion R1 --criterion R2 --approved -- npm test
```

Resolve the plugin root from the loaded skill. The approval flag records existing
authority; it does not grant permission. Commands are argument lists, not shell
strings. Never put credentials into arguments. Use an explicit executable on
Windows if needed. The helper does not install anything, select a model, connect
to Studio, commit, push, or publish. It is not a sandbox: approved application
tests are executable code and their side effects still need appropriate scope.

The helper records command, criterion IDs, exit code, execution status, times,
and source fingerprints before and after execution. It covers tracked changes,
deletions, nonignored untracked files, and ordinary hidden source/config files.
Private environment/key/credential paths and common dependency/generated folders
are excluded. Those exclusions are not covered by this fingerprint. A test
depending on external state, ignored files, sandbox data, credentials, or deployed
functions needs separate current evidence; a matching hash cannot establish it.

Only ordinary runtime environment variables are inherited. Tests requiring extra
sandbox configuration need another approved execution path; do not broaden the
helper environment to ambient cloud secrets. A command that needs to show detailed
failure output can be run directly through the approved host. The helper retains
an output digest, not raw output or full logs, to reduce secret leakage.

Receipts are new private JSON files under `.studio/verification/`. Refuse symlinks,
tracked setup folders and evidence paths not excluded from Git. If the workspace
isn't prepared, use direct verification and disclose that no helper receipt was
created; do not automatically change Git ignores or overwrite setup files.

Before relying on a receipt after further edits, the coordinator or verifier runs:

```text
python3 -I "<plugin-root>/scripts/verification_record.py" inspect --workspace "<absolute app root>" --record "<receipt path>"
```

Changed source or edits during the command produce `stale`, even if exit code was
zero. Missing executable produces `not_run`; nonzero exit produces `failed`;
timeout produces `timed_out`. None is a pass. Inspection can only assess local
source freshness, not authenticity or external state. Receipts are locally
editable, not signed attestations. Do not treat one as a security boundary.

A passing receipt means **that command exited successfully for that source**.
Criterion IDs are supplied by the caller, not validated coverage. The coordinator
must still check that the command meaningfully exercises the requirement. Build
success is not browser verification; mocked tests are not live backend validation.
UI image inspection and UX interactions remain separate evidence.

The Readiness Reviewer receives the receipt, latest inspection result, and actual
coverage/gaps; it does not execute the helper itself or infer full readiness.
The helper always returns `ready_to_preview: false` because it cannot make that
whole-change decision. Rerun affected checks after relevant edits; do not rerun
unchanged checks solely because the assistant is about to send another message.
