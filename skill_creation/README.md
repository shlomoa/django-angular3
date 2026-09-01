# Skill Creation Working Set

This folder splits `doc/GENERATE_AI_AUTOMATIONS.md` into smaller working files for the
skill authoring cadence described in `doc/SKILL_AUTHORING_PLAN.md`.

This folder is intentionally skill-specific. It is the working set for the
SKILLS subset of the broader AI automation model; it is not the execution workspace for TOOLS, HOOKS, or PLUGINS.

No sibling `tools_creation/` workspace is defined today. Tool candidates are
still tracked at the design and analysis level in `doc/` rather than as a
split, step-by-step authoring program comparable to the eleven skills.

`doc/GENERATE_AI_AUTOMATIONS.md` remains the canonical Skill source. These files are
derived working copies for planning, implementing, and verifying one Skill at a
time through the cadence in `doc/SKILL_AUTHORING_PLAN.md`. If a split file appears incomplete or inconsistent with
`doc/GENERATE_AI_AUTOMATIONS.md`, resolve the discrepancy against `doc/GENERATE_AI_AUTOMATIONS.md` and
then update the split file.

For the umbrella automation model and primitive-selection policy, use
`doc/GENERATE_AI_AUTOMATIONS.md`, `doc/ARCHITECTURE.md`,
`doc/REQUIREMENTS.md`, and `doc/APP_BUILDER_REQUIREMENTS.md`. Use this folder
only when the task is specifically about authoring, reviewing, or verifying a
skill.

All ngdj-dependent Skill work in this folder follows the identity, ownership,
and upstream-source policy in `doc/ARCHITECTURE.md` §2.6. Command examples in
the split files describe djng integration use; they do not define ngdj command
names, options, schemas, or behavior and must be revalidated against the
applicable upstream source when changed.

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
    01-angular-workspace-foundation.md
    02-angular-app-composition.md
    03-angular-api-integration.md
    04-angular-data-service-composition.md
    05-angular-field-component-composition.md
    06-angular-form-field-composition.md
    07-angular-component-composition.md
    08-angular-complex-component-composition.md
    09-angular-reactive-form-composition.md
    10-angular-page-composition.md
    11-angular-site-composition.md
```

## Use

For each skill phase, read the matching file from `skills/` plus only the
shared files that the skill references or needs. Render provider-native output
through the applicable adapter; this folder is authoring material, not rendered
or installed Skill output.
