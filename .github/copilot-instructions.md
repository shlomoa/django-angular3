# Repo Instructions

## General instructions

Read the external source of truth (SSOT) for general instructions from https://github.com/shlomoa/shlomoa/blob/main/.github/copilot-instructions.md It is mandatory.

## django-angular3 repo specific instructions

### Two-Package Architecture

See `doc/ARCHITECTURE.md` §2.5 (djng), §2.6 (ngdj), §3.3–3.4 for the authoritative
description of the two-package split and each package's responsibilities.

### Terminology

Use these terms consistently in all code, docs, and skills:

- **djng**: the `django-angular3` meta-tool — this repository. See `doc/ARCHITECTURE.md` §2.5.
- **ngdj**: use the canonical identity and upstream-source policy in
	`doc/ARCHITECTURE.md` §2.6; do not redefine its commands or options in djng.
- **djangoangular**: the code name for the tight Django–Angular integration
	formed by djng and ngdj; see `doc/ARCHITECTURE.md` §2.6.1.
- **generated app** or **app**: the full-stack application produced by using
	djng and ngdj together. This is not this repository.
- **Automation naming layers**: four distinct naming layers in the djng/ngdj
	 automation subsystem. Authoritative definition: `doc/ARCHITECTURE.md` §2.23.

### Config file convention

See `doc/` for authoritative definitions of configuration files and their roles.

### Project overview

See `README.md` for the project overview and `doc/ARCHITECTURE.md` §3.3 for
the authoritative description of djng's role in the toolchain.

### Repository Map

- `django_angular3/cli.py`: standalone CLI entry point.
- `django_angular3/management/commands/`: Django management command wrappers.
- `django_angular3/config.py`: project config loading and normalization.
- `django_angular3/validation.py`: OpenAPI, UI, and project config validation.
- `django_angular3/angular.py`: Angular command resolution and execution helpers.
- `django_angular3/settings.py`: Django setting defaults and compatibility.
- `tests/`: unittest test suite.
- `tests/fixtures/artifacts/`: reusable OpenAPI, OpenUI, and generator-config fixtures.
- `doc/REQUIREMENTS.md` and `doc/ARCHITECTURE.md`: target platform context.

### Django Project vs Django App

See `doc/ARCHITECTURE.md` §2.21 for the authoritative definition.

### Project principles

- Prefer existing patterns and best-known methods in this repository.
- Do not assume that existing implementations in djng or ngdj are complete or
	correct. Verify djng behavior locally and resolve ngdj facts through
	`doc/ARCHITECTURE.md` §2.6 and its upstream sources. Define required ngdj
	changes in the upstream project rather than creating a competing djng
	definition.
- Keep Django and DRF responsible for backend data, authentication,
	authorization, and administrative capabilities.
- Keep Angular responsible for the user-facing route tree and SPA experience.
- Treat OpenAPI as the source of truth for CRM-facing contract-derived content.
- Treat OpenUI as the separate UI-description input. It may complement or
	reference API-contract-derived content; validate cross-input consistency.
- Prefer small, explicit, deterministic build and validation steps.
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

#### Development and test cycles

- **`djng`**: unit tests for services, permissions, and model behavior; API
	tests for serializers, endpoints, authentication, and contract-producing
	behavior; database-backed tests for critical workflows. For any Python-side
	change run ruff lint and format checks, the repository unittest suite, and
	the relevant `django-admin` dry runs to verify inspectable outputs:

	```bash
	ruff check django_angular3 tests
	ruff format django_angular3 tests
	python -m unittest discover -s tests -p 'test*.py'
	```
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

- With `DEBUG=True`, failures raised by djng management commands or build_app
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
