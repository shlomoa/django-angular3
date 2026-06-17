# Configuration

`django-angular3` reads two kinds of configuration:

- **`django-angular3.json`** — a per-project file describing the project, its
  OpenAPI and UI sources, and Angular workspace settings. Used by both the
  standalone CLI and the Django management commands.
- **`DJANGO_ANGULAR3`** — an optional dictionary in your Django project's
  `settings.py` that controls executable paths, the command allowlist, and
  workspace defaults. Only relevant when running inside a Django project.

## The `django-angular3.json` file

This file lives in the root of your project. Most commands accept its path as a
positional argument and default to `django-angular3.json` in the current
directory when omitted.

```json
{
  "project": { "name": "simple_crm" },
  "openapi": { "source": "schema.yaml" },
  "ui": { "source": "ui.json" },
  "angular": {
    "output": "build/angular",
    "workspace": { "packageManager": "pnpm", "style": "scss", "routing": true }
  }
}
```

All relative paths are resolved against the directory that contains the
configuration file.

### Fields

| Key | Required | Description |
|---|:---:|---|
| `project.name` | ✓ | Non-empty project name. |
| `openapi.source` | ✓ | Path to the OpenAPI source document (JSON or YAML). |
| `openapi.openapiGeneratorConfig` | — | Path to an OpenAPI Generator config file. |
| `openapi.ngOpenApiGenConfig` | — | Path to an `ng-openapi-gen` config file. |
| `ui.source` | ✓ | Path to the UI definition document. |
| `angular.output` | ✓ | Output directory for generated Angular artifacts. `angular.package` is accepted as an alias. |
| `angular.workspace.packageManager` | — | Package manager for the workspace (e.g. `pnpm`). |
| `angular.workspace.style` | — | Stylesheet format (e.g. `scss`). |
| `angular.workspace.routing` | — | Whether to enable Angular routing. |

`project`, `openapi`, `ui`, and `angular` must all be present and must be
mappings. Validate the file at any time:

```bash
django-angular3 validate-project django-angular3.json
```

## Django settings: `DJANGO_ANGULAR3`

When `django_angular3` is installed in a Django project, add it to
`INSTALLED_APPS` to enable the `ng_*` management commands:

```python
INSTALLED_APPS = [
    # ...
    "django_angular3",
]
```

Override only the values you need under `DJANGO_ANGULAR3`. The example below
shows the full supported surface together with its defaults:

```python
DJANGO_ANGULAR3 = {
    "config_path": "django-angular3.json",
    "node_executable": "node",
    "pnpm_executable": "pnpm",
    "ng_executable": "ng",
    "command_allowlist": ["ng_openapi_gen"],
    "package_manager": "pnpm",
    "build_configuration": "production",
    "style": "scss",
    "routing": True,
}
```

| Setting | Default | Description |
|---|---|---|
| `config_path` | `"django-angular3.json"` | Default project config path used when a command's path argument is omitted. |
| `node_executable` | `"node"` | Node.js executable. |
| `pnpm_executable` | `"pnpm"` | pnpm executable. |
| `ng_executable` | `"ng"` | Angular CLI executable. |
| `command_allowlist` | `("ng_openapi_gen",)` | Commands permitted to actually execute Angular tooling. |
| `package_manager` | `"pnpm"` | Workspace package manager. |
| `build_configuration` | `"production"` | Angular build configuration. |
| `style` | `"scss"` | Workspace stylesheet format. |
| `routing` | `True` | Whether the workspace enables routing. |

### The command allowlist

Angular commands only execute when the resolved command name is in
`command_allowlist`. The default allowlist permits only `ng_openapi_gen`. To let
other commands run, add them explicitly:

```python
DJANGO_ANGULAR3 = {
    "command_allowlist": ["ng_workspace", "ng_openapi_gen", "ng_build"],
}
```

Commands not in the allowlist still work with `--dry-run`, which prints the
resolved Angular subprocess calls without executing them.

```{note}
The legacy `npm_executable` and `npx_executable` overrides are still accepted
and mapped to `pnpm_executable` for compatibility with older settings modules.
```
