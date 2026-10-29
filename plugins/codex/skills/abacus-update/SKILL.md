---
name: abacus-update
description: Get the latest app code from the Studio-authorized client development branch. Use for update my app, pull latest changes or sync from GitHub. Not for updating the plugin itself, submitting changes or publishing.
---

Resolve `<plugin-root>` from the absolute source path of this loaded skill: two directories above its directory. Substitute that real path in commands; it is not an environment variable. Skill references name packaged workflows, not a Claude Skill tool. Read references/codex/delegation.md before any specialist handoff; use approved project-scoped Abacus profiles when available.

Read and apply [Client communication](../../references/client-communication.md) completely.
Read [Update workspace](../../references/changes/update.md) completely.
Resolve scripts against `<plugin-root>/scripts/`.
An explicit request to update the app authorizes fetch and a safe fast-forward,
not pushing or discarding unfinished work. An ambiguous “sync” needs clarification
only if the direction (download versus submit) is unclear.
For unfinished/diverged work, offer the documented explicit local-only integration
option. Conflict handling uses the shared playbook, not a new agent or silent
overwrite. Local checkpoint/merge authority never becomes push authority.
