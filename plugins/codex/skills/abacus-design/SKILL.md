---
name: abacus-design
description: Improve your app's design, layout, and accessibility with Impeccable.
---

Resolve `<plugin-root>` from the absolute source path of this loaded skill: two directories above its directory. Substitute that real path in commands; it is not an environment variable. Skill references name packaged workflows, not a Claude Skill tool. Read references/codex/delegation.md before any specialist handoff; use approved project-scoped Abacus profiles when available.

Read and apply [Client communication](../../references/client-communication.md) completely.
Before authorized implementation edits, apply [Task freshness](../../references/engineering/task-freshness.md).
For mockup/prototype requests, first apply [Mockup-first](../../references/engineering/mockup-first.md)
to preserve sample-data isolation, scope and stop/continue boundaries. A preview
does not require a new command or automatically authorize backend implementation.
Use the project-local Impeccable skill at `.agents/skills/impeccable/SKILL.md`.
For a configured Studio app, first use `abacus-project-knowledge` to retrieve
the shared suite overview once per task and relevant design/workflow agreements.
Only current approved records establish requirements. Reuse unchanged context
within the task; suite awareness does not authorize changing another app.
Read its complete instructions before taking design actions and follow the
references it selects. Resolve its skill directory to that project-local folder,
not this wrapper's directory, when invoking its launcher or reading references.

Route `simplify` to `distill`; pass other supported actions and the user's target
through. With no action or target, ask which screen or component to improve.
When the user describes a design goal, select the appropriate workflow from
Impeccable's instructions. Do not require subcommands.
Codex can also use Impeccable directly when the user's design request fits.

For a bounded screenshot-only review, the coordinator can use the packaged role
`ui-reviewer` and bundled UI review playbook without running a full
Impeccable audit or making design changes. Supply approved current images and
relevant project design guidance; missing optional Impeccable does not prevent
basic visual review. Actual design work still follows the pinned package above.

For actual design work, if the package is missing, explain that Studio setup must install the enabled
design package. Do not fetch an arbitrary latest version or install global skills.
If another Impeccable installation wins name resolution, use the project-local
instructions explicitly so this workflow uses Studio's pinned version.

Do not install hooks or change Codex permissions as part of design work. The
package's engine launcher may download a version-pinned executable on first use;
respect host permissions and report that requirement if blocked. Installation of
skill files is not permission to execute scripts unrestrictedly.

Design work does not authorize submission, publishing, migrations, or production
deployment. Keep credentials and generated local caches out of submissions.
