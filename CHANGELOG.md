# Changelog

All notable changes to this project are documented in this file.

The format is inspired by Keep a Changelog and follows semantic versioning for released
package versions. Releases before this file are described on the
[GitHub releases page](https://github.com/shlomoa/django-angular3/releases).

## [Unreleased]

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

- `tool.ngAddPackage` pins `angular-django2@0.7.0` (was `0.6.1`) and the package requires
  `openui-spec==0.12.1` (was `0.12.0`).
- `ng_reactive_form --definition` is deprecated in favor of `--document`; exactly one of the
  two is required.
- `last-check` builds the application (`ng_build`) until the terminal validation commands
  exist.

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
