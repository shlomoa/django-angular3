# Configuration

`djng` keeps tool behavior separate from generated-app identity and inputs.
The authoritative definitions, fields, defaults, ownership, and lifecycle are
in the executable configuration models; their categories and relationships
are specified in `doc/specifications/SPECIFICATIONS.md` §2
<a href="https://github.com/shlomoa/django-angular3/blob/main/doc/specifications/SPECIFICATIONS.md#2-configuration-and-inputs" target="_blank" rel="noopener noreferrer" aria-label="Open Configuration and inputs in the source documentation in a new tab">↗</a>.

## Configuration and inputs

| Item | Owner | Purpose |
|---|---|---|
| `django-angular3.json` | `djng` | Static tool configuration: Angular execution settings, global `ng-openapi-gen` settings, and `drf-spectacular` settings. |
| Project configuration | generated-app user | Generated-app identity and artifact locations. See `doc/specifications/SPECIFICATIONS.md` §2.1 <a href="https://github.com/shlomoa/django-angular3/blob/main/doc/specifications/SPECIFICATIONS.md#21-configuration-and-input-categories" target="_blank" rel="noopener noreferrer" aria-label="Open Configuration and input categories in the source documentation in a new tab">↗</a>. |
| OpenAPI schema | generated-app user | API-contract input or the artifact exported from Django/DRF. |
| OpenUI concrete UI document | generated-app user | Structured UI-description input. |

`DJANGO_ANGULAR3` and `DjangoAngularSettings` are derived from the static tool
configuration; they are not independent configuration authorities. Likewise,
the workspace's `ng-openapi-gen.json` is a per-run artifact derived by `djng`;
do not maintain it as production configuration.

## Static tool configuration

`django-angular3.json` configures `djng` itself. It supplies:

- global `ngOpenApiGen` options;
- `drfSpectacular.settings`, scoped to schema export;
- Angular workspace, application, and build defaults; and
- tool executable names, command allowlist, and default `ng add` package.

Start with the packaged `django-angular3.json` template. Commands consume this
static configuration; they do not accept its path as an argument.

## Generated-app project configuration

The project configuration identifies a generated app and names the paths that
a command uses for its OpenAPI schema, OpenUI concrete UI document, and Angular
workspace. Its filename, discovery, ownership, and field requirements are
specified in `doc/specifications/SPECIFICATIONS.md` §2.1
<a href="https://github.com/shlomoa/django-angular3/blob/main/doc/specifications/SPECIFICATIONS.md#21-configuration-and-input-categories" target="_blank" rel="noopener noreferrer" aria-label="Open Configuration and input categories in the source documentation in a new tab">↗</a>
and implemented by the executable
configuration model.

Use `django-angular3 validate-project` or `python manage.py validate_project`
to validate the discovered project configuration and referenced inputs.

## Derived run-time configuration

When `ng_openapi_gen` runs, `djng` combines the global `ngOpenApiGen` settings
with the discovered project's schema and workspace paths. It writes a derived
`ng-openapi-gen.json` in the Angular workspace, then invokes the locally
installed generator with `pnpm exec ng-openapi-gen -c <generated-config-path>`.

When `export_schema` runs, `djng` scopes the derived
`drfSpectacular.settings` to the direct `drf-spectacular` management-command
invocation. Neither derived configuration is a user-maintained command input.

## Command behavior

Project-operating commands do not accept configuration-file path arguments.
Their `--dry-run` output shows the discovered project and static tool
configuration paths, derived artifact paths, and resolved subprocess calls.
See the [command reference](commands.md) for the supported command interfaces.
