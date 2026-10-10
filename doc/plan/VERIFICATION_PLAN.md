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
- create generated applications under `scratch/e2e/<run-id>/`;
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

### First slice: the tutorial flow

[#232](https://github.com/shlomoa/django-angular3/issues/232) implemented the
first runnable slice, `DJNG_E2E=1 python -m tests.e2e.run_e2e`, with the
`End-to-end` workflow (`.github/workflows/e2e.yml`). It runs the bundled
tutorial project through the real tools and is not driven by the scenario
matrix. Its stages, prerequisites and environment variables are in
`CONTRIBUTING.md` ("End-to-end validation"). It selected `@playwright/test` as the
browser-automation runner; the Python orchestrator starts it.

| Stage | Covered |
|---|---|
| Backend and contract | tutorial install, seeded database, `export_schema` with the real `drf-spectacular` (paths, schemas, `info`, rotation to `schema.previous.json`), `validate-openapi` |
| Construction (wrappers directly, Track W) | `ng_workspace`, `ng_gen_app --document`, `ng_openapi_setup`, `ng_openapi_gen`, `ng_page --document`, the `table` schematic, `ng_data_service` |
| Compilation | `ng_build` |
| Runtime | Playwright against `runserver` and `ng serve`: shell and navigation, data alignment with the API and the seed, pagination, the failure path |
| `build_app` (Track B, phase 2) | after a document and a schema change: the dry run derives the steps, the run succeeds, the evidence pins the ngdj package and mapping versions |

Differences from the harness structure above, to be settled when the scenario
suite gets its own runner:

- The generated application is created under `scratch/e2e-<id>/` (through
  `tests/workspace_temp.py`), not `scratch/e2e/<run-id>/`. The area is removed on
  exit; `E2E_KEEP=1` keeps it, after a success as well as after a failure.
- Evidence, reports, traces and screenshots go to `build/e2e-evidence/`, not
  `e2e/test-output/`.
- The ports are fixed (Django 8000, Angular 4200), not allocated dynamically.
- Visual targets and `DEMO.md` reproduction entries are not registered.
- `build_app` from nothing (Track B phase 1) is not covered; it waits on
  [#209](https://github.com/shlomoa/django-angular3/issues/209) and
  previous-configuration discovery. The `ng_data_service` step of `build_app`
  also waits on [#207](https://github.com/shlomoa/django-angular3/issues/207).

#### Findings of the first runs (2026-10-08)

The runs showed these differences between the tools and their documentation or
the flow's design. The flow works around each one and records the relevant ones
in the `findings` of its `summary.json`. Each is tracked in the issue named in the
last column.

| Finding | Owner | Handling in the flow | Issue |
|---|---|---|---|
| `export_schema` dropped `drfSpectacular.settings` (`info.title` and `version` were `""` and `0.0.0`) | djng | Fixed ([#223](https://github.com/shlomoa/django-angular3/issues/223)); the flow asserts `info` against the tool configuration | [#223](https://github.com/shlomoa/django-angular3/issues/223) (fixed) |
| The tutorial's `app.openui.json` puts `DashboardPage` under `Application`, which `material-app --document` rejects | djng (tutorial) | The flow uses an `html` root with the `Application` and its pages as siblings | [#238](https://github.com/shlomoa/django-angular3/issues/238) |
| A `table` cannot be composed into a `DashboardPage` (supported: `SurfaceContainers`, `Form`, `TextInputs`, `RangeControl`) | ngdj | The table is a sibling element; the host glue places it in the page | [angular-django2#212](https://github.com/shlomoa/angular-django2/issues/212) |
| `material-app` builds sidenav links from `Navigation` and `NavItem`, not from every `DashboardPage` as its documentation says | ngdj | The document declares `Navigation` | [angular-django2#212](https://github.com/shlomoa/angular-django2/issues/212) |
| `ng-openapi-gen` 1.x generates the functional client (`api.ts`, `fn/`, `models/`) and no `services/`; djng's `ngOpenApiGen` configuration accepts only `serviceSuffix` and `modelIndex`, and the `data-service` schematic wraps a `<Resource>ApiService` | djng and ngdj | The host glue uses the generated `Api` class; the generated data service is not part of the build | [#240](https://github.com/shlomoa/django-angular3/issues/240) |
| `ng_openapi_gen` wrote the client to `<workspace>/generated/ng-openapi-gen`, replacing the `output` of the `ng-openapi-gen.json` that `ng_openapi_setup` wrote | djng | Fixed ([#239](https://github.com/shlomoa/django-angular3/issues/239)): `ng_openapi_gen` keeps the `output` of `ng_openapi_setup`; the flow asserts it is inside the application project | [#239](https://github.com/shlomoa/django-angular3/issues/239) (fixed) |
| `openapi-setup` and the `data-service` schematic default to the workspace-root `src/` instead of the application project | ngdj | `ng_openapi_setup` now defaults to the application project, and `ng_data_service --path` places the service (a workspace-relative path: the non-document `data-service` form ignores `--project` for its location) ([#239](https://github.com/shlomoa/django-angular3/issues/239)); the flow passes explicit project paths and asserts the location | [angular-django2#212](https://github.com/shlomoa/angular-django2/issues/212) |
| The generated `ResourceAdapter` only logs a failed request; no generated artifact shows an error state | ngdj | The failure spec asserts the log and the host glue's own error state | [angular-django2#212](https://github.com/shlomoa/angular-django2/issues/212) |
| The tutorial's `shop` app has no migrations, so `migrate` alone creates no tables | djng (tutorial) | The flow uses `migrate --run-syncdb` | [#238](https://github.com/shlomoa/django-angular3/issues/238) |
| Under CI environment variables pnpm 10 refuses installs that update the lockfile, including the one the Angular CLI runs | tooling | The flow removes the CI markers from the tools' environment | none; documented in `CONTRIBUTING.md` |
| `oasdiff` is downloaded at first use and fails behind a restrictive egress policy | djng | The flow requires it pre-installed | [#241](https://github.com/shlomoa/django-angular3/issues/241) |

#### Integration validation run (2026-10-09)

A run of the first slice with `E2E_TRACKS=W` validated that the `ngdj` commands that `djng`
wraps generate an Angular Material frontend from the tutorial DRF model and configuration,
and that the browser reads Django data through the REST interface.

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -p 'test*.py'` with `DJNG_REQUIRE_NGDJ=1`, `ruff check`, `ruff format --check` | Passed: 298 tests, 4 skipped (Sphinx build absent, `build_app` work in progress, the E2E flow itself) |
| `ngdj` contract tests against the sibling `angular-django2` 0.7.0 | Passed |
| E2E Track W, stages 0–6 (backend, schema export, workspace and Material app, API client, build, Playwright P1–P4) | Passed on Node 24.21.0 |
| `E2E_BREAK=model-field`, `openui-route`, `proxy` | Failed at stages 2, 6 and 6, as required |
| E2E Track B (`build_app` phase 2) | Not run in that session: `oasdiff` could not be downloaded, because the session's GitHub access did not include `oasdiff/oasdiff` ([#241](https://github.com/shlomoa/django-angular3/issues/241)); run on 2026-10-10, see below |

Stage 0 rejects Node 22.22.0, because `ngdj` requires `^22.22.3 || ^24.15.0 || >=26`; the run
used Node 24.21.0. Screenshots, traces and the Playwright report are in
`build/e2e-evidence/`.

The run is the local-development topology of `doc/specifications/SPECIFICATIONS.md` §5.2:
`ng serve` proxies `/api` to Django, so the browser sees one origin and CORS does not arise.
The production-like topology of §5.1 is not provided by either repository. A probe of
`runserver` on the generated workspace after the passing run found:

| Finding | Owner | Evidence |
|---|---|---|
| Django has no route for the built application: `GET /` and `GET /customers` return 404, so a hard refresh on an Angular route fails | djng | `build/e2e-evidence/production-topology-probe.txt` |
| No static-file or base-href strategy: `ng_build` leaves `dist/<app>/browser` with `<base href="/">`, and neither `ngdj` nor `djng` passes `--base-href` or `--deploy-url` | ngdj and djng | same |
| No CORS configuration (no `corsheaders`), so an Angular origin different from Django's gets no `Access-Control-*` headers; the dev proxy and a same-origin deployment avoid the need | djng | same |
| The `/ng/build` page that the repository instructions require returns 404 | djng | same |
| The generated client uses relative `/api/v1/...` paths and the `csrftoken` cookie with the `X-CSRFToken` header, which match Django's defaults | none | same |

The production-like topology was open at the time of this run; the next section closes it.

#### Django serves the built application (2026-10-10)

`django_angular3.spa` serves the bundle `ng_build` leaves in `dist/<app>/browser` from Django
on the same origin as the API (README, "Serving the built application"). The tutorial project
is wired with it, and stage 6b of the real-tools flow starts Django alone, with no Angular dev
server and no proxy, and drives the bundle with Playwright: the dev-server specs P1–P4 again,
and D1–D6 (`tests/e2e/specs/django-served.spec.ts`).

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -p 'test*.py'` with `DJNG_REQUIRE_NGDJ=1`, `ruff check`, `ruff format --check` | Passed: 320 tests, 4 skipped; `tests/test_spa.py` has 12 of them |
| E2E Track W, stages 0–6b | Passed on Node 24.21.0 (local run and the `e2e` job of the pull request): P1–P4 and D1–D6, 12 of 12 |
| `E2E_BREAK=django-dist`, `model-field`, `openui-route`, `proxy` | Failed at stages 6b, 2, 6 and 6, as required |
| E2E Track B (`build_app` phase 2) | Passed together with Track W (stages 0–6b and B, 157 s): after a document change (an added `reportsPage`) and a schema change (`Health`), the dry run derives the steps and the run succeeds; `build-evidence.json` pins `angular-django2@0.7.0`, mapping version 1 and `openui-spec` 0.12.1 |

Track B ran with `oasdiff` v1.33.0 built from source in the sandbox (`go install` of that tag
with the go1.27.1 toolchain, both fetched through the checksum-verified Go module proxy),
because the session's GitHub access does not include `oasdiff/oasdiff`
([#241](https://github.com/shlomoa/django-angular3/issues/241)); the GitHub job downloads
the latest release instead. A source build reports `oasdiff version main`, which is what
`tool-versions.json` records; `go version -m` on the binary gives the module version.

Findings of the 2026-10-09 probe, as they stand now:

| Finding | Status |
|---|---|
| `GET /` and `GET /customers` returned 404 | Resolved: 200 with `index.html`; D1 hard-refreshes `/customers` and `/products` |
| No static-file or base-href strategy | Resolved without a build flag: the bundle is served from the root, which matches the `<base href="/">` that `ngdj` emits. A deployment under a path prefix would still need `--base-href` and `--deploy-url`, which neither repository passes |
| No CORS configuration | Not needed on one origin: D5 asserts every API call goes to the Django origin and that Django sends no `Access-Control-*` header. A separate Angular origin would still need `corsheaders`, which is not provided |
| The generated client uses relative `/api/v1/...` paths and the `csrftoken` / `X-CSRFToken` names | Unchanged, and now exercised through Django (D3, D5) |
| The `/ng/build` page that the repository instructions require | Still open: the page does not exist. `GET /ng/build` now returns the application's `index.html` through the fallback, which is not that page |

The view reads the files through Django. That suits development, tests and small
deployments; behind real traffic a reverse proxy or a static-file layer serves the same
directory. CSRF-protected writes and sign-in are not covered by this stage: the specs only
read, and the tutorial API allows anonymous access.

Evidence of the stage is under `build/e2e-evidence/`: `playwright-django-report/`,
`playwright-django-results/` (traces) and `screenshots-django/` (`D1-refresh-customers`,
`D1-refresh-products`, `D2-products`, `D4-admin`, and the P1–P4 set).

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

- Execute each scenario against a real generated Angular workspace. The
  real-tools flow of `tests/e2e/run_e2e.py` (see the "End-to-end validation"
  section of `CONTRIBUTING.md`) is the first such run: tutorial project, real
  `drf-spectacular` export, real Angular CLI, ngdj and `ng-openapi-gen`, and a
  browser against Django. It covers the wrappers directly (Track W) and
  `build_app` after a document and schema change (Track B phase 2); the
  per-scenario matrix remains to be run the same way.
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
- [#232 — Real-tools end-to-end flow: DRF schema export, generated Angular app, and Playwright through the UI against Django](https://github.com/shlomoa/django-angular3/issues/232)
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
