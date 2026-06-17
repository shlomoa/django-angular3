# django-angular3

`django-angular3` enables seamless integration of Django, Django REST Framework (DRF), and Angular — giving teams a contract-first, automation-ready bridge between a DRF backend and an Angular Material frontend.

Project website: <https://djangoangular.com/>

Documentation: <https://django-angular3.readthedocs.io/>

Related docs:
- `doc/ARCHITECTURE.md` — architecture, integration boundaries, and design decisions
- `TODO.md` — implementation sequencing, delivery roadmap, and open items

It allows you to:
- Keep Django responsible for data, authentication, and administration.
- Keep Angular responsible for the end-user application and client-side route tree.
- Use OpenAPI as the source of truth for CRM-facing functionality.
- Support bespoke non-CRM pages, reactive forms, and workflows via a separate structured input source.
- Automate the handoff from backend API contract to Angular integration artifacts through a deterministic, repeatable pipeline.

## Requirements

See [doc/REQUIREMENTS.md](doc/REQUIREMENTS.md) for the full requirements.

## Installation

```bash
pip install django-angular3
```

To install from a local clone:

```bash
pip install -e /path/to/django-angular3/
```

## Django app integration

If you install `django-angular3` into a Django project, add the app to
`INSTALLED_APPS` to enable the bundled `ng_` management commands.

```python
INSTALLED_APPS = [
    # ...
    "django_angular3",
]
```

Or use the explicit app config path:

```python
INSTALLED_APPS = [
    # ...
    "django_angular3.apps.DjangoAngular3Config",
]
```

The specialized Node/Angular tool settings live in
`django_angular3/settings.py` and are configured through `DJANGO_ANGULAR3` in
your Django project's `settings.py`. Only set the values you want to override;
the example below shows the full supported settings surface, including an
optional `config_path` override:

```python
DJANGO_ANGULAR3 = {
    "config_path": "django-angular3.json",
    "ng_executable": "ng",
    "pnpm_executable": "pnpm",
    "node_executable": "node",
    "command_allowlist": ["ng_openapi_gen"],
    "package_manager": "pnpm",
    "build_configuration": "production",
    "style": "scss",
    "routing": True,
}
```

The current settings surface and defaults are:

- `config_path`: `"django-angular3.json"` - default project config path used
  when a CLI or management command path is omitted
- `node_executable`: `"node"`
- `pnpm_executable`: `"pnpm"`
- `ng_executable`: `"ng"`
- `command_allowlist`: `("ng_openapi_gen",)`
- `package_manager`: `"pnpm"`
- `build_configuration`: `"production"`
- `style`: `"scss"`
- `routing`: `True`

Legacy `npm_executable` and `npx_executable` overrides are still accepted and
mapped to `pnpm_executable` for compatibility with older settings modules.
Commands are only executed when the resolved django-angular3 command name is in
`command_allowlist`. The default allowlist only permits `ng_openapi_gen`.

Once installed, Django and the standalone CLI expose the same Angular command
resolution flow:

```bash
./manage.py ng_new django-angular3.json --dry-run
./manage.py ng_workspace django-angular3.json --dry-run
./manage.py ng_config django-angular3.json --dry-run
./manage.py ng_add django-angular3.json --dry-run
./manage.py ng_gen_app django-angular3.json --dry-run
./manage.py ng_openapi_gen django-angular3.json --dry-run
./manage.py ng_build django-angular3.json --dry-run
```

- `ng_new` creates an empty Angular workspace
- `ng_workspace` runs the upstream-aligned workspace bootstrap flow: `ng new`, workspace defaults, `ng add angular-django2`, and `ng generate angular-django2:ng-workspace`
- `ng_config` applies workspace defaults such as package manager, style, and routing
- `ng_add` installs and registers the configured Angular schematic package
- `ng_gen_app` generates an Angular application inside the configured workspace
- `ng_openapi_gen` runs a locally installed `ng-openapi-gen` for the configured OpenAPI source

`ng_openapi_gen` resolves to `pnpm exec`, so it only uses dependencies that
are already installed in the Angular workspace. It does not download and
execute packages at runtime.
- `ng_build` builds the configured Angular application

> **Naming note**: The `ng_*` command names (e.g. `ng_workspace`, `ng_openapi_gen`) are the
> **frozen CLI wrapper layer** — stable entry points that never change. The automation subsystem
> uses two separate layers with distinct names: **TOOL contracts** are deterministic
> agent-callable operations (e.g. `angular_workspace_scaffold`, `openapi_schema_export`) and
> **SKILL names** are AI-guided session identifiers (e.g. `angular-workspace-foundation`,
> `angular-api-integration`). See `doc/ARCHITECTURE.md §2.23` for the authoritative definition.

If you want these commands to execute instead of only dry-run, configure the
command allowlist to include the django-angular3 commands you want to permit.

Use `--app-name <name>` with `ng_gen_app` to override the generated Angular
application name.

At the moment this reusable Django app contributes configuration helpers and
management commands; it does not yet ship models, URLs, templates, static
assets, or migrations, so there is no extra URL inclusion or migration step for
the package itself.

## Example

Let's take a look at a simple example of starting from Django REST framework and
then layering Angular Material integration on top.

Start by creating a DRF-backed project in the usual way:

```bash
pip install djangorestframework
django-admin startproject mysite .
./manage.py migrate
./manage.py createsuperuser
```

Now edit your project's `urls.py` module:

```python
from django.contrib.auth.models import User
from django.urls import include, path
from rest_framework import routers, serializers, viewsets


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "is_staff"]


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r"users", UserViewSet)


# Django serves API and authentication routes.
urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
```

Add the following to your `settings.py` module:

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
    ]
}
```

At this point, Django + DRF own the backend data and authentication services.

The next step is to export the OpenAPI contract from that backend and use it as
the source for Angular-side CRM-facing integration.

A simplified schema fragment might look like this:

```yaml
paths:
  /api/users/:
    get:
      operationId: listUsers
    post:
      operationId: createUser
  /api/users/{id}/:
    get:
      operationId: retrieveUser
    patch:
      operationId: updateUser
```

Non-CRM pages and bespoke workflows are then supplied separately.

For example:

```yaml
pages:
  - route: /dashboard
    kind: dashboard

forms:
  - id: invite-user
    mode: reactive
    submit:
      action: createUser
```

The scaffolded first version in this repository already includes example inputs.
For the contributor workflow around local validation and build-plan generation,
see [Contributing](CONTRIBUTING.md).

## Documentation

User-facing usage documentation is published at
<https://django-angular3.readthedocs.io/>:

- [Getting started](https://django-angular3.readthedocs.io/en/latest/getting-started.html) — install, run the bundled tutorial, and complete the workflow end to end.
- [Configuration](https://django-angular3.readthedocs.io/en/latest/configuration.html) — the `django-angular3.json` schema and the `DJANGO_ANGULAR3` settings.
- [Usage workflow](https://django-angular3.readthedocs.io/en/latest/workflow.html) — the contract-first cycle for your own project.
- [Command reference](https://django-angular3.readthedocs.io/en/latest/commands.html) — every command in both the standalone CLI and management-command form.

The project website is available at <https://djangoangular.com/>.

Current project documents:

- [Contributing](CONTRIBUTING.md)
- [Releasing](doc/RELEASING.md)
- [Requirements](doc/REQUIREMENTS.md)
- [Architecture](doc/ARCHITECTURE.md)

## Status

This project now includes a first scaffolded Python package, example specs, and
the current contributor workflow. The repository does not yet include a
frontend workspace. Actual code generation and Angular assembly are still
pending.
