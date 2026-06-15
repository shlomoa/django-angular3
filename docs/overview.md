# Overview

`django-angular3` (djng) is the Python half of a two-package toolchain for
contract-first Django REST Framework and Angular Material integration.

## What it does

- Validates project configuration, OpenAPI inputs, and UI definition files.
- Emits deterministic build plans consumed by `build_app`.
- Wraps Angular CLI commands through frozen `ng_*` management commands.
- Hosts the SKILL and TOOL contracts that orchestrate Angular workspace
  generation via `angular-django2` (ngdj) schematics.

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
