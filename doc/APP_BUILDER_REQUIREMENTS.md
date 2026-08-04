# App Builder Requirements

## Purpose

The **generated app** is the integrated Django-Angular application that
`build_app` receives, modifies, validates, and delivers.

`djng` provides deterministic Django management commands for bounded work such
as schema extraction and ngdj wrapper invocation. `build_app` is the generated
app's orchestration command. It is invoked as:

```bash
django-admin build_app <config> [options]
# or equivalently:
python manage.py build_app <config> [options]
```

### Build algorithm

`build_app` builds the generated app; it does not emit a build plan or a
procedure graph. For every run it performs this ordered algorithm:

1. Validate the current `django-angular3.json`, OpenAPI schema, and OpenUI
   document.
2. Identify the difference between the previous and current project
  configurations.
3. Identify the difference between the previous and current OpenAPI schemas.
4. Identify the structural difference between the previous and current OpenUI
   document trees, including each node's `id`, `type`, `attrs`, and ordered
   `children`.
5. Translate the identified change sets into the required change commands.
6. Execute those commands against the generated-app workspace.
7. Validate the generated outputs and the resulting integrated application.

The comparison inputs determine what changes; command execution performs those
changes; validation decides whether the build succeeded. A command failure or
failed validation halts the build and surfaces the failure through Django's
normal command error reporting.

---

## Inputs

### Required

| Input | Source | Format | Notes |
|---|---|---|---|
| `django-angular3.json` | Tool configuration file | JSON | Must contain `project.name`, `openapi.source`, `openui.source`, and `angular.output`. Read as current and always authoritative. |
| Current OpenAPI schema | `openapi.source` | YAML or JSON (OAS 3.x) | The current schema version. |
| Previous project configuration | `--previous-config <path>` | JSON | Prior `django-angular3.json`; used only for the `config` change lane. |
| Previous OpenAPI schema | `--previous-schema <path>`, otherwise the current source's `.previous` sibling | YAML or JSON (OAS 3.x) | The explicit flag takes precedence. Absent on a first run; the schema change type is `start-from-scratch`. |
| Current `app.openui.json` | `openui.source` | JSON (`openui.schema.json`) | OpenUI concrete document defining non-CRM UI artifacts. |
| Previous `app.openui.json` | `--previous-openui <path>`, otherwise the current source's `.previous` sibling | JSON (`openui.schema.json`) | Resolved by the same explicit-override then adjacent-artifact algorithm as the previous OpenAPI schema. Absent on a first run; the OpenUI change type is `start-from-scratch`. |

`openui.source` selects the current OpenUI document; it does not name the document
format or the ChangeSet lane. `app.openui.json` is the generated-app filename
convention. Its grammar is defined by
`openui.schema.json` and its vocabulary by `openui.json` in
[shlomoa/openui-spec](https://github.com/shlomoa/openui-spec); djng owns only
the configured input path and its build-stage handling. See
`ARCHITECTURE.md` §8.5.

### Optional

| Input | Flag | Notes |
|---|---|---|
| Dry run | `--dry-run` | Diagnostic validation and debugging mode: validate inputs, identify changes, and show ordered change commands without executing them or modifying the generated-app workspace. |
| Force mode | `--force start-from-scratch` | Override comparison results and execute the full initial-build command set. |
| Breaking-change acknowledgement | `--acknowledge-breaking` | Permit execution after the breaking-change gate reports OpenAPI breaking changes. |

### Configuration keys read from `django-angular3.json`

| Key | Required | Purpose |
|---|---|---|
| `project.name` | yes | Workspace and app name |
| `openapi.source` | yes | Current OpenAPI schema path and schema-lane input selector |
| `openui.source` | yes | Current `app.openui.json` path and OpenUI-lane input selector |
| `angular.output` | yes | Generated-app workspace root |
| `angular.workspace.*` | no | Workspace settings such as package manager, style, and routing |

---

## Change Derivation

### OpenAPI change detection

Schema comparison uses `oasdiff`:

```bash
oasdiff diff <previous-schema> <current-schema> --format json
```

oasdiff output is parsed to classify the change and affected resources.

| Type | Signal | Meaning |
|---|---|---|
| `start-from-scratch` | No previous schema | First build; generate schema-derived artifacts. |
| `no-change` | Empty diff | Skip schema-derived commands. |
| `add-things` | Additions only | New endpoints, resources, or properties. |
| `remove-things` | Removals only | Deleted endpoints, resources, or properties. |
| `replace-things` | Additions and removals | Modified resources; execute removals before additions. |
| `breaking` | Breaking changes reported | Stop unless `--acknowledge-breaking` is present. |

When breaking changes are found, the builder must stop and output:

```
Breaking schema changes detected. Review the oasdiff report before proceeding.
Re-run with --acknowledge-breaking to continue.
```

### OpenUI change detection

OpenUI comparison is a structural diff of current and previous `app.openui.json`
document trees. It compares each node's `id`, `type`, `attrs`, and ordered
`children`, and records affected node IDs and their add, modify, or delete
operation. If no previous OpenUI document is available, OpenUI-specific change
detection is skipped; the first-run command set still creates the configured UI
artifacts required by the generated app.

### Project-configuration change detection

The `config` lane compares every supported `django-angular3.json` key with the
previous configuration. A changed source key remains an input selector for its
own lane; it is nevertheless reported in `config.affected_keys` because source
selection is build-relevant.

| Configuration key change | `config` type | Required effect |
|---|---|---|
| `project.name` | `replace-things` | Replace the project-level workspace and application foundation for the new identity. |
| `angular.output` | `replace-things` | Materialize the generated application at the new workspace root. |
| `angular.workspace.*` | `modify-things` | Apply the changed workspace settings. |
| `openapi.source`, `openapi.openapiGeneratorConfig`, or `openapi.ngOpenApiGenConfig` | `modify-things` | Use the selected contract and generator settings for schema comparison and API-client generation. |
| `openui.source` | `modify-things` | Use the selected OpenUI document for OpenUI comparison and UI construction. |

Any supported configuration-key addition, removal, or value replacement must
be represented in `affected_keys`. Unsupported configuration keys or changes
without a defined command translation must fail explicitly.

### ChangeSet

The builder uses a typed `ChangeSet` internally to carry comparison results
into command translation. It is not a build plan and does not replace command
execution.

```json
{
  "config": {
    "type": "modify-things | replace-things | no-change | start-from-scratch",
    "affected_keys": ["angular.workspace.style"]
  },
  "schema": {
    "type": "add-things | remove-things | replace-things | start-from-scratch | no-change | breaking",
    "affected_resources": ["Customer", "Order"],
    "breaking": false
  },
  "openui": {
    "type": "add-things | remove-things | replace-things | no-change | start-from-scratch",
    "affected_nodes": ["dashboardPage", "customerEditForm"]
  }
}
```

---

## Change Command Translation and Execution

`build_app` translates the `ChangeSet` into an ordered sequence of executable
commands. Each command has a stable identity, mode, inputs, and a
human-readable reason. Translation is deterministic for the same current and
previous inputs; commands not selected by either change set are omitted.

### Automation boundaries

The selected commands invoke the following documented automation contracts.
Tool and hook names remain distinct from CLI wrapper command names, as defined
by the automation naming layers in `ARCHITECTURE.md` §2.23.

| Construction concern | Primitive | Tool contract | Hook contract | Direct-build role |
|---|---|---|---|---|
| Schema export from DRF | TOOL | `openapi_schema_export` | — | Produce the current OpenAPI artifact when required. |
| Schema validation | TOOL | `validate_openapi_schema` | — | Validate the schema before construction. |
| Pre-construction validation | HOOK | — | `pre-construction` | Block Angular generation until required inputs are valid. |
| Schema diff | TOOL | `oasdiff_diff` | — | Derive schema changes. |
| Breaking-change gate | HOOK | — | `breaking-change` | Block execution until acknowledged or resolved. |
| Angular workspace scaffold | TOOL | `angular_workspace_scaffold` | — | Create the workspace for a first build. |
| Angular app scaffold | TOOL | `angular_app_scaffold` | — | Create the primary Angular application. |
| Typed Angular client generation | TOOL | `angular_api_client_generate` | — | Generate the typed API client. |
| Post-generation verification | HOOK | — | `post-generation` | Record and enforce per-command structural checks. |
| Session-end audit | HOOK | — | `session-stop` | Archive run information and write a session summary. |

### Change-to-command mapping

| Source change | Selected command category | Mode |
|---|---|---|
| Configuration start-from-scratch | Workspace and application foundation commands | create |
| Configuration replacement (`project.name` or `angular.output`) | Project-level workspace and application foundation commands | replace |
| Configuration modification | The command category for each affected configuration key | modify |
| Schema start-from-scratch | Workspace, app, API-integration, data-service, and required OpenUI commands | create |
| Schema addition | API-integration and data-service commands for affected resources, followed by dependent UI commands | create |
| Schema removal | Dependent UI, data-service, and API-integration commands for affected resources | delete |
| Schema replacement | Removal commands followed by creation commands for affected resources | delete, then create |
| OpenUI page addition, modification, or removal | `angular-page-composition` | create, modify, or delete |
| OpenUI standalone component addition, modification, or removal | `angular-component-composition` | create, modify, or delete |
| OpenUI complex component addition, modification, or removal | `angular-complex-component-composition` | create, modify, or delete |
| OpenUI reactive form addition, modification, or removal | `angular-reactive-form-composition` | create, modify, or delete |
| OpenUI site-navigation change | `angular-site-composition` | modify |

The implementation must define the precise wrapper invocation for every row
before claiming support for that change type. Unsupported changes must fail
explicitly; `build_app` must not silently omit them.

### Execution order

Commands must satisfy this dependency order:

```
1  angular-workspace-foundation   (foundation)
2  angular-app-composition         (depends on 1)
3  angular-api-integration         (depends on 2)
4  angular-data-service-composition (depends on 3)
5  angular-field-component-composition (depends on 2)
6  angular-form-field-composition   (depends on 2)
7  angular-component-composition    (depends on 2)
8  angular-complex-component-composition (depends on 2)
9  angular-reactive-form-composition (depends on 2, 6; optionally 4)
10 angular-page-composition         (depends on 2; composes 4, 7, 8, 9)
11 angular-site-composition         (composes 2–10)
```

Commands that delete removed resources precede commands that create replacement
or new resources at the same dependency level. Schema-derived commands precede
OpenUI-derived commands at the same level. Mandatory validation commands run
last.

`--dry-run` reports ordered commands, modes, inputs, and reasons, but does not
execute commands or modify the generated-app workspace. It is a command preview,
not a build-plan artifact.

---

## Durable Artifacts

The durable artifact of a successful run is the generated application at
`angular.output`. Diagnostic artifacts support troubleshooting and validation;
they are not a substitute for execution.

| Artifact | Format | Storage path |
|---|---|---|
| Generated application files | TypeScript / HTML / SCSS / JSON | `angular.output` workspace root |
| oasdiff report | JSON or YAML | `build/` |
| ChangeSet | JSON | `build/` |
| Command execution and validation log | JSONL or text | `build/` |

---

## Functional Requirements

### FR-1: Change detection

- The builder must validate current project sources before comparison.
- The builder must compare all supported project-configuration keys and carry
  their changes in the `config` lane.
- The builder must detect schema changes using `oasdiff`.
- The builder must detect non-CRM changes by structurally diffing OpenUI
  document trees.
- The builder must halt on breaking schema changes unless
  `--acknowledge-breaking` is set.
- If no previous schema is available, the schema change type is
  `start-from-scratch`.

### FR-2: Command translation and execution

- The command sequence must be deterministic for the same inputs.
- Translation must apply dependency ordering for deterministic tool commands,
  AI-guided SKILL commands, enforced gates, and terminal validation.
- Each selected command must include a reason for its inclusion.
- Commands not triggered by either change set must not execute.
- `build_app` must execute selected commands in order; it must not emit a build
  plan or procedure graph instead of executing them.

### FR-3: Dry run `[DEBUG]`

- `--dry-run` is for validation and debugging only. It must validate inputs,
  identify changes, and report translated commands without invoking automation
  or modifying the generated-app workspace.
- The preview must be human-readable and include command order, mode, inputs,
  and reason.

### FR-4: Breaking-change gate

- When oasdiff detects breaking changes, the builder must stop, print the report
  summary, and exit non-zero.
- Breaking changes may be bypassed only with `--acknowledge-breaking`.
- The `breaking-change` hook contract in
  `doc/GENERATE_AI_AUTOMATIONS.md` is the single point of enforcement.

### FR-5: Start-from-scratch mode

- `--force start-from-scratch` overrides comparison results and executes the
  full initial-build command set, including deterministic prerequisites and
  required SKILL commands in dependency order.

### FR-6: OpenUI-only changes

- When the schema is unchanged but the OpenUI document changed, execute only
  the OpenUI-derived commands and required terminal validation.
- Schema-derived commands must not rerun unless triggered by a schema change.

### FR-7: Combined changes

- When both sources change, schema-derived commands are ordered before
  OpenUI-derived commands at the same dependency level.

### FR-8: Automation command execution

- Each selected SKILL command must make a Claude Agent SDK call with the
  specified SKILL(s) enabled, command inputs as the prompt, and
  `angular.output` as the generated-app workspace.
- Each selected tool command must execute the corresponding deterministic tool
  contract with structured inputs and outputs.
- Each selected gate must enforce its blocking check or lifecycle side effect
  before downstream commands continue.

### FR-9: Command and hook failure handling

- A failed tool command must halt execution and prevent dependent commands from
  starting.
- A failed command must report its identity, automation contract, error
  category, message, and structured details to the command output and run log.
- A failing pre- or post-execution hook must halt the build. A `session-stop`
  hook may only append warnings and must not change the run's exit code.
- The builder must not silently retry a failed command or hook.

### FR-10: Terminal validation

- Every successful execution sequence must finish with one or more validation
  commands.
- Validation must consume recorded construction outputs where available and
  verify generated files, Angular build health, and required backend/frontend
  integration checks.
- A run is successful only when every terminal validation command succeeds.
- Specific integration acceptance criteria remain tracked in `TODO.md`.

---

## Non-Functional Requirements

- Change derivation and command translation must complete in under 30 seconds
  for typical schema and OpenUI document sizes, excluding `oasdiff` execution.
- The builder must be testable with mock oasdiff output so oasdiff does not
  need to be installed for the test suite.
- Dry-run command previews must be available for CI inspection without modifying
  the generated-app workspace.

---

## Glossary

For authoritative definitions see `ARCHITECTURE.md` §2 and §19.

| Term | Definition | See |
|---|---|---|
| **AI automations** | The full automation model used by `djng`: SKILLS, TOOLS, HOOKS, and PLUGINS. | `ARCHITECTURE.md` §2, `GENERATE_AI_AUTOMATIONS.md` |
| **`djng`** | The `django-angular3` solution: this repository, Django package, and tool. | `ARCHITECTURE.md` §2.5 |
| **`ngdj`** | The `angular-django2` companion Angular package. | `ARCHITECTURE.md` §2.6 |
| **`build_app`** | The `djng` management command that compares inputs, translates changes to commands, executes them, and validates the generated app. | §Purpose |
| **SKILLS** | Bounded AI skills that guide selected agent sessions. | `ARCHITECTURE.md` §2.14 |
| **TOOLS** | Deterministic callable capabilities for bounded operations. | `GENERATE_AI_AUTOMATIONS.md` |
| **HOOKS / gates** | Deterministic lifecycle-triggered or blocking automations. | `GENERATE_AI_AUTOMATIONS.md` |
| **ChangeSet** | Typed project-configuration, OpenAPI, and OpenUI comparison results used to select change commands. | §Change Derivation |
| **`app.openui.json`** | The generated app's OpenUI concrete UI document. | `ARCHITECTURE.md` §8.5 |
