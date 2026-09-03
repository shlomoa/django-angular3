# Tutorial: Overview

`django-angular3` enables seamless integration of Django, Django REST Framework
(DRF), and Angular — giving teams a contract-first, automation-ready bridge
between a DRF backend and an Angular Material frontend.

For the full description see the
[project README](https://github.com/shlomoa/django-angular3#readme).

## Prerequisites

- **Python 3.10+** with `pip`.
- **Node.js** and **pnpm** — only needed once you generate or build the Angular
  workspace. Validation works without them.

You do not need a Django project to try the validation commands: the
[standalone CLI](commands.md) runs them directly.

## 1. Install the package

```bash
pip install django-angular3
```

Add to `INSTALLED_APPS` to enable the `ng_*` management commands:

```python
INSTALLED_APPS = [
    ...
    "django_angular3",
]
```

To work from a local clone instead:

```bash
pip install -e /path/to/django-angular3/
```

Verify the standalone CLI is available:

```bash
django-angular3 --help
```

## Core commands

```bash
django-admin validate-project
django-admin build_app --dry-run
django-admin ng_workspace --dry-run
django-admin ng_openapi_gen --dry-run
```

## Tutorial navigation

- **Next tutorial page:** [Install the tutorial project](tutorial.md)

```{toctree}
:hidden:
:maxdepth: 2

tutorial
configuration
workflow
commands
api/index
```
