# Usage workflow

`django-angular3` is **contract-first**: the OpenAPI schema exported from your
DRF backend is the source of truth for CRM-facing functionality, and bespoke
non-CRM pages and forms are supplied separately as a structured UI definition.
This page describes the end-to-end cycle for your own project. For a guided
run-through using a ready-made sample, start with
[Getting started](getting-started.md).

## Responsibilities

- **Django + DRF** own backend data, authentication, authorization, and
  administration.
- **Angular Material** owns the end-user application and the client-side route
  tree.
- **OpenAPI** is the source of truth for CRM-facing, contract-derived content.
- **The UI definition** supplies bespoke non-CRM pages, reactive forms, and
  workflows, kept separate from the OpenAPI-derived content.

## The cycle

```text
DRF backend ──export_schema──▶ OpenAPI schema ─┐
                                               ├─▶ validate-project ──▶ build / build_app
UI definition ─────────────────────────────────┘                              │
                                                                               ▼
                          Angular Material app ◀── ng_build ◀── ng_workspace + ng_openapi_gen
```

### 1. Export the OpenAPI contract

Inside a Django project with a live DRF backend, export the schema as a
versioned artifact. This is a Django management command (it needs DRF and
`drf-spectacular`):

```bash
python manage.py export_schema django-angular3.json
# or: python manage.py export_schema django-angular3.json --format yaml --dry-run
```

`export_schema` rotates the previous schema alongside the current one (inserting
`.previous` before the file extension) so later steps can detect changes.

### 2. Supply the UI definition

Author or update the structured UI definition referenced by `ui.source` in your
`django-angular3.json`. This describes non-CRM pages and forms, for example:

```yaml
pages:
  - route: /dashboard
    kind: dashboard

forms:
  - id: invite-user
    mode: reactive
    submit:
      action: createUser
```

### 3. Validate

Validate the project configuration and its referenced sources before building.
Each piece can also be validated in isolation:

```bash
django-angular3 validate-project django-angular3.json
django-angular3 validate-openapi schema.yaml
django-angular3 validate-ui ui.json
```

### 4. Generate the build plan

Produce a deterministic build plan. Use `--dry-run` to preview it:

```bash
# Standalone CLI — validation + build plan, no Django project required:
django-angular3 build django-angular3.json --dry-run

# Inside a generated app — schema-change-driven AI-automation plan:
python manage.py build_app django-angular3.json --dry-run
```

`build` emits a deterministic build plan from the validated project.
`build_app` (a management command) drives the plan from schema change detection
and maps skill/mode pairs to management command names for AI-automation
workflows.

### 5. Scaffold and build the Angular app

The `ng_*` commands wrap the Angular toolchain. They require Node.js and pnpm.
Preview any of them with `--dry-run`:

```bash
django-angular3 ng_workspace django-angular3.json     # bootstrap the workspace
django-angular3 ng_openapi_gen django-angular3.json   # generate API client from OpenAPI
django-angular3 ng_build django-angular3.json          # build the Angular app
```

`ng_openapi_gen` runs a locally installed `ng-openapi-gen` via `pnpm exec`, so
it only uses dependencies already present in the workspace — it never downloads
and executes packages at runtime.

### 6. Iterate

The workflow is iterative. After the backend schema changes, business records
change, or you adjust the UI definition, re-export the schema, re-validate, and
re-run the build and Angular steps. Re-verify frontend/backend alignment after
each cycle.

## Which interface should I use?

- Use the **standalone CLI** (`django-angular3 <command>`) for validation,
  build-plan generation, and Angular wrappers without a Django project — for
  example in CI or while working in this repository.
- Use the **Django management commands** (`python manage.py <command>`) inside a
  generated app — especially for `export_schema`, `build_app`, and full
  workspace lifecycle management.

See the [command reference](commands.md) for the complete list and the
availability of each command in both interfaces.
