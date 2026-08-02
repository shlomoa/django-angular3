# Command reference

`django-angular3` exposes two distinct command interfaces that serve different
contexts. They share the `ng_*` Angular wrapper layer but differ in invocation
requirements and available commands.

## The two interfaces

| | Standalone CLI | Django management commands |
|---|---|---|
| **Invoked as** | `django-angular3 <command>` | `django-admin <command>` or `python manage.py <command>` |
| **Requires Django project** | No | Yes — `django_angular3` must be in `INSTALLED_APPS` and `DJANGO_SETTINGS_MODULE` must be set |
| **Requires DRF / drf-spectacular** | No | Only for `export_schema` |
| **Primary use** | Validation and Angular wrappers without a project | Full app lifecycle — including schema export, AI-automation plans, and workspace management |

## Use cases

**Use the standalone CLI** when:
- Working in the `django-angular3` repository itself (no generated app present).
- Running validation in CI without a Django project.
- Validating OpenAPI, UI definition, or project config files in isolation.
- Invoking Angular wrapper commands from outside a Django project.

**Use the Django management commands** when:
- Operating inside a generated app that has `django_angular3` in `INSTALLED_APPS`.
- Exporting the OpenAPI schema from a live DRF backend (`export_schema`).
- Generating an AI-automation build plan that reacts to schema changes (`build_app`).
- Managing the full Angular workspace lifecycle, including modify and delete operations.

## Standalone CLI commands

Invoked as `django-angular3 <command> [args]`.

| Command | Description |
|---|---|
| `validate-openapi <path>` | Validate an OpenAPI source document. |
| `validate-openui <path>` | Validate a UI definition document. |
| `validate-project [path]` | Validate a `django-angular3` project configuration. Defaults to `django-angular3.json`. |
| `ng_new [path]` | Create an empty Angular workspace. |
| `ng_workspace [path]` | Bootstrap the configured workspace: `ng new`, workspace defaults, `ng add angular-django2`, and schematic generation. |
| `ng_config [path]` | Apply workspace defaults (package manager, style, routing). |
| `ng_add [path]` | Run `ng add` for an Angular package. Accepts `--package <name>`. |
| `ng_gen_app [path]` | Generate an Angular application inside the configured workspace via the `angular-django2:material-app` schematic. Accepts `--app-name <name>`; SSR and zoneless behavior come from the project configuration. |
| `ng_complex_component [path]` | Generate, update, or delete an advanced Angular Material component via `angular-django2:complex-component`. Requires `--name`, `--target-path`, and `--features`; accepts `--project`, `--mode {create,modify,delete}`, and `--confirm` (required for delete). |
| `ng_openapi_gen [path]` | Run a locally installed `ng-openapi-gen` via `pnpm exec` for the configured OpenAPI source. |
| `ng_build [path]` | Build the configured Angular application. |
| `install-tutorial [dest]` | Copy the bundled `simple_crm` tutorial project to `dest` (default: `simple_crm`). Prints migration and run steps on success. |

Commands shown with `[path]` default to `django-angular3.json` when omitted. All
`ng_*` commands accept `--dry-run` to print the resolved Angular subprocess call
list without invoking Angular tooling.

## Django management commands

Invoked as `django-admin <command> [args]` or `python manage.py <command> [args]`.

| Command | Description |
|---|---|
| `export_schema <config>` | Export the OpenAPI schema from DRF (via drf-spectacular) and persist it as a versioned artifact. Rotates the previous schema alongside the current one for `build_app` change detection. Accepts `--format {json,yaml}` (default: `json`) and `--dry-run`. |
| `build_app <config>` | Validate the configured OpenAPI and UI sources, then generate a deterministic build plan driven by schema change detection. Maps skill/mode pairs to the corresponding management command names for AI-automation workflows. Accepts `--previous-schema <path>`, `--previous-config <path>`, `--output-format {json,yaml,text}` (default: `json`), `--output <dir>` (default: `build`), `--dry-run`, `--force start-from-scratch`, and `--acknowledge-breaking`. |
| `ng_new [path]` | Create an empty Angular workspace. |
| `ng_workspace [path]` | Bootstrap the configured workspace. |
| `ng_workspace_modify [path]` | Reapply angular-django2 workspace bootstrap and django-angular3 defaults to an existing workspace. |
| `ng_workspace_delete [path]` | Delete the generated Angular workspace entirely. |
| `ng_config [path]` | Apply workspace defaults. |
| `ng_add [path]` | Run `ng add` for an Angular package. Accepts `--package <name>`; defaults to the `ng_add_package` project setting. |
| `ng_gen_app [path]` | Generate an Angular application via the `angular-django2:material-app` schematic. Accepts `--app-name <name>`; SSR and zoneless behavior come from the project configuration. |
| `ng_complex_component [path]` | Generate, update, or delete an advanced Angular Material component via `angular-django2:complex-component`. Requires `--name`, `--target-path`, and `--features`; accepts `--project`, `--mode {create,modify,delete}`, and `--confirm` (required for delete). |
| `ng_openapi_gen [path]` | Run `ng-openapi-gen` via `pnpm exec`. |
| `ng_build [path]` | Build the configured Angular application. |

All management `ng_*` commands accept `--dry-run` to print the resolved Angular
subprocess call list without invoking Angular tooling.

## Command availability summary

| Command | Standalone CLI | Management commands |
|---|:---:|:---:|
| `validate-openapi` | ✓ | — |
| `validate-openui` | ✓ | — |
| `validate-project` | ✓ | — |
| `export_schema` | — | ✓ |
| `build_app` | — | ✓ |
| `ng_new` | ✓ | ✓ |
| `ng_workspace` | ✓ | ✓ |
| `ng_workspace_modify` | — | ✓ |
| `ng_workspace_delete` | — | ✓ |
| `ng_config` | ✓ | ✓ |
| `ng_add` | ✓ | ✓ |
| `ng_gen_app` | ✓ | ✓ |
| `ng_complex_component` | ✓ | ✓ |
| `ng_openapi_gen` | ✓ | ✓ |
| `ng_build` | ✓ | ✓ |
| `install-tutorial` | ✓ | — |
