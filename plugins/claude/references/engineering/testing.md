# Behavior-first testing

Use the project's testing framework and configured commands. Identify public boundaries that cover the change: an API request, component interaction, service interface, or critical user journey. Explain important coverage tradeoffs; ask only when they materially affect scope or cost.

For behavior changes, prefer one vertical slice at a time: write a test that fails for the intended missing behavior, run it and establish why it fails, implement the smallest correct change, then rerun. Do not write a batch of speculative tests before understanding the implementation. Refactor safely after passing tests where it serves the requested change.

Assert externally observable behavior, not private implementation details. Expected outcomes must be independent of the implementation. Mock genuine external boundaries when needed, not every internal collaborator. Include relevant failure and permission cases, not just a happy path.

For bug fixes, the regression test must reproduce the actual failure pattern. If a meaningful test cannot be run, document the limitation and use another observable verification method; never claim a passing test from inspection alone.

Run focused checks during development, then relevant configured checks before completion. Submit still executes and verifies Studio's own approved checks; local tests do not replace them.

For structured changes, read [Command evidence](verification-records.md) to record
approved checks against current local source. Passing command receipts do not
establish criterion coverage, browser behavior, live integrations, or readiness.

For visible behavior, read [Local browser verification](browser-verification.md).
Exercise the approved user flow and inspect desktop/mobile screenshots using an
image-capable tool. A screenshot file is evidence of capture, not a passing test
or proof it was visually inspected. Missing auth, blocked network requests, stale
source, and unexecuted checks must be reported. Builder-reported evidence is not
independent verification or publishing approval.
