---
name: status
description: Check only Studio connection, role, and granted access.
disable-model-invocation: true
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/studio_git.py" connection-status`.
It uses the one shared helper authorization and Studio's get_connection_status
tool privately. No selected app or local project is needed. It never opens
browser sign-in. Report only Connected/Not connected, returned roles, and
granted access. No role assigned means the returned roles list is empty.

Map projects:read to View apps, local:write to Local development,
conversations:read to Read conversations, and messages:write to Send Studio requests.
An administrator role does not expand granted_scopes. Never infer a role.
On a service/network error say Could not verify connection. If the helper
environment is missing, say Status unavailable and offer Setup; do not install
packages or start sign-in as part of Status.

If the user explicitly asks for setup diagnostics or provides a workspace to
check, also run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup_health.py" --workspace
"<explicit absolute workspace>"` with the approved Python environment. Without
a workspace, omit that argument. This is a local read-only check, not a repair.
Report actionable findings briefly. The manifest version is on disk, not proof
of the running session's version or the latest release. Connection still comes
only from connection-status; health results never prove a working preview.

For ordinary connection Status, never search the home directory, inspect workspace markers, enumerate apps,
fetch Git, check runtimes, test previews, or run the helper's Git `status` action.
The helper reads its own OS credential entry privately; never inspect or print
credential values in Claude. Do not expand ordinary Status into a health check.
