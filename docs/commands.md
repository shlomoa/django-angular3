# Command reference

`djng` exposes two distinct command interfaces that serve different contexts.
They share the `ng_*` Angular wrapper layer but differ in invocation requirements
and available commands.

## The two interfaces

| | Standalone CLI | Django management commands |
|---|---|---|
| **Invoked as** | `django-angular3 <command>` | `django-admin <command>` or `python manage.py <command>` |
| **Requires Django project** | No | Yes — `django_angular3` must be in `INSTALLED_APPS` and `DJANGO_SETTINGS_MODULE` must be set |
| **Requires DRF / drf-spectacular** | No | Only for `export_schema` |
| **Primary use** | Validation and Angular wrappers without a project | Schema export and Angular workspace management inside a generated app |

## Project configuration discovery

Commands that operate on the generated app use the project-configuration
discovery rules in `doc/REQUIREMENTS.md` §4.2.4.

The static `djng` tool configuration, `django-angular3.json`, supplies derived
tool settings and is likewise not a command argument. Document validation
commands retain their document path because that is the artifact to validate,
not application configuration.

## Use cases

**Use the standalone CLI** when:
- Working in the `django-angular3` repository itself (no generated app present).
- Running validation in CI without a Django project.
- Validating OpenAPI, UI definition, or project config files in isolation.
- Invoking Angular wrapper commands from outside a Django project.

**Use the Django management commands** when:
- Operating inside a generated app that has `django_angular3` in `INSTALLED_APPS`.
- Exporting the OpenAPI schema from a live DRF backend (`export_schema`).
- Directly constructing and validating the generated app from schema and OpenUI changes (`build_app`).
- Managing the full Angular workspace lifecycle, including modify and delete operations.

## Standalone CLI commands

Invoked as `django-angular3 <command> [args]`.

| Command | Description |
|---|---|
| `validate-openapi <path>` | Validate an OpenAPI source document. |
| `validate-openui <path>` | Validate a UI definition document. |
| `validate-project` | Validate the discovered project configuration. |
| `ng_new` | Create an empty Angular workspace. |
| `ng_workspace` | Bootstrap the configured workspace: `ng new`, workspace defaults, `ng add angular-django2`, and schematic generation. |
| `ng_config` | Apply workspace defaults (package manager, style, routing). |
| `ng_add` | Run `ng add` for an Angular package. Accepts `--package <name>`. |
| `ng_gen_app` | Generate an Angular application inside the configured workspace via the `angular-django2:material-app` schematic. Accepts `--app-name <name>`; SSR and zoneless behavior come from the derived tool configuration. |
| `ng_complex_component` | Generate, update, or delete an advanced Angular Material component via `angular-django2:complex-component`. Requires `--name`, `--target-path`, and `--features`; accepts `--project`, `--mode {create,modify,delete}`, and `--confirm` (required for delete). |
| `ng_openapi_gen` | Run a locally installed `ng-openapi-gen` via `pnpm exec` for the discovered OAS artifact. |
| `ng_build` | Build the discovered Angular application. |
| `install-tutorial [dest]` | Copy the bundled `simple_crm` tutorial project to `dest` (default: `simple_crm`). Prints migration and run steps on success. |

All `ng_*` commands accept `--dry-run` for diagnostic validation and debugging.
It prints the discovered project and static tool configuration paths, derived
artifact paths, and resolved Angular subprocess calls without invoking Angular
tooling.

## Django management commands

Invoked as `django-admin <command> [args]` or `python manage.py <command> [args]`.

| Command | Description |
|---|---|
| `export_schema` | Export the OAS schema from DRF (via drf-spectacular) to the discovered project artifact. Rotates the previous schema alongside the current one for future `build_app` change detection. Accepts `--format {json,yaml}` (default: `json`) and `--dry-run`. |
| `build_app` | Validate the project inputs and begin the app-build planning workflow. The planner is not implemented yet. Accepts `--current-config <path>` and `--previous-config <path>` overrides, plus `--dry-run`, `--force start-from-scratch`, and `--acknowledge-breaking`. See `doc/APP_BUILDER_REQUIREMENTS.md` §Inputs for default discovery and previous-configuration fallback behavior. |
| `ng_new` | Create an empty Angular workspace. |
| `ng_workspace` | Bootstrap the discovered workspace. |
| `ng_workspace_modify` | Reapply angular-django2 workspace bootstrap and djng defaults to the discovered workspace. |
| `ng_workspace_delete` | Delete the discovered Angular workspace entirely. |
| `ng_config` | Apply derived workspace defaults. |
| `ng_add` | Run `ng add` for an Angular package. Accepts `--package <name>`; defaults to the derived `ngAddPackage` setting. |
| `ng_gen_app` | Generate an Angular application via the `angular-django2:material-app` schematic. Accepts `--app-name <name>`; SSR and zoneless behavior come from derived tool settings. |
| `ng_complex_component` | Generate, update, or delete an advanced Angular Material component via `angular-django2:complex-component`. Requires `--name`, `--target-path`, and `--features`; accepts `--project`, `--mode {create,modify,delete}`, and `--confirm` (required for delete). |
| `ng_openapi_gen` | Run `ng-openapi-gen` via `pnpm exec` for the discovered OAS artifact. |
| `ng_build` | Build the discovered Angular application. |

All management `ng_*` commands accept `--dry-run` for diagnostic validation and
debugging, printing discovery and derived-path metadata with the resolved
Angular subprocess call list without invoking Angular tooling.

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
