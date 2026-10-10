# Tutorial: Build the tutorial project

The bundled `simple_crm` project lets you continue from the installed `djng`
package to a running Django backend and Angular workspace, and then change the UI
and rebuild it.

## 2. Install the tutorial project

Copy the bundled project into a working directory:

```bash
django-angular3 install-tutorial simple_crm
```

This creates:
- A `simple_crm/` folder containing a Django project (`simple_crm`),
- A DRF app (`shop`) with its initial migration
- `schema.yaml` exported from the above DRF app.
- `app.openui.json` containing the OpenUI requirements: an `html` root with the
  `Application` (`Routing` and `Navigation`) and, next to it, the customers and products
  pages.
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

## 6. Change the UI and rebuild with `build_app`

Once the workspace exists, `ng_workspace` has installed `angular-django2` in it, and
`build_app` can work out what a change to the OpenUI document needs. It compares the
current inputs with a baseline, translates the differences into ordered steps, and runs
them. The baseline is not discovered yet: you pass it with `--previous-config`.

Keep a copy of the OpenUI document as it is now, and a copy of the project configuration
that points at it. Name the second file `django-angular3-simple_crm.previous.json`:

```bash
cp app.openui.json app.previous.openui.json
cp django-angular3-simple_crm.json django-angular3-simple_crm.previous.json
```

In `django-angular3-simple_crm.previous.json`, change `openuiSpecification` to
`"app.previous.openui.json"`. Then add an orders page to `app.openui.json`: a route inside
`appRouting`, a navigation item inside `appNavigation`, and the page next to the
`Application`, as a sibling of the other two pages. `angular-django2` compiles the
`Application` from its `Routing` and `Navigation`; a `DashboardPage` inside the
`Application` is rejected.

```json
{
  "id": "ordersRoute",
  "type": "Route",
  "attrs": {
    "uses.path": "\"orders\"",
    "uses.target": "\"ordersPage\"",
    "uses.title": "\"Orders\""
  }
}
```

```json
{
  "id": "ordersNavigation",
  "type": "NavItem",
  "attrs": { "uses.label": "\"Orders\"", "uses.route": "\"ordersRoute\"" }
}
```

```json
{
  "id": "ordersPage",
  "type": "DashboardPage",
  "attrs": { "uses.route": "\"orders\"", "uses.title": "\"Orders\"" }
}
```

Preview the steps. `build_app` downloads `oasdiff` the first time it compares the
OpenAPI schemas:

```bash
python manage.py build_app --previous-config django-angular3-simple_crm.previous.json --dry-run
```

The output is JSON. It reports the pinned `angular-django2` package and command mapping,
and one entry per step:

| Stage | Step | Mode | Command | Element |
|---|---|---|---|---|
| 2 | `angular_app_scaffold` | update | `ng_gen_app` (`material-app`) | `crmApp` (the new navigation item) |
| 2 | `angular_app_scaffold` | update | `ng_gen_app` (`material-app`) | `crmApp` (the new route) |
| 10 | `ngdj_add_page` | create | `ng_page` (`page`) | `ordersPage` |
| 12 | `last-check` | validate | `ng_build` | |

The new route and navigation item change the `Application`, so the application is
regenerated: only the text
between the `openui:begin` and `openui:end` comments in the generated files is replaced,
and edits you made around it are kept. The new page is generated once. Each step's
`reason` says what required it and what a second run does on existing output.

When the steps look right, drop `--dry-run` to run them. Like step 5, this needs Node.js
and pnpm. The run stops at the first failure and writes `build/build-evidence.json` with
the exit code and output of every call:

```bash
python manage.py build_app --previous-config django-angular3-simple_crm.previous.json
```

After a successful build, make the current state the baseline for the next change:

```bash
cp app.openui.json app.previous.openui.json
```

`build_app` refuses what `angular-django2` cannot do yet instead of skipping it. For
example, changing the `uses.title` of `customersPage` fails with `ngdj does not support update of
OpenUI node type DashboardPage (unsupported)`, quoting the upstream reason and the issue
that tracks it. See {ref}`Changes build_app turns into steps <build-app-steps>`
for what is supported.

## Tutorial navigation

- **Parent:** [Overview](index.md)
- **Previous:** [Overview](index.md)

## Next steps

- [Configuration](configuration.md) — configuration guidance and references.
- [Usage workflow](workflow.md) — the end-to-end contract-first cycle for your
  own project.
- [Command reference](commands.md) — every command, in both the standalone CLI
  and Django management-command form.
