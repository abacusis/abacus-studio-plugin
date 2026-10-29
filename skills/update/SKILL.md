---
name: update
description: Get the latest app code from the Studio-authorized client development branch. Use for update my app, pull latest changes or sync from GitHub. Not for updating the plugin itself, submitting changes or publishing.
---

Read and apply [Client communication](../../references/client-communication.md) completely.
Read [Update workspace](../../references/changes/update.md) completely.
Resolve scripts against `${CLAUDE_PLUGIN_ROOT}/scripts/`.
An explicit request to update the app authorizes fetch and a safe fast-forward,
not pushing or discarding unfinished work. An ambiguous “sync” needs clarification
only if the direction (download versus submit) is unclear.
For unfinished/diverged work, offer the documented explicit local-only integration
option. Conflict handling uses the shared playbook, not a new agent or silent
overwrite. Local checkpoint/merge authority never becomes push authority.
