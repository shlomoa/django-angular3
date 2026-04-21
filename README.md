# django-angular3

Angular Material integration for Django REST framework.

The starting point for this project is Django REST framework. `django-angular3`
is intended for applications where:

- Django + DRF own data, authentication, APIs, and data administration services
- Angular Material owns the user-facing application and client-side routing
- OpenAPI is the source of truth for CRM-facing functionality
- non-CRM pages, reactive forms, and bespoke workflows come from a separate
  structured input source

* * *

## Overview

`django-angular3` is a contract-first integration package for teams building
Angular Material frontends on top of Django REST framework backends.

Some reasons you might want to use it:

- Start from a DRF backend instead of inventing a parallel backend model.
- Keep Django responsible for data, authentication, and data administration.
- Keep Angular responsible for the end-user application and route tree.
- Use OpenAPI to drive CRM-facing client-side integration.
- Support non-CRM pages and workflows without forcing them into the OpenAPI
  path.

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

In that model:

- Django + DRF continue to serve the API, authentication, and data
  administration services
- Angular Material renders the user-facing SPA
- Angular owns routes such as `/dashboard` and other end-user pages
- backend-owned routes remain under Django control

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
