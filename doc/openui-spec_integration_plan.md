# openui-spec integration plan

## What openui-spec provides

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

## Task 3: Validation and test updates

**Status: Partial.** Steps 3.1, 3.2, and 3.4 are complete. Step 3.3 has
standalone CLI coverage and Step 3.5 has fixture coverage; their `build_app`
acceptance portions remain deferred. Step 3.6 remains outstanding.

### Step 3.3 — CLI and build-command integration coverage

**Status: Partial.** `tests/test_cli.py` covers standalone `validate-openui`
and `validate-project` success and invalid-OpenUI failure paths. Generated-app
`build_app` coverage remains deferred while that command is WIP.

**Target:** new `tests/test_cli.py`.

Add CLI tests for `validate-openui <app.openui.json>` and `validate-project`.
Verify valid fixtures return success and invalid OpenUI documents return failure
with the validation path. Add generated-app command coverage showing that
`build_app` rejects an invalid OpenUI source before change detection. This test file
is new because no current test module exercises these CLI commands.


### Step 3.5 — Three-lane scenario fixtures and acceptance coverage

**Status: Partial.** `spec/examples/` provides valid scenario configurations,
shared source artifacts, and a manifest covering all eight change-lane
combinations plus breaking, source-selection, and replacement cases. Direct
ChangeSet, command-ordering, and dry-run non-modification assertions remain
deferred until `build_app` is implemented.

**Targets:** `tests/`, `tests/test_export_schema.py`, and
`spec/examples/`.

Materialize and test the full $2^3$ matrix of incremental `config`, OpenAPI,
and OpenUI changes documented in `TEST_EXAMPLES.md`. Also retain coverage for
first-run, breaking, OpenUI-source-selection, and replacement cases. Each test
must assert all three ChangeSet lanes, selected commands, command ordering, and
dry-run non-modification behavior.

### Step 3.6 — Verification gate

After implementation, run Ruff format and lint checks plus the full unittest
suite specified in `.github/copilot-instructions.md`. Also run the relevant
`django-admin validate-openui`, `django-admin validate-project`, and
`django-admin build_app --dry-run` commands in a generated-app-compatible Django
configuration. Record the OpenUI format reference and commands in the
implementation change.

---

## Task 4: Complete direct `build_app` execution

**Status: Not started.** `build_app` is WIP; its current implementation is not
evidence that any Task 4 requirement is complete.

### Step 4.1 — Define previous-input handling

**Status: Planned.** Define how `build_app` receives the accepted prior project
state and prior OpenUI document before implementing comparison. The current
OpenUI input is selected by `artifacts.openuiSpecification`; do not introduce
an undocumented `--previous-openui` flag or `.previous` convention. Record the
chosen prior-state mechanism once in `doc/APP_BUILDER_REQUIREMENTS.md`, then
use it consistently in the command, examples, and tests.

### Step 4.2 — Implement command execution

**Targets:** `django_angular3/management/commands/build_app.py`,
`django_angular3/angular.py`, and the required direct execution boundaries.

Discover `django-angular3-project.json`; use `artifacts.openapiSchema`,
`artifacts.openuiSpecification`, and `artifacts.angularWorkspace` as the
current inputs and output location. Validate inputs, derive the `config`,
schema, and OpenUI change lanes from the accepted prior state, translate each
supported change directly to an executable command, and execute in dependency
order. An unsupported change must fail explicitly rather than being omitted.

`--dry-run` is diagnostic-only: it validates inputs, derives changes, reports
ordered commands with their modes, inputs, and reasons, and must not modify the
generated-app workspace. Normal execution must halt on the first wrapper, tool,
hook, or validation failure and surface the failure through Django's normal
error reporting.

### Step 4.3 — Define command translation and output validation

**Targets:** `doc/APP_BUILDER_REQUIREMENTS.md`, `TODO.md`, and
`django_angular3/management/commands/build_app.py`.

Define one complete mapping for every supported config, OpenAPI, and OpenUI
add, modify, delete, replacement, and first-run change. The mapping must name
the executable boundary, its mode, inputs, ordering prerequisites, and terminal
validation. Record missing wrappers as unsupported requirements until they
exist; execution must never silently skip their corresponding change. Define
post-execution generated-file checks, Angular build, and required integration
checks. Command execution and terminal validation—not an emitted plan—are the
build result.

### Step 4.4 — Add direct-build acceptance coverage

**Targets:** `tests/test_export_schema.py`, new focused `build_app` tests, and
the scenario fixtures in `doc/TEST_EXAMPLES.md`.

Implement the direct-build cases documented by Task 3.5 using the scenario
fixtures: every $2^3$ `config` × OpenAPI × OpenUI combination, plus first-run,
replacement, breaking-change, source-selection, deletion, and command-failure
cases. Assert all three derived lanes, selected executable boundaries, command
ordering, executed wrappers, and validated outputs—not an emitted plan. Cover
dry-run separately by asserting no generated-app files are modified.
