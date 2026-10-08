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

(what-build-app-runs-and-refuses)=

## What `build_app` runs and refuses

`build_app --dry-run` prints the ordered steps for the detected changes. The ngdj command
mapping that ships in the installed `angular-django2` package decides what ngdj supports,
so `djng` follows it instead of keeping its own list. The authoritative rules and tables
are in `doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Change-to-command mapping
[↗](https://github.com/shlomoa/django-angular3/blob/main/doc/requirements/APP_BUILDER_REQUIREMENTS.md#change-to-command-mapping){.modal-link}.

Supported today:

- A changed project name or workspace location selects the workspace and application
  foundation steps. A changed artifact selector selects only the final validation.
- A new OpenUI page, form, component or complex component selects the matching wrapper step.
  A new `tabs`, `dialog`, `stepper` or `table` element selects the matching
  `ng generate angular-django2:<command>` step, which has no wrapper. A change inside the
  `Application` element, including its routes, navigation and toolbar, selects an update of
  the application.
- A new OpenAPI path selects the client regeneration and its data service. A new schema
  selects the client regeneration.

Refused with an error that quotes the upstream reason and gap issue:

- Updating or deleting any other OpenUI node.
- A change to an OpenAPI operation, and updating or deleting a path or schema, because ngdj
  cannot update or delete data services.
- A node type with no `djng` Tool yet (`form-field`, `field-component`, `html`, `link`) or
  one the mapping does not cover.

Each step names the wrapper that runs it (through the crosswalk of
`doc/ARCHITECTURE.md` §3.6.4.1) and carries the options it needs, resolved from the project
configuration and the mapping: `name`, `target_path` and `project` for a page,
`document` and `node_id` for an OpenUI element, and so on. `--dry-run` prints them and
changes nothing. Without `--dry-run`, `build_app` first refuses to run steps with an unresolved
option (a data service has no `resource` until the resource identity rule is decided,
[shlomoa/django-angular3#207](https://github.com/shlomoa/django-angular3/issues/207)); it then copies an OpenUI
document that lies outside the Angular workspace to `.django-angular3/` in the workspace,
runs the steps level by level, halts at the first failure and writes
`build-evidence.json` to `--output` (default `build/`) with each call's exit code and
output and the pinned `angular-django2` package and mapping versions. `--force` is
refused until it is implemented. The final `last-check` gate builds the application
(`ng_build`) until the terminal validation commands exist.

Not implemented yet: translating a change into an `ng_openapi_setup` step, running a schema export step, and
detecting changes of `django-angular3.json`. Translating OpenUI and OpenAPI changes needs the `angular-django2`
package installed in the Angular workspace at the version `tool.ngAddPackage` pins (a
registry name such as `angular-django2@0.7.0`, not a path), so it cannot translate them for a
workspace that does not exist yet.

## Command ownership

- **ngdj schematics** use the identity, ownership, and upstream-source policy in
	`doc/ARCHITECTURE.md` §3.4
	[↗](https://github.com/shlomoa/django-angular3/blob/main/doc/ARCHITECTURE.md#34-ngdj){.modal-link}
	Follow the CLI reference linked there for
	schematic behavior, options, prerequisites, and examples.
- **djng wrappers** are the `ng_*` commands defined by this repository. Their
	executable mappings are defined by `_COMMAND_BUILDERS` in
	`django_angular3/angular.py`.
- This page owns djng wrapper arguments and interface availability. It does not
	redefine ngdj schematic contracts.
- `djng` validates OpenUI through the installed Python `openui-spec` tooling;
	it does not require a Node.js or TypeScript parser. `ngdj` owns consumption
	of the canonical OpenUI TypeScript parser. Both boundaries use only
	selectors, component types, and attribute contracts defined by
	`openui-spec`; see `doc/ARCHITECTURE.md` §3.4.1.
- djng emits every multiword Angular CLI option in kebab-case (for example,
	`--auth-guard` and `--openapi-spec-file`) so Angular CLI accepts the resolved
	invocation.

## Standalone-only commands

Invoked as `django-angular3 <command> [args]`.

| Command | Description |
|---|---|
| `validate-openapi <path>` | Validate an OpenAPI source document. |
| `validate-openui <path>` | Validate a canonical OpenUI JSON UI-definition document through `openui-spec`. |
| `validate-project` | Validate the discovered project configuration. |
| `install-tutorial [dest]` | Copy the bundled `simple_crm` tutorial project to `dest` (default: `simple_crm`). Prints migration and run steps on success. |

## Shared Angular wrappers

These commands are available through both interfaces. Invoke them as either
`django-angular3 <command>` or `django-admin <command>` / `python manage.py
<command>`.

| Command | djng behavior and arguments |
|---|---|
| `ng_new` | Create an empty Angular workspace. |
| `ng_workspace` | Bootstrap the configured workspace: `ng new`, workspace defaults, ngdj registration, and schematic generation. Accepts `--document <path>`, a workspace-relative OpenUI document for the workspace setup. |
| `ng_config` | Apply workspace defaults such as package manager, style, and routing. |
| `ng_add` | Run `ng add`; accepts `--package <name>` and otherwise uses the derived `ngAddPackage` setting. |
| `ng_gen_app` | Generate the configured Angular application. Accepts `--app-name <name>`, `--document <path>` (a workspace-relative OpenUI document) and `--node-id` (requires `--document`); SSR and zoneless behavior come from derived tool settings. |
| `ng_material_setup` | Configure Angular Material. Accepts `--project`, `--theme`, `--typography`/`--no-typography`, and `--animations`/`--no-animations`; unset options use ngdj defaults. |
| `ng_page` | Generate a routed page. Requires `--name` and `--target-path`; accepts `--project`, `--route-path`, `--access`, `--auth-guard`, `--navigation-label`, `--navigation-icon`, `--document <path>` (a workspace-relative OpenUI document) and `--node-id` (requires `--document`). |
| `ng_component` | Generate a standalone OnPush component. Requires `--name`; accepts `--target-path`, `--project`, `--document <path>` (a workspace-relative OpenUI document) and `--node-id` (requires `--document`). |
| `ng_complex_component` | Generate, modify, or delete an advanced Material component. Requires `--name`, `--target-path`, and `--features`; accepts `--project`, `--mode {create,modify,delete}`, delete confirmation via `--confirm`, `--document <path>` (a workspace-relative OpenUI document; requires `--mode create`) and `--node-id` (requires `--document`). |
| `ng_reactive_form` | Generate a typed reactive form. Requires `--name` and exactly one of `--document <path>` (a workspace-relative OpenUI document, with optional `--node-id`) or the deprecated `--definition`; accepts `--target-path`, `--project`, and `--primitives-path`. |
| `ng_openapi_gen` | Run the workspace-local `ng-openapi-gen` via `pnpm exec` for the discovered OpenAPI artifact. |
| `ng_openapi_setup` | Configure OpenAPI client generation and Django integration helpers. Accepts `--output-path`, `--helpers-path`, `--skip-helpers`, `--skip-tests`, and `--auth-scheme` (`bearer` or `basic`). |
| `ng_data_service` | Generate a typed data-service wrapper. Requires `--resource`; accepts `--project`. |
| `ng_build` | Build the discovered Angular application. |

All shared wrappers accept `--dry-run`. It reports discovered configuration,
derived artifact paths, and resolved subprocess calls without invoking Angular
tooling.

## Management-only commands

Invoked as `django-admin <command> [args]` or `python manage.py <command> [args]`.

| Command | Description |
|---|---|
| `export_schema` | Export the OAS schema from DRF (via drf-spectacular) to the discovered project artifact. Rotates the previous schema alongside the current one (`api.json` → `api.previous.json`) to provide the baseline file; a previous project configuration selects it through its `artifacts.openapiSchema` for `build_app` change detection. Accepts `--format {json,yaml}` (default: `json`) and `--dry-run`. |
| `build_app` | Detects project-configuration, OpenAPI and OpenUI changes and, with `--dry-run`, prints the ordered build steps as JSON (stage, step, mode, target, element id, wrapper command, parameters, unresolved parameters and reason). Without `--dry-run` it runs them in order against the Angular workspace, halts at the first failure and writes `build-evidence.json` to `--output`; static-configuration changes are not detected yet. OpenUI and OpenAPI changes are translated with the command mapping of the `angular-django2` package installed in the Angular workspace, so the package must be installed. Accepts `--current-config <path>` and `--previous-config <path>` overrides, plus `--dry-run`, `--output <dir>` and `--force start-from-scratch` (not implemented; refused). See {ref}`What build_app runs and refuses <what-build-app-runs-and-refuses>`. Each configuration independently resolves its OpenAPI and OpenUI artifact selectors; the previous configuration supplies the baseline documents. See `doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Inputs [↗](https://github.com/shlomoa/django-angular3/blob/main/doc/requirements/APP_BUILDER_REQUIREMENTS.md#inputs){.modal-link} for discovery behavior. |
| `clean` | Remove temporary Python build and package artifacts, including `build`, `dist`, root `*.egg-info`, caches, and Python bytecode. Accepts `--dry-run`. |
| `distclean` | Run `git clean -f -d` from the current project directory, removing all untracked files and directories while preserving ignored and tracked files. Accepts `--dry-run`, which passes `-n` to Git. |
| `ng_workspace_modify` | Reapply angular-django2 workspace bootstrap and djng defaults to the discovered workspace. |
| `ng_workspace_delete` | Delete the discovered Angular workspace entirely. |
