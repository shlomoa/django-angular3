# django-angular3

`django-angular3` enables seamless integration of Django, Django REST Framework (DRF), and Angular — giving teams a contract-first, automation-ready bridge between a DRF backend and an Angular Material frontend.

Project website: <https://djangoangular.com/>

Documentation: <https://django-angular3.readthedocs.io/>

Related docs:
- `doc/ARCHITECTURE.md` — architecture, integration boundaries, and design decisions
- `doc/specifications/SPECIFICATIONS.md` — exact platform structures and
  topology definitions
- `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` — exact AI automation
  module organization and realization
- `doc/specifications/TEST_SCENARIO_SPECIFICATIONS.md` — exact build-scenario
  suite realization and coverage
- `doc/contracts/CHANGE_MODEL_CONTRACTS.md` — shared Change Model and interface boundaries
- `doc/contracts/TOOL_CONTRACTS.md` — deterministic Tool contracts
- `doc/contracts/HOOK_CONTRACTS.md` — lifecycle Hook contracts
- `doc/contracts/PROVIDER_ADAPTER_CONTRACTS.md` — provider-adapter contracts
- `doc/contracts/PLUGIN_CONTRACTS.md` — Plugin packaging contracts
- `doc/contracts/SKILL_CONTRACTS.md` — Skill contracts and catalog ownership
- `doc/contracts/TEST_SCENARIO_CONTRACTS.md` — build-scenario input and expected
  oracle boundaries
- `doc/plan/CONFIGURATION_PLAN.md` — configuration planning
- `doc/plan/CONSTRUCTION_PLAN.md` — construction sequencing and backlog
- `doc/plan/AUTOMATION_PLAN.md` — automation sequencing and backlog
- `doc/plan/APPLICATION_DELIVERY_PLAN.md` — generated-application delivery
- `doc/plan/VERIFICATION_PLAN.md` — verification sequencing and backlog

It allows you to:
- Keep Django responsible for data, authentication, and administration.
- Keep Angular responsible for the end-user application and client-side route tree.
- Use OpenAPI as the source of truth for API-contract-derived functionality.
- Support pages, reactive forms, navigation, and workflows through an OpenUI concrete UI document.
- Automate the handoff from backend API contract to Angular integration artifacts through a deterministic, repeatable pipeline.

## Requirements

See the [requirements corpus](doc/requirements/REQUIREMENTS.md) for product,
generated-application, `build_app`, and AI automation requirements.

## Installation

```bash
pip install django-angular3
```

To install from a local clone:

```bash
pip install -e /path/to/django-angular3/
```

### OpenAPI and OpenUI validation

`django-angular3` uses [openapi-spec-validator] for full OAS compliance
validation of OpenAPI documents and [openui-spec] to validate structured OpenUI
documents against its schema and catalog. Both are pure-Python dependencies
installed automatically with the package — no external validation toolchain is
required.

OpenAPI documents are validated against the full OpenAPI specification using
`openapi-spec-validator`; OpenUI documents are validated through
`openui-spec`.

[openapi-spec-validator]: https://openapi-spec-validator.readthedocs.io/
[openui-spec]: https://github.com/shlomoa/openui-spec

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

The static `django-angular3.json` configures djng's Angular tool settings,
including executable resolution and its command allowlist. `DJANGO_ANGULAR3`
and `DjangoAngularSettings` are derived from that file; they are not independent
configuration authorities. The generated app's identity and artifact locations
are instead supplied by the project configuration defined in
`doc/specifications/SPECIFICATIONS.md` §2.1.

Once installed, Django and the standalone CLI expose the same Angular command
resolution flow. Use `--dry-run` only for diagnostic validation and debugging;
it resolves commands without executing Angular tooling:

```bash
./manage.py ng_new --dry-run
./manage.py ng_workspace --dry-run
./manage.py ng_config --dry-run
./manage.py ng_add --dry-run
./manage.py ng_gen_app --dry-run
./manage.py ng_page --name orders --target-path src/app/features/orders --dry-run
./manage.py ng_component --name order-card --dry-run
./manage.py ng_reactive_form --name contact --definition forms/contact.json --dry-run
./manage.py ng_site --defaults --dry-run
./manage.py ng_openapi_gen --dry-run
./manage.py ng_build --dry-run
```

- `ng_new` creates an empty Angular workspace
- `ng_workspace` runs the upstream-aligned workspace bootstrap flow: `ng new`, workspace defaults, `ng add angular-django2`, and `ng generate angular-django2:workspace-setup`
- `ng_config` applies workspace defaults such as package manager, style, and routing
- `ng_add` installs and registers the configured Angular schematic package
- `ng_gen_app` generates an Angular application inside the configured workspace via the `angular-django2:material-app` schematic, forwarding `--ssr`, `--zoneless`, and `--defaults` to align with the Angular CLI `ng new` defaults
- `ng_material_setup` configures Angular Material in an existing project via the `angular-django2:material-setup` schematic, forwarding optional `--theme`, `--typography`, and `--animations`
- `ng_page`, `ng_component`, `ng_reactive_form`, and `ng_site` wrap the matching `angular-django2` schematics without changing their deterministic behavior
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
> `angular-api-integration`). See `doc/ARCHITECTURE.md §2.22` for the authoritative definition.

To execute these commands, include the relevant commands in the static tool
configuration's `tool.commandAllowlist`, then invoke them without `--dry-run`.

Use `--app-name <name>` with `ng_gen_app` to override the generated Angular
application name.

Beyond these workspace wrappers, `angular-django2` ships schematics for
composing bespoke feature UI. `ng generate angular-django2:component <name>`
scaffolds a standalone component seeded with begin/end embedding hooks, and
`ng generate angular-django2:embed-component --component=<child.ts> --parent=<parent.ts>`
wires a generated child into a parent — importing the class, registering it in the
parent standalone `imports` array, feeding input signals, and binding outputs to
`on<Output>()` handler stubs. Embedding is idempotent, so it is safe to re-run
during iterative development. See the [Usage workflow](https://django-angular3.readthedocs.io/en/latest/workflow.html)
for the full generate → embed composition flow.

For advanced Material components, use the `ng_complex_component` wrapper. It
invokes `angular-django2:complex-component`, which owns theme mixins, nested
child composition, projection slots, CDK overlay support, and create/modify/
delete lifecycle handling:

```bash
./manage.py ng_complex_component \
  --name dashboard-card --target-path src/app/features/dashboard \
  --features mixins,nested,projection --dry-run
```

Use `--mode delete --confirm` for deletion. Add `ng_complex_component` to
`tool.commandAllowlist` before running without `--dry-run`.

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
the source for API-contract-derived Angular integration.

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

Under the generated-app convention, UI requirements are supplied in the
project-root `app.openui.json` selected by
`artifacts.openuiSpecification`. The OpenUI concrete UI document may
complement or reference API-contract-derived content. Its role, grammar, and
catalog relationship are defined by the
[OpenUI artifact-role SSOT](https://github.com/shlomoa/openui-spec/blob/main/spec/README.md#specification-artifacts-grammar-vs-catalog);
see the [OpenUI examples](https://openui-spec.readthedocs.io/en/latest/examples/)
for the per-scope vocabulary.

For example:

```json
{
  "id": "root",
  "version": "0.0.1",
  "type": "Application",
  "children": [
    {
      "id": "dashboardPage",
      "type": "DashboardPage"
    },
    {
      "id": "inviteUserForm",
      "type": "FormView",
      "attrs": {
        "title": "\"Invite user\"",
        "(submit)": "createUser(form.value)"
      }
    }
  ]
}
```

The scaffolded first version in this repository already includes example inputs.
For the contributor workflow around local validation, see
[Contributing](CONTRIBUTING.md).

## Documentation

User-facing usage documentation is published at
<https://django-angular3.readthedocs.io/>:

- [Tutorial](https://django-angular3.readthedocs.io/en/latest/) — install, run the bundled tutorial, and complete the workflow end to end.
- [Configuration](https://django-angular3.readthedocs.io/en/latest/configuration.html) — configuration guidance and references.
- [Usage workflow](https://django-angular3.readthedocs.io/en/latest/workflow.html) — the contract-first cycle for your own project.
- [Command reference](https://django-angular3.readthedocs.io/en/latest/commands.html) — every command in both the standalone CLI and management-command form.

The project website is available at <https://djangoangular.com/>.

Current project documents:

- [Contributing](CONTRIBUTING.md)
- [Releasing](doc/RELEASING.md)
- [Requirements](doc/requirements/REQUIREMENTS.md)
- [Specifications](doc/specifications/SPECIFICATIONS.md)
- [AI automation specifications](doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md)
- [Test scenario specifications](doc/specifications/TEST_SCENARIO_SPECIFICATIONS.md)
- [Change model contracts](doc/contracts/CHANGE_MODEL_CONTRACTS.md)
- [Tool contracts](doc/contracts/TOOL_CONTRACTS.md)
- [Hook contracts](doc/contracts/HOOK_CONTRACTS.md)
- [Provider adapter contracts](doc/contracts/PROVIDER_ADAPTER_CONTRACTS.md)
- [Plugin contracts](doc/contracts/PLUGIN_CONTRACTS.md)
- [Skill contracts](doc/contracts/SKILL_CONTRACTS.md)
- [Test scenario contracts](doc/contracts/TEST_SCENARIO_CONTRACTS.md)
- [Architecture](doc/ARCHITECTURE.md)
- [Configuration plan](doc/plan/CONFIGURATION_PLAN.md)
- [Construction plan](doc/plan/CONSTRUCTION_PLAN.md)
- [Automation plan](doc/plan/AUTOMATION_PLAN.md)
- [Application delivery plan](doc/plan/APPLICATION_DELIVERY_PLAN.md)
- [Verification plan](doc/plan/VERIFICATION_PLAN.md)

## Status

This project now includes a first scaffolded Python package, example inputs, and
the current contributor workflow. The repository does not yet include a
frontend workspace. Actual code generation and Angular assembly are still
pending.
