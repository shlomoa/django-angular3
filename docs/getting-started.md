# Getting started

This walkthrough takes you from an empty machine to a running tutorial project
in a few minutes. It uses the bundled `simple_crm` tutorial — a small Django +
DRF project that already ships an OpenAPI schema, a UI definition, and a
`django-angular3.json` tool configuration and a
`django-angular3-<project_name>.json` project configuration — so you can see the full
contract-first workflow without writing a backend from scratch.

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

To work from a local clone instead:

```bash
pip install -e /path/to/django-angular3/
```

Verify the standalone CLI is available:

```bash
django-angular3 --help
```

## 2. Install the tutorial project

The package bundles a ready-made tutorial. Copy it into a working directory:

```bash
django-angular3 install-tutorial simple_crm
```

This creates:
- A `simple_crm/` folder containing a Django project (`simple_crm`),
- A DRF app (`shop`)
- `schema.yaml` exported from the above DRF app.
- `app.openui.json` containing the OpenUI requirements.
- `django-angular3.json` static tool configuration file.
- `django-angular3-<project_name>.json` generated-app project configuration file.
The command prints the next steps on success.

## 3. Run the Django backend

```bash
cd simple_crm
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

At this point Django and DRF own the backend data, authentication, and
administration. Visit <http://127.0.0.1:8000/admin/> to sign in with the
superuser you just created.

## 4. Validate the project configuration

From inside the tutorial directory, validate the configuration and its
referenced OpenAPI and OpenUI sources:

```bash
python manage.py validate_project
```

`validate_project` uses the project-configuration discovery rules in
`doc/REQUIREMENTS.md` §4.2.4. See [Command reference](commands.md) for the
command interface.

## 5. Scaffold the Angular workspace

These steps require Node.js and pnpm. Each `ng_*` command accepts `--dry-run`
for diagnostic validation and debugging, printing discovered configuration,
derived paths, and resolved Angular subprocess calls without executing them:

```bash
python manage.py ng_workspace --dry-run
```

When you are ready to execute, drop `--dry-run`:

```bash
python manage.py ng_workspace
python manage.py ng_openapi_gen
python manage.py ng_build
```

`ng_workspace` runs the full bootstrap flow (`ng new`, workspace defaults,
`ng add angular-django2`, and schematic generation), `ng_openapi_gen` generates
Angular API client artifacts from the OpenAPI schema, and `ng_build` builds the
configured Angular application.

## Next steps

- [Configuration](configuration.md) — configuration guidance and references.
- [Usage workflow](workflow.md) — the end-to-end contract-first cycle for your
  own project.
- [Command reference](commands.md) — every command, in both the standalone CLI
  and Django management-command form.
