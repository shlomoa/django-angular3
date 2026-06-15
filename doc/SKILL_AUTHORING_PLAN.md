# Skill Authoring Plan

## Scope

This document captures the working plan for authoring the eleven Angular
skills described in `GENERATE_AI_AUTOMATIONS.md`. It records the decisions made during
the planning conversation, the framework that will be applied uniformly to
every skill, and the items that remain open or evolving.

This is a skills-only sub-plan. The broader AI automation model — including
the roles of TOOLS, HOOKS, and PLUGINS alongside SKILLS — is defined in
`GENERATE_AI_AUTOMATIONS.md`, `ARCHITECTURE.md`, `REQUIREMENTS.md`, and
`APP_BUILDER_REQUIREMENTS.md`. This document covers only the authoring and
verification plan for the SKILLS subset.

The document is itself part of the planning record. It does not replace
`GENERATE_AI_AUTOMATIONS.md`, which is the design specification, or `CLAUDE.md` and
`.github/copilot-instructions.md`, which are the operating rules. Any conflict
between this document and either of those is resolved in favor of the
operating rules.

## Project context

`djng` (`django-angular3`) is the solution — this repository, the Django
package, and the tool. It contains the agent, the AI automation subsystem,
`build_app`, and all configuration files. It produces generated apps that combine Django REST
Framework on the backend with Angular Material on the frontend, generated
against a contract-first OpenAPI specification. This document is concerned
only with the SKILLS subset of that automation subsystem. See §Glossary.

There are two configuration files that skills must not conflate.

`django-angular3.json` is the `djng` tool configuration. It tells the tool
how to behave: workspace root path (`angular.output`), project name
(`project.name`), OpenAPI source path (`openapi.source`), package manager,
stylesheet format, routing settings, and so on. This file is **golden** —
`build_app` reads it as current and authoritative on every run; it is never
diffed between runs and its changes take effect immediately on the next
invocation. The eleven skills authored from `GENERATE_AI_AUTOMATIONS.md` operate on a
generated app. Their run-time inputs are sourced from the generated app's
`django-angular3.json`.

`<project>.project.json` is the generated app configuration file (placeholder
name — schema and final name are not yet defined; see `TODO.md`). It defines
the UI artifacts — pages, components, forms — used for non-CRM change
detection. `build_app` diffs this file between runs to detect non-CRM changes;
it is not golden. Skills that depend on non-CRM changes receive them as part
of the `ChangeSet` procedure input, not by reading `<project>.project.json`
directly.

Either configuration file may legitimately contain pointers to other files
that are not yet present. A pointer to a missing-but-promised file is a valid
pipeline state, not an error: it represents work that an earlier skill in the
orchestration is responsible for producing. Only invalid (malformed or
unparseable) referenced files are hard errors.

## Two-tier input model

Two distinct kinds of "input" matter and they are kept separate when a skill
is described.

Author-time input is what the skill author needs in order to write the skill.
This includes the capability the skill provides, the conditions under which it
should be invoked, the format of its output, and the format and constraints of
the run-time input the skill must accept. Author-time input is a description,
not an instance.

Run-time input is the concrete values an orchestrator provides when invoking
the skill. For these eleven skills, run-time input comes from two sources:

- **`django-angular3.json` keys** — read directly by the skill from the
  generated app's tool configuration file (e.g., `angular.output`,
  `project.name`, `openapi.source`). This file is golden; the skill reads it
  as current.
- **Procedure-level inputs** — supplied by `build_app` as the prompt for each
  guided agent session. These include resource names, component names, form
  names, placement hints, and similar procedure-specific values that vary per
  procedure node in the graph.

Run-time input is never typed in chat by a human end user.

Each skill's `Inputs` section in `GENERATE_AI_AUTOMATIONS.md` is best understood as a
schema describing both layers: which keys are read directly from the generated
app's `django-angular3.json`, and which are procedure-level values supplied by
`build_app`. The authored SKILL.md will be explicit about the layer for every
input.

## Skill format and output location

Skills are authored in the standard Anthropic Agent Skill format — a
`SKILL.md` with YAML frontmatter (`name`, `description`), a markdown body, and
optional `scripts/`, `references/`, and `assets/` subdirectories. The custom
format described in `GENERATE_AI_AUTOMATIONS.md` (with `user-invocable: false`,
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
`ARCHITECTURE.md`, and `REQUIREMENTS.md`, is `drf-spectacular` for
OpenAPI schema export from the consuming Django project, `oasdiff` for schema
diff and change detection (breaking changes block downstream generation until
acknowledged), and `ng-openapi-gen` for Angular client generation. No
alternative Angular client generator is in scope, and no alternative OpenAPI
diff tool is in scope.

Skills do not call Angular CLI, `ng-openapi-gen`, or `oasdiff` directly.

This document does not redefine when those responsibilities should move to
TOOLS, HOOKS, or PLUGINS in the broader automation model; it only defines how
the authored SKILLS must behave within the current governed construction flow.

`oasdiff` is run by `build_app` during the Change Derivation phase, before
any skill is invoked. Skills receive the resulting `ChangeSet` as procedure
input. A skill must never re-run `oasdiff` itself.

For Angular operations, skills invoke this repository's Python wrappers
(`ng_new`, `ng_add`, `ng_config`, `ng_gen_app`, `ng_openapi_gen`, `ng_build`,
`ng_workspace_delete`), which honor the operating principle that Angular
tooling must not download packages at runtime and that workspace dependencies
are used locally via `pnpm exec`. Each skill bundles the wrappers it needs in
its `scripts/` directory.

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
`django-angular3.json` keys feed them, the files it produces, the scripts and
shared context it depends on, the open questions to be resolved during
implementation, and the test prompts that will exercise it.

Implementation including test generation. Write the SKILL.md body, create
`scripts/`, `references/`, and `assets/` as needed, and author the test
prompts and assertions agreed in Plan.

App builder procedure integration. Once the skill is created, add a procedure
that uses it in the app builder program.

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
`GENERATE_AI_AUTOMATIONS.md` so that earlier skills' outputs are available as ground
truth when test cases for later skills are exercised.

This ordering is the authoring and verification order for the skills subset.
It is not, by itself, the complete statement of the mixed automation order for
`build_app`; that broader execution model is defined in
`APP_BUILDER_REQUIREMENTS.md`.

`GENERATE_AI_AUTOMATIONS.md` has been split into smaller working files under
`skill_creation/` to keep each phase focused. During authoring, read the
matching `skill_creation/skills/<number>-<skill-name>.md` file plus only the
needed files from `skill_creation/shared/`. `GENERATE_AI_AUTOMATIONS.md` remains the
original design specification; if the split copy is incomplete or inconsistent,
resolve against `GENERATE_AI_AUTOMATIONS.md` and update the split file.

For the authoritative dependency chain and ordering, see `APP_BUILDER_REQUIREMENTS.md` §Procedure Graph.

## Ongoing and open items

`django-angular3.json` is treated as evolving. Its schema is updated
incrementally as each skill reveals what it actually needs to read; it is not
refreshed up-front and not deferred to a separate post-skills task.

The Angular workspace fixture used to verify generated skills end-to-end is
created when the first skill that needs it (`angular-workspace-foundation`) reaches its
Verification phase. There is no fixture today.

Open questions that surface during a skill's Plan phase are recorded in this
document under that skill's section, kept until resolved, and removed once the
resolution is captured in the skill itself.

## Status

Document cascade complete. `APP_BUILDER_REQUIREMENTS.md`, `GENERATE_AI_AUTOMATIONS.md`,
and this document have been revised and aligned. This document now serves as
the skills-specific sub-plan under the broader AI automation model. The next
action is to begin the Plan phase for `angular-workspace-foundation`.

---

## Glossary

For authoritative definitions see `ARCHITECTURE.md` §2 and §19.

| Term | Definition | See |
|---|---|---|
| **AI automations** | The full automation model used by `djng`: SKILLS, TOOLS, HOOKS, and PLUGINS working together for bounded construction and integration. This document addresses only the SKILLS subset. | `ARCHITECTURE.md` §19, `GENERATE_AI_AUTOMATIONS.md` |
| **`djng`** | The `django-angular3` solution — this repository, the Django package, and the tool. Contains the agent, the AI automation subsystem, `build_app`, and all configuration files. | `ARCHITECTURE.md` §2.5 |
| **`ngdj`** | The `angular-django2` companion Angular package. Provides the Angular-side schematics and templates invoked by the agent during construction. | `ARCHITECTURE.md` §2.6 |
| **`build_app`** | The `djng` Django management command. Entry point that drives the agent through the procedure graph. | `APP_BUILDER_REQUIREMENTS.md` |
| **the agent** | The agentic orchestrator bundled in `djng`. At implementation level, driven by the Claude Agent SDK. | `ARCHITECTURE.md` §2.16 |
| **SKILLS** | Bounded AI skills (`SKILL.md` files) bundled in `djng` that guide the agent within each guided agent session. The subject of this document. | `ARCHITECTURE.md` §2.14, `GENERATE_AI_AUTOMATIONS.md` |
| **guided agent session** | A single agent session in which the agent carries out one procedure, guided by the specified SKILL(s). | `ARCHITECTURE.md` §2.13 |

## References

| Term | Description | Link |
|---|---|---|
| Claude Code Skills Documentation | General documentation for SKILL development. |[Claude Code Skills Documentation]|
| Claude Code SDK - creating skills | Documentation for creating skills using Claude Code SDK. |[Claude Code SDK - creating skills]|

[Claude Code Skills Documentation]: https://code.claude.com/docs/en/skills
[Claude Code SDK - creating skills]: https://code.claude.com/docs/en/agent-sdk/skills#creating-skills

---
