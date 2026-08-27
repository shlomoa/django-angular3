# Open Items — djng/ngdj

## 1. Derive Angular-Django2 Capabilities and Wrappers

Resolve ngdj facts through `doc/ARCHITECTURE.md` §2.6. The executable djng
wrapper registry is `django_angular3/angular.py::_COMMAND_BUILDERS`, and
`docs/commands.md` owns its public interface documentation.

### 1.1 Decide required wrappers and compositions

Decide whether service, class, field-component, form-field, application,
project-structure, embed-component, and app-shell require dedicated wrappers,
bounded composition, or explicit unsupported status.

### 1.2 Add requirement-driven wrappers

Add only wrappers justified by approved djng requirements; do not mirror the
complete upstream schematic surface.

### 1.3 Align wrapper documentation

Label direct upstream usage as ngdj invocation and align workspace creation
references with the composite `ng_workspace` flow.

## 2. Finalize AI Automation Contracts

`doc/GENERATE_AI_AUTOMATIONS.md` owns the canonical Skill, Tool, Hook, and
Plugin contracts.

### 2.1 Resolve construction Tool contracts

Complete the operation-support and canonical Tool decisions tracked by issue
#57 for page, component, complex-component, reactive-form, and site concerns.
Reconcile the crosswalk, Tool catalog, builder mapping, and phased plan before
implementing issues #162 or #164.

### 2.2 Keep Skill sources aligned

Keep `skill_creation/` aligned with the canonical Skills catalog and
`doc/SKILL_AUTHORING_PLAN.md` without duplicating normative contracts.

## 3. Complete OpenAPI Contract Processing

### 3.1 Reconcile oasdiff with the Change Model

Replace the coarse change categories in `build_app.py` with the canonical
Change Model from `doc/REQUIREMENTS.md` §4.2.9.

## 4. Complete djng Generation Entry Points

### 4.1 Implement approved wrapper and composition decisions

Implement the decisions from §1 with dry-run, command-contract, and public
interface coverage.

## 5. Complete Direct `build_app` Execution

`doc/APP_BUILDER_REQUIREMENTS.md` owns the direct-build contract.

### 5.1 Implement previous-input handling

Resolve baseline OpenAPI and OpenUI artifacts through the previous project
configuration. Do not add a separate `--previous-openui` input or `.previous`
OpenUI filename convention.

### 5.2 Implement atomic change derivation

Derive supported static-configuration, project-configuration, OpenAPI, and
OpenUI `create`, `delete`, `update`, and `move` changes, including first-run
creation when no baseline exists.

### 5.3 Implement deterministic command translation

Map each supported atomic change to its executable boundary, mode, inputs,
ordering prerequisites, and terminal validation. Fail explicitly for every
unsupported required change.

### 5.4 Implement direct execution and dry run

Execute wrappers, Tools, and Hooks in dependency order, halt on the first
failure, and surface it through Django error handling. Keep `--dry-run`
diagnostic-only and non-mutating.

### 5.5 Implement terminal validation

Use `ng_build` as the compile gate and add the integration and global
acceptance checks required by `doc/APP_BUILDER_REQUIREMENTS.md` FR-9.

## 6. Author Skills

### 6.1 Author the eleven canonical Skills

Follow `doc/SKILL_AUTHORING_PLAN.md` for each Skill: plan, implement, test,
integrate with `build_app`, and verify explicit acceptance criteria.

## 7. Implement Provider-Neutral Orchestration

### 7.1 Implement provider-neutral adapter contracts

Implement session lifecycle, Skill loading, Tool dispatch, Hook normalization,
structured results, cancellation, timeouts, and credential handling without
changing direct-execution semantics.

### 7.2 Add credential-free adapter tests

Cover success, unmet acceptance, timeout or context exhaustion, Tool denial,
Hook failure, evidence handling, and teardown with provider-independent stubs.

### 7.3 Implement provider adapters

Implement and runtime-gate the Claude, OpenAI, Gemini, and Copilot adapters
against the provider-neutral contract.

## 8. Complete Automated Verification

### 8.1 Add direct-build scenario coverage

Use `doc/TEST_EXAMPLES.md` fixtures to cover all configuration, OpenAPI, and
OpenUI scenario-axis combinations, plus first-run, source-selection, mixed
create/delete, deletion, and command-failure cases.

### 8.2 Add composed generated-app acceptance coverage

Verify that djng selects, orders, and composes upstream ngdj operations in a
real generated Angular workspace without duplicating ngdj's schematic tests.

### 8.3 Add global acceptance regression coverage

Verify cross-Skill interface consistency, backend-contract/Angular-client
alignment, and runnable application flows according to
`doc/REQUIREMENTS.md` §6.4 and `doc/ARCHITECTURE.md` §§7.2–7.3.

## 9. Build One Business Module End to End

### 9.1 Implement and verify one complete business module

Build one module through the governed wrappers, Tools, Hooks, Skills, direct
execution, and global acceptance gate.

## 10. Add Operational Verification

### 10.1 Implement audit logging and health checks

Add durable audit records and generated-app health checks.

### 10.2 Add staging smoke tests

Verify representative generated-app workflows in staging.

## 11. Implement the Automation Phases

`doc/phased_implementation_plan.md` owns the implementation sequence and
acceptance criteria.

### 11.1 Execute the phased implementation plan

Implement and verify its remaining phases without copying their contracts or
acceptance criteria into this backlog.

## 12. Make Command Execution Cross-Platform

### 12.1 Test Angular executable resolution

Cover Windows and non-Windows defaults and explicit `tool.executables` values.

### 12.2 Validate subprocess portability

Validate Python subprocess path resolution, environment handling, and shell
invocation on Windows, Linux, and macOS.

## 13. Add Direct OpenUI Validation

### 13.1 Add the management command

Add `django-admin validate_openui <path>` as a thin wrapper around
`validate_openui_file(path)`. Propagate upstream diagnostics without copying
OpenUI grammar, catalog, or duplicate-ID validation logic.

### 13.2 Add command tests

Cover a valid document and propagation of an upstream `openui-spec`
diagnostic.

## 14. Complete OpenUI Integration

OpenUI artifact roles remain defined by the external artifact-role SSOT linked
from `doc/ARCHITECTURE.md` §2.9.1.

### 14.1 Add invalid-input build coverage

Verify that `build_app` rejects an invalid OpenUI document before change
derivation.

### 14.2 Implement the OpenUI transformation boundary

Transform validated canonical OpenUI atomic changes into explicit ngdj
construction inputs without treating ngdj's package-local site assembly
definition as a canonical OpenUI document.

### 14.3 Add transformation and integration coverage

Cover the transformation contract, unsupported changes, command ordering,
dry-run non-modification, and composed generated-app output.
