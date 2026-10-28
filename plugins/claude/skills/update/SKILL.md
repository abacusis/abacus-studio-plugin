---
name: update
description: Get the latest app code from the Studio-authorized client development branch. Use for update my app, pull latest changes or sync from GitHub. Not for updating the plugin itself, submitting changes or publishing.
---

Read and apply [Client communication](../../references/client-communication.md) completely.
[Update workspace](../../references/changes/update.md) completely.
Resolve scripts against `${CLAUDE_PLUGIN_ROOT}/scripts/`.
An explicit request to update the app authorizes fetch and a safe fast-forward,
not pushing or discarding unfinished work. An ambiguous “sync” needs clarification
only if the direction (download versus submit) is unclear.
