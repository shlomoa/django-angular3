# Overview

`django-angular3` (djng) is the Python half of a two-package toolchain for
contract-first Django REST Framework and Angular Material integration.

## What it does

- Validates project configuration, OpenAPI inputs, and UI definition files.
- Emits deterministic build plans consumed by `build_app`.
- Wraps Angular CLI commands through frozen `ng_*` management commands.
- Hosts the SKILL and TOOL contracts that orchestrate Angular workspace
  generation via `angular-django2` (ngdj) schematics.

## Automation naming layers

The toolchain uses four distinct naming layers (see `doc/ARCHITECTURE.md §2.23`
for the authoritative definition):

| Layer | Example | Stability |
|---|---|---|
| CLI wrapper commands | `ng_workspace`, `ng_openapi_gen` | Frozen — never renamed |
| TOOL contracts | `angular_workspace_scaffold`, `openapi_schema_export` | Stable API |
| SKILL names | `angular-workspace-foundation`, `angular-api-integration` | Stable API |
| Concern keys | `angular.workspace`, `contract.schema-export` | Internal |

## Installation

```bash
pip install django-angular3
# With YAML support:
pip install django-angular3[yaml]
```

Add to `INSTALLED_APPS` to enable the `ng_*` management commands:

```python
INSTALLED_APPS = [
    ...
    "django_angular3",
]
```

## Core commands

```bash
django-admin validate-project django-angular3.json
django-admin build django-angular3.json --dry-run
django-admin build_app django-angular3.json --dry-run
django-admin ng_workspace django-angular3.json --dry-run
django-admin ng_openapi_gen django-angular3.json --dry-run
```
