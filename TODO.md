# Open Items — djng/ngdj

## 0. Classify configuration files and align documentation and code

**Status: In progress — inventory and execution plan drafted; taxonomy
alignment and rollout remain incomplete**

Define and apply the following configuration-file categories consistently in
djng documentation and code. Each configuration file must identify its category,
owner, input mechanism, and relationship to command-line arguments.

| Category | Purpose | Examples |
|---|---|---|
| **Tool-internal configuration** | Configures djng itself. | `django-angular3.json` |
| **Command input configuration set** | Supplies command inputs, implicitly by default or explicitly by path; may replace or duplicate command-line arguments. | A command's default or explicitly selected input set |
| **Specification configuration** | Defines or supplies an external contract or grammar consumed by djng. | OpenAPI 3.0 schema; OpenUI `openui.schema.json` |

**Progress evidence:** `REQUIREMENTS.md` §4.2 inventories configuration files,
ownership, and purposes; `doc/configuration_files_and_settings.md` records the
remaining ordered execution work. Neither yet adopts this three-category
taxonomy as its authoritative classification.

**Remaining work:** Resolve the terminology conflict between this taxonomy and
the `Project configuration` / `Tool configurations` / `OAS schema` / `OpenUI
specification` labels currently used in `REQUIREMENTS.md` §4.2. Then establish
the chosen definitions in that single authoritative reference, align
`README.md`, `docs/`, `doc/`, command help, configuration loading, validation,
and tests, and retire the temporary execution-plan document after its steps are
complete.

Review and align `README.md`, `docs/`, `doc/`, command help, configuration
loading, validation, and tests to use these categories without conflating tool
settings, command inputs, and specifications. Establish the authoritative
configuration-file reference and make other documentation link to it rather
than restating these definitions.

---

## 1. Non-CRM UI Input Format: OpenUI Defined

**Status: Partially implemented — configured input and validation complete;
build-time structural diffing pending**

The generated app's non-CRM UI source is the OpenUI concrete document selected
by `artifacts.openuiSpecification` in `django-angular3-<project_name>.json`.
`spec/openui/app.openui.json` is this repository's fixture. Each concrete
document conforms to `openui.schema.json` and uses the vocabulary in
`openui.json` from
[shlomoa/openui-spec](https://github.com/shlomoa/openui-spec). Non-CRM change
detection must still be implemented in `build_app` by structurally diffing the
OpenUI document tree.

| | |
|---|---|
| **Completed** | `django_angular3/config.py` resolves `artifacts.openuiSpecification`; `django_angular3/validation.py` validates concrete documents through `OpenUiJson`, including schema, catalog, and duplicate-ID checks. |
| **Remaining work** | Implement previous-OpenUI input handling, an OpenUI ChangeSet domain, and structural document-tree diffing in `django_angular3/management/commands/build_app.py`. |
| **Origin** | `APP_BUILDER_REQUIREMENTS.md` §Inputs, §Change Derivation; `ARCHITECTURE.md` §7.1 stage 4; `REQUIREMENTS.md` §4.2.2 |
| **Input sources** | `artifacts.openuiSpecification` in the generated-app project configuration; `spec/openui/app.openui.json` fixture |

---

## 2. Derive Angular-Django2 Capabilities and Wrappers

**Status: In progress**

### 2.0 Previous OpenUI input interface

**Status: Resolved — pending implementation**

`build_app` resolves the previous OpenUI document by the same algorithm used
for the previous OpenAPI schema: `--previous-openui <path>` takes precedence;
otherwise it uses the `.previous` sibling of the current `openui.source`. The
`--previous-config` argument is reserved for the project-configuration change
domain. This interface must be implemented consistently by `build_app`, examples,
and tests.

Derive the complete set of `angular-django2` capabilities and `djng` command
wrappers needed to materialize the required Angular-side outputs.

- Wrappers implemented: `ng_new`, `ng_workspace`, `ng_add`, `ng_config`,
  `ng_gen_app`, `ng_openapi_gen`, `ng_build`, `ng_workspace_delete`,
  `ng_workspace_modify`.
- `ng_gen_app` now emits the explicit Angular 22 `material-app` choices
  (`--ssr=false`, `--zoneless=true`, `--defaults`) sourced from the `ssr` and
  `zoneless` Angular settings, matching the upstream `angular-django2:material-app`
  contract.
- `ng_workspace` now represents the upstream-aligned empty-workspace bootstrap
  flow: `ng new` + workspace defaults + `ng add angular-django2` +
  `ng generate angular-django2:workspace-setup`.
- Broader repository docs under `doc/` still need wording alignment where they
  describe workspace creation as `ng_new`-first rather than the composite
  `ng_workspace` flow.
- Complete derivation aligned with all 11 SKILLS not yet done; see §2.1 for the
  outstanding `angular-django2` (ngdj) capability alignment tasks.

### 2.1 angular-django2 (ngdj) capability alignment

`angular-django2` (ngdj) was released with new and clarified schematic
capabilities. Each ngdj change below is mapped to the corresponding djng
alignment action (wrapper, direct-build command, or SKILL/doc wording) and its
current status. `Done` items already have djng-side evidence; `Pending` items
still require a djng wrapper, direct-build command, or SKILL/doc alignment.

| ngdj change | djng alignment action | Status |
|---|---|---|
| Explicit Angular 22 `material-app` flags (`--ssr=false`, `--zoneless=true`, `--defaults`) | `ng_gen_app` emits the explicit flags via `build_ng_gen_app_invocations` in `django_angular3/angular.py`, driven by the `ssr`/`zoneless` defaults in `django_angular3/settings.py`. | Done |
| Non-interactive app generation (`--defaults`) | Emitted by `ng_gen_app` (`angular.py`). | Done |
| SSR disabled by default in generated app (`--ssr=false`) | Emitted by `ng_gen_app` from the `ssr` setting default (`settings.py`). | Done |
| Zoneless app generation (`--zoneless=true`) | Emitted by `ng_gen_app` from the `zoneless` setting default (`settings.py`). | Done |
| Positional names for `component`/`service`/`class` pass-through generators | Add djng wrappers (or direct-build commands) that pass the generator name as a positional argument, not `--name=...`. | Pending |
| Project-relative `--path` for `component`/`service`/`class` | Wrappers must pass `--project=<app> --path=src/app/features/...` and expect output under `projects/<app>/src/app/features/...`. | Pending |
| Component generation seeds embedding hooks (begin/end markers in TS/HTML) | Marker contract documented in the component-composition SKILL (`skill_creation/skills/07-angular-component-composition.md` §Component embedding, mirrored in `doc/GENERATE_AI_AUTOMATIONS.md`) and the user workflow (`docs/workflow.md` §6). | Done |
| New `embed-component` command (local mode) | File-mode `embed-component` usage documented in `docs/workflow.md` §6, `README.md`, and SKILL 07; a djng `embed-component` wrapper / direct-build command is still to be added. | Doc done; wrapper pending |
| Embed generated component into app root | Documented as embedding a feature component into `projects/<app>/src/app/app.ts` in `docs/workflow.md` §6 and SKILL 07; wrapper composition pending. | Doc done; wrapper pending |
| Compose nested component hierarchy | Repeated child→parent, parent→app-root `embed-component` flow documented in `docs/workflow.md` §6 and SKILL 07; wrapper support pending. | Doc done; wrapper pending |
| Embed existing package component (package mode, `--from=<module>`) | Package-mode usage (`--from`, exported class as `--component`) documented in `docs/workflow.md` §6 and SKILL 07; a djng wrapper is still to be added. | Doc done; wrapper pending |
| Explicit selector for package component (`--selector`) | Support `--selector=<element-selector>` in the package-mode wrapper. | Pending |
| Explicit inputs/outputs for package component (`--inputs`/`--outputs`) | Support comma-separated `--inputs`/`--outputs` in the package-mode wrapper. | Pending |
| Angular Material component embedding example | Add a SKILL/doc example embedding a Material package component (e.g. `MatDateRangePicker`). | Pending |
| Rebuild after embedding (`ng build <app>`) | Reuse the existing `ng_build` wrapper as the post-embedding verification step. | Pending |
| OpenAPI bootstrap command (`openapi-setup --openapi_spec_file`, `npm install`, `npm run generate:api`) | `build_app` must execute `openapi-setup` when selected by schema changes; add a standalone djng `openapi-setup` wrapper and align the bootstrap workflow (`--openapi_spec_file`, install, `generate:api`). | Pending |
| Data service wrapper command (`data-service <resource> --project=<app>`) | `build_app` must execute the required `ng-data-service` command; add a standalone djng `data-service` wrapper passing `--project`. | Pending |
| `data-service` schematic must generate a typed `search` method | `test_data_service_schematic_generates_typed_wrapper` in `tests/test_ngdj_requirements.py` asserts `"search"` is present in `projects/angular-django2/schematics/data-service/index.ts`. The assertion currently fails — the method is absent from the schematic. Either restore the `search` method in ngdj or update the contract requirement and the test to reflect the agreed interface. | Failing — ngdj/djng contract gap |
| Lower-level app setup alternative (`application` → `material-setup` → `project-structure` → `app-shell`) | Document/derive wrappers for the lower-level schematic flow as an alternative to one-shot `material-app`. | Pending |
| `workspace-setup` file hooks are not normal CLI flags | Document for wrapper authors that advanced `workspace-setup` `files` hooks are programmatic (wrapper schematic, test runner, or direct factory), not nested CLI flags. | Pending |

---

## 3. Revise and Finalize GENERATE_AI_AUTOMATIONS.md

**Status: Substantially complete**

Revise and finalize `GENERATE_AI_AUTOMATIONS.md` as the design specification
for the complete AI automation model needed for bounded construction and
integration, covering SKILLS, TOOLS, HOOKS, and PLUGINS.

- Revise `doc/GENERATE_AI_AUTOMATIONS.md` to define primitive boundaries and
  selection policy across SKILLS, TOOLS, HOOKS, and PLUGINS.
- Keep the `skill_creation` folder aligned with the skills subset of
  `doc/GENERATE_AI_AUTOMATIONS.md`, with detailed descriptions and example
  prompts for each SKILL.
- Keep SKILL dependencies, shared context expectations, templates, invocation
  boundaries, and mixed automation execution-model references aligned with
  `doc/GENERATE_AI_AUTOMATIONS.md` and `doc/SKILL_AUTHORING_PLAN.md`.
- `GENERATE_AI_AUTOMATIONS.md` now carries normative per-capability catalogs for
  all four primitives (Tool Contracts, Hook Contracts, Plugin Contracts, Skills)
  alongside the primitive-selection policy; the umbrella framing no longer
  treats SKILLS as the only detailed family. `skill_creation` skill frontmatter
  (`description`, `when_to_use`) is aligned with the authoritative SKILLS subset.

---

## 4. OpenAPI Schema Extraction and Contract Validation

**Status: Substantially implemented**

Implement the OpenAPI schema extraction, contract normalization, and validation
on the Django/DRF side.

- oasdiff integration exists, but its coarse change categories in `build_app.py`
  must be reconciled with the canonical Change Model before it is treated as
  supported behavior.
- Schema extraction via `drf-spectacular` is the consuming Django project's
  responsibility.

---

## 5. djng Generator Entry Points and Wrappers

**Status: Substantially implemented**

Implement the `djng` generator app entry points and the governed wrappers around
`ngdj` actions used for workspace, app, contract-derived, and non-CRM
construction.

- All current workspace/app/contract wrappers implemented, including the
  explicit `ng_workspace` bootstrap wrapper aligned with the upstream
  `angular-django2:workspace-setup` schematic. Non-CRM construction wrappers
  depend on item 1 (MR1).

---

## 6. app-builder Change Detection and Direct Execution

**Status: Partially implemented**

Implement app-builder atomic change derivation, direct execution of the
selected construction commands, and terminal validation from current and
previous schema/OpenUI inputs.

- `build_app.py` contains a superseded coarse schema-category implementation;
  it must be reconciled with the canonical Change Model in `REQUIREMENTS.md`
  §4.2.9 before it is treated as supported behavior.
- A missing baseline must emit atomic `create` changes; the
  `--force start-from-scratch` CLI option selects the initial workspace command
  sequence, including the upstream-aligned `ng_workspace` bootstrap contract.
- Config change detection covers only project rename. OpenUI document-tree
  change detection and Angular UI command dispatch are not implemented yet.
- Current command selection produces CLI command strings. It must be replaced
  with direct wrapper and SDK execution, failure handling, and terminal validation.
- Example 1 input files now exist at `django_angular3/examples/01_simple_crm/` (see item 9);
  examples 2–12 still need their own input files before scenarios 2–12 can be verified.

---

## 7. Create SKILLS

**Status: Not started**

Author each of the eleven SKILLS using the per-skill cadence defined in
`doc/SKILL_AUTHORING_PLAN.md`: plan, implementation including tests, app-builder
command integration, and verification.

Per-SKILL acceptance criteria must be defined during the Plan phase of each
SKILL — the exact conditions the agent must verify before declaring a procedure
complete, the tools used to verify them, and what "done" means locally. Without
this, the agent cannot evaluate completion and may terminate arbitrarily.

| Failure mode | Mechanism | Consequence |
|---|---|---|
| Premature convergence | Agent judges acceptance criteria satisfied when they are not | Defect silently passes through |
| Underspecified acceptance criteria | SKILL instructions do not define pass/fail precisely enough | Arbitrary termination |
| Tool / wrapper failure | ngdj schematic or djng wrapper errors consistently | Agent exhausts retries, surfaces partial output |
| Hallucination | Agent generates code that looks correct but has subtle bugs | Passes agent's own self-check; defect persists |

---

## 8. Implement Orchestration Flow

**Status: Not started**

Implement the iterative orchestration flow through the provider-neutral adapter
contract. The Claude adapter uses the Claude Agent SDK; OpenAI, Gemini, and
Copilot adapters must preserve the same direct-command execution semantics.
Construction invokes a selected provider session with canonical SKILLS enabled
until acceptance conditions are satisfied.

Failure handling must be specified: `build_app` must halt and surface a
structured error when a provider session ends without evidence of success. The
first implementation does not retry automatically or promise rollback.

| Failure mode | Mechanism | Consequence |
|---|---|---|
| Agent context exhaustion | Long repair loops fill the session context window | Session ends mid-work; partial output written to disk |
| SDK timeout | Session runs too long | Hard stop; no guarantee of rollback |

`build_app` currently has no mechanism to detect that a provider session ended
without satisfying its acceptance criteria. It has no adapter orchestration or
normalized session evidence boundary.

### Provider-adapter verification backlog

The authoritative adapter-contract cases and expected assertions are in
`doc/phased_implementation_plan.md` Phase 5. Implement provider-independent
unit tests with stubs before any provider SDK integration. Each real-provider
suite is credential- and runtime-gated; absent credentials skip that suite and
must not affect the provider-independent contract tests.

| Adapter | Stub contract tests | Credential/runtime-gated integration suite |
|---|---|---|
| Claude Agent SDK | Success, unmet acceptance, timeout/context exhaustion, tool denial, post-tool failure, teardown | Verify Agent SDK session, native hooks, skill loading, result normalization, and teardown. |
| OpenAI Agents / Responses | Same provider-neutral contract cases | Verify Responses/agent session plus local function-tool guard and hook-manager normalization. |
| Gemini SDK / Antigravity | Same provider-neutral contract cases | Verify function-tool session plus decorator/wrapper lifecycle normalization. |
| Copilot SDK | Same provider-neutral contract cases | Verify session tools, permission/pre-post handlers, and lifecycle normalization. |

An adapter is not implemented until both its provider-independent contract
tests and its own credential/runtime-gated integration suite pass.

---

## 9. Automated Verification

**Status: Not started**

Add automated verification across contract checks, construction-output checks,
integration checks, and test-based verification.

### 9.1 Example Input Files

The twelve scenarios in `doc/TEST_EXAMPLES.md` require input files for each example.
Example 1 is now bundled in the package at `django_angular3/examples/01_simple_crm/`.
Examples 2–12 still need their input files under `spec/examples/<example-name>/`.

| Example | Location | Status |
|---|---|---|
| 1 Simple CRM | `django_angular3/examples/01_simple_crm/` | ✓ exists |
| 2 Add Resource | `spec/examples/02-add-order/` | missing |
| 3 Breaking Change | `spec/examples/03-breaking-change/` | missing |
| 4 Workspace Configuration | `spec/examples/04-workspace-style/` | missing; config-diff implementation pending |
| 5 OpenUI-Source Configuration | `spec/examples/05-openui-source/` | missing; config/OpenUI diff implementation pending |
| 6 OpenUI Change | `spec/examples/06-add-dashboard/` | missing; OpenUI diffing pending |
| 7 Combined | `spec/examples/07-combined-change/` | missing |
| 8 Replace Resource | `spec/examples/08-replace-resource/` | missing |
| 9 No Change | `spec/examples/09-no-change/` | missing |
| 10 Configuration + OpenAPI | `spec/examples/10-config-openapi/` | missing; config-diff implementation pending |
| 11 Configuration + OpenUI | `spec/examples/11-config-openui/` | missing; config/OpenUI diff implementation pending |
| 12 Configuration + OpenAPI + OpenUI | `spec/examples/12-all-change-domains/` | missing; config/OpenUI diff implementation pending |

Example 1 is runnable. Examples 2, 3, 7, 8, and 9 have no remaining
change-derivation dependency beyond their fixtures. Examples 4, 5, 10, 11, and
12 require complete configuration diffing; Examples 6, 7, 11, and 12 require
OpenUI structural diffing.

### 9.2 E2E Verification Specification Missing

| Aspect | Current state | What is missing | Why it matters |
|---|---|---|---|
| Terminal validation | `ng_build` is the final validation command in the direct build sequence. | `ng_build` only confirms the Angular app compiles. It does not verify backend API / Angular client alignment, runtime integration, or business-logic correctness. | A build that compiles is not the same as a working integrated application. |
| Backend/frontend alignment | REQUIREMENTS.md §4.2.2 requires "alignment between backend behavior, generated Angular integration artifacts, and frontend composition." | No specification of how this alignment is verified programmatically. | Alignment can silently break when the OpenAPI schema diverges from the running backend. |
| Full-stack E2E test spec | REQUIREMENTS.md §4.16 defines four verification categories. | None has a concrete acceptance test specification. §6.4 Mandatory Acceptance Scenarios header exists but content is not populated. | No pass/fail criterion beyond "Angular compiled." |
| ngdj test surface | ngdj schematics are not tested by the djng test suite. | No specification for how SKILL-generated ngdj outputs are tested against a real Angular workspace. | Correctness of the generated Angular application depends on ngdj schematic outputs, which are currently unverified. |

### 9.3 Global Acceptance Criteria Not Specified

Local acceptance by each SKILL does not imply global correctness. A
representative failure chain:

```
openapi-setup       generates  OrderApiService.getOrder(id: number)
ng-data-service wraps it as load(id: string)   ← locally valid TypeScript
ng-page         calls      dataService.load(route.params.id)  ← locally valid
```

Each agent declared "done." `ng_build` passes. At runtime, a string is silently
passed where a number is expected. No existing check catches this.

Global acceptance criteria must cover: cross-SKILL interface consistency,
backend contract / Angular client alignment, and runtime smoke tests.
`ARCHITECTURE.md` §2.17 defines "correct working application" but provides no
concrete test that decides it.

Where this must land:
- **Global acceptance criteria**: `doc/REQUIREMENTS.md` §6.4 (currently empty)
  and `doc/APP_BUILDER_REQUIREMENTS.md` §Functional Requirements (new FR for
  terminal verification).
- **Failure handling**: `doc/APP_BUILDER_REQUIREMENTS.md` as a new functional
  requirement.
- **Local-to-global gap**: architectural decision required; must be recorded in
  `doc/ARCHITECTURE.md` §7.2 or §7.3.

---

## 10. Build One Business Module End to End

**Status: Not started**

Build one business module end to end using the generator app, app builder,
SKILLS, and wrappers together.

---

## 11. Audit Logging, Health Checks, and Staging Smoke Tests

**Status: Not started**

Add audit logging, health checks, generator verification, and staging smoke
tests.

---

## 12. Architecture Alignment: Tools, Hooks, Skills, Plugins

**Status: Planned — design alignment recorded in
`doc/phased_implementation_plan.md`; implementation phases remain open.**

Implement the architectural contracts recorded in
`doc/GENERATE_AI_AUTOMATIONS.md`. This item feeds item 3 so that document
remains the umbrella design specification for the full automation model rather
than SKILLS alone.

- Convert deterministic construction and contract operations currently treated
  as SKILL/script responsibilities into explicit tool contracts (for example:
  schema export, schema diff, contract validation, and Angular/client generation
  wrappers).
- Add lifecycle enforcement points as hooks for gates and mandatory side
  effects (for example: breaking-change gate, migration-triggered schema export,
  pre-construction contract validation, post-run verification logging,
  session-stop archiving/audit).
- Define packaging boundaries for reusable capability bundles (plugin-oriented
  grouping), including:
  - djng Angular construction capability bundle
  - ngdj scaffold capability bundle
  - contract lifecycle capability bundle
- Document primitive-selection policy (Skill vs Tool vs Hook vs Plugin) in
  architecture/requirements docs so new capabilities are categorized
  consistently.
- Derive a phased implementation plan with acceptance criteria for the above,
  including test and verification coverage updates where behavior moves from
  AI-guided flow to deterministic tool/hook enforcement.
  See `doc/phased_implementation_plan.md`.

---

## 13. Platform-Aware command execution

- Add unit tests for platform-aware Angular executable resolution. Simulate
  Windows and non-Windows defaults, and verify the intended behavior when
  `tool.executables` supplies explicit executable values.
- Validate all Python subprocess calls for cross-platform compatibility, including path resolution, environment variables, and shell invocation.

---

## 14. Direct OpenUI validation management command

**Status: Planned**

Add `django_angular3/management/commands/validate_openui.py`, exposed as:

```text
django-admin validate_openui <path>
```

The command must be a thin wrapper around `validate_openui_file(path)`:

- write each validation diagnostic to stderr and raise `CommandError` when the
  document is invalid;
- report success only when validation returns no errors;
- contain no OpenUI grammar, catalog, or duplicate-ID validation logic.

Add command tests for a valid document and for propagation of an upstream
`openui-spec` diagnostic. This keeps `OpenUiJson` as the single validation
authority while providing the explicit Django command surface required by
Task 2.2 of `doc/openui-spec_integration_plan.md`.

---

## 15. openui-spec integration plan - remaining items

### What openui-spec provides

The `openui-spec` defines three layered artifacts:

- **`openui.schema.json`** — grammar: validates the shape of any OpenUI JSON document
- **`openui.json`** — catalog: machine-readable vocabulary of all scope objects (Application, Controls, Behaviors, Pages, Views, Containers, Widgets, …)
- **concrete UI document** (`input.json`) — a schema-valid document using vocabulary from the catalog; this is the user-authored UI description
- **`OpenUiJson` tooling API** — the published validation and editing boundary
	that validates a concrete document against both the grammar and catalog and
	rejects duplicate object IDs

The concrete document format defines the non-CRM input consumed by the djng
integration contract.

---

### Task 3: Validation and test updates

**Status: Partial.** Steps 3.1, 3.2, and 3.4 are complete. Step 3.3 has
standalone CLI coverage and Step 3.5 has fixture coverage; their `build_app`
acceptance portions remain deferred. Step 3.6 remains outstanding.

#### Step 3.3 — CLI and build-command integration coverage

**Status: Partial.** `tests/test_cli.py` covers standalone `validate-openui`
and `validate-project` success and invalid-OpenUI failure paths. Generated-app
`build_app` coverage remains deferred while that command is WIP.

**Target:** new `tests/test_cli.py`.

Add CLI tests for `validate-openui <app.openui.json>` and `validate-project`.
Verify valid fixtures return success and invalid OpenUI documents return failure
with the validation path. Add generated-app command coverage showing that
`build_app` rejects an invalid OpenUI source before change detection. This test file
is new because no current test module exercises these CLI commands.


#### Step 3.5 — Three-domain scenario fixtures and acceptance coverage

**Status: Partial.** `spec/examples/` provides valid scenario configurations,
shared source artifacts, and a manifest covering all eight scenario-axis
combinations plus source-selection and mixed create/delete cases. Direct
ChangeSet, command-ordering, and dry-run non-modification assertions remain
deferred until `build_app` is implemented.

**Targets:** `tests/`, `tests/test_export_schema.py`, and
`spec/examples/`.

Materialize and test the full $2^3$ matrix of incremental configuration,
OpenAPI, and OpenUI scenario axes documented in `TEST_EXAMPLES.md`. Also retain
coverage for first-run, OpenUI-source-selection, and mixed create/delete cases.
Each test must assert the relevant canonical ChangeSet domains, selected commands, command ordering, and
dry-run non-modification behavior.

#### Step 3.6 — Verification gate

After implementation, run Ruff format and lint checks plus the full unittest
suite specified in `.github/copilot-instructions.md`. Also run the relevant
`django-admin validate-openui`, `django-admin validate-project`, and
`django-admin build_app --dry-run` commands in a generated-app-compatible Django
configuration. Record the OpenUI format reference and commands in the
implementation change.

---

### Task 4: Complete direct `build_app` execution

**Status: Not started.** `build_app` is WIP; its current implementation is not
evidence that any Task 4 requirement is complete.

#### Step 4.1 — Define previous-input handling

**Status: Planned.** Define how `build_app` receives the accepted prior project
state and prior OpenUI document before implementing comparison. The current
OpenUI input is selected by `artifacts.openuiSpecification`; do not introduce
an undocumented `--previous-openui` flag or `.previous` convention. Record the
chosen prior-state mechanism once in `doc/APP_BUILDER_REQUIREMENTS.md`, then
use it consistently in the command, examples, and tests.

#### Step 4.2 — Implement command execution

**Targets:** `django_angular3/management/commands/build_app.py`,
`django_angular3/angular.py`, and the required direct execution boundaries.

Discover `django-angular3-<project_name>.json`; use `artifacts.openapiSchema`,
`artifacts.openuiSpecification`, and `artifacts.angularWorkspace` as the
current inputs and output location. Validate inputs, derive the canonical
ChangeSet domains from the accepted prior state, translate each supported atomic
change directly to an executable command, and execute in dependency order. An
unsupported change must fail explicitly rather than being omitted.

`--dry-run` is diagnostic-only: it validates inputs, derives changes, reports
ordered commands with their modes, inputs, and reasons, and must not modify the
generated-app workspace. Normal execution must halt on the first wrapper, tool,
hook, or validation failure and surface the failure through Django's normal
error reporting.

#### Step 4.3 — Define command translation and output validation

**Targets:** `doc/APP_BUILDER_REQUIREMENTS.md`, `TODO.md`, and
`django_angular3/management/commands/build_app.py`.

Define one complete mapping for every supported static configuration, project
configuration, invocation, OpenAPI, and OpenUI `create`, `delete`, `update`,
and `move` change. The mapping must name the executable boundary, its mode,
inputs, ordering prerequisites, and terminal validation. Record missing
wrappers as unsupported requirements until they exist; execution must never
silently skip their corresponding change. Define post-execution generated-file
checks, Angular build, and required integration checks. Command execution and
terminal validation—not an emitted plan—are the build result.

#### Step 4.4 — Add direct-build acceptance coverage

**Targets:** `tests/test_export_schema.py`, new focused `build_app` tests, and
the scenario fixtures in `doc/TEST_EXAMPLES.md`.

Implement the direct-build cases documented by Task 3.5 using the scenario
fixtures: every $2^3$ configuration × OpenAPI × OpenUI scenario-axis
combination, plus first-run, mixed create/delete, source-selection, deletion,
and command-failure cases. Assert all relevant derived ChangeSet domains,
selected executable boundaries, command ordering, executed wrappers, and
validated outputs—not an emitted plan. Cover dry-run separately by asserting
no generated-app files are modified.

---
