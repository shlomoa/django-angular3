# Configuration Plan

## Purpose and boundary

Tool and project configuration planning, derived configuration artifacts, and configuration implementation work.

Normative behavior remains owned by the referenced requirements,
specifications, contracts, architecture, and executable/configuration sources.
GitHub owns issue scope and tracking.

## Related domain plans

- [Construction Plan](CONSTRUCTION_PLAN.md)

## Static tool configuration

### Planning details

- Its derivation chain is: <!-- STEP7-7b038c39c2f8 -->
- `django-angular3.json` → `DJANGO_ANGULAR3` → `DjangoAngularSettings` <!-- STEP7-93af13358fb5 -->

## Project configuration

### Planning details

- `project.name`: a non-empty generated-application name; <!-- STEP7-0886af0f884e -->
- `artifacts.openapiSchema`: a non-empty relative path to the OAS schema; <!-- STEP7-8aa951949413 -->
- `artifacts.openuiSpecification`: a non-empty relative path to the OpenUI concrete UI document; <!-- STEP7-312f324d917d -->
- `artifacts.angularWorkspace`: a non-empty relative path to the Angular workspace. <!-- STEP7-2ba194560769 -->
- For example, a generated application can declare its identity and artifact locations with: <!-- STEP7-d407e00f0ad8 -->
- `<previous-schema>` and `<current-schema>` are required run-time parameters, selected from the previous and current project configurations respectively. The `diff` subcommand and resolved executable are owned by `djng`, not exposed as user-editable project settings. <!-- STEP7-b5745cce721e -->

### Corrected current identities

- The packaged project-configuration template uses the current tracked identity `django-angular3-project.json`; generated applications use `django-angular3-<project_name>.json` beside `manage.py`. <!-- STEP7-a94d80b03582 -->

### Authoritative references

- Configuration authority: SPECIFICATIONS §2, django_angular3/settings.py, and django_angular3/config.py. <!-- STEP7-85de87afdfb4 -->
- OpenUI authority: external artifact-role SSOT via ARCHITECTURE §2.8.1; djng integration: APP_BUILDER_REQUIREMENTS and the Construction plan's OpenAPI/OpenUI construction flow. <!-- STEP7-cb115945fa28 -->

## Derived configuration artifacts

### Planning details

- `pnpm exec ng-openapi-gen -c <generated-config-path>` <!-- STEP7-2d6eb280fd98 -->
- For example, a derived file for a project with an OAS schema at `django_angular3/examples/01_simple_crm/schema.yaml` and an Angular workspace at `build/angular` is: <!-- STEP7-8a8842b3a8d0 -->
- `tests/fixtures/artifacts/ng-openapi-gen/ng-openapi-gen.json` is a validation-only fixture, not a released or production configuration source. <!-- STEP7-bdd9efbafd69 -->
- `drfSpectacular.settings` is derived from django-angular3.json and used by `djng` for schema export. The resulting OpenAPI document is an OAS schema, not `drf-spectacular` tool configuration. See example `drfSpectacular.settings` clause in `django-angular3.json` schema above. <!-- STEP7-6ef67b95f4bc -->
- `oasdiff.settings` is derived from the `oasdiff` clause in `django-angular3.json` and used by `djng` when it invokes `oasdiff` for schema comparison. The static setting selects JSON output so `djng` can parse the diff result deterministically; it is not an OAS schema or independently editable project configuration. <!-- STEP7-a014c9426e1a -->
- For example, the `oasdiff` clause above derives: <!-- STEP7-4515da192613 -->
- For each comparison, `djng` obtains the platform-specific executable from `ensure_oasdiff()` and invokes: <!-- STEP7-31a21cdd2055 -->

### Authoritative references

- Tool authority: TOOL_CONTRACTS.md; sequencing only belongs in a domain plan. <!-- STEP7-e0941140daa3 -->
- Automation authority: automation requirements/specification and split primitive contracts. <!-- STEP7-eff3a9094b6e -->

## Configuration implementation work

No current implementation work is assigned exclusively to this domain.

## Tracked GitHub issues

No tracked issue is assigned exclusively to this domain.

Issue bodies, status, timestamps, relationships, dependency lists, and
acceptance criteria are intentionally not copied into this plan.
