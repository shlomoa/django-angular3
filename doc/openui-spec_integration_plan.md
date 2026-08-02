# openui-spec integration plan

## What openui-spec provides

The `openui-spec` defines three layered artifacts:

- **`openui.schema.json`** — grammar: validates the shape of any OpenUI JSON document
- **`openui.json`** — catalog: machine-readable vocabulary of all scope objects (Application, Controls, Behaviors, Pages, Views, Containers, Widgets, …)
- **concrete UI document** (`input.json`) — a schema-valid document using vocabulary from the catalog; this is the user-authored UI description

The concrete document format directly resolves the `<project>.project.json` "schema TBD" blocker in APP_BUILDER_REQUIREMENTS.md and TODO §1.

---

## Task 1: Documentation updates

Documentation must treat the published OpenUI specification as the single
source of truth for the non-CRM UI document grammar and vocabulary. This
repository should describe only the djng integration contract: the configured
input location, the OpenUI version and local artifacts it accepts, and the
build-stage behavior. It must link to the OpenUI specification rather than
duplicating its grammar, catalog, or scope definitions.

### Step 1.1. — Anchor the format in ARCHITECTURE.md (foundational)
**Target:** `doc/ARCHITECTURE.md §8.5`  
Add a reference to `shlomoa/openui-spec` as the format authority for the non-CRM input source. Name the concrete document as an OpenUI concrete UI document conforming to `openui.schema.json` with vocabulary from `openui.json`. Settle the file name (e.g. `app.ui.json` or keep `input.json`).  
**Why first:** all other documents derive from this anchor.

### Step 1.2. — Formalize the stage in REQUIREMENTS.md (gap named in TODO §1)
**Target:** `doc/REQUIREMENTS.md §4.2.2`  
Add the missing sentence naming the non-CRM content stage as a discrete governed construction stage, referencing `ARCHITECTURE.md §7.1 stage 4`.  
**Why second:** depends on the format name established in Step 1.

### Step 1.3. — Resolve TBDs in APP_BUILDER_REQUIREMENTS.md
**Target:** APP_BUILDER_REQUIREMENTS.md  
Replace the three ⚠️/TBD markers (schema definition, diff function, `<project>.project.json` name) with concrete references: the file name settled in Step 1, `openui.schema.json` as the validation schema, and a note that diff behavior operates on the OpenUI document tree.

### Step 1.4. — Update the spec/ui example
**Target:** example.ui.json  
Rewrite the example to use the openui-spec concrete document format (`id`, `version`, `type`, `attrs`, `children` per `openui.schema.json`) instead of the current custom `pages`/`forms` shape. Reference the per-scope examples at `openui-spec.readthedocs.io/en/latest/examples/` as the vocabulary source.

### Step 1.5. — Update README.md
**Target:** `README.md` (line 231 area)  
Replace the YAML `pages`/`forms` snippet (the old custom format) with an equivalent openui-spec concrete document JSON example. The copilot-instructions require `README.md` to be updated for user-facing workflow or command changes; switching the UI input format is user-facing.  
**Why here:** depends on the format and file name settled in Steps 1 and 4.

### Step 1.6. — Close / update TODO §1
**Target:** `TODO.md §1`  
Change status from **Blocked** to **In progress** or **Resolved — pending implementation**. Record openui-spec as the format definition. List the remaining open items: validation implementation in `validation.py`, final file name if still to be confirmed, and `REQUIREMENTS.md §4.2.2` gap if not yet closed.

**Dependency chain:** Step 1 → Steps 2, 3 (parallel) → Step 4 → Step 5 → Step 6.  
Steps 2 and 3 can be done in the same pass once the file name is anchored. Step 4 requires the name and format to be settled. Step 5 (README.md) follows Step 4. Step 6 should be the final close-out pass.

---

## Task 2: Code updates

### Step 2.1 — Update project configuration and examples

**Targets:** `django_angular3/config.py`, `django-angular3.json`, and the
tutorial configuration under `django_angular3/examples/`.

Retain `ui.source` as the concrete OpenUI document path. Update the root and
tutorial configuration to use the file name selected by Task 1. Continue to
report a clear configuration error when that source is missing or is not a file.

### Step 2.2 — Replace legacy UI-shape validation

**Target:** `django_angular3/validation.py`.

Replace the legacy `pages`/`forms` validation with deterministic validation of
the OpenUI concrete-document format: root `version`, `id: "root"`, `type`,
optional `attrs`, and recursive `children`; element ID/type naming rules;
`attrs` string-or-null values; and no loose properties. Return stable,
path-qualified errors suitable for the existing CLI and Django management-command
wrappers. Keep document-loading errors separate from format errors.

### Step 2.3 — Align the UI document with generated-project configuration

**Targets:** `django_angular3/config.py` and `django_angular3/validation.py`.

Treat `django-angular3.json` as the greater generated-project configuration and
its `ui.source` as the selected `project.ui.json`. Validate the UI document in
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
`spec/ui/example.ui.json`,
`django_angular3/examples/01_simple_crm/django-angular3.json`, and
`django_angular3/examples/01_simple_crm/ui.json`.

Update the root scaffold and tutorial fixtures to point at and contain valid
OpenUI documents. In `tests/test_cli_scaffold.py`, retain coverage that
`load_project_config()` resolves `ui.source`, `validate_project_config()`
accepts the complete project. Add failures for a missing UI source and an
invalid OpenUI document through `validate_project_config()`.

### Step 3.3 — CLI and build-command integration coverage

**Target:** new `tests/test_cli.py`.

Add CLI tests for `validate-openui <project.ui.json>` and `validate-project`.
Verify valid fixtures return success and invalid OpenUI documents return failure
with the validation path. Add generated-app command coverage showing that
`build_app` rejects an invalid UI source before change detection. This test file
is new because no current test module exercises these CLI commands.

### Step 3.4 — Documentation-fixture regression coverage

**Targets:** `README.md`, `spec/ui/example.ui.json`,
`django_angular3/examples/01_simple_crm/ui.json`, and
`tests/test_cli_scaffold.py`.

Make the README show or link to the same `spec/ui/example.ui.json` fixture that
the test suite validates. Retain direct validation of that fixture and the
tutorial fixture in `tests/test_cli_scaffold.py`, so the documented examples
remain conformant without parsing Markdown snippets in tests.

### Step 3.5 — Verification gate

After implementation, run Ruff format and lint checks plus the full unittest
suite specified in `.github/copilot-instructions.md`. Also run the relevant
`django-admin validate-openui`, `django-admin validate-project`, and
`django-admin build_app --dry-run` commands in a generated-app-compatible Django
configuration. Record the OpenUI format reference and commands in the
implementation change.

---

## Task 4: Amend `build_app` from planning to direct build execution

### Step 4.1 — Resolve the previous-OpenUI interface

**Decision tracked in:** `TODO.md` §2.0.

Choose whether the prior OpenUI document is resolved through
`--previous-config` or supplied directly through `--previous-ui <path>`. The
selection is required before changing command arguments, examples, tests, or
the previous-state loader.

### Step 4.2 — Replace change-plan emission with command execution

**Targets:** `django_angular3/management/commands/build_app.py` and
`django_angular3/angular.py`.

Retain comparison of current and previous OpenAPI and OpenUI inputs. Replace
the emitted procedure graph, `build-plan.*` output, `--output-format`, and
`--output` with direct translation of both change sets into supported command
wrappers, followed by execution in dependency order. `--dry-run` must report
the commands that would execute and must not modify the generated-app
workspace. A wrapper failure must halt the build and propagate through Django
error reporting.

### Step 4.3 — Define command translation and output validation

**Targets:** `doc/APP_BUILDER_REQUIREMENTS.md`, `TODO.md`, and
`django_angular3/management/commands/build_app.py`.

Specify the command selected for every OpenAPI and OpenUI add, modify, and
delete change, including the required missing wrappers. Define validation after
execution: generated-file checks, Angular build, and the required integration
checks. Do not retain a plan/procedure-graph artifact as a substitute for
executing or validating the build.

### Step 4.4 — Replace obsolete planning documentation

**Targets:** `doc/APP_BUILDER_REQUIREMENTS.md`, `doc/ARCHITECTURE.md`,
`doc/REQUIREMENTS.md`, `doc/GENERATE_AI_AUTOMATIONS.md`,
`doc/TEST_EXAMPLES.md`, `doc/phased_implementation_plan.md`,
`doc/SKILL_AUTHORING_PLAN.md`, `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md`,
`docs/commands.md`, `docs/workflow.md`, related skills, and generated Sphinx
output.

Replace procedure-graph and build-plan language with the direct six-step build
algorithm: validate current inputs; compare OAS; compare OpenUI; translate
changes to commands; execute; validate results. Preserve only current-state
comparison, explicit execution order, mandatory gates, and terminal validation.

### Step 4.5 — Add direct-build acceptance coverage

**Targets:** `tests/test_export_schema.py`, new focused `build_app` tests, and
the scenario fixtures in `doc/TEST_EXAMPLES.md`.

Test first-run, OAS-only, OpenUI-only, combined, deletion, breaking-change, and
command-failure cases. Assert executed wrappers and validated outputs—not an
emitted plan. Cover dry-run separately by asserting no generated-app files are
modified.
