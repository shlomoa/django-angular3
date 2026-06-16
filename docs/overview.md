# Overview

`django-angular3` enables seamless integration of Django, Django REST Framework
(DRF), and Angular — giving teams a contract-first, automation-ready bridge
between a DRF backend and an Angular Material frontend.

For the full description see the [project README](https://github.com/shlomoa/django-angular3#readme).

## Installation

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

## Core commands

```bash
django-admin validate-project django-angular3.json
django-admin build django-angular3.json --dry-run
django-admin build_app django-angular3.json --dry-run
django-admin ng_workspace django-angular3.json --dry-run
django-admin ng_openapi_gen django-angular3.json --dry-run
```
