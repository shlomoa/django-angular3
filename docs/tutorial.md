# Tutorial: Install the tutorial project

The bundled `simple_crm` project lets you continue from the installed `djng`
package to a running Django backend and Angular workspace.

## 2. Install the tutorial project

Copy the bundled project into a working directory:

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
`doc/specifications/SPECIFICATIONS.md` §2.1 [↗](https://github.com/shlomoa/django-angular3/blob/main/doc/specifications/SPECIFICATIONS.md#21-configuration-and-input-categories){.modal-link}
See [Command reference](commands.md) for the command interface.

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
python manage.py ng_gen_app
python manage.py ng_openapi_gen
python manage.py ng_build
```

`ng_workspace` runs the full bootstrap flow (`ng new`, workspace defaults,
`ng add angular-django2`, and schematic generation), `ng_gen_app` generates the
Angular Material application inside the workspace, `ng_openapi_gen` generates
Angular API client artifacts from the OpenAPI schema, and `ng_build` builds the
configured Angular application.

## Tutorial navigation

- **Parent:** [Overview](index.md)
- **Previous:** [Overview](index.md)

## Next steps

- [Configuration](configuration.md) — configuration guidance and references.
- [Usage workflow](workflow.md) — the end-to-end contract-first cycle for your
  own project.
- [Command reference](commands.md) — every command, in both the standalone CLI
  and Django management-command form.
