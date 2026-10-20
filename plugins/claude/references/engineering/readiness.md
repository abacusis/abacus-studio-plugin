# Assess the whole change, not just the last successful check

The local coordinator supplies the accepted specification and criterion IDs,
current source including uncommitted/untracked edits, required check/review scope,
actual evidence and provenance, findings/dispositions, questions and correction
count. Readiness Reviewer reads these artifacts without running checks or editing.
It evaluates completeness and consistency; it does not certify evidence authenticity.

## Reconcile the evidence

For supplied command receipts, require a current coordinator/verifier inspection
using [Command evidence](verification-records.md). A stale, failed, timed-out,
not-run or missing required check is not a pass. A successful command proves only
its actual coverage; criterion labels and receipts cannot establish readiness on
their own. Do not run the helper from this read-only assessment.

For each criterion and relevant required review, identify the actual source/spec
checked, execution reporter, action/result and accessible evidence. Match current
source, not merely HEAD or a familiar filename. A planned test, stale screenshot,
Builder assurance or summary that disagrees with underlying evidence is not a pass.
Missing source identity or changed relevant code needs refreshed evidence.

Review scope is proportionate: UI for visible changes, UX for affected user tasks,
Security for sensitive boundaries, and the agreed functional/code checks. Preserve
coordinator-established required checks and documented not-applicable reasons.
If applicability is ambiguous, surface the uncertainty; do not waive checks or add
unrelated audits. A missing reviewer is not silently not applicable. Optional
polish does not block unless tied to agreed behavior or demonstrated consequences.
Material security Needs validation and required unverified flow/visual checks
prevent a readiness claim. Do not relabel them passed because other reviews passed.

## Choose one outcome

- **Ready to preview:** work exists, every required criterion/check and relevant
  review is complete for current source/spec, and no blocking finding, material
  validation gap or unresolved decision remains. Disclose nonblocking limitations.
- **Needs changes:** an actual defect or unmet requirement remains. Also list any
  missing or stale evidence; they do not disappear because a defect takes priority.
- **Needs human input:** no established defect takes priority, but a consequential
  decision, access, missing/stale required evidence or unresolved review disagreement
  prevents readiness. Explain what is needed and who can provide it.

Examples: all reviews look good but a required test never ran → Needs human input.
A required test actually failed → Needs changes. Tests passed on an older source
state → Needs human input pending recheck. Complete current checks with an optional
spacing suggestion → may be Ready to preview, with that limitation disclosed.

## Handoff, not approval

Return a brief outcome, criterion/review evidence matrix, blockers, optional notes,
and next action. Attribute supplied results honestly; no independently executed
tests are implied. The coordinator handles questions, approved checks and Builder
corrections. The existing maximum two correction rounds is shared across all
reviews, not a new allowance per agent. Require affected evidence to rerun after
fixes; after the limit, request new scoped direction instead of looping.

Ready to preview is not a publishing Approver decision, Abacus technical approval,
security certification, Git submission or deployment. Submit and Request publish
remain separate authorized workflows. This adds no browser tools, credentials,
source mutations, runtime quality gate, durable job state, or progress dashboard.
