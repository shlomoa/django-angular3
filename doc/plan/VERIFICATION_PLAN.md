# Verification Plan

## Purpose and boundary

Scenario, construction, integration, visual, interactive, terminal, global,
cross-platform, and staging verification.

Normative behavior remains owned by the referenced requirements,
specifications, contracts, architecture, and executable/configuration sources.
GitHub owns issue scope and tracking.

## Related domain plans

- [Configuration Plan](CONFIGURATION_PLAN.md)
- [Construction Plan](CONSTRUCTION_PLAN.md)
- [Automation Plan](AUTOMATION_PLAN.md)
- [Application Delivery Plan](APPLICATION_DELIVERY_PLAN.md)

## Scenario coverage

### Planning details

- See `doc/specifications/TEST_SCENARIO_SPECIFICATIONS.md` §7 for the canonical scenario definitions and expected outputs. <!-- STEP7-73e2b2d89da4 -->
- **Start from scratch**: a cold-start build with no previous state, invoking <!-- STEP7-aa63b920ffdb -->
- the full automation chain from workspace creation through app assembly and verification <!-- STEP7-25bece09a65e -->
- **Schema evolution — add**: an incremental schema change that adds a <!-- STEP7-0ac616eb7046 -->
- resource; only the required automation commands run, and existing workspace, app, and components are preserved <!-- STEP7-95229e9b51fe -->
- **Schema evolution — removal**: an incremental schema change removes a <!-- STEP7-ecd76149fb41 -->
- **OpenUI-only change**: an `app.openui.json` change with no schema change; only <!-- STEP7-8bdc9eef607b -->
- OpenUI-derived automation commands run <!-- STEP7-540aefacdf3d -->
- **Combined schema and OpenUI change**: both the contract and the OpenUI <!-- STEP7-d0dc2b209acb -->
- input source change in the same build; both change paths activate and interleave correctly <!-- STEP7-93a29d49b360 -->
- **Full replacement**: a resource is removed and a different resource is <!-- STEP7-8d2b4356ad3b -->
- added; remove steps precede add steps at the same dependency level <!-- STEP7-fdc9c054504f -->
- Skill acceptance does not compose into cross-Skill interface consistency, backend-contract / Angular-client alignment, and runnable application flows <!-- STEP7-a7273355a0df -->

### Open backlog

- [ ] Use the canonical scenario fixtures to cover all configuration, OpenAPI, and OpenUI scenario-axis combinations, plus first-run, source-selection, mixed create/delete, deletion, and command-failure cases. <!-- STEP7-b03bd33e95b1 -->

### Authoritative references

- Automation authority: automation requirements/specification and split primitive contracts. <!-- STEP7-7385437b03bd -->

## Construction and integration verification

### Open backlog

- [ ] Verify that djng selects, orders, and composes upstream ngdj operations in a real generated Angular workspace without duplicating ngdj's schematic tests. <!-- STEP7-3c60ec5f30ec -->

### Implementation sequence

- As behaviour moves from AI-guided Skill flow to deterministic tool/hook enforcement, test ownership moves with it: <!-- STEP7-9618b79718b9 -->
- Operations promoted to **Tools** (Phase 1) gain deterministic unit tests with <!-- STEP7-3048ead969d6 -->
- fixed inputs/outputs, replacing reliance on Skill self-checks. <!-- STEP7-7b2c9d4b7091 -->
- Gates and side effects promoted to **Hooks** (Phase 2) gain lifecycle-event <!-- STEP7-804fd6f71190 -->
- and exit-code tests, replacing "the agent remembered to do it" assumptions. <!-- STEP7-5f1757d8aba9 -->
- **Skills** (Phase 4) retain component/behaviour tests for generative output. <!-- STEP7-01a8c3183084 -->
- (Phase 7) own cross-Skill and integration correctness — the properties no single primitive's tests can establish. <!-- STEP7-ad63a88e25bf -->
- **Provider adapters** (Phase 5) first share a credential-free stub matrix; <!-- STEP7-37293ce82449 -->
- each real adapter then runs that matrix plus provider-specific rendering and lifecycle checks in an isolated, explicitly opted-in runtime suite. Missing credentials or SDKs skip live tests without prompting or exposing values. <!-- STEP7-e005967aff29 -->
- The default verification path remains credential-free: <!-- STEP7-bdd9f4471cda -->
- `ruff format django_angular3 tests` <!-- STEP7-055b07f996cc -->
- `ruff check django_angular3 tests` <!-- STEP7-2476e5b3fffe -->
- focused tests for the affected automation/build boundaries <!-- STEP7-924f34f342bd -->
- `python -m unittest discover -s tests -p 'test*.py'` <!-- STEP7-526734476145 -->
- generated-app-compatible `django-admin build_app --dry-run` coverage <!-- STEP7-b9002c79c218 -->
- Update implementation status, capability metadata, and the backlog only from actual test evidence. Provider-neutral stub success alone does not establish provider support. <!-- STEP7-be20b23163a3 -->

## Visual and interactive verification

### Scope and repository surfaces

Every user-facing artifact type introduced by a Skill, schematic, OpenUI
scope, or `ng_*` command must gain a reproducible visual demonstration when
that artifact type is first introduced. This is an artifact-type gate, not a
per-PR screenshot requirement.

Each repository retains its own verification surface:

| Repository | Visual verification surface | Tracking |
|---|---|---|
| `openui-spec` | Generated-examples application | `openui-spec#149` |
| `angular-django2` (`ngdj`) | `/ui` reference application and generated Angular application | `angular-django2#27`; parser dependencies `#98` and `#103` |
| `django-angular3` (`djng`) | Runnable generated application and gated `/ng/build` diagnostics | Application-delivery issues and `django-angular3#84` |

The cross-repository build order is `openui-spec` → `angular-django2` →
`django-angular3`. A single unified demo site is not required.

### Capture and reproduction gate

For each registered user-facing artifact type, verification must:

1. Boot the relevant generated or reference application against seeded fixture
	data.
2. Capture at least one full-page screenshot that demonstrates the artifact
	and upload it as a CI build artifact.
3. Fail when the application cannot boot or screenshot capture fails.
4. Never fail on visual difference; this plan does not require screenshot
	baselines, pixel diffing, or a flakiness budget.
5. Keep the result interactive through a checked-in `DEMO.md` that records the
	exact local server command, fixture setup, URL, and actions needed to
	reproduce each capture.

### Lifecycle enforcement

The planned deterministic `demo-capture` Tool and Hook are tracked by issues
#162 and #163. Before implementation, the normative Hook contract must be
added to `doc/contracts/HOOK_CONTRACTS.md` using its canonical seven-field
shape. This plan constrains that future contract as follows:

| Field | Planning constraint |
|---|---|
| Name | `demo-capture` |
| Purpose | Prove that a user-facing construction output renders and remains locally reproducible. |
| Trigger event | `post-tool`, after `post-generation` succeeds for a Tool that produces a user-facing artifact. |
| Deterministic action | Boot the application with seeded data, capture registered full-page screenshots, upload or record their artifact paths, and verify the corresponding `DEMO.md` reproduction entry. |
| Failure behavior | Halt on boot or capture failure using the Hook contract's structured failure and exit-code rules; never compare pixels or invoke AI judgment. |
| Allowed wrapped tools | The catalogued generation Tools that produce user-facing artifacts, plus catalogued dev-server and headless-browser Tools defined by #162. |
| Implementation reference | The implementation delivered through #162 and #163. |

Until the Hook exists, repository CI provides the same deterministic boot,
capture, artifact-upload, and reproduction-documentation gate. The Hook later
absorbs that enforcement without changing its acceptance semantics.

### Explicit exclusions

- A unified cross-repository demo site.
- Visual-regression or pixel-difference testing.
- Persistent demo hosting such as GitHub Pages or preview environments.

## Terminal and global acceptance

### Planning details

- **Global acceptance gate**: terminal verification fails the run when local <!-- STEP7-e8898cb29cfe -->

### Open backlog

- [ ] Verify cross-Skill interface consistency, backend-contract/Angular-client alignment, and runnable application flows according to `doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-10 and `doc/ARCHITECTURE.md` §§7.2–7.3. <!-- STEP7-a674b317b27a -->

### Implementation sequence

- **Goal**: Implement the terminal validation required by FR-9 and FR-10. <!-- STEP7-bc7fc7051940 -->
- **Dependencies**: Phases 3–5. <!-- STEP7-b64d9320145e -->
- Implement the terminal validation commands required by FR-9 and FR-10. <!-- STEP7-0bd00cbb73b6 -->
- Cover the four verification categories in `doc/ARCHITECTURE.md` §7.3: <!-- STEP7-30200c217ebf -->
- contract, construction-output, integration, and test-based verification. <!-- STEP7-a6b00647f6ef -->
- Apply AIR-3 and AIR-5 to terminal acceptance evidence. <!-- STEP7-82084302ca09 -->
- Terminal verification satisfies FR-8 and FR-9 in <!-- STEP7-f48531f20d7a -->
- `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. <!-- STEP7-ffa4f4c12abb -->
- Terminal-verification tests: success only on all-pass; failure path mirrors <!-- STEP7-9aef0114edc4 -->
- FR-8; verification consumes recorded tool outputs rather than rescanning. <!-- STEP7-d3ddd0bca0b4 -->
- **Dependencies**: Phases 4–6. <!-- STEP7-7c7b1d450fe1 -->
- The global acceptance requirement is defined by `doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-10. Its architectural ownership and rationale are defined in `doc/ARCHITECTURE.md` §§7.2–7.3. <!-- STEP7-c7ca12d651cc -->
- Implement the FR-10 global acceptance gate after the Phase 6 terminal validation foundation exists. <!-- STEP7-09837627733f -->
- Keep the global gate independent of any individual Skill's local acceptance decision. <!-- STEP7-4efbf1bceafe -->
- The implemented gate satisfies FR-10 in <!-- STEP7-92dddc92427b -->
- A regression test reproducing the interface-drift failure chain and asserting the global gate catches it. <!-- STEP7-661b93179860 -->
- **Terminal verification** (Phase 6) and the **global acceptance gate** <!-- STEP7-a4d9adc06886 -->

### Corrected current identities

- Cross-Skill interface-drift regression coverage maps to the Verification plan's global acceptance gate. <!-- STEP7-83db36d80726 -->

### Sequence structure

The source phase structure includes work-item, acceptance, and test
coverage blocks. Their substantive claims are rendered in this plan.

## Cross-platform and staging verification

No current verification work is assigned exclusively to this domain section.

## E2E validation

### Purpose and authority

E2E validation determines whether `djng` and `ngdj` produce an accepted,
runnable Django–Angular generated application. The flow begins with current
and previous generated-app inputs and finishes after contract,
construction-output, integration, compilation, and runtime acceptance.

`doc/specifications/TEST_SCENARIO_SPECIFICATIONS.md` owns the canonical
scenarios, inputs, expected outcomes, and their realization, and
`doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-9 and FR-10 own terminal
and global acceptance. This section sequences their E2E implementation.

### Repository responsibilities

| Repository | Responsibility | Validation source |
|---|---|---|
| `openui-spec` | Validate specification-derived generated examples and their registered visual demonstrations. | Generated-examples validation and `openui-spec#149` |
| `angular-django2` (`ngdj`) | Validate schematics and supported compositions in real Angular workspaces. | `docs/INTEGRATION_TESTING.md`, `tests/schematics.e2e.spec.ts`, and `npm run test:e2e` |
| `django-angular3` (`djng`) | Validate `build_app` orchestration and final acceptance of the composed Django–Angular application. | This plan and the django-angular3 E2E harness |

A released OpenUI package and ngdj package that have passed their respective
repository validation are inputs to the django-angular3 E2E suite.

### Implementation dependencies

The E2E implementation depends on:

1. Project-configuration discovery and baseline resolution from
	`doc/specifications/SPECIFICATIONS.md` §2.2.
2. Deterministic wrappers and Tool contracts for every scenario operation.
3. Operation-support decisions tracked by issues #57 and #162.
4. Direct `build_app` planning and execution tracked by issue #164.
5. Guided Skill execution tracked by issues #58 and #165 for scenarios that
	select Skills.
6. Structured execution evidence required by FR-8 and FR-9.
7. A released ngdj package containing the required schematic surface.
8. Registered visual demo targets and local reproduction instructions for
	every user-facing artifact type included in a scenario.

The scenario-invocation specification records the current implementation
status.

### Harness structure

The django-angular3 E2E harness will:

- use Example 1 from `django_angular3/examples/01_simple_crm/`;
- use Examples 2–12 from `tests/fixtures/scenarios/`;
- derive scenario selection from
  `tests/fixtures/scenarios/scenario-matrix.json`;
- keep runner code and runtime-flow definitions separate from fixture data;
- create generated applications under `tmparea/e2e/<run-id>/`;
- store reports, traces, screenshots, and logs under `e2e/test-output/`;
- allocate service ports dynamically;
- use bounded readiness and execution timeouts;
- stop backend, frontend, browser, and child processes during teardown;
- remove successful test areas; and
- preserve a failed test area when explicit debug retention is enabled;
- register visual capture targets by generated artifact type; and
- verify each target has a corresponding checked-in `DEMO.md` reproduction
	entry.

The E2E implementation issue will select and configure the browser-automation
runner used for user-facing flows.

### Implementation sequence

#### 1. Harness foundation

- Add the E2E runner entry point and configuration.
- Add generated-app test-area creation, cleanup, and debug retention.
- Add process lifecycle, dynamic port allocation, readiness checks, and
  diagnostic collection.
- Add fixture loading through normal project-configuration discovery.
- Record the django-angular3 and ngdj versions for each run.

#### 2. Scenario dry-run coverage

- Execute `build_app --dry-run` for the canonical scenario suite.
- Assert the canonical atomic changes and ordered commands.
- Verify command identity, mode, inputs, reason, and dependency order.
- Verify that each dry run preserves the generated workspace and accepted
  state.
- Cover the full scenario matrix from the scenario-invocation specification.

#### 3. Generated-application construction

- Execute each scenario against a real generated Angular workspace.
- Run selected wrappers, Tools, Hooks, and Skills in dependency order.
- Verify generated-output ownership and idempotence.
- Verify preservation of unaffected output during incremental scenarios.
- Verify deletion-before-creation ordering for replacement scenarios.
- Verify omission of commands unrelated to the detected changes.

#### 4. Integration and terminal validation

- Verify the generated Angular client against the exported OpenAPI contract.
- Verify types and signatures across API-client, data-service, form,
  component, page, route, and site boundaries.
- Verify composition of OpenAPI- and OpenUI-derived output.
- Run `ng_build`.
- Run generated-workspace type, lint, and test checks when configured.
- Apply the terminal acceptance requirements in FR-9.

#### 5. Runtime and global acceptance

Start the generated backend and frontend and verify the representative flows
owned by `doc/requirements/APPLICATION_FUNCTIONAL_REQUIREMENTS.md`:

- application startup and Angular routing;
- sign-in and sign-out;
- Django session handling;
- CSRF-protected mutations;
- authentication and authorization enforcement;
- permission-aware navigation;
- representative business-module list, detail, create, update, and deactivate
  or delete flows;
- client-side and server-side validation;
- filtering, sorting, pagination, and deterministic ordering; and
- user-safe handling of validation and server failures.

Run each registered `demo-capture` target against the seeded application and
upload its screenshots as CI artifacts. A boot or capture failure fails global
acceptance; screenshot differences do not.

Verify the local-development topology from
`doc/specifications/SPECIFICATIONS.md` §5.2 and the production-like topology
from §5.1. Apply the FR-10 global acceptance gate after construction,
integration, compilation, and runtime validation.

#### 6. Failure and recovery coverage

Add cases for:

- invalid static configuration;
- invalid project configuration;
- invalid OpenAPI input;
- invalid OpenUI input;
- unsupported atomic changes;
- wrapper or Tool failure;
- blocking Hook failure;
- unmet Skill acceptance;
- terminal-validation failure;
- service-start failure; and
- runtime-flow failure.

Each case will verify:

- halt at the failing boundary;
- suppression of dependent commands;
- a non-zero result;
- preservation of the previous accepted state; and
- failure attribution by scenario, gate, command, and contract.

### Evidence

Each run will record:

- scenario and run identity;
- django-angular3 and ngdj versions;
- sanitized input hashes;
- derived atomic changes;
- ordered command results;
- Tool and Hook results;
- generated-output checks;
- compilation and terminal results;
- runtime-flow results;
- visual target identities, screenshot artifact paths, and capture results;
- the `DEMO.md` reproduction entry associated with each visual target;
- timestamps; and
- the final acceptance decision.

Evidence serialization and redaction follow the automation contracts
referenced by `doc/plan/AUTOMATION_PLAN.md`.

### Completion criteria

Completion requires execution of the canonical scenario suite and its required
failure variants through real `build_app` boundaries. The acceptance criteria
then follow the governing requirement order:

1. **FR-2 and FR-3:** dry-run and direct execution are deterministic, and dry
	run preserves the generated workspace and accepted state.
2. **FR-5 and FR-6:** single-source and combined-change scenarios select and
	order only their required work while preserving unaffected output.
3. **FR-8:** failures stop at the responsible boundary, suppress dependent
	commands, preserve the previous accepted state, and provide actionable
	attribution.
4. **FR-9:** contract, construction-output, integration, compilation, and
	terminal validation succeed.
5. **FR-10:** global acceptance verifies cross-Skill consistency,
	backend/OpenAPI/client/UI alignment, and the required runtime flows.
6. The local-development and production-like application topologies pass their
	runtime flows.
7. Recorded evidence explains every acceptance decision.
8. Every registered user-facing artifact type boots, captures successfully,
   uploads its evidence, and has reproducible local instructions.
9. Issue #84 is closed from execution evidence.

## Tracked GitHub issues

- [#84 — Implement staged verification across contract, construction, integration, and tests](https://github.com/shlomoa/django-angular3/issues/84) <!-- STEP7-dda276a46eaf -->
- [#162 — Phase 7: implement deterministic TOOL contracts](https://github.com/shlomoa/django-angular3/issues/162)
- [#163 — Phase 8: implement direct lifecycle HOOK contracts](https://github.com/shlomoa/django-angular3/issues/163)
- [#160 — Phase 5: add credential-free provider-neutral automation tests](https://github.com/shlomoa/django-angular3/issues/160) <!-- STEP7-33102fa31a8b -->
- [#161 — Phase 6: verify and document the foundation boundary](https://github.com/shlomoa/django-angular3/issues/161) <!-- STEP7-295acb362ccd -->

Issue bodies, status, timestamps, relationships, dependency lists, and
acceptance criteria are intentionally not copied into this plan.

### Cross-repository visibility dependencies

- [angular-django2#27 — Assemble UI-description-derived content into the generated Angular application](https://github.com/shlomoa/angular-django2/issues/27)
- [angular-django2#98 — Integrate the canonical TypeScript OpenUI parser/validator package](https://github.com/shlomoa/angular-django2/issues/98)
- [angular-django2#103 — Wire the canonical parser into the schematics pipeline](https://github.com/shlomoa/angular-django2/issues/103)
- [openui-spec#149 — Align generators with the specification](https://github.com/shlomoa/openui-spec/issues/149)
