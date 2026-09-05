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
discovery, filename, and baseline-resolution behavior in
`doc/specifications/SPECIFICATIONS.md` §2.2
[↗](https://github.com/shlomoa/django-angular3/blob/main/doc/specifications/SPECIFICATIONS.md#22-project-configuration-discovery-and-baseline-resolution){.modal-link}

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

## Command ownership

- **ngdj schematics** use the identity, ownership, and upstream-source policy in
	`doc/ARCHITECTURE.md` §2.6
	[↗](https://github.com/shlomoa/django-angular3/blob/main/doc/ARCHITECTURE.md#26-ngdj){.modal-link}
	Follow the CLI reference linked there for
	schematic behavior, options, prerequisites, and examples.
- **djng wrappers** are the `ng_*` commands defined by this repository. Their
	executable mappings are defined by `_COMMAND_BUILDERS` in
	`django_angular3/angular.py`.
- This page owns djng wrapper arguments and interface availability. It does not
	redefine ngdj schematic contracts.
- djng emits every multiword Angular CLI option in kebab-case (for example,
	`--auth-guard` and `--openapi-spec-file`) so Angular CLI accepts the resolved
	invocation.

## Standalone-only commands

Invoked as `django-angular3 <command> [args]`.

| Command | Description |
|---|---|
| `validate-openapi <path>` | Validate an OpenAPI source document. |
| `validate-openui <path>` | Validate a UI definition document. |
| `validate-project` | Validate the discovered project configuration. |
| `install-tutorial [dest]` | Copy the bundled `simple_crm` tutorial project to `dest` (default: `simple_crm`). Prints migration and run steps on success. |

## Shared Angular wrappers

These commands are available through both interfaces. Invoke them as either
`django-angular3 <command>` or `django-admin <command>` / `python manage.py
<command>`.

| Command | djng behavior and arguments |
|---|---|
| `ng_new` | Create an empty Angular workspace. |
| `ng_workspace` | Bootstrap the configured workspace: `ng new`, workspace defaults, ngdj registration, and schematic generation. |
| `ng_config` | Apply workspace defaults such as package manager, style, and routing. |
| `ng_add` | Run `ng add`; accepts `--package <name>` and otherwise uses the derived `ngAddPackage` setting. |
| `ng_gen_app` | Generate the configured Angular application. Accepts `--app-name <name>`; SSR and zoneless behavior come from derived tool settings. |
| `ng_material_setup` | Configure Angular Material. Accepts `--project`, `--theme`, `--typography`/`--no-typography`, and `--animations`/`--no-animations`; unset options use ngdj defaults. |
| `ng_page` | Generate a routed page. Requires `--name` and `--target-path`; accepts `--project`, `--route-path`, `--access`, `--auth-guard`, `--navigation-label`, and `--navigation-icon`. |
| `ng_component` | Generate a standalone OnPush component. Requires `--name`; accepts `--target-path` and `--project`. |
| `ng_complex_component` | Generate, modify, or delete an advanced Material component. Requires `--name`, `--target-path`, and `--features`; accepts `--project`, `--mode {create,modify,delete}`, and delete confirmation via `--confirm`. |
| `ng_reactive_form` | Generate a typed reactive form. Requires `--name` and `--definition`; accepts `--target-path`, `--project`, and `--primitives-path`. |
| `ng_site` | Assemble or maintain a site. Create/modify requires exactly one of `--source` or `--defaults`; delete uses the ownership manifest and requires `--confirm-delete`. Accepts `--project`, `--operation`, `--auth-guard`, and CSRF-name options. |
| `ng_openapi_gen` | Run the workspace-local `ng-openapi-gen` via `pnpm exec` for the discovered OpenAPI artifact. |
| `ng_openapi_setup` | Configure OpenAPI client generation and Django integration helpers. Accepts `--output-path`, `--helpers-path`, `--skip-helpers`, and `--skip-tests`. |
| `ng_data_service` | Generate a typed data-service wrapper. Requires `--resource`; accepts `--project`. |
| `ng_build` | Build the discovered Angular application. |

All shared wrappers accept `--dry-run`. It reports discovered configuration,
derived artifact paths, and resolved subprocess calls without invoking Angular
tooling.

## Management-only commands

Invoked as `django-admin <command> [args]` or `python manage.py <command> [args]`.

| Command | Description |
|---|---|
| `export_schema` | Export the OAS schema from DRF (via drf-spectacular) to the discovered project artifact. Rotates the previous schema alongside the current one for future `build_app` change detection. Accepts `--format {json,yaml}` (default: `json`) and `--dry-run`. |
| `build_app` | Exposes the app-build command interface, but planning and execution are not implemented yet. Accepts `--current-config <path>` and `--previous-config <path>` overrides, plus `--dry-run` and `--force start-from-scratch`. Each configuration independently resolves its OpenAPI and OpenUI artifact selectors; the previous configuration supplies the baseline documents. See `doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Inputs [↗](https://github.com/shlomoa/django-angular3/blob/main/doc/requirements/APP_BUILDER_REQUIREMENTS.md#inputs){.modal-link} for discovery behavior. |
| `ng_workspace_modify` | Reapply angular-django2 workspace bootstrap and djng defaults to the discovered workspace. |
| `ng_workspace_delete` | Delete the discovered Angular workspace entirely. |
