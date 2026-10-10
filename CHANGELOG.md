# Changelog

All notable changes to this project are documented in this file.

The format is inspired by Keep a Changelog and follows semantic versioning for released
package versions. Releases before this file are described on the
[GitHub releases page](https://github.com/shlomoa/django-angular3/releases).

## [Unreleased]

### Added

- `django_angular3.spa.angular_urlpatterns()`: a catch-all view that serves the built Angular
  application from Django on the same origin as the API. Where the files are is configuration, not
  a Django setting: `artifacts.angularWorkspace` of the project configuration plus the new
  mandatory `angular.build.browserOutputPath` of `django-angular3.json` (existing tool
  configurations must add it; every command that runs Angular tooling fails without it).
  Bundle files are served by name, any other path gets `index.html` so a hard refresh
  on an Angular route works, and a wrong `/api/`, `/api-auth/`, `/admin/` or `/static/` URL or a
  stale asset hash is a 404. A missing build raises `ImproperlyConfigured`. The tutorial project
  is wired with it, and the real-tools flow has a stage 6b that drives the bundle served by Django
  alone, with the `django-dist` break variant. See
  [Serving the built application](https://github.com/shlomoa/django-angular3/blob/main/README.md#serving-the-built-application).
- A real-tools end-to-end flow, `DJNG_E2E=1 python -m tests.e2e.run_e2e`: it exports the tutorial
  project's schema with `drf-spectacular`, creates an Angular workspace and application with the
  Angular CLI and `angular-django2`, generates the API client with `ng-openapi-gen`, builds the
  application and drives it with Playwright against Django, optionally followed by a `build_app`
  run after a document and schema change. It is skipped unless `DJNG_E2E=1` is set. The
  `End-to-end` GitHub workflow runs it on demand, nightly and on pull requests that touch the
  package or the flow. See
  [End-to-end validation](https://github.com/shlomoa/django-angular3/blob/main/CONTRIBUTING.md#end-to-end-validation)
  ([shlomoa/django-angular3#232](https://github.com/shlomoa/django-angular3/issues/232)).

- `ng_data_service --path` (CLI and `manage.py`) forwards the schematic's `--path`, so a
  data service can be placed inside the application project
  ([shlomoa/django-angular3#239](https://github.com/shlomoa/django-angular3/issues/239)).

### Changed

- **Breaking:** `django-angular3.json` is mandatory and has no fallback. It is found next to the
  project configuration (`settings.BASE_DIR` in a configured Django runtime, otherwise the current
  directory) and every command that reads it (`ng_*`, `build_app`, `export_schema`, ...) fails with
  an error naming the expected path when it is missing. Before, a project without one silently
  used the packaged example (title `Example API`, the tutorial's output path and pin), and the
  tool configuration was looked up in the current directory only. The packaged file is now only the
  template `install-tutorial` copies. `tool.ngAddPackage` is mandatory too, and the Python defaults
  for the Angular settings and the pin are gone; only the platform names of the executables remain
  as defaults.

- `tool.ngAddPackage` pins `angular-django2@0.7.1` (was `0.7.0`). Its `data-service` schematic computes the
  import of the generated `ng-openapi-gen` client from the `output` of `ng-openapi-gen.json`, instead of
  the fixed `../api/services`, so a generated data service compiles against the client `ng_openapi_gen`
  generates ([shlomoa/angular-django2#213](https://github.com/shlomoa/angular-django2/issues/213)). The
  command mapping is unchanged. The end-to-end flow now builds with the generated `CustomersDataService`
  in the application instead of removing it
  ([shlomoa/django-angular3#240](https://github.com/shlomoa/django-angular3/issues/240)).

### Fixed

- The tutorial project (`django-angular3 install-tutorial`) works with the tools it names: its
  `app.openui.json` has the shape `angular-django2` compiles (an `html` root with the
  `Application` and its pages as siblings, instead of `DashboardPage` elements inside the
  `Application`, which `ng generate angular-django2:material-app --document` rejected), and its
  `shop` app ships `migrations/0001_initial.py`, so `python manage.py migrate` creates the
  `shop_customer` and `shop_product` tables. The tutorial and Example 1 of the scenario suite
  follow the new document
  ([shlomoa/django-angular3#238](https://github.com/shlomoa/django-angular3/issues/238)).
- `ng_openapi_gen` no longer replaces the `output` of `ng-openapi-gen.json` with
  `<workspace>/generated/ng-openapi-gen`: it keeps the one `ng_openapi_setup` wrote, which
  `generate:api` uses too, and `ng_openapi_setup` now defaults to `app/api` under the
  application project's source root (`src/app/api` in a workspace without one)
  ([shlomoa/django-angular3#239](https://github.com/shlomoa/django-angular3/issues/239)).
- The `ngOpenApiGen` clause of `django-angular3.json` accepts and requires `services`, and the
  shipped defaults are `services: true` and `serviceSuffix: "ApiService"`. With `ng-openapi-gen`
  1.x, `ng_openapi_gen` now generates a `<Resource>ApiService` per OpenAPI tag, the class the
  `angular-django2` `data-service` schematic wraps; before, it generated only the functional
  client, or classes named `<Resource>Api`. Existing `django-angular3.json` files must add
  `"services": true` and change `serviceSuffix` to `"ApiService"`
  ([shlomoa/django-angular3#240](https://github.com/shlomoa/django-angular3/issues/240)).
- `export_schema` applies `drfSpectacular.settings` of `django-angular3.json` again: the exported
  `info.title` and `info.version` were `""` and `0.0.0` because `drf-spectacular` re-read
  `REST_FRAMEWORK` instead of `SPECTACULAR_SETTINGS` after the settings were reloaded
  ([shlomoa/django-angular3#223](https://github.com/shlomoa/django-angular3/issues/223)).

## [0.3.6]

### Added

- `build_app` translates the detected project-configuration, OpenAPI and OpenUI changes into
  ordered steps and runs them. In `v0.3.5` it exposed only the command interface; its
  translation and execution were not implemented. `--dry-run` prints the steps with their
  stage, mode, target, wrapper command, resolved parameters and reason. Without `--dry-run`
  the steps run level by level, the run halts at the first failure, and
  `build-evidence.json` is written to `--output` (default `build/`) with the argv, exit code
  and output of every call and the pinned `angular-django2` package and mapping versions.
  `--force` is refused until it is implemented. See
  [Changes `build_app` turns into steps](https://djangoangular.com/commands/#changes-build-app-turns-into-steps).
- `build_app` reads which `angular-django2` command compiles which OpenUI node type, and
  which operations it supports, from `schematics/command-mapping.json` of the package
  installed in the Angular workspace. It keeps no copy, so the package must be installed at
  the version `tool.ngAddPackage` pins.
- A new OpenUI `Tabs`, `dialog`, `Stepper` or `table` element is generated with
  `ng generate angular-django2:<command>`. These four commands have no `ng_*` wrapper; the
  steps are named by the Tool contracts `ngdj_add_tabs`, `ngdj_add_dialog`,
  `ngdj_add_stepper` and `ngdj_add_table`.
- `ng_openapi_setup` accepts `--auth-scheme bearer|basic`, forwarded to the
  `openapi-setup` schematic. `bearer` is the default and leaves the output unchanged. The
  scheme is fixed when the helpers are first generated: a later run keeps the existing
  `django-transport.ts`.
- `ng_workspace`, `ng_gen_app`, `ng_page`, `ng_component`, `ng_complex_component` and
  `ng_reactive_form` accept `--document` (a workspace-relative OpenUI document) and, except
  `ng_workspace`, `--node-id` to compile an OpenUI element.
- `jsonschema>=4.18` is a dependency; it validates the command mapping.

### Changed

- The tutorial builds the bundled project and then changes its OpenUI document and rebuilds
  it with `build_app --previous-config`. `build_app` does not discover the previous
  configuration yet: without `--previous-config` it compares the configuration with itself
  and finds no change.
- `tool.ngAddPackage` pins `angular-django2@0.7.0` (was `0.6.1`) and the package requires
  `openui-spec==0.12.1` (was `0.12.0`).
- `ng_reactive_form --definition` is deprecated in favor of `--document`; exactly one of the
  two is required.
- `last-check` builds the application (`ng_build`) until the terminal validation commands
  exist.

### Fixed

- Relative paths for ngdj schematics now reject Windows drive-qualified, rooted, and
  parent-traversal paths on every platform.

### Removed

- **Breaking:** `tool.commandAllowlist` is no longer a supported key of
  `django-angular3.json`, and the default allowlist is gone. Configuration validation now
  fails with `tool contains unsupported key(s): commandAllowlist`.

### Upgrade notes

- Delete `tool.commandAllowlist` from your `django-angular3.json`.
- Install `angular-django2@0.7.0` in the Angular workspace before running `build_app` on
  OpenUI or OpenAPI changes.
- Replace `ng_reactive_form --definition <file>` with `--document <openui document>`.
- `build_app` fails explicitly, quoting the upstream reason and gap issue, for what
  `angular-django2` cannot do yet: updating or deleting any OpenUI node other than
  `Application`, changing an OpenAPI operation, and updating or deleting a path or schema.
  Static-configuration changes are not detected yet, and `form-field`, `field-component`,
  `html` and `link` have no `djng` Tool.
