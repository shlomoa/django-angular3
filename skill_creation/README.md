# Skill Creation Working Set

This folder splits `doc/GENERATE_AI_AUTOMATIONS.md` into smaller working files for the
skill authoring cadence described in `doc/SKILL_AUTHORING_PLAN.md`.

This folder is intentionally skill-specific. It is the working set for the
SKILLS subset of the broader AI automation model; it is not the planning or
execution workspace for TOOLS, HOOKS, or PLUGINS.

No sibling `tools_creation/` workspace is defined today. Tool candidates are
still tracked at the design and analysis level in `doc/` rather than as a
split, step-by-step authoring program comparable to the eleven skills.

`doc/GENERATE_AI_AUTOMATIONS.md` remains the original design specification. These files are
the operational source for planning, implementing, and verifying one skill at a
time. If a split file appears incomplete or inconsistent with
`doc/GENERATE_AI_AUTOMATIONS.md`, resolve the discrepancy against `doc/GENERATE_AI_AUTOMATIONS.md` and
then update the split file.

For the umbrella automation model and primitive-selection policy, use
`doc/GENERATE_AI_AUTOMATIONS.md`, `doc/ARCHITECTURE.md`,
`doc/REQUIREMENTS.md`, and `doc/APP_BUILDER_REQUIREMENTS.md`. Use this folder
only when the task is specifically about authoring, reviewing, or verifying a
skill.

Create a sibling folder such as `tools_creation/` only if tool work reaches
the same level of dedicated authoring cadence: named tool specifications,
shared authoring guidance, review workflow, and split working files that are
easier to manage separately than in `doc/`.

## Layout

```text
skill_creation/
  README.md
  skill-building.md
  shared/
    skill-architecture.md
    angular-conventions.md
    angular-material-patterns.md
    openapi-integration.md
    templates.md
  skills/
    01-ng-workspace.md
    02-ng-app.md
    03-ng-api.md
    04-ng-data-service.md
    05-ng-field-component.md
    06-ng-form-field.md
    07-ng-component.md
    08-ng-complex-component.md
    09-ng-reactive-form.md
    10-ng-page.md
    11-ng-site.md
```

## Use

For each skill phase, read the matching file from `skills/` plus only the
shared files that the skill references or needs. Keep authored skills in
`.claude/skills/<skill-name>/`; this folder is planning and source material,
not the installed skill output.
