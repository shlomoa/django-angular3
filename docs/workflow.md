# Usage workflow

`django-angular3` coordinates separate OpenAPI and OpenUI inputs. The OpenAPI
schema describes the API contract, while the OpenUI concrete UI document
describes the UI; both may concern complementary aspects of the same feature.
This page describes the end-to-end cycle for your own project. For a guided
run-through using a ready-made sample, start with
[Getting started](getting-started.md).

## Responsibilities

- **Django + DRF** own backend data, authentication, authorization, and
  administration.
- **Angular Material** owns the end-user application and the client-side route
  tree.
- **OpenAPI** is the source of truth for API-contract-derived content.
- **The UI definition** supplies descriptions of pages, reactive forms, and
  workflows and may complement or reference OpenAPI-derived content while
  remaining a separate input artifact.

## The cycle

```{mermaid}
flowchart TD
  toolConfig[django-angular3.json<br/>static tool configuration] --> validate[Validate project inputs]
  projectConfig[django-angular3-<project_name>.json<br/>project configuration] --> validate
  drf[DRF backend] -->|export_schema| schema[OpenAPI schema]
  schema --> validate
  openui[OpenUI document] --> validate
  validate --> identify[build_app: identify changes]
  identify --> configChanges[Configuration changes]
  identify --> schemaChanges[OpenAPI changes]
  identify --> openuiChanges[OpenUI changes]
  configChanges --> project[Implement project-level changes]
  schemaChanges --> dataModel[Implement data-model changes]
  openuiChanges --> angularUi[Implement Angular UI changes]
  project --> execute[Execute in dependency order]
  dataModel --> execute
  angularUi --> execute
  execute --> verify[Validate generated app]
```

### 1. Export the OpenAPI contract

Inside a Django project with a live DRF backend, export the schema as a
versioned artifact. This is a Django management command (it needs DRF and
`drf-spectacular`):

```bash
python manage.py export_schema
# or: python manage.py export_schema --format yaml --dry-run
```

`export_schema` rotates the previous schema alongside the current one (inserting
`.previous` before the file extension) so later steps can detect changes.

### 2. Supply the UI definition

Author or update the OpenUI concrete UI document referenced by
`artifacts.openuiSpecification` in the discovered project configuration. The
generated app convention names this document `app.openui.json`. Its grammar and vocabulary are defined by
the [OpenUI artifact-role SSOT](https://github.com/shlomoa/openui-spec/blob/main/spec/README.md#specification-artifacts-grammar-vs-catalog), not by djng;
consult the [OpenUI per-scope examples](https://openui-spec.readthedocs.io/en/latest/examples/)
when authoring the OpenUI concrete UI document. The repository fixture at
[`tests/fixtures/artifacts/openui/example.openui.json`](https://github.com/shlomoa/django-angular3/blob/main/tests/fixtures/artifacts/openui/example.openui.json)
shows the accepted concrete-document structure.

#### Compare OpenUI versions

OpenUI change semantics are owned by the upstream
[OpenUI JSON comparison tool](https://openui-spec.readthedocs.io/en/latest/tooling/comparison/),
not by `djng`. Until `build_app` integrates this planned comparison step, run
the tool from an `openui-spec` checkout with its repository-local interpreter,
passing the accepted reference document first and the candidate document
second:

```powershell
.\.venv\Scripts\python bin\compare_openui_json.py reference.json new.json
```

```bash
./.venv/bin/python bin/compare_openui_json.py reference.json new.json
```

Use `--output changelog.json` (or `-o changelog.json`) to write the
deterministic changelog to a file. The tool matches identified lists by their
unique `id`, so reordering those items does not produce a change. Its `remove`,
`add`, and `change` entries map to `djng` `delete`, `create`, and `update`
Changes respectively; `djng` must not reimplement OpenUI comparison semantics.

### 3. Validate

Validate the project configuration and its referenced sources before building.
Each piece can also be validated in isolation:

```bash
django-angular3 validate-project
django-angular3 validate-openapi schema.yaml
django-angular3 validate-openui openui.json
```

### 4. Build and validate the generated app

`build_app` is reserved for the generated-app construction planner. The current
implementation discovers and validates the project inputs, but its planning and
execution workflow is not implemented yet. Do not rely on it to build or
validate a generated app; use the individual wrappers below while the planner
is completed. Its target requirements are documented in
`doc/APP_BUILDER_REQUIREMENTS.md`.

### 5. Run individual Angular wrappers when needed

The `ng_*` commands wrap the Angular toolchain. They require Node.js and pnpm.
Use `--dry-run` only to validate and debug a wrapper invocation without
executing it:

```bash
django-angular3 ng_workspace     # bootstrap the workspace
django-angular3 ng_openapi_gen   # generate API client from OpenAPI
django-angular3 ng_build         # build the Angular app
```

`ng_openapi_gen` runs a locally installed `ng-openapi-gen` via `pnpm exec`, so
it only uses dependencies already present in the workspace — it never downloads
and executes packages at runtime.

### 6. Compose Angular feature components

API-contract-derived artifacts (the API client, data services, and inferred
pages) come from the schema. Explicitly authored feature UI is composed from Angular
components generated by the `angular-django2` schematics and wired into the
visible application hierarchy. This is a repeatable **generate → embed**
workflow.

The commands below are Angular schematics; run them inside the generated
workspace with `pnpm exec ng generate ...` (the same locally installed toolchain
the `ng_*` wrappers use). Replace `<app-name>` with your application name.

For an advanced Material component that needs theme mixins, nested children,
projection slots, or CDK overlay behavior, use the `ng_complex_component`
wrapper rather than assembling those features through `embed-component` alone:

```bash
django-angular3 ng_complex_component \
  --name dashboard-card --target-path src/app/features/dashboard \
  --features mixins,nested,projection --dry-run
```

The wrapper delegates to `angular-django2:complex-component`. Use `--mode
modify` to add features, or `--mode delete --confirm` to remove the generated
component and registered theme mixin.

#### Generate a feature component

Generate a component into the intended Angular project instead of leaving it
disconnected or workspace-root-relative:

```bash
ng generate angular-django2:component dashboard-card \
  --project=<app-name> --path=src/app/features/dashboard
```

This creates the component under
`projects/<app-name>/src/app/features/dashboard/dashboard-card/` as a standalone
`OnPush` component. Unlike a plain `ng generate component`, the generated
TypeScript and template files are seeded with stable **begin/end embedding
hooks** — marker pairs around the import, injected-services, input, output, and
template `children` sections. These markers are the well-known insertion points
the `embed-component` schematic targets, so a generated component is ready to be
wired into a parent without hand-editing.

#### Embed a generated child into a parent

Generating a component does not make it visible. Wire it into a parent
component with `embed-component`, using workspace-relative `.ts` paths:

```bash
ng generate angular-django2:embed-component \
  --component=projects/<app-name>/src/app/features/dashboard/dashboard-card/dashboard-card.ts \
  --parent=projects/<app-name>/src/app/app.ts
```

**Before** — making the child visible meant several manual, error-prone edits to
the parent: add the child selector to the template, import the child class,
register it in the standalone `imports` array, wire each input/output signal, and
hand-write output callback methods.

**After** — `embed-component` performs that wiring through the generated hooks:

- inserts the child element after the parent template `children` marker
- feeds each child input signal
- binds each child output signal to an `on<Output>($event)` handler
- imports the child class in the parent
- registers the child in the parent standalone `imports` array
- adds not-implemented `on<Output>()` handler stubs to the parent class

You then fill in the generated `on<Output>()` stubs with real behavior.

#### Compose a nested feature hierarchy

Repeat the two steps to build a feature area from several components and embed the
feature parent into the app shell. Each `embed-component` call names one child
(`--component`) and one parent (`--parent`):

```bash
ng generate angular-django2:component hero-card \
  --project=<app-name> --path=src/app/features/dashboard
ng generate angular-django2:component dashboard \
  --project=<app-name> --path=src/app/features/dashboard
ng generate angular-django2:embed-component \
  --component=projects/<app-name>/src/app/features/dashboard/hero-card/hero-card.ts \
  --parent=projects/<app-name>/src/app/features/dashboard/dashboard/dashboard.ts
ng generate angular-django2:embed-component \
  --component=projects/<app-name>/src/app/features/dashboard/dashboard/dashboard.ts \
  --parent=projects/<app-name>/src/app/app.ts
```

`hero-card` is embedded into `dashboard`, then `dashboard` is embedded into the
root `app` component, producing a visible nested UI.

To embed a third-party component (for example an Angular Material control), use
package mode by adding `--from` and treating `--component` as the exported class
name, optionally with `--selector`, `--inputs`, and `--outputs`:

```bash
ng generate angular-django2:embed-component \
  --component=MatDateRangePicker --from=@angular/material/datepicker \
  --parent=projects/<app-name>/src/app/app.ts
```

#### Re-run embedding safely

`embed-component` is designed to be **idempotent**: re-running the same embed
during iterative development does not duplicate the child selector, the import,
the `imports` array entry, or the `on<Output>()` handler stubs. After embedding,
rebuild to verify the composition compiles:

```bash
django-angular3 ng_build
```

### 7. Iterate

The workflow is iterative. After the backend schema changes, business records
change, or you adjust the UI definition, re-export the schema, re-validate, and
re-run the build and Angular steps. Re-verify frontend/backend alignment after
each cycle.

## Which interface should I use?

- Use the **standalone CLI** (`django-angular3 <command>`) for validation and
  Angular wrappers without a Django project — for
  example in CI or while working in this repository.
- Use the **Django management commands** (`python manage.py <command>`) inside a
  generated app — especially for `export_schema`, `build_app`, and full
  workspace lifecycle management.

See the [command reference](commands.md) for the complete list and the
availability of each command in both interfaces.
