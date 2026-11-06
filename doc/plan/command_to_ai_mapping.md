# Command to AI mapping: implementation status

Status snapshot of every existing and planned `djng` command, with the Tool contract and
Skill each one maps to. As of 2026-11-06, branch `claude/tender-maxwell-htqiz5` at
`9567c13`. This is a status view, not a contract: it will drift as work lands.

The names are owned elsewhere and are not redefined here:

- Wrapper, Tool and Skill names: the automation naming crosswalk,
  [`ARCHITECTURE.md` §3.6.4.1](../ARCHITECTURE.md#3641-automation-naming-crosswalk).
- Tool contracts: [`TOOL_CONTRACTS.md`](../contracts/TOOL_CONTRACTS.md).
- Skill contracts: [`SKILL_CONTRACTS.md`](../contracts/SKILL_CONTRACTS.md).
- Command arguments and interface availability: [`docs/commands.md`](../../docs/commands.md).

## Status key

- **Existing**: the command runs.
- **Not fully implemented**: the command exists but a documented piece is missing, such as a
  `build_app` step, an input or a Tool.
- **Missing**: no operator command exists, though a Tool or Skill contract may.

## What applies to every row

- No `SKILL.md` exists in the repository. `.claude/skills/` and `.agents/skills/` contain only
  `shared/`. All 11 Skills exist only as contract text and as working copies in
  `skill_creation/skills/`.
- The Tool contracts are backed only by the command wrappers. `django_angular3/tools.py`
  contains only the `oasdiff` download helpers, and the contracts describe the structured
  Tool outputs as planned.
- The four lifecycle Hooks (`pre-construction`, `migration-triggered`, `post-generation`,
  `session-stop`) have no handler yet; their contracts say "planned handler".

## Mapping

| Command | Concern | Tool contract | Skill | Status | Gap |
|---|---|---|---|---|---|
| `ng_new` | angular.workspace | `angular_workspace_scaffold` | `angular-workspace-foundation` | Existing | |
| `ng_workspace` | angular.workspace | `angular_workspace_scaffold` | `angular-workspace-foundation` | Existing | |
| `ng_workspace_modify` | angular.workspace | none | `angular-workspace-foundation` | Not fully implemented | Management command only. The scaffold Tool covers only a fresh workspace ([`COMMAND_MAPPING_PLAN.md`](COMMAND_MAPPING_PLAN.md) decision 1). |
| `ng_workspace_delete` | angular.workspace | none | `angular-workspace-foundation` | Not fully implemented | Management command only. No Tool contract for delete. |
| `ng_gen_app` | angular.app | `angular_app_scaffold` | `angular-app-composition` | Existing | |
| `ng_add` | angular.app | `angular_app_scaffold` (named in its implementation reference) | none | Existing | Not in the crosswalk's wrapper column. |
| `ng_page` | angular.page | `ngdj_add_page` | `angular-page-composition` | Existing | Tool structured outputs planned. |
| `ng_component` | angular.component | `ngdj_add_component` | `angular-component-composition` | Existing | Tool structured outputs planned. |
| `ng_complex_component` | angular.complex-component | `ngdj_add_complex_component` | `angular-complex-component-composition` | Existing | Tool structured outputs planned. |
| `ng_reactive_form` | angular.reactive-form | `ngdj_add_reactive_form` | `angular-reactive-form-composition` | Existing | Tool structured outputs planned. |
| `ng_data_service` | angular.data-service | `ngdj_add_data_service` | `angular-data-service-composition` | Existing | The resource is the OpenAPI tag of the subject ([#207](https://github.com/shlomoa/django-angular3/issues/207)); a path the OpenAPI document lacks leaves it unresolved. |
| `ng_openapi_gen` | angular.api-client | `angular_api_client_generate` | `angular-api-integration` | Existing | |
| `ng_openapi_setup` | none | `ngdj_run_schematic` (step carries `openapi-setup`) | none | Existing | `build_app` adds one step before the client for OpenAPI changes. |
| `export_schema` | contract.schema-export | `openapi_schema_export` | none | Not fully implemented | `build_app` cannot run a schema-export step yet. |
| `validate-openapi` (CLI) | contract.schema-validate | `validate_openapi_schema` † | none | Not fully implemented | The CLI exists, but the Tool wrapper and the `pre-construction` Hook are planned. |
| `validate-openui`, `validate-project` | none | none | none | Existing | Outside the crosswalk. |
| `ng_config`, `ng_material_setup`, `ng_build` | none | none | none | Existing | Outside the crosswalk. `ng_build` is the temporary `last-check` gate in `build_app`. |
| `build_app` | orchestrator | all the OpenUI and API Tools | all, through the planned guided session | Not fully implemented | Static-configuration changes are not detected, `--force` is refused, and there is no schema-export step. It cannot derive OpenUI or OpenAPI steps for a workspace that does not exist yet. Guided Skill sessions are not implemented. |
| `clean`, `distclean`, `install-tutorial` | none | none | none | Existing | Utility commands. |
| none (tabs) | angular.tabs | `ngdj_add_tabs` | none | Missing | `build_app` runs `ng generate angular-django2:tabs` directly. |
| none (dialog) | angular.dialog | `ngdj_add_dialog` | none | Missing | Same as tabs. |
| none (stepper) | angular.stepper | `ngdj_add_stepper` | none | Missing | Same as tabs. |
| none (table) | angular.table | `ngdj_add_table` | none | Missing | Same as tabs. |
| none (form-field) | angular.form-field | none | `angular-form-field-composition` | Missing | `build_app` refuses it as "no Tool". |
| none (field-component) | angular.field-component | none | `angular-field-component-composition` | Missing | `build_app` refuses it as "no Tool". |
| none (feature) | angular.feature | `ngdj_add_feature` | none | Missing | Planned wrapper. |
| none (schematic runner) | cross-cutting | `ngdj_run_schematic` | none | Missing | Planned wrapper. |
| none (oasdiff) | contract.schema-diff | `oasdiff_diff`, `oasdiff_changelog` | none | Missing | Only the `ensure_oasdiff()` helper exists. The diff wrapper is planned. |
| none (site) | none | none | `angular-site-composition` | Missing | Not a row in the crosswalk. It has a Skill contract and nothing else. |

† This link is inferred. The crosswalk gives that concern no wrapper.

## Limits of this snapshot

- The "structured outputs planned" notes come from the Tool contracts read (#1 to #18 except
  #3 and #7). The code behind each wrapper was checked only through `_COMMAND_BUILDERS` in
  `django_angular3/angular.py` and the parsers in `django_angular3/cli.py`.
- Commands that the crosswalk does not list (`ng_config`, `ng_add`, `ng_material_setup`,
  `ng_build`, `ng_openapi_setup`, the validators and the utilities) have no Tool or Skill
  mapping by design or by omission; this file does not decide which.
