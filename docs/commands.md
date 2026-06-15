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
| **Primary use** | Validation, build-plan generation, Angular wrappers without a project | Full app lifecycle — including schema export, AI-automation plans, and workspace management |

## Use cases

**Use the standalone CLI** when:
- Working in the `django-angular3` repository itself (no generated app present).
- Running validation and build-plan generation in CI without a Django project.
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
| `validate-ui <path>` | Validate a UI definition document. |
| `validate-project [path]` | Validate a `django-angular3` project configuration. Defaults to `django-angular3.json`. |
| `build [path]` | Validate a project and emit a deterministic build plan. Accepts `--dry-run` and `--output <dir>`. |
| `ng_new [path]` | Create an empty Angular workspace. |
| `ng_workspace [path]` | Bootstrap the configured workspace: `ng new`, workspace defaults, `ng add angular-django2`, and schematic generation. |
| `ng_config [path]` | Apply workspace defaults (package manager, style, routing). |
| `ng_add [path]` | Run `ng add` for an Angular package. Accepts `--package <name>`. |
| `ng_gen_app [path]` | Generate an Angular application inside the configured workspace. Accepts `--app-name <name>`. |
| `ng_openapi_gen [path]` | Run a locally installed `ng-openapi-gen` via `pnpm exec` for the configured OpenAPI source. |
| `ng_build [path]` | Build the configured Angular application. |
| `install-tutorial [dest]` | Copy the bundled `simple_crm` tutorial project to `dest` (default: `simple_crm`). Prints migration and run steps on success. |

All commands default `path` to `django-angular3.json` when omitted. All `ng_*`
commands accept `--dry-run` to print the resolved Angular subprocess call list
without invoking Angular tooling.

## Django management commands

Invoked as `django-admin <command> [args]` or `python manage.py <command> [args]`.

| Command | Description |
|---|---|
| `export_schema <path>` | Export the OpenAPI schema from DRF (via drf-spectacular) and persist it as a versioned artifact. Rotates the previous schema alongside the current one for `build_app` change detection. Accepts `--format yaml` and `--dry-run`. |
| `build_app <path>` | Generate a deterministic build plan driven by schema change detection. Maps skill/mode pairs to the corresponding management command names for AI-automation workflows. |
| `ng_new [path]` | Create an empty Angular workspace. |
| `ng_workspace [path]` | Bootstrap the configured workspace. |
| `ng_workspace_modify [path]` | Reapply angular-django2 workspace bootstrap and django-angular3 defaults to an existing workspace. |
| `ng_workspace_delete [path]` | Delete the generated Angular workspace entirely. |
| `ng_config [path]` | Apply workspace defaults. |
| `ng_add [path]` | Run `ng add` for an Angular package. |
| `ng_gen_app [path]` | Generate an Angular application. |
| `ng_openapi_gen [path]` | Run `ng-openapi-gen` via `pnpm exec`. |
| `ng_build [path]` | Build the configured Angular application. |

## Command availability summary

| Command | Standalone CLI | Management commands |
|---|:---:|:---:|
| `validate-openapi` | ✓ | — |
| `validate-ui` | ✓ | — |
| `validate-project` | ✓ | — |
| `build` | ✓ | — |
| `export_schema` | — | ✓ |
| `build_app` | — | ✓ |
| `ng_new` | ✓ | ✓ |
| `ng_workspace` | ✓ | ✓ |
| `ng_workspace_modify` | — | ✓ |
| `ng_workspace_delete` | — | ✓ |
| `ng_config` | ✓ | ✓ |
| `ng_add` | ✓ | ✓ |
| `ng_gen_app` | ✓ | ✓ |
| `ng_openapi_gen` | ✓ | ✓ |
| `ng_build` | ✓ | ✓ |
| `install-tutorial` | ✓ | — |
