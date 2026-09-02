# Skill Authoring Plan

## Scope

This document defines the per-Skill authoring and verification cadence for the eleven canonical guided Skills in `doc/contracts/SKILL_CONTRACTS.md`. Use a Skill only for AI judgment, interpretation, iterative repair, or refinement; deterministic generation belongs to a Tool contract.

It does not redefine Skill contracts, repository-wide sequencing, or `build_app` behavior, which are owned by `doc/contracts/SKILL_CONTRACTS.md`, `doc/plan/PHASED_IMPLEMENTATION_PLAN.md`, and `doc/requirements/APP_BUILDER_REQUIREMENTS.md`, respectively. `angular-django2` owns its public generation behavior; Skills use the upstream sources referenced by `ARCHITECTURE.md` §2.6 rather than restating them.

Skills preserve intentional contract-derived representations across backend models, OpenAPI, generated TypeScript models, and Angular validation; they must not introduce competing hand-maintained sources.

## Two-tier input model

Two distinct kinds of input are kept separate when a Skill is described.

**Authoring information** defines and verifies the Skill: purpose and selection conditions, canonical runtime input/output contracts, dependencies, permitted capabilities, acceptance criteria, test cases, expected evidence, and provider-neutral context requirements. It is planning metadata, not an invocation payload.

**Runtime input** is the single validated structured object that `build_app` supplies for one selected guided command through the provider adapter. Depending on the canonical Skill contract, it may contain:

- validated static settings required by the selected command;
- validated project identity and artifact locations;
- command-specific values derived during translation, such as affected resource/component identities and placement hints;
- the relevant atomic `ChangeSet` subset or affected identities; and
- bounded prior-command outcomes or acceptance evidence required by a declared dependency.

Skills consume these values without rereading configuration files, re-deriving changes, or parsing raw `oasdiff` output. Guided sessions receive runtime input from `build_app` through the provider adapter; interactive chat is not a canonical runtime-input source.

Each Skill's `Inputs` section in `doc/contracts/SKILL_CONTRACTS.md` defines only its runtime schema. Authoring information belongs to this plan and the corresponding derived working copy, not to the runtime payload.

## Skill sources and derived output

The [Skills Catalog in `SKILL_CONTRACTS.md`](contracts/SKILL_CONTRACTS.md#skills-catalog) is the canonical `djng` Skill source for stable name, purpose, modes, inputs, outputs, dependencies, and acceptance criteria. Numbered files in `skill_creation/skills/` are derived authoring working copies; when they differ, update the working copy rather than creating a competing source.

The executable canonical catalog and provider-neutral Skill resolver planned in `doc/plan/PHASED_IMPLEMENTATION_PLAN.md` Phase 4 will provide runtime metadata without parsing this plan, working copies, or provider-native files.

Provider adapters/renderers derive native prompts, tool registrations, Skill files, or packages from the canonical contract. Every rendering must preserve canonical identity, purpose, inputs, outputs, dependencies, acceptance criteria, and Tool/Hook bindings and pass provider-package conformance tests. Native metadata, filesystem layouts, invocation syntax, and permissions are derived concerns, not the cross-provider format.

Shared context remains with canonical Skill material. A renderer may inline or package it only when required; the copy is an artifact, not an independent source. Rendered output belongs under the ignored build/distribution location planned in `doc/plan/PHASED_IMPLEMENTATION_PLAN.md` Phase 8 and must not modify canonical sources. See `doc/contracts/SKILL_CONTRACTS.md` §Canonical skill contract and provider renderings.

## Tooling boundary

The deterministic integration toolchain and contracts are owned by `doc/contracts/TOOL_CONTRACTS.md`, `doc/requirements/APP_BUILDER_REQUIREMENTS.md`, and their implementations: `drf-spectacular` for OpenAPI export, `oasdiff` for schema comparison, `ng-openapi-gen` for Angular client generation, and governed wrappers around public `angular-django2` schematics. This plan neither redefines them nor introduces alternative generators or diff tools.

A Skill must not invoke raw Angular CLI, `ng-openapi-gen`, or `oasdiff` binaries, bundle a wrapper, or recreate deterministic schematic logic in scripts. `build_app` derives changes before guided execution; a Skill consumes structured command input rather than rerunning the diff.

When guided work needs a deterministic operation, the provider adapter may request only a canonical, allowed Tool. The direct execution controller validates and runs it, applies allowlisting and Hooks, records evidence, and determines failure consequences. A Skill/provider result cannot bypass those gates or mark a command/run successful.

Executability follows the effective `tool.commandAllowlist` in static `django-angular3.json`: the library fallback permits only `ng_openapi_gen`, while repository/generated configurations may allow more wrappers. `--dry-run` is diagnostic and non-mutating; its support proves neither a canonical Tool contract nor a completed `build_app` mapping. Skills must not infer executability from wrapper availability or dry-run output.

## Per-skill cadence

Every Skill follows four ordered stages with explicit user approval between them:

1. **Plan** — capture intent, conduct the interview, and sketch `name`, `description`, runtime inputs and their sources, produced files, scripts/shared context, implementation questions, and test prompts.
2. **Implementation and test generation** — update the canonical contract and derived working copy; create required scripts, references, assets, prompts, and assertions; render/test native artifacts only through the applicable adapter.
3. **`build_app` command integration** — add the selected Skill command after the Skill exists.
4. **Verification** — run and grade with-Skill versus baseline tests, render results, incorporate feedback, and after approval run provider-package conformance tests before publishing a derived artifact.

Subagents may work within any stage—for example, parallel with-Skill and baseline verification—but must not collapse or cross stage boundaries.

## Per-skill input validation

Each Skill validates its canonical runtime-input shape and Skill-specific semantic preconditions. Shared configuration, artifact, Tool, Hook, and dependency validation stays at the owning direct `build_app` boundaries and is not duplicated per Skill. Missing inputs have only the meanings in `doc/requirements/APP_BUILDER_REQUIREMENTS.md`; Skills introduce no promised-artifact state.

## Skill authoring order and working copies

Author Skills in canonical dependency order so declared dependencies' outputs are test ground truth. Select a Skill only for genuinely underspecified, interpretive, or post-generation refinement; validated structured inputs use deterministic Tools without a provider session.

This is only Skill authoring/verification order; `doc/requirements/APP_BUILDER_REQUIREMENTS.md` defines the complete mixed-automation execution order.

For focused authoring, use the matching `skill_creation/skills/<number>-<skill-name>.md` plus only needed `skill_creation/shared/` files. These are split working copies of `doc/contracts/SKILL_CONTRACTS.md`; resolve incompleteness or inconsistency against the canonical catalog and update the split file.

See `doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Execution order for the authoritative dependency chain.

## Glossary

For authoritative definitions see `ARCHITECTURE.md` §2 and §19.

---
