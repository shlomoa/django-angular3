Explore: Trace ngdj command usage

Now I have complete coverage. Here's a thorough read-only analysis of all ngdj command and schematic integrations in djng:

## Implemented Commands & Schematics

### Direct Wrapper Invocations (Exposed via CLI & Django Management Commands)

**1. ng_new** — Create empty Angular workspace
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L73-L95) (`build_ng_new_invocations`)
- **Exact Command**: `ng new <project_name> --defaults --skip-git --skip-install --no-create-application --package-manager=<pnpm|npm> --directory=<output_dir>`
- **Exposed via**:
	- CLI: `django-angular3 ng_new <config_path>`
	- Management: `django-admin ng_new <config_path>`
- **Callers**: [cli.py](django_angular3/cli.py#L43-L53), [management/ng_new.py](django_angular3/management/commands/ng_new.py)

**2. ng_config** — Configure Angular workspace defaults
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L120-L155)
- **Exact Commands**: Three separate `ng config` invocations:
	- `ng config cli.packageManager <pnpm|npm>`
	- `ng config schematics.@schematics/angular:application.style <scss|css>`
	- `ng config schematics.@schematics/angular:application.routing <true|false>`
- **Exposed via**: CLI (`django-angular3 ng_config`), Management (`django-admin ng_config`)
- **Callers**: [cli.py](django_angular3/cli.py#L72-L82), [management/ng_config.py](django_angular3/management/commands/ng_config.py)

**3. ng_build** — Build configured Angular application
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L158-L173)
- **Exact Command**: `ng build <project_name> --configuration=<production|development>`
- **Exposed via**: CLI (`django-angular3 ng_build`), Management (`django-admin ng_build`)
- **Callers**: [cli.py](django_angular3/cli.py#L83-L96), [management/ng_build.py](django_angular3/management/commands/ng_build.py)

**4. ng_gen_app** — Generate Angular application with ngdj schematic
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L176-L200)
- **Exact Command**: `ng generate angular-django2:material-app <app_name> --style=<scss|css> [--routing|--no-routing] --ssr=<true|false> --zoneless=<true|false> --defaults`
- **ngdj Schematic**: `angular-django2:material-app`
- **Exposed via**: CLI (`django-angular3 ng_gen_app [--app-name <name>]`), Management (`django-admin ng_gen_app [--app-name]`)
- **Callers**: [cli.py](django_angular3/cli.py#L97-L115), [management/ng_gen_app.py](django_angular3/management/commands/ng_gen_app.py)

**5. ng_openapi_gen** — Generate API client from OpenAPI schema
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L203-L218)
- **Exact Command**: `pnpm exec ng-openapi-gen -c|i <source_path>`
- **Exposed via**: CLI (`django-angular3 ng_openapi_gen`), Management (`django-admin ng_openapi_gen`)
- **Callers**: [cli.py](django_angular3/cli.py#L116-L130), [management/ng_openapi_gen.py](django_angular3/management/commands/ng_openapi_gen.py)
- **Note**: `ng_openapi_gen` is in `DEFAULT_ANGULAR_SETTINGS.command_allowlist` by default ([settings.py](django_angular3/settings.py#L19))

**6. ng_add** — Install Angular package with schematics
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L221-L238)
- **Exact Command**: `ng add <package> --skip-confirmation`
- **Default Package**: `angular-django2` (from `ng_add_package` setting)
- **Exposed via**: CLI (`django-angular3 ng_add [--package <pkg>]`), Management (`django-admin ng_add [--package]`)
- **Callers**: [cli.py](django_angular3/cli.py#L131-L151), [management/ng_add.py](django_angular3/management/commands/ng_add.py)

**7. ng_workspace** — Bootstrap workspace with ngdj
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L241-L255)
- **Composite**: Combines `ng_new` + `ng_config` + `ng_add` + workspace schematic invocation
- **ngdj Schematic Invoked**: `angular-django2:workspace-setup` (via `ng generate`)
- **Exposed via**: CLI (`django-angular3 ng_workspace`), Management (`django-admin ng_workspace`)
- **Callers**: [cli.py](django_angular3/cli.py#L57-L70), [management/ng_workspace.py](django_angular3/management/commands/ng_workspace.py)

**8. ng_workspace_modify** — Reapply workspace bootstrap and defaults
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L257-L276)
- **Composite**: Combines `ng_config` + `ng_add` + workspace schematic invocation
- **ngdj Schematic Invoked**: `angular-django2:workspace-setup`
- **Exposed via**: Management only (`django-admin ng_workspace_modify`)
- **Callers**: [management/ng_workspace_modify.py](django_angular3/management/commands/ng_workspace_modify.py)

**9. ng_workspace_delete** — Delete entire Angular workspace
- **Location**: [django_angular3/angular.py](django_angular3/angular.py#L279-L297)
- **Implementation**: Python `shutil.rmtree()` via `sys.executable -c`
- **Exposed via**: Management only (`django-admin ng_workspace_delete`)
- **Callers**: [management/ng_workspace_delete.py](django_angular3/management/commands/ng_workspace_delete.py)

---

## ngdj Schematics Invoked

**Directly Invoked** (wrapped by djng commands):
1. `angular-django2:workspace-setup` — Called by `ng_workspace` and `ng_workspace_modify`
	 - Invocation: `ng generate angular-django2:workspace-setup <project_name>`
	 - Location: [angular.py](django_angular3/angular.py#L104-L109)

2. `angular-django2:material-app` — Called by `ng_gen_app`
	 - Invocation: `ng generate angular-django2:material-app <app_name> [flags]`
	 - Location: [angular.py](django_angular3/angular.py#L180-L191)

---

## Build Plan Integration (Automation Naming Layer)

[build_app.py](django_angular3/management/commands/build_app.py#L15-L39) defines `_command_for_skill(skill, mode)` mapping:

### Canonical Schematic Keys (Current)
| Skill | Mode | Mapped Command | Implementation Status |
|---|---|---|---|
| `workspace-setup` | `create` | `ng_workspace` | ✅ Implemented |
| `material-app` | `create` | `ng_gen_app` | ✅ Implemented |
| `openapi-setup` | `create` | `ng_openapi_gen` | ✅ Implemented |
| `openapi-setup` | `modify` | `ng_openapi_gen` | ✅ Implemented |

### Legacy Skill Names (Backward Compat)
| Skill | Mode | Mapped Command | Implementation Status |
|---|---|---|---|
| `angular-workspace-foundation` | `create` | `ng_workspace` | ✅ Implemented |
| `angular-workspace-foundation` | `modify` | `ng_workspace_modify` | ✅ Implemented |
| `angular-workspace-foundation` | `delete` | `ng_workspace_delete` | ✅ Implemented |
| `angular-app-composition` | `create` | `ng_gen_app` | ✅ Implemented |
| `angular-app-composition` | `modify` | `ng_gen_app` | ✅ Implemented |
| `angular-api-integration` | `create` | `ng_openapi_gen` | ✅ Implemented |
| `angular-api-integration` | `modify` | `ng_openapi_gen` | ✅ Implemented |

---

## Planned but NOT Implemented

### Skills with No Command/Schematic Implementation

[build_app.py](django_angular3/management/commands/build_app.py#L370-L430) references these plan steps but **no command builder exists**:

| Plan Skill | Mode | Fallback Behavior | Status | Docs Reference |
|---|---|---|---|---|
| `ng-data-service` | `create`, `modify`, `delete` | Falls through to `skill.replace("-", "_")` → `ng_data_service` | ❌ Command builder missing | [e2e_enabling_documentation_plan.md](e2e_enabling_documentation_plan.md#L113), [GENERATE_AI_AUTOMATIONS.md](doc/GENERATE_AI_AUTOMATIONS.md#L6635) |

### Skills in ARCHITECTURE (Plan Layer Only, No CLI/Command Exposure)

From [GENERATE_AI_AUTOMATIONS.md](doc/GENERATE_AI_AUTOMATIONS.md#L46-L53), these are defined in the automation naming crosswalk **without CLI wrappers or TOOL contracts**:

| Concern Key | SKILL Name | Mode | CLI Wrapper | Implementation |
|---|---|---|---|---|
| `angular.data-service` | `angular-data-service-composition` | — | — | 🛑 Planned |
| `angular.field-component` | `angular-field-component-composition` | — | — | 🛑 Planned |
| `angular.form-field` | `angular-form-field-composition` | — | — | 🛑 Planned |
| `angular.component` | `angular-component-composition` | — | — | 🛑 Planned |
| `angular.complex-component` | `angular-complex-component-composition` | — | — | 🛑 Planned |
| `angular.reactive-form` | `angular-reactive-form-composition` | — | — | 🛑 Planned |
| `angular.page` | `angular-page-composition` | — | — | 🛑 Planned |
| `angular.site` | `angular-site-composition` | — | — | 🛑 Planned |

### ngdj Schematics Required by the Skills — Current CLI Status

The previous list was copied from the Phase B skill-to-schematic mapping in
[`e2e_enabling_documentation_plan.md`](../e2e_enabling_documentation_plan.md).
That plan contains historical placeholder names. The authoritative current
source is the [ngdj CLI reference](https://angular-django2.readthedocs.io/en/latest/cli/),
verified on 2026-07-31.

| Skill | Current ngdj schematic status |
|---|---|
| `angular-workspace-foundation` | Available: `angular-django2:workspace-setup`. |
| `angular-app-composition` | Available: `angular-django2:material-app`. |
| `angular-api-integration` | Available: `angular-django2:openapi-setup`. |
| `angular-data-service-composition` | Available as `angular-django2:data-service`; `angular-django2:ng-data-service` is not a documented schematic. |
| `angular-field-component-composition` | No matching `ng-field-component` schematic is documented. |
| `angular-form-field-composition` | No matching `ng-form-field` schematic is documented. |
| `angular-component-composition` | Available building blocks: `angular-django2:component` and `angular-django2:embed-component`; `angular-django2:ng-component` is not documented. |
| `angular-complex-component-composition` | Available: `angular-django2:complex-component`; it composes `component` and `embed-component` for nested children and provides mixins, projection slots, CDK overlay support, and create/modify/delete lifecycle handling. |
| `angular-reactive-form-composition` | No matching `ng-reactive-form` schematic is documented. |
| `angular-page-composition` | No matching `ng-page` schematic is documented. |
| `angular-site-composition` | No matching `ng-site` schematic is documented. |

`material-app`, `workspace-setup`, `openapi-setup`, `data-service`, `component`,
and `embed-component` are current ngdj CLI schematics. The remaining named
placeholders require an explicit ngdj design and implementation decision; they
must not be treated as existing CLI commands.

`complex-component` owns the advanced feature set for Skill 8. It reuses
`embed-component` for idempotent child-to-parent wiring rather than duplicating
that behavior.

---

## Command Allowlist Context

[settings.py](django_angular3/settings.py#L19) defines:
```python
"command_allowlist": ("ng_openapi_gen",)
```

Only `ng_openapi_gen` executes by default. All other `ng_*` commands plan dry-runs unless allowlist is explicitly broadened in project settings ([GENERATE_AI_AUTOMATIONS.md](doc/GENERATE_AI_AUTOMATIONS.md#L2300)).
