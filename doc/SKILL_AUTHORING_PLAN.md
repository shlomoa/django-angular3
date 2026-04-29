# Skill Authoring Plan

## Scope

This document captures the working plan for authoring the eleven Angular
skills described in `GENERATE_SKILLS.md`. It records the decisions made during
the planning conversation, the framework that will be applied uniformly to
every skill, and the items that remain open or evolving.

The document is itself part of the planning record. It does not replace
`GENERATE_SKILLS.md`, which is the design specification, or `CLAUDE.md` and
`.github/copilot-instructions.md`, which are the operating rules. Any conflict
between this document and either of those is resolved in favor of the
operating rules.

## Project context

`django-angular3` is a Python tool. It does not on its own run an Angular
workspace; it produces project instances that combine Django REST Framework on
the backend with Angular Material on the frontend, generated against a
contract-first OpenAPI specification.

There are therefore two distinct configuration files in play, and they must
not be conflated.

`django-angular3.json` configures this repository — the meta-tool. It tells
the tool how to behave: where to look for OpenAPI input, where to write build
plans, which package manager to use, and so on.

`django_project.json` is a configuration file carried by each generated
project. It supplies project-specific inputs (workspace name, application
name, route prefixes, theming choices, OpenAPI source paths for that project,
UI specification paths, and so on). The eleven skills authored from
`GENERATE_SKILLS.md` operate on a generated project, so the bulk of their
run-time input is sourced from `django_project.json` and from files it points
to.

Either file may legitimately contain pointers to other files that are not yet
present. A pointer to a missing-but-promised file is a valid pipeline state,
not an error: it represents work that an earlier skill in the orchestration is
responsible for producing. Only invalid (malformed or unparseable) referenced
files are hard errors.

## Two-tier input model

Two distinct kinds of "input" matter and they are kept separate when a skill
is described.

Author-time input is what the skill author needs in order to write the skill.
This includes the capability the skill provides, the conditions under which it
should be invoked, the format of its output, and the format and constraints of
the run-time input the skill must accept. Author-time input is a description,
not an instance.

Run-time input is the concrete values an end user (or, more typically, an
orchestrator) provides when invoking the skill. For these eleven skills,
run-time input is sourced from `django_project.json` and from files it points
to, never from prompts typed in chat by a human end user.

Each skill's `Inputs` section in `GENERATE_SKILLS.md` is best understood as a
schema describing both layers: which keys are read directly from
`django_project.json`, and which are paths the skill must dereference and
parse. The authored SKILL.md will be explicit about the layer for every input.

## Skill format and output location

Skills are authored in the standard Anthropic Agent Skill format — a
`SKILL.md` with YAML frontmatter (`name`, `description`), a markdown body, and
optional `scripts/`, `references/`, and `assets/` subdirectories. The custom
format described in `GENERATE_SKILLS.md` (with `user-invocable: false`,
`context: fork`, `allowed-tools`, `{{context:...}}`, `{{template:...}}`, and
`.tpl` files) is treated as design notation only; no skill file is produced in
that format.

Each finished skill is committed to `.claude/skills/<skill-name>/` in this
repository so it is part of the codebase and reviewable. Each finished skill
is also packaged into a `.skill` archive via the skill-creator's
`package_skill.py` and installed into the Cowork skills folder so it is
auto-discoverable in this session.

Shared context files (`angular-conventions.md`, `angular-material-patterns.md`,
`openapi-integration.md`) live at `.claude/skills/shared/` and are referenced
from individual skills via relative paths. Packaging is responsible for
inlining these shared files into each `.skill` archive so the installed
package is self-contained.

## Tooling boundary

The integration toolchain for the generated project, per `README.md`,
`doc/ARCHITECTURE.md`, and `doc/REQUIREMENTS.md`, is `drf-spectacular` for
OpenAPI schema export from the consuming Django project, `oasdiff` for schema
diff and change detection (breaking changes block downstream generation until
acknowledged), and `ng-openapi-gen` for Angular client generation. No
alternative Angular client generator is in scope, and no alternative OpenAPI
diff tool is in scope.

Skills do not call Angular CLI, `ng-openapi-gen`, or `oasdiff` directly. They
invoke this repository's Python wrappers (`ng_new`, `ng_config`,
`ng_openapi_gen`, `ng_build`, and so on), which honor the operating principle
that Angular tooling must not download packages at runtime and that workspace
dependencies are used locally via `pnpm exec`. Each skill bundles the
wrappers it needs in its `scripts/` directory.

The default settings surface for this repository (per `README.md`) is `pnpm`
as the package manager, `scss` as the stylesheet format, routing enabled,
`build_configuration` of `production`, and a command allowlist that defaults
to only `ng_openapi_gen` — meaning wrappers plan dry-runs by default and only
`ng_openapi_gen` actually executes unless the user explicitly broadens the
allowlist. Skills must respect this surface and not assume executability of
other planned commands.

## Per-skill cadence

Every skill goes through three phases, in order, with explicit user approval
between phases.

Plan. Capture intent, conduct the interview, and produce a sketch of the
skill: its `name`, its `description`, the run-time inputs it accepts and which
`django_project.json` keys feed them, the files it produces, the scripts and
shared context it depends on, the open questions to be resolved during
implementation, and the test prompts that will exercise it.

Implementation including test generation. Write the SKILL.md body, create
`scripts/`, `references/`, and `assets/` as needed, and author the test
prompts and assertions agreed in Plan.

Verification. Run the tests (with-skill versus baseline), grade them, render
the result for review, and incorporate feedback. Once Verification is
approved, the skill is packaged into a `.skill` archive and installed into the
Cowork skills folder.

Subagents may be used inside any phase where they are useful — for example,
to run the with-skill and baseline test cases in parallel during Verification
— provided their use does not collapse or cross phase boundaries.

## Per-skill input validation

Each skill validates its own inputs and is responsible for distinguishing
three states that an indirect input can be in: present, promised but missing,
and invalid. There is no shared validation helper. The cost of duplicating
classification logic across eleven skills is accepted in exchange for keeping
each skill self-contained and packageable.

## Description optimization

Even though the eleven skills are invoked by an outer orchestrator that knows
them by name, the standard skill-creator description-optimization loop
(`run_loop.py`) is run for each skill. The optimized description is committed
and packaged. Redundant optimization is treated as low-cost insurance.

## Single-source-of-truth exception

The single-source-of-truth principle stated in
`.github/copilot-instructions.md` continues to apply to this repository's own
code, scripts, context, and templates. The chosen target architecture for
generated projects — Django REST Framework, Angular Material, OpenAPI client
generation — inherently duplicates contract definitions across layers (server
models, OpenAPI schema, generated TypeScript models, form validators). That
duplication is approved and is not eliminated.

## The eleven skills

The skills are authored in the dependency order suggested by
`GENERATE_SKILLS.md` so that earlier skills' outputs are available as ground
truth when test cases for later skills are exercised.

1. `ng-workspace` — Angular Material workspace boilerplate (foundation;
   depends on nothing).
2. `ng-app` — Angular Material application inside a workspace (depends on 1).
3. `ng-api` — Angular API client generation from OpenAPI (depends on 2).
4. `ng-data-service` — Angular data model service wrapping a generated
   `<Resource>ApiService` (depends on 3).
5. `ng-small-field` — Angular Material small field-level component (depends
   on 2).
6. `ng-form-field` — Angular Material form field with `ControlValueAccessor`
   (depends on 2).
7. `ng-component` — Angular generic component generation (depends on 2).
8. `ng-complex-component` — Angular Material complex component (depends
   on 2).
9. `ng-reactive-form` — Angular Material reactive form (depends on 2 and 6;
   optionally on 4).
10. `ng-page` — Angular Material page generation (depends on 2; composes 4,
    7, 8, and 9).
11. `ng-site` — Angular Material site generation (composes 2 through 10).

## Ongoing and open items

`django-angular3.json` is treated as evolving. Its schema is updated
incrementally as each skill reveals what it actually needs to read; it is not
refreshed up-front and not deferred to a separate post-skills task.

The Angular workspace fixture used to verify generated skills end-to-end is
created when the first skill that needs it (`ng-workspace`) reaches its
Verification phase. There is no fixture today.

Open questions that surface during a skill's Plan phase are recorded in this
document under that skill's section, kept until resolved, and removed once the
resolution is captured in the skill itself.

## Status

Planning phase complete. The next action is to begin the Plan phase for
`ng-workspace`.
