# openui-spec integration plan

## What openui-spec provides

The `openui-spec` defines three layered artifacts:

- **`openui.schema.json`** — grammar: validates the shape of any OpenUI JSON document
- **`openui.json`** — catalog: machine-readable vocabulary of all scope objects (Application, Controls, Behaviors, Pages, Views, Containers, Widgets, …)
- **concrete UI document** (`input.json`) — a schema-valid document using vocabulary from the catalog; this is the user-authored UI description

The concrete document format defines the non-CRM input consumed by the djng
integration contract.

---

## Task 0: Remove the build-planning model from documentation — complete

**Targets:** all repository documentation and skills that describe `build_app`,
including `README.md`, `CONTRIBUTING.md`, `TODO.md`, `doc/`, `docs/`,
`skill_creation/`, root-level planning documents, and generated Sphinx output.

Before documenting or implementing OpenUI integration, remove claims that
`build_app` emits a build plan, procedure graph, plan file, or unexecuted
command list. Establish direct execution as the only documented model: validate
current inputs; compare OpenAPI and OpenUI; translate changes into commands;
execute in dependency order; and validate the generated app. Preserve historical
references only when explicitly labelled as superseded. Update the relevant
examples, diagrams, command descriptions, skills, and roadmap text so they do
not reintroduce the build-planning model.

---

## Task 1: Documentation updates — complete

Documentation must treat the published OpenUI specification as the single
source of truth for the non-CRM UI document grammar and vocabulary. This
repository should describe only the djng integration contract: the configured
input location, the OpenUI version and local artifacts it accepts, and the
build-stage behavior. It must link to the OpenUI specification rather than
duplicating its grammar, catalog, or scope definitions.

### Step 1.1. — Anchor the format in ARCHITECTURE.md (foundational)
**Target:** `doc/ARCHITECTURE.md §8.5`  
Complete. `ARCHITECTURE.md` names `spec/openui/app.openui.json` as the OpenUI
concrete UI document and references `openui.schema.json` and `openui.json` as
the external format authorities.

### Step 1.2. — Formalize the stage in REQUIREMENTS.md (gap named in TODO §1)
**Target:** `doc/REQUIREMENTS.md §4.2.2`  
Complete. `REQUIREMENTS.md` names non-CRM content construction as the discrete
governed construction stage.

### Step 1.3. — Complete the APP_BUILDER_REQUIREMENTS.md contract
**Target:** APP_BUILDER_REQUIREMENTS.md  
Complete. The requirements define the `app.openui.json` input, OpenUI document
tree comparison, and the three-lane `config` / `schema` / `openui` ChangeSet.

### Step 1.4. — Update the spec/openui example
**Target:** app.openui.json
Complete for `spec/openui/app.openui.json`. The tutorial fixture remains a legacy
`pages` / `forms` document and is migrated by Task 2.2.

### Step 1.5. — Update README.md
**Target:** `README.md` (line 231 area)  
Complete. The README identifies `spec/openui/app.openui.json` as the non-CRM input
and links to the OpenUI vocabulary examples.

### Step 1.6. — Close / update TODO §1
**Target:** `TODO.md §1`  
Complete. `TODO.md` records OpenUI as the format authority and tracks the
remaining implementation work.

The settled integration contract is: `openui.source` selects
`app.openui.json`; the prior document is supplied by `--previous-openui` or,
when omitted, the current source's `.previous` sibling.

---

## Task 2: OpenUI grammar validation and project-context validation

### Step 2.1 — Update project configuration and examples

**Targets:** `django_angular3/config.py`, `django-angular3.json`, and the
tutorial configuration under `django_angular3/examples/`.

**Status: Complete.** `openui.source` is the required configuration key, and
the root and tutorial configurations select `app.openui.json`. The loader
rejects the legacy `ui` mapping and project validation reports missing OpenUI
sources clearly.

### Step 2.2 — Replace legacy UI-shape validation **(next)**

**Target:** `django_angular3/validation.py`.

Replace the legacy `pages`/`forms` validation with deterministic validation of
the OpenUI concrete-document format: root `version`, `id: "root"`, `type`,
optional `attrs`, and recursive `children`; element ID/type naming rules;
`attrs` string-or-null values; and no loose properties. Return stable,
path-qualified errors suitable for the existing CLI and Django management-command
wrappers. Keep document-loading errors separate from format errors.

### Step 2.3 — Align the OpenUI document with generated-project configuration

**Targets:** `django_angular3/config.py` and `django_angular3/validation.py`.

Treat `django-angular3.json` as the generated-project configuration and its
`openui.source` as the selected `app.openui.json`. Validate the OpenUI document in
that project context: it is the non-CRM input used alongside the configured
OpenAPI source and Angular output. Add only cross-input validation that the
document format and implemented assembly contract require; do not introduce
OpenUI catalog validation in this task.

### Step 2.4 — Preserve generated-app build boundaries

**Target:** `django_angular3/management/commands/build_app.py`.

Keep `validate-openui` as the explicit non-CRM stage before assembly. `build_app`
owns project-source validation before change detection. Update its procedure
labels and outputs to identify the OpenUI document, but do not implement Angular
assembly in this task.

---

## Task 3: Validation and test updates

### Step 3.1 — Unit coverage for grammar validation

**Targets:** new `tests/test_validation.py` and
`tests/test_cli_scaffold.py`.

Create `tests/test_validation.py` for direct unit tests of
`validate_openui_document()`. Cover a valid OpenUI concrete document and invalid
cases for: a non-object document; missing or invalid top-level `version`, `id`,
or `type`; invalid element IDs/types; invalid `attrs` value types; unrecognized
loose properties; and malformed `children`. Assert path-qualified,
deterministic diagnostics. Update `tests/test_cli_scaffold.py` so its example
and tutorial UI-document tests load the new OpenUI fixtures.

### Step 3.2 — Generated-project configuration integration coverage

**Targets:** `tests/test_cli_scaffold.py`, `django-angular3.json`,
`spec/openui/app.openui.json`,
`django_angular3/examples/01_simple_crm/django-angular3.json`, and
`django_angular3/examples/01_simple_crm/app.openui.json`.

The root scaffold and tutorial configuration already point at
`app.openui.json`. After Step 2.2 migrates the tutorial document, extend
`tests/test_cli_scaffold.py` to retain coverage that
`load_project_config()` resolves `openui.source`, `validate_project_config()`
accepts the complete project. Add failures for a missing OpenUI source and an
invalid OpenUI document through `validate_project_config()`.

### Step 3.3 — CLI and build-command integration coverage

**Target:** new `tests/test_cli.py`.

Add CLI tests for `validate-openui <app.openui.json>` and `validate-project`.
Verify valid fixtures return success and invalid OpenUI documents return failure
with the validation path. Add generated-app command coverage showing that
`build_app` rejects an invalid OpenUI source before change detection. This test file
is new because no current test module exercises these CLI commands.

### Step 3.4 — Documentation-fixture regression coverage

**Targets:** `README.md`, `spec/openui/app.openui.json`,
`django_angular3/examples/01_simple_crm/app.openui.json`, and
`tests/test_cli_scaffold.py`.

Make the README show or link to the same `spec/openui/app.openui.json` fixture that
the test suite validates. Retain direct validation of that fixture and the
tutorial fixture in `tests/test_cli_scaffold.py`, so the documented examples
remain conformant without parsing Markdown snippets in tests.

### Step 3.5 — Three-lane scenario fixtures and acceptance coverage

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

### Step 4.1 — Resolve the previous-OpenUI interface

**Status: Complete.** The prior OpenUI document uses the same
explicit-override then
adjacent-`.previous` algorithm used for OpenAPI: `--previous-openui <path>`
takes precedence; otherwise use the `.previous` sibling of the current
`openui.source`.

### Step 4.2 — Implement command execution

**Targets:** `django_angular3/management/commands/build_app.py` and
`django_angular3/angular.py`.

Retain comparison of current and previous OpenAPI and OpenUI inputs. Translate
both change sets directly into supported command wrappers, then execute them in
dependency order. `--dry-run` is diagnostic-only: it must validate inputs,
identify changes, report the commands that would execute, and not modify the
generated-app workspace. A wrapper failure must halt the build and propagate
through Django error reporting.

### Step 4.3 — Define command translation and output validation

**Targets:** `doc/APP_BUILDER_REQUIREMENTS.md`, `TODO.md`, and
`django_angular3/management/commands/build_app.py`.

Specify the command selected for every OpenAPI and OpenUI add, modify, and
delete change, including the required missing wrappers. Define validation after
execution: generated-file checks, Angular build, and the required integration
checks. Command execution and validation are the build result.

### Step 4.4 — Add direct-build acceptance coverage

**Targets:** `tests/test_export_schema.py`, new focused `build_app` tests, and
the scenario fixtures in `doc/TEST_EXAMPLES.md`.

Implement the direct-build cases documented by Task 3.5: every $2^3$
`config` × OpenAPI × OpenUI combination, plus first-run, replacement,
breaking-change, source-selection, deletion, and command-failure cases. Assert
executed wrappers and validated outputs—not an emitted plan. Cover dry-run
separately by asserting no generated-app files are modified.
