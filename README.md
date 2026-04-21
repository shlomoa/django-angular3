# django-angular3

`django-angular3` is a contract-first integration package for teams building Angular Material frontends on top of Django REST framework (DRF) backends.

It allows you to:
- Keep Django responsible for data, authentication, and administration.
- Keep Angular responsible for the end-user application and client-side route tree.
- Use OpenAPI as the source of truth for CRM-facing functionality.
- Support bespoke non-CRM pages, reactive forms, and workflows via a separate structured input source.

## Requirements

To use this package as intended, your application should have:

- a Django REST framework backend
- an OpenAPI specification exported from that backend
- an Angular Material frontend for the user-facing product
- a separate input source for non-CRM UI definitions
- a routing model where Angular owns the user-facing route tree
- a deployment model where Django serves backend services and Angular serves the
  user-facing SPA

## Installation

Install from source:

```bash
python -m pip install -e .
```

If you want YAML support for OpenAPI or UI definition files:

```bash
python -m pip install -e .[yaml]
```

For reusable-app style test runs, use either:

```bash
python runtests.py
python -m django test tests --settings=tests.test_settings
```

The current scaffold includes a Django app-style package surface and a direct
CLI. Run the CLI directly for the bundled project config:

```bash
django-angular3 validate-project django-angular3.json
django-angular3 build django-angular3.json --output build
django-angular3 ng_new django-angular3.json --dry-run

python -m django_angular3.cli validate-project django-angular3.json
python -m django_angular3.cli build django-angular3.json --output build
python -m django_angular3.cli ng_new django-angular3.json --dry-run
```

The standalone CLI keeps the existing validation/build subcommands in
kebab-case and uses the same `ng_` snake_case names as the Django management
commands for the Angular wrappers. The examples above show the supported
subcommand names as they exist today.

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

The specialized Node/NPM/Angular settings live in
`django_angular3/settings.py` and are configured through `DJANGO_ANGULAR3` in
your Django project's `settings.py`. Only set the values you want to override;
the example below shows the full supported settings surface, including an
optional `config_path` override:

```python
DJANGO_ANGULAR3 = {
    "config_path": "django-angular3.json",
    "ng_executable": "ng",
    "npx_executable": "npx",
    "npm_executable": "npm",
    "node_executable": "node",
    "package_manager": "npm",
    "build_configuration": "production",
    "style": "scss",
    "routing": True,
}
```

The current settings surface and defaults are:

- `config_path`: `"django-angular3.json"` - default project config path used
  when a CLI or management command path is omitted
- `node_executable`: `"node"`
- `npm_executable`: `"npm"`
- `npx_executable`: `"npx"`
- `ng_executable`: `"ng"`
- `package_manager`: `"npm"`
- `build_configuration`: `"production"`
- `style`: `"scss"`
- `routing`: `True`

Once installed, Django and the standalone CLI expose the same Angular command
planning flow:

```bash
./manage.py ng_new django-angular3.json --dry-run
./manage.py ng_config django-angular3.json --dry-run
./manage.py ng_gen_app django-angular3.json --dry-run
./manage.py ng_openapi_gen django-angular3.json --dry-run
./manage.py ng_build django-angular3.json --dry-run
```

- `ng_new` creates an empty Angular workspace
- `ng_config` applies workspace defaults such as package manager, style, and routing
- `ng_gen_app` generates an Angular application inside the configured workspace
- `ng_openapi_gen` runs `ng-openapi-gen` for the configured OpenAPI source
- `ng_build` builds the configured Angular application

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

Public usage documentation is not available yet.

Current project documents:

- [Contributing](CONTRIBUTING.md)
- [Requirements](doc/REQUIREMENTS.md)
- [Architecture](doc/ARCHITECTURE.md)

## Status

This project now includes a first scaffolded Python package, example specs, and
the current contributor workflow. The repository does not yet include a
frontend workspace. Actual code generation and Angular assembly are still
pending.
