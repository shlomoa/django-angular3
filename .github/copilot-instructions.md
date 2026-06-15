# django-angular3 Repo Instructions

Read [these instructions](https://github.com/shlomoa/internal/blob/main/github/copilot-instructions.md)

The linked document is the source of truth for the general instructions used in
this repository.

## Repo specific

### Two-Package Architecture

The djng/ngdj toolchain is split across two complementary packages:

- **djng** (`django-angular3`, this repo): Python CLI, Angular command wrappers,
	validation, and build-plan generation. Also hosts the Claude skills that
	orchestrate generated-app setup.
- **ngdj** (`angular-django2`, `C:\Users\shlom\source\repos\shlomoa\angular-django2`):
	Angular schematics collection. Installed into a generated app workspace via
	`ng add angular-django2`. Requirements for ngdj are derived from djng
	development and from skill authoring — they flow outward, not inward.

### Terminology

Use these terms consistently in all code, docs, and skills:

- **djng**: the `django-angular3` meta-tool — this repository.
- **ngdj**: the `angular-django2` companion Angular npm package.
- **generated app** or **app**: the full-stack application produced by using
	djng and ngdj together. This is not this repository.
- **Automation naming layers**: the four distinct naming layers in the
	djng/ngdj automation subsystem. Each has a different stability contract:
	- `ng_*` commands (e.g. `ng_workspace`, `ng_openapi_gen`) are the **frozen
	  CLI wrapper** layer — stable command-line entry points, never renamed.
	- **TOOL contracts** (e.g. `angular_workspace_scaffold`) are deterministic
	  agent-callable operations exposed via MCP.
	- **SKILL names** (e.g. `angular-workspace-foundation`) are AI-guided
	  session identifiers for guided agent sessions.
	- **Concern keys** (e.g. `angular.workspace`) are internal routing
	  identifiers used in build plans.
	Authoritative definition: `doc/ARCHITECTURE.md` §2.23.

### Config file convention

See `doc/` for authoritative definitions of configuration files and their roles.

### Project overview

`django-angular3` (djng) is the Python half of a two-package toolchain for
contract-first Django REST Framework and Angular Material integration. It works
alongside `angular-django2` (ngdj), the companion Angular schematics package.
Together they produce generated full-stack applications.

The current repository is a Python-only scaffold: it validates project
configuration, OpenAPI inputs, and structured UI definition files, and it can
emit deterministic build plans or plan Angular CLI wrapper commands via Python
wrappers that ngdj schematics then execute.

Preserve the reusable Django app shape. Do not assume this repository already
contains a full Django project or Angular workspace.

### Repository Map

- `django_angular3/cli.py`: standalone CLI entry point.
- `django_angular3/management/commands/`: Django management command wrappers.
- `django_angular3/config.py`: project config loading and normalization.
- `django_angular3/validation.py`: OpenAPI, UI, and project config validation.
- `django_angular3/build.py`: deterministic build plan creation and writing.
- `django_angular3/angular.py`: Angular command resolution and execution helpers.
- `django_angular3/settings.py`: Django setting defaults and compatibility.
- `tests/`: unittest test suite.
- `spec/openapi/`: source OpenAPI examples and generator configs.
- `spec/ui/`: structured UI definition examples.
- `doc/REQUIREMENTS.md` and `doc/ARCHITECTURE.md`: target platform context.

### Django Project vs Django App

A **Django project** is the root configuration container: it holds `settings.py`,
the root `urls.py`, `wsgi.py`/`asgi.py`, and `manage.py`. There is exactly one
project per deployed application.

A **Django app** is a self-contained module within a project that owns a specific
domain: its own models, views, serializers, admin registrations, and migrations.
A project can contain one or more apps. The app name is domain-driven (e.g.
`shop`, `accounts`, `inventory`) and is distinct from the project name.

In the djng/ngdj toolchain:
- `project.name` in `django-angular3.json` names the Django project and the
	Angular workspace.
- `app.name` names the primary Django app **and** the Angular application
	generated inside that workspace. They share the same name by convention.

### Project principles

- Prefer existing patterns and best-known methods in this repository.
- Do not assume that existing implementations in djng or ngdj are complete or
	correct. Verify before reusing. Requirements for ngdj are derived from djng
	development; the ngdj codebase is expected to evolve alongside skills work.
- Keep Django and DRF responsible for backend data, authentication,
	authorization, and administrative capabilities.
- Keep Angular responsible for the user-facing route tree and SPA experience.
- Treat OpenAPI as the source of truth for CRM-facing contract-derived content.
- Keep bespoke non-CRM UI definitions separate from OpenAPI-derived content.
- Prefer small, explicit, deterministic build and validation steps.
- Keep command planning separate from command execution.
- Do not make Angular tooling download packages at runtime. `ng_openapi_gen`
	should continue to use locally installed workspace dependencies via
	`pnpm exec`.

### Development and Verification Workflow

#### Command paradigm

All djng commands are implemented as **custom Django management commands**
(see [Django docs: custom management commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)).
In a generated app — or any Django project that has `django_angular3` in
`INSTALLED_APPS` — the canonical invocation is:

```bash
django-admin <command> [args]
# or equivalently from a project with manage.py:
python manage.py <command> [args]
```

This repository also ships a **standalone CLI** (`django-angular3` entry point)
for meta-tool development and CI in this repo, where a full Django project
configuration is not required. When writing skills, documentation, or
requirements for the generated app, use `django-admin <command>`.

#### Core local commands

```bash
python -m pip install -e .
python -m pip install -e .[yaml]
python -m unittest discover -s tests -p "test*.py"
django-admin validate-project django-angular3.json
django-admin build django-angular3.json --dry-run
django-admin build_app django-angular3.json --dry-run
```

Preview Angular wrapper commands through djng rather than invoking Angular
tooling directly:

```bash
django-admin ng_new django-angular3.json --dry-run
django-admin ng_add django-angular3.json --dry-run
django-admin ng_config django-angular3.json --dry-run
django-admin ng_gen_app django-angular3.json --dry-run
django-admin ng_openapi_gen django-angular3.json --dry-run
django-admin ng_build django-angular3.json --dry-run
```

#### Development and test cycles

- **`djng`**: unit tests for services, permissions, and model behavior; API
	tests for serializers, endpoints, authentication, and contract-producing
	behavior; database-backed tests for critical workflows. For any Python-side
	change use the repository unittest suite and the relevant `django-admin`
	dry runs to verify inspectable outputs.
- **`ngdj`**: unit tests for services and utility logic; component tests for
	forms, tables, route-protected pages, and generated UI behavior; end-to-end
	tests for login and the main business module workflows. Keep Angular
	operations wrapper-driven from `djng` and use workspace-local dependencies
	via `pnpm exec`.
- **Integration**: automated coverage across contract, integration, and
	composed application behavior. Verification is iterative — re-verify
	frontend/backend alignment after schema changes, business-record changes, and
	each build or verification cycle. Include smoke tests in staging before
	production release.

#### Generated-app development feedback

- With `DEBUG=True`, failures raised by djng management commands or app-builder
	runs in the generated app must surface through Django's normal error
	reporting, not be swallowed or reduced to stdout-only output.
- The generated app must expose a development-only `/ng/build` page gated by
	`DEBUG=True` or `ENABLE_NG_BUILD_PAGE=True` so Angular build health, TypeScript
	errors and warnings, bundle summary, and retrigger controls are visible during
	development.

### Documentation Notes

- Update `README.md` for user-facing workflow or command changes.
- Update `CONTRIBUTING.md` for contributor workflow changes.
- Update `doc/ARCHITECTURE.md` or `doc/REQUIREMENTS.md` only for intentional
	changes to target architecture or product requirements.

---
