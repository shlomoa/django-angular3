# Configuration files and settings



## Ordered execution plan


2. **Complete Angular command configuration**
   - Finalize the static `django-angular3.json` `angular` and `tool` clauses,
     including their defaults and platform-aware executable behavior.
   - Implement and validate:

     `django-angular3.json` → `DJANGO_ANGULAR3` → `AngularSettings`

   - Use the derived `AngularSettings` only in `djng` commands that run
     Angular and `angular-django2` commands.
   - Remove independent `DJANGO_ANGULAR3` authority and validate the static
     tool settings where Angular commands require them.

3. **Complete direct `drf-spectacular` CLI configuration**
   - Finalize `drfSpectacular.settings` as the static configuration used only
     when `djng` runs the direct `drf-spectacular` CLI.
   - Derive and validate the CLI settings for schema export without merging
     them into Angular or `ng-openapi-gen` settings.

4. **Complete consumer project configuration**
  - Finalize the canonical `django-angular3-<project_name>.json` schema and its
     `ProjectConfig` derivation.
   - Define project-file discovery for Django management commands and the
     standalone CLI.
   - Release `django_angular3/templates/django_angular3/`
    `django-angular3-<project_name>.json` as the consumer starting template.
   - Keep `django_angular3/examples/01_simple_crm/`
    `django-angular3-<project_name>.json` as the Simple CRM tutorial configuration;
     its artifact paths must resolve within that example.
   - Move command-test configuration to a test-owned fixture. Tests must not
     depend on the repository-root project configuration or use a packaged
     consumer template or tutorial example as a general-purpose fixture.
    Remove the repository-root `django-angular3-<project_name>.json` once its test
     dependency is replaced.
   - Remove legacy combined-project configuration parsing and compatibility
     aliases; reject legacy project fields in validation tests.

5. **Complete `ng-openapi-gen` configuration and run integration**
   - Finalize `ngOpenApiGen` as global generator configuration used only by
     `djng` commands that run `ng-openapi-gen` through `angular-django2`.
   - Combine its global values with `ProjectConfig` run-time input and
     workspace locations to derive the per-run output and
     `ng-openapi-gen.json`, then invoke the workspace-local generator with
     `-c`.
   - Remove `ngOpenApiGenConfig`, `ng_openapi_gen_config`, and external
     production generator-config paths. Keep
     `spec/openapi/ng-openapi-gen/ng-openapi-gen.json` validation-only and
     exclude it from releases.
   - Test global-setting validation, derived-file content, invocation, and
     rejection of legacy generator configuration.

6. **Cut over public command interfaces and coupled documentation**
   - Make management commands and the standalone CLI use derived settings and
     discovered `ProjectConfig`; retain only command-specific inputs and
     overrides, and expose derived paths and configuration in dry runs.
   - Remove public configuration-file path arguments.
   - Update command help, CLI and management-command documentation, and
     command-usage examples in the same change; do not publish documentation
     for an interface that is not implemented.
   - Test command help and parsing without path parameters.

7. **Verify the configuration integrations**
   - Run Ruff format/lint, the full unittest suite, and relevant dry-run
     command checks after the completed configuration and interface cutovers.

8. **Align remaining published documentation with implemented behavior**
   - Update `docs/configuration.md`, user-facing workflow documentation,
     app-builder requirements, and design documents after the command-interface
     cutover. Command help, command documentation, and command-usage examples
     are updated in Step 6.
   - Reference `REQUIREMENTS.md` for fields and lifecycle; do not duplicate
     field tables or publish legacy combined-file/path-argument guidance.
   - Rebuild Sphinx documentation.

9. **Retire this temporary work file**
   - Transfer configuration definitions and classification to
     `REQUIREMENTS.md`, user-facing behavior to `docs`, and this execution
     plan to a durable implementation tracker or completed-work record.
   - Verify no field table, lifecycle rule, configuration definition, or
     published document depends on this file.
   - Search for incoming links and obsolete terminology, delete
     `configuration_files_and_settings.md` only when none remain, then run
     final repository verification.
