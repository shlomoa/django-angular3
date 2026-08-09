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
Complete. Both `spec/openui/app.openui.json` and the tutorial fixture use valid
OpenUI concrete documents.

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

### Step 2.2 — Delegate OpenUI validation to openui-spec

**Status: Complete.**

**Targets:** `pyproject.toml`, `requirements.txt`,
`django_angular3/validation.py`, `spec/openui/app.openui.json`,
`django_angular3/examples/01_simple_crm/app.openui.json`, and the associated
tests.

Raise djng's minimum supported Python version to 3.12 and declare
`openui-spec` as a runtime dependency. Replace the legacy `pages`/`forms`
validator with the published `OpenUiJson` API from `openui-spec`; djng must not
duplicate the OpenUI grammar, catalog, or duplicate-ID rules. Delegate concrete
document validation to `OpenUiJson.load(...).validate()` and surface its
diagnostics through the existing CLI and Django management-command wrappers.
Keep djng document-loading and dependency-boundary failures separate from
OpenUI format failures. Add concise docstrings to the public validation
functions: `validate_openapi_document`, `validate_openui_document`,
`validate_openapi_file`, `validate_openui_file`, and `validate_project_config`.
Migrate the tutorial `app.openui.json` from its legacy shape to a valid OpenUI
concrete document in the same step. The root fixture must also use types
supported by the released OpenUI catalog.

### Step 2.3 — Align the OpenUI document with generated-project configuration

**Status: Complete.**

**Targets:** `django_angular3/config.py` and `django_angular3/validation.py`.

Treat `django-angular3.json` as the generated-project configuration and its
`openui.source` as the selected `app.openui.json`. Validate the OpenUI document in
that project context: it is the non-CRM input used alongside the configured
OpenAPI source and Angular output. Add only cross-input validation that the
implemented assembly contract requires. OpenUI grammar, catalog-type, and
duplicate-ID validation remain delegated to `openui-spec`.

### Step 2.4 — Preserve generated-app build boundaries

**Status: Complete.**

**Target:** `django_angular3/management/commands/build_app.py`.

Keep `validate-openui` as the explicit non-CRM stage before assembly. `build_app`
owns project-source validation before change detection. Update its procedure
labels and outputs to identify the OpenUI document, but do not implement Angular
assembly in this task.

---

## Task 3: Validation and test updates

**Status: Partial.** Steps 3.2, 3.3, 3.5, and 3.6 remain outstanding.

### Step 3.1 — Unit coverage for delegated OpenUI validation

**Status: Complete.**

**Targets:** new `tests/test_validation.py` and
`tests/test_cli_scaffold.py`.

Create `tests/test_validation.py` for direct unit tests of
`validate_openui_document()` and `validate_openui_file()`. Cover a valid
concrete document and upstream validation failures for schema shape, unsupported
catalog types, and duplicate IDs. Assert that djng preserves actionable
upstream diagnostics and keeps document-loading failures distinct. Update
`tests/test_cli_scaffold.py` so its example and migrated tutorial fixtures are
validated through the delegated boundary.

### Step 3.2 — Generated-project configuration integration coverage

**Status: Partial.** Valid project configurations and legacy `ui` rejection are
covered. Coverage for missing OpenUI sources and invalid OpenUI documents through
`validate_project_config()` remains outstanding.

**Targets:** `tests/test_cli_scaffold.py`, `django-angular3.json`,
`spec/openui/app.openui.json`,
`django_angular3/examples/01_simple_crm/django-angular3.json`, and
`django_angular3/examples/01_simple_crm/app.openui.json`.

The root scaffold and tutorial configuration already point at
`app.openui.json`. After Step 2.2 migrates the tutorial document, extend
`tests/test_cli_scaffold.py` to retain coverage that
`load_project_config()` resolves `openui.source`, `validate_project_config()`
accepts the complete project. Add failures for a missing OpenUI source and an
invalid document reported by `openui-spec` through `validate_project_config()`.

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
