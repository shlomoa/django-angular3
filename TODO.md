# Open Items — djng/ngdj

## 1. Derive Angular-Django2 Capabilities and Wrappers

**Status: In progress**

### 1.0 Previous OpenUI input interface

**Status: Resolved — implementation pending**

`build_app` accepts the current and previous project configurations through
`--current-config` and `--previous-config`. Each configuration independently
resolves its `artifacts.openapiSchema` and `artifacts.openuiSpecification`
selectors, so the previous configuration supplies the baseline OpenAPI and
OpenUI documents. No separate `--previous-openui` input or `.previous` OpenUI
filename convention is part of the interface. Command execution, examples, and
tests must implement this configuration-pair contract consistently.

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
- Complete derivation aligned with all 11 SKILLS not yet done; see §1.1 for the
  outstanding `angular-django2` (ngdj) capability alignment tasks.

### 1.1 angular-django2 (ngdj) capability alignment

`angular-django2` (ngdj) was released with new and clarified schematic
capabilities. Each ngdj change below is mapped to the corresponding djng
alignment action (wrapper, direct-build command, or SKILL/doc wording) and its
current status. `Done` items already have djng-side evidence; `Pending` items
still require a djng wrapper, direct-build command, or SKILL/doc alignment.

| ngdj change | djng alignment action | Status |
|---|---|---|
| Positional names for `component`/`service`/`class` pass-through generators | Add djng wrappers (or direct-build commands) that pass the generator name as a positional argument, not `--name=...`. | Pending |
| Project-relative `--path` for `component`/`service`/`class` | Wrappers must pass `--project=<app> --path=src/app/features/...` and expect output under `projects/<app>/src/app/features/...`. | Pending |
| New `embed-component` command (local mode) | File-mode `embed-component` usage documented in `docs/workflow.md` §6, `README.md`, and SKILL 07; a djng `embed-component` wrapper / direct-build command is still to be added. | Doc done; wrapper pending |
| Embed generated component into app root | Documented as embedding a feature component into `projects/<app>/src/app/app.ts` in `docs/workflow.md` §6 and SKILL 07; wrapper composition pending. | Doc done; wrapper pending |
| Compose nested component hierarchy | Repeated child→parent, parent→app-root `embed-component` flow documented in `docs/workflow.md` §6 and SKILL 07; wrapper support pending. | Doc done; wrapper pending |
| Embed existing package component (package mode, `--from=<module>`) | Package-mode usage (`--from`, exported class as `--component`) documented in `docs/workflow.md` §6 and SKILL 07; a djng wrapper is still to be added. | Doc done; wrapper pending |
| Explicit selector for package component (`--selector`) | Support `--selector=<element-selector>` in the package-mode wrapper. | Pending |
| Explicit inputs/outputs for package component (`--inputs`/`--outputs`) | Support comma-separated `--inputs`/`--outputs` in the package-mode wrapper. | Pending |
| Angular Material component embedding example | Add a SKILL/doc example embedding a Material package component (e.g. `MatDateRangePicker`). | Pending |
| Rebuild after embedding (`ng build <app>`) | Reuse the existing `ng_build` wrapper as the post-embedding verification step. | Pending |
| OpenAPI bootstrap command (`openapi-setup --openapi_spec_file`, `npm install`, `npm run generate:api`) | Standalone djng `ng_openapi_setup` wrapper added (`django_angular3/management/commands/ng_openapi_setup.py`, CLI, `build_ng_openapi_setup_invocations`) resolving `angular-django2:openapi-setup` with `--output-path`/`--helpers-path`/`--skip-helpers`/`--skip-tests`. Remaining: `build_app` must execute it when selected by schema changes (blocked on the unimplemented `build_app` engine). | Wrapper done; build_app wiring pending |
| `openapi-setup` helper artifacts (`django-transport.ts`, `resource-adapter.ts`, `index.ts`, `provideDjangoApiTransport`) from ngdj PR #55 | Documented in SKILL 03 (`skill_creation/skills/03-angular-api-integration.md`) and asserted by `test_openapi_setup_schematic_emits_django_integration_helpers` in `tests/test_ngdj_requirements.py`. `ng_openapi_setup` exposes `--skip-helpers`/`--skip-tests`. | Done |
| Data service wrapper command (`data-service <resource> --project=<app>`) | Standalone djng `ng_data_service` wrapper added (`django_angular3/management/commands/ng_data_service.py`, CLI, `build_ng_data_service_invocations`) passing `--project`. Remaining: `build_app` must execute it (blocked on the unimplemented `build_app` engine). | Wrapper done; build_app wiring pending |
| `data-service` schematic must generate a typed `search` method | Present in ngdj `projects/angular-django2/schematics/data-service/templates.ts` (not `index.ts`); the earlier "Failing" note was stale. `test_data_service_schematic_exposes_search_wrapper` in `tests/test_ngdj_requirements.py` now asserts it. | Done |
| Lower-level app setup alternative (`application` → `material-setup` → `project-structure`) | Standalone djng `ng_material_setup` wrapper added (`django_angular3/management/commands/ng_material_setup.py`, CLI, `build_ng_material_setup_invocations`) resolving `angular-django2:material-setup` with `--project`/`--theme`/`--typography`/`--animations`. Remaining: `application` and `project-structure` wrappers for the full lower-level flow. | material-setup done; remaining schematics pending |
| `app-shell` schematic (SSR/prerender pass-through) | Per the ngdj 0.4.1 tutorial and CLI index, `angular-django2:app-shell` wraps Angular's SSR/prerender app-shell feature and is unrelated to the Material sidenav layout (which `material-app` produces). It is not part of the lower-level layout chain; a djng wrapper is optional and deprioritized. | Pending (deprioritized) |
| `workspace-setup` file hooks are not normal CLI flags | Document for wrapper authors that advanced `workspace-setup` `files` hooks are programmatic (wrapper schematic, test runner, or direct factory), not nested CLI flags. | Pending |

---

## 2. Revise and Finalize GENERATE_AI_AUTOMATIONS.md

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

## 3. OpenAPI Schema Extraction and Contract Validation

**Status: Substantially implemented**

Implement the OpenAPI schema extraction, contract normalization, and validation
on the Django/DRF side.

- oasdiff integration exists, but its coarse change categories in `build_app.py`
  must be reconciled with the canonical Change Model before it is treated as
  supported behavior.
- Schema extraction via `drf-spectacular` is the consuming Django project's
  responsibility.

---

## 4. djng Generator Entry Points and Wrappers

**Status: Substantially implemented**

Implement the `djng` generator app entry points and the governed wrappers around
`ngdj` actions used for workspace, app, contract-derived, and non-CRM
construction.

- All current workspace/app/contract wrappers implemented, including the
  explicit `ng_workspace` bootstrap wrapper aligned with the upstream
  `angular-django2:workspace-setup` schematic. Non-CRM construction wrappers
  depend on the OpenUI input work described by this TODO.

---

## 5. build_app Change Detection and Direct Execution

**Status: Partially implemented**

Implement build_app atomic change derivation, direct execution of the
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
- Example 1 input files now exist at `django_angular3/examples/01_simple_crm/` (see item 8);
  examples 2–12 still need their own input files before scenarios 2–12 can be verified.

---

## 6. Create SKILLS

**Status: Not started**

Author each of the eleven SKILLS using the per-skill cadence defined in
`doc/SKILL_AUTHORING_PLAN.md`: plan, implementation including tests, build_app
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

## 7. Implement Orchestration Flow

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

### 7.1 Provider-adapter verification backlog

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

## 8. Automated Verification

**Status: Not started**

Add automated verification across contract checks, construction-output checks,
integration checks, and test-based verification.

### 8.1 Example Input Files

All twelve scenarios in `doc/TEST_EXAMPLES.md` now have input fixtures:
Example 1 is bundled at `django_angular3/examples/01_simple_crm/`, and Examples
2–12 are under `tests/fixtures/scenarios/`. Fixture presence and source
validation are covered by `tests/test_cli_scaffold.py`; direct-build acceptance
coverage remains deferred until `build_app` is implemented.

### 8.2 E2E Verification Specification Missing

| Aspect | Current state | What is missing | Why it matters |
|---|---|---|---|
| Terminal validation | `ng_build` is the final validation command in the direct build sequence. | `ng_build` only confirms the Angular app compiles. It does not verify backend API / Angular client alignment, runtime integration, or business-logic correctness. | A build that compiles is not the same as a working integrated application. |
| Backend/frontend alignment | REQUIREMENTS.md §4.2.2 requires "alignment between backend behavior, generated Angular integration artifacts, and frontend composition." | No specification of how this alignment is verified programmatically. | Alignment can silently break when the OpenAPI schema diverges from the running backend. |
| Full-stack E2E test spec | REQUIREMENTS.md §4.16 defines four verification categories. | None has a concrete acceptance test specification. §6.4 Mandatory Acceptance Scenarios header exists but content is not populated. | No pass/fail criterion beyond "Angular compiled." |
| ngdj test surface | ngdj schematics are not tested by the djng test suite. | No specification for how SKILL-generated ngdj outputs are tested against a real Angular workspace. | Correctness of the generated Angular application depends on ngdj schematic outputs, which are currently unverified. |

### 8.3 Global Acceptance Criteria Not Specified

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

## 9. Build One Business Module End to End

**Status: Not started**

Build one business module end to end using the generator app,
SKILLS, and wrappers together.

---

## 10. Audit Logging, Health Checks, and Staging Smoke Tests

**Status: Not started**

Add audit logging, health checks, generator verification, and staging smoke
tests.

---

## 11. Architecture Alignment: Tools, Hooks, Skills, Plugins

**Status: Planned — design alignment recorded in
`doc/phased_implementation_plan.md`; implementation phases remain open.**

Implement the architectural contracts recorded in
`doc/GENERATE_AI_AUTOMATIONS.md`. This item feeds item 2 so that document
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

## 12. Platform-Aware command execution

- Add unit tests for platform-aware Angular executable resolution. Simulate
  Windows and non-Windows defaults, and verify the intended behavior when
  `tool.executables` supplies explicit executable values.
- Validate all Python subprocess calls for cross-platform compatibility, including path resolution, environment variables, and shell invocation.

---

## 13. Direct OpenUI validation management command

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
authority while providing the explicit Django command surface.

---

## 14. openui-spec integration plan - remaining items

### 14.0 What openui-spec provides

The external `openui-spec` project defines three peer artifacts:

- **Schema (`openui.schema.json`)** — the grammar and structural rules for an
  OpenUI specification document.
- **Catalog (`openui.json`)** — the library of documented OpenUI items,
  including applications, controls, behaviors, pages, views, containers, and
  widgets.
- **Concrete UI document** — an application-specific UI manifest that
  follows the schema grammar and is composed of items defined by the catalog.

`OpenUiJson` and the `openui-json` CLI are validation and editing tooling for
these artifacts; they are not a fourth OpenUI artifact. Concrete examples
distributed by `openui-spec` and `djng` are non-normative test fixtures, not
artifact definitions or application UI sources of truth.

OpenUI is a unified, technology-independent UI abstraction, not an internal
djangoangular format. A concrete UI document can be implemented using Angular,
Qt, or another UI technology. In djangoangular, `djng` governs the concrete UI
document and converts its manifest into explicit construction,
build, or generation operations that materialize the application.

---

### 14.1 Validation and test updates

**Status: Partial.** Standalone CLI and fixture coverage exist; their
`build_app` acceptance portions remain deferred. The verification gate remains
outstanding.

#### Step 14.1.1 — CLI and build-command integration coverage

**Status: Partial.** `tests/test_cli.py` covers standalone `validate-openui`
and `validate-project` success and invalid-OpenUI failure paths. Generated-app
`build_app` coverage remains deferred while that command is WIP.

Add generated-app command coverage showing that `build_app` rejects an invalid
OpenUI source before change detection.


#### Step 14.1.2 — Three-domain scenario fixtures and acceptance coverage

**Status: Partial.** `tests/fixtures/scenarios/` provides valid scenario
configurations, shared source artifacts, and a manifest covering all eight
scenario-axis combinations plus source-selection and mixed create/delete
cases. Direct ChangeSet, command-ordering, and dry-run non-modification
assertions remain deferred until `build_app` is implemented.

**Targets:** `tests/`, `tests/test_export_schema.py`, and
`tests/fixtures/scenarios/`.

Materialize and test the full $2^3$ matrix of incremental configuration,
OpenAPI, and OpenUI scenario axes documented in `TEST_EXAMPLES.md`. Also retain
coverage for first-run, OpenUI-source-selection, and mixed create/delete cases.
Each test must assert the relevant canonical ChangeSet domains, selected commands, command ordering, and
dry-run non-modification behavior.

#### Step 14.1.3 — Verification gate

After implementation, run Ruff format and lint checks plus the full unittest
suite specified in `.github/copilot-instructions.md`. Also run the relevant
`django-admin validate-openui`, `django-admin validate-project`, and
`django-admin build_app --dry-run` commands in a generated-app-compatible Django
configuration. Record the OpenUI format reference and commands in the
implementation change.

---

### 14.2 Complete direct `build_app` execution

**Status: Not started.** `build_app` is WIP; its current implementation is not
evidence that any §14.2 requirement is complete.

#### 14.2.1 — Define previous-input handling

**Status: Resolved — implementation pending.** `build_app` receives the current
and previous project configurations through `--current-config` and
`--previous-config`. Each configuration independently resolves its selected
OpenAPI and OpenUI artifacts; the previous configuration therefore supplies
the baseline documents. No separate `--previous-openui` flag or `.previous`
OpenUI filename convention is part of the interface. Implement this contract
consistently in comparison, examples, and tests.

#### 14.2.2 — Implement command execution

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

#### 14.2.3 — Define command translation and output validation

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

#### 14.2.4 — Add direct-build acceptance coverage

**Targets:** `tests/test_export_schema.py`, new focused `build_app` tests, and
the scenario fixtures in `doc/TEST_EXAMPLES.md`.

Implement the direct-build cases documented by Step 14.1.2 using the scenario
fixtures: every $2^3$ configuration × OpenAPI × OpenUI scenario-axis
combination, plus first-run, mixed create/delete, source-selection, deletion,
and command-failure cases. Assert all relevant derived ChangeSet domains,
selected executable boundaries, command ordering, executed wrappers, and
validated outputs—not an emitted plan. Cover dry-run separately by asserting
no generated-app files are modified.

---

## 15. Input and Construction Responsibility SSOT

The generated application uses distinct but composable sources and execution
boundaries:

- **OpenUI** is the technology-independent contract for UI structure and
  behavior. An OpenUI concrete UI document can describe routing, navigation,
  pages, views, controls, widgets, and behaviors regardless of whether the UI
  presents OpenAPI-backed business data or independently authored workflows.
  The external `openui-spec` project owns the schema, catalog, concrete UI
  specification contract, and their conformance rules. OpenUI is not internal
  to djangoangular and does not prescribe Angular or any other implementation
  technology. Examples distributed by either project are non-normative test
  fixtures. In djangoangular, `djng` governs each selected concrete UI
  specification, derives the required changes, and converts them into explicit
  construction operations.
- **OpenAPI** provides the implementation-independent API contract abstraction
  between the Django/DRF backend and its consumers. In the djangoangular
  lifecycle, the API contract originates in one of two modes. In model-first
  mode, the Django/DRF API layer exports operations and data schemas informed by
  the Django data model. In contract-first mode, an existing OpenAPI document
  originates the backend data model and DRF elaboration. Both modes converge on
  a versioned OpenAPI schema file as the durable API contract representation
  once the backend exists. That file is the input for generating Angular API
  clients, integration artifacts, and API-contract-derived UI requirements and
  construction inputs. Those generated outputs do not become competing sources
  of truth. OpenUI may additionally describe how API-backed data and operations
  are presented and used in the UI.
- **`ngdj`** owns deterministic Angular-specific construction operations,
  including workspace setup, application setup, and Angular code
  transformations. It validates each explicit schematic invocation, accepted
  options or bounded input fragment, Angular workspace preconditions, and the
  construction invariants it owns before applying a mutation. These commands
  are execution mechanisms, not UI-content definitions.
- **`djng`** owns input governance, validation, change derivation, command
  selection, orchestration, cross-source integration, and final generated-app
  verification. It validates selected OpenAPI and OpenUI inputs against their
  governing contracts, validates project configuration and cross-input
  consistency, rejects unsupported derived changes or missing construction
  capabilities before execution, and verifies the composed generated app after
  orchestration.

Validation is required at all three boundaries. Validation by `openui-spec`
does not replace `djng` validation of the concrete inputs and composition it
governs, and `djng` validation does not replace `ngdj` validation of the
invocation and Angular mutation boundary it executes.

OpenAPI-derived and OpenUI-described concerns may intersect in the generated
UI. Their source identities must remain explicit rather than being collapsed
into one document or classified as mutually exclusive CRM and non-CRM content.

### 15.1 OpenUI responsibility boundary

- [x] 15.1.1. Audit the existing purpose, artifact-role, and glossary SSOT in
  `openui-spec/spec/README.md`.
  - The purpose statement correctly defines OpenUI as an
    implementation-independent Web UI contract and does not use CRM/non-CRM as
    a scope boundary.
  - The glossary already covers applications, routing, navigation, behaviors,
    pages, views of business objects and workflows, controls, widgets, and
    concrete UI documents without tying them to a data-source classification.
  - The grammar/catalog/concrete-document artifact roles are defined once and
    are correctly referenced by `openui-spec/docs/REQUIREMENTS.md`.
  - The three artifacts are peers: schema, catalog, and concrete UI
    specification. Validation and editing tooling is not another artifact.
  - OpenUI is an external, unified UI abstraction rather than a djangoangular
    format. Djangoangular-specific consumption and orchestration boundaries
    belong to `djng` and `ngdj` documentation, not the OpenUI specification.
  - Examples in `openui-spec` and `djng` are non-normative test fixtures.
  - Framework-associated names do not compromise technology independence.
    OpenUI represents element types, attribute names, and attribute values as
    structurally constrained strings. A name such as `ng-template` may be
    familiar from one framework while remaining an OpenUI type name that an
    Angular, QML, or other target compiler can materialize according to the
    declared contract. OpenUI stores these values but does not execute them or
    prescribe their target implementation.
  - Incremental generation is a technology-independent lifecycle notion and
    genuine use case. It defines reconciliation outcomes between a concrete UI
    document and an existing manifestation without prescribing Angular,
    QML, files, schematics, or another target implementation. It does not need
    to repeat the UI-object semantics defined by the glossary and scope
    contracts.
- [x] 15.1.2. Update `openui-spec` only if an actual defect is identified in
  its schema, catalog, concrete UI document, or implementation-independent
  boundary; do not add djangoangular-specific responsibilities to it.
  - No actual `openui-spec` defect was identified. The three-artifact contract,
    framework-associated string representation, and incremental-generation
    notion are consistent with its technology-independent boundary. No
    `openui-spec` change is required.
- [x] 15.1.3. Reference only the OpenUI specification and concrete-document
  SSOT from `djng` and `ngdj`.
  - `djng` maintained documentation now references the upstream OpenUI
    specification and artifact-role SSOT instead of restating schema, catalog,
    and concrete UI document responsibilities.
  - `ngdj` requirements reference the same external SSOT and explicitly avoid
    redefining it. Its repository-specific `site` input is identified in
    documentation, published schematic metadata, and runtime diagnostics as a
    site assembly definition, not mislabeled as an OpenUI concrete UI document.
- [ ] 15.1.4. Remove local definitions that incorrectly restrict OpenUI to
  non-CRM UI.

### 15.2 Replace CRM and non-CRM terminology

Investigate existing uses of `CRM` and `non-CRM` and replace them with terms
based on source and derivation:

- **API-contract-derived** — derived from OpenAPI.
- **UI-description-derived** — derived from an OpenUI concrete UI document.
- **explicitly authored UI** — UI declarations not inferred from OpenAPI.
- **Angular construction operation** — a deterministic `ngdj` workspace or
  code transformation.

A concern may be both API-contract-backed and UI-description-derived; these
classifications are not mutually exclusive.

- [ ] 15.2.1. Inventory and classify existing terminology in `djng` and
  `ngdj`.
- [ ] 15.2.2. Approve the canonical replacement terms.
- [ ] 15.2.3. Update `openui-spec` only if its existing generic UI boundary is
  incomplete.
- [ ] 15.2.4. Update `ngdj` references.
- [ ] 15.2.5. Update `djng` references.
- [ ] 15.2.6. Align GitHub issues and tests that still call `ngdj`-specific
  inputs “non-CRM OpenUI.”
