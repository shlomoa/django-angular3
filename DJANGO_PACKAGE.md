To create a **Django package** in the usual sense, you are normally building a **reusable Django app** that is also a standard **Python package**. Django’s own guidance treats reusable apps this way, and modern Python packaging guidance centers on `pyproject.toml`. ([Django Project][1])

## 1) What it has to contain

At minimum, a reusable Django package should contain:

* a **Python package directory** with `__init__.py`
* Django app code such as `models.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `migrations/`
* package metadata in **`pyproject.toml`**
* documentation like `README.md`
* a license file if you intend to publish it
* tests
* any templates/static files inside the app package, not in some project-global location, so the app stays self-contained and reusable. ([Django Project][1])

A typical layout looks like this:

```text
my_django_package/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ src/
│  └─ myapp/
│     ├─ __init__.py
│     ├─ apps.py
│     ├─ models.py
│     ├─ views.py
│     ├─ urls.py
│     ├─ admin.py
│     ├─ migrations/
│     │  └─ __init__.py
│     ├─ templates/
│     │  └─ myapp/
│     │     └─ ...
│     ├─ static/
│     │  └─ myapp/
│     │     └─ ...
│     └─ templatetags/
│        └─ ...
└─ tests/
   ├─ __init__.py
   ├─ test_settings.py
   └─ test_*.py
```

### Important Django-specific pieces

**`apps.py`**
Django uses an app registry, and reusable apps commonly expose an `AppConfig` class there. ([Django Project][2])

```python
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"
```

**`migrations/`**
If your package defines models, it should ship with its migrations so downstream projects can apply them normally. This is standard Django app behavior. ([Django Project][2])

**Templates and static files**
Keep them namespaced under your app, for example:

```text
templates/myapp/...
static/myapp/...
```

That avoids collisions and makes the package reusable. Django explicitly recommends app-specific template placement. ([Django Project][3])

### `pyproject.toml`

Modern Python packaging expects package metadata in `pyproject.toml`, with at least a `[build-system]` section and typically `[project]`. ([Python Packaging][4])

Example:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-django-package"
version = "0.1.0"
description = "A reusable Django app"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "Django>=5.1",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
myapp = [
    "templates/myapp/**/*.html",
    "static/myapp/**/*",
]
```

That is the modern direction from the Python Packaging User Guide. ([Python Packaging][5])

## 2) How to integrate it

There are two integration levels: **install it as a Python package**, then **enable it as a Django app**.

### Install it

For local development:

```bash
pip install -e .
```

For a published package:

```bash
pip install my-django-package
```

Python packaging tools build and install packages from the metadata in `pyproject.toml`. ([Python Packaging][5])

### Enable it in Django

Add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "myapp",
]
```

or, if you prefer the explicit config path:

```python
INSTALLED_APPS = [
    # ...
    "myapp.apps.MyAppConfig",
]
```

Django discovers installed applications through its application registry. ([Django Project][2])

### Include URLs if the package exposes views

In the consuming project’s `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("myapp/", include("myapp.urls")),
]
```

If your package is designed to be mounted more than once or embedded in larger systems, URL naming and namespacing matter for reuse. Django supports URL namespaces for this reason. ([Django Project][6])

### Run migrations

If the package contains models:

```bash
python manage.py migrate
```

### If you have templates/static/admin/management commands

They work normally once the app is in `INSTALLED_APPS`, provided they are packaged correctly inside the app. That is one reason Django emphasizes self-contained reusable apps. ([Django Project][1])

## 3) How to test it

Django documents a common pattern for testing reusable apps: keep a `tests/` package alongside the app and provide a small test settings module plus a `runtests.py` entry point when needed. ([Django Project][7])

A simple structure:

```text
tests/
├─ __init__.py
├─ test_settings.py
└─ test_models.py
```

Example `tests/test_settings.py`:

```python
SECRET_KEY = "test-secret-key"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "myapp",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True
ROOT_URLCONF = "tests.urls"
```

Example test:

```python
from django.test import TestCase

class SmokeTest(TestCase):
    def test_basic(self):
        self.assertTrue(True)
```

### Run tests

Using Django’s test runner:

```bash
python -m django test --settings=tests.test_settings
```

Django’s testing docs describe both writing tests and a reusable-app pattern using the Django test runner. ([Django Project][8])

### What to test

For a Django package, usually test:

* models
* forms
* views
* URLs
* template rendering
* admin integration if relevant
* migrations if your package is model-heavy
* settings-dependent behavior
* static/template discovery if the package depends on it

Django’s testing framework is built to support app-level testing with isolated settings and a test database. ([Django Project][8])

## Practical checklist

A Django package is in good shape if it has:

* `pyproject.toml`
* `README.md`
* installable package structure
* `apps.py`
* migrations if models exist
* namespaced templates/static
* tests with their own test settings
* clear integration instructions:

  * install
  * add to `INSTALLED_APPS`
  * include URLs if needed
  * run migrations

## Recommended minimal blueprint

If you want the smallest clean starting point, use this:

```text
my-django-package/
├─ pyproject.toml
├─ README.md
├─ src/
│  └─ myapp/
│     ├─ __init__.py
│     ├─ apps.py
│     ├─ urls.py
│     ├─ views.py
│     ├─ templates/myapp/
│     └─ static/myapp/
└─ tests/
   ├─ __init__.py
   ├─ test_settings.py
   └─ test_smoke.py
```

Then grow it only as needed.

If you want, I can generate for you a **complete starter skeleton** for a reusable Django package with `pyproject.toml`, sample app files, and test setup.

[1]: https://docs.djangoproject.com/en/6.0/intro/reusable-apps/?utm_source=chatgpt.com "Advanced tutorial: How to write reusable apps"
[2]: https://docs.djangoproject.com/en/6.0/ref/applications/?utm_source=chatgpt.com "Applications"
[3]: https://docs.djangoproject.com/en/6.0/intro/tutorial07/?utm_source=chatgpt.com "Writing your first Django app, part 7"
[4]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/?utm_source=chatgpt.com "Writing your pyproject.toml"
[5]: https://packaging.python.org/tutorials/packaging-projects/?utm_source=chatgpt.com "Packaging Python Projects"
[6]: https://docs.djangoproject.com/en/6.0/releases/1.1/?utm_source=chatgpt.com "Django 1.1 release notes"
[7]: https://docs.djangoproject.com/en/6.0/topics/testing/advanced/?utm_source=chatgpt.com "Advanced testing topics"
[8]: https://docs.djangoproject.com/en/6.0/topics/testing/overview/?utm_source=chatgpt.com "Writing and running tests"
