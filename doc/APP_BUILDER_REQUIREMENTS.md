# App Builder Requirements

## Purpose

The **generated app** is the integrated Django-Angular application that
`build_app` receives, modifies, validates, and delivers.

`djng` provides deterministic Django management commands for bounded work such
as schema extraction and ngdj wrapper invocation. `build_app` is the generated
app's planned orchestration command. Its public interface discovers the project
configuration; it is invoked as:

```bash
django-admin build_app [options]
# or equivalently:
python manage.py build_app [options]
```

> **Implementation status:** the current command exposes its documented
> argument interface, then raises `NotImplementedError` because planning and
> execution are not implemented. This document specifies the target behavior;
> it must not be read as a claim that those target behaviors are already
> available.

### Build algorithm

`build_app` builds the generated app; it does not emit a build plan or a
procedure graph. For every run it performs this ordered algorithm:

1. Validate the discovered project configuration, static tool configuration,
  OpenAPI schema, and OpenUI document.
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

### Provider adapters and enforcement ownership

`ARCHITECTURE.md` §2.12.1 is the authoritative provider-adapter capability
matrix. Provider-native hooks, handlers, and wrappers may map provider events
into the adapter interface, but they are not independent correctness gates.
During direct `build_app` execution, `djng` applies the selected TOOL and HOOK
contracts, dependency ordering, failure handling, and terminal validation;
those command-execution boundaries remain authoritative regardless of the
provider used by an agent session.

---

## Inputs

### Required

| Input | Source | Format | Notes |
|---|---|---|---|
| `django-angular3.json` | Static tool configuration | JSON | Global `djng` tool settings, including Angular, `ngOpenApiGen`, and `drfSpectacular.settings`; not a project configuration or command argument. |
| Current project configuration | `--current-config <path>`, otherwise discovered `django-angular3-<project_name>.json` | JSON | The discovered default is defined in `REQUIREMENTS.md` §4.2.4. |
| Current OpenAPI schema | `artifacts.openapiSchema` | YAML or JSON (OAS 3.x) | The current schema version. |
| Previous project configuration | `--previous-config <path>`, otherwise the current configuration path with `.json` replaced by `.previous.json` | JSON | Resolves its own artifact selectors independently of the current configuration. A missing previous configuration starts a build from scratch. |
| Previous OpenAPI schema | `artifacts.openapiSchema` from the previous project configuration | YAML or JSON (OAS 3.x) | Baseline contract selected by the previous configuration. Absent on a first run; the OpenAPI domain emits `create` changes for the candidate contract. |
| Current `app.openui.json` | `artifacts.openuiSpecification` | JSON (`openui.schema.json`) | OpenUI concrete document defining non-CRM UI artifacts. |
| Previous `app.openui.json` | `artifacts.openuiSpecification` from the previous project configuration | JSON (`openui.schema.json`) | Baseline OpenUI document selected by the previous configuration. Absent on a first run; the OpenUI domain emits `create` changes for the candidate document. |

Each project configuration resolves its own artifact selectors relative to its
location. The current configuration selects the candidate OpenAPI and OpenUI
documents; the previous configuration selects their baselines. The
`--previous-config` argument remains a project-configuration input and no
separate `--previous-openui` argument or `.previous` OpenUI filename convention
is defined. `artifacts.openuiSpecification` does not name the document format
or the ChangeSet domain. `app.openui.json` is the generated-app filename
convention. Its grammar is defined by
`openui.schema.json` and its vocabulary by `openui.json` in
[shlomoa/openui-spec](https://github.com/shlomoa/openui-spec); djng owns only
the configured input path and its build-stage handling. See
`ARCHITECTURE.md` §8.5.

### Optional

| Input | Flag | Notes |
|---|---|---|
| Current configuration override | `--current-config <path>` | Override the discovered current project configuration. |
| Previous configuration override | `--previous-config <path>` | Override the derived previous project configuration. |
| Dry run | `--dry-run` | Diagnostic validation and debugging mode: validate inputs, identify changes, and show ordered change commands without executing them or modifying the generated-app workspace. |
| Force mode | `--force start-from-scratch` | Override comparison results and execute the full initial-build command set. |

### Configuration model

The project configuration supplies the locations used by the builder. Static
tool settings remain in `django-angular3.json`. The authoritative project
configuration definition and discovery rules are in `REQUIREMENTS.md` §4.2.4.

---

## Change Derivation

The canonical Change Model, including `Change`, the four domains, identity
rules, baseline/candidate semantics, and the complete `ChangeSet` schema, is
defined in `REQUIREMENTS.md` §4.2.9. This section defines how `build_app`
applies that model.

For every run, the builder must compare the accepted baseline and candidate
normalized semantic state, emit atomic `create`, `delete`, `update`, or `move`
changes, and then translate those changes to commands. A missing baseline emits
`create` changes for the candidate state. An empty atomic-change list means
there are no changes in that domain. Coarse category strings and an ad-hoc
per-domain `type` field are not part of the builder contract.

| Domain | Builder derivation requirement |
|---|---|
| `static_config` | Compare only validated static-configuration fields. Treat command-allowlist entries as set members. |
| `project_config` | Compare project identity and all artifact selectors. Record selector changes separately from changes in selected OpenAPI or OpenUI content. |
| `openapi` | Parse structured `oasdiff` output into atomic contract changes. Preserve complete contract identity and source diff evidence before deriving resource hints. |
| `openui` | Compare declared OpenUI node identities, attributes, parent relations, and ordered children. Missing, duplicate, or invalid node identities fail validation. |

Unsupported input, unknown configuration keys, and unsupported `oasdiff` output
shapes must fail explicitly. They must never be interpreted as no change.

---

## Change Command Translation and Execution

`build_app` translates the `ChangeSet` into an ordered sequence of executable
commands. Each command has a stable identity, mode, inputs, and a
human-readable reason. Translation is deterministic for the same current and
previous inputs; commands not selected by either change set are omitted.

### Automation boundaries

The selected commands invoke the following documented automation contracts.
Tool and hook names remain distinct from CLI wrapper command names, as defined
by the automation naming layers in `ARCHITECTURE.md` §2.23. Contract identity
and command-composition cardinalities are defined in
`GENERATE_AI_AUTOMATIONS.md` §Contract identity and relationship cardinality;
this document selects and composes those contracts but does not redefine them.

| Construction concern | Primitive | Tool contract | Hook contract | Direct-build role |
|---|---|---|---|---|
| Schema export from DRF | TOOL | `openapi_schema_export` | — | Produce the current OpenAPI artifact when required. |
| Schema validation | TOOL | `validate_openapi_schema` | — | Validate the schema before construction. |
| Pre-construction validation | HOOK | — | `pre-construction` | Block Angular generation until required inputs are valid. |
| Schema diff | TOOL | `oasdiff_diff` | — | Derive schema changes. |
| Angular workspace scaffold | TOOL | `angular_workspace_scaffold` | — | Create the workspace for a first build. |
| Angular app scaffold | TOOL | `angular_app_scaffold` | — | Create the primary Angular application. |
| Typed Angular client generation | TOOL | `angular_api_client_generate` | — | Generate the typed API client. |
| Optional interpretive refinement | SKILL | — | — | Handle only selected work that structured inputs and deterministic schematics do not fully specify. |
| Post-generation verification | HOOK | — | `post-generation` | Record and enforce per-command structural checks. |
| Session-end audit | HOOK | — | `session-stop` | Archive run information and write a session summary. |

### Change-to-command mapping

| Source atomic change | Selected command category | Mode |
|---|---|---|
| Initial-domain `create` | Workspace, application, API-integration, data-service, and required OpenUI commands | create |
| `project_config` `update` or `move` | Project-level workspace and application foundation commands | matching operation |
| `static_config` `update` | The command category for the supported configuration subject | update |
| `openapi` `create` | API-integration and data-service commands for affected subjects, followed by dependent UI commands | create |
| `openapi` `delete` | Dependent UI, data-service, and API-integration commands for affected subjects | delete |
| `openapi` `update` | Targeted dependent client, service, and UI commands | update |
| `openui` page `create`, `update`, `delete`, or `move` | `ng_page` wraps `angular-django2:page` for create; deterministic TOOL contract and remaining operation mappings are not yet defined | Not yet defined for `build_app` |
| `openui` standalone component `create`, `update`, `delete`, or `move` | `ng_component` wraps `angular-django2:component` for create; deterministic TOOL contract and remaining operation mappings are not yet defined | Not yet defined for `build_app` |
| `openui` complex component `create`, `update`, `delete`, or `move` | `ng_complex_component` wraps `angular-django2:complex-component`; deterministic TOOL contract and complete atomic-operation mapping are not yet defined | Not yet defined for `build_app` |
| `openui` reactive form `create`, `update`, `delete`, or `move` | `ng_reactive_form` wraps `angular-django2:reactive-form` for create; deterministic TOOL contract and remaining operation mappings are not yet defined | Not yet defined for `build_app` |
| `openui` navigation `update` or `move` | `ng_site` wraps `angular-django2:site` for its bounded create, modify, and delete operations; deterministic TOOL contract and navigation-move composition are not yet defined | Not yet defined for `build_app` |

The direct wrappers define precise invocations for the ngdj operations they
support, but `build_app` must still define the deterministic TOOL contract and
atomic-operation mapping for every row before claiming change-driven support.
Unsupported changes must fail explicitly; `build_app` must not silently omit
them.

### Execution order

Commands must satisfy this dependency order:

```
1  angular_workspace_scaffold       (TOOL; foundation)
2  angular_app_scaffold             (TOOL; depends on 1)
3  angular_api_client_generate      (TOOL; depends on 2)
```

The TOOL contracts and dependency order for the remaining deterministic `ngdj`
schematic operations are not yet defined. Existing direct wrappers do not by
themselves establish `build_app` support. The contracts and ordering must be
specified before those operations are added to this execution order or claimed
as supported by `build_app`.

An optional matching `angular-*-composition` SKILL command may follow its
deterministic TOOL command only when the selected work is genuinely
underspecified or requires interpretive refinement. It is not part of the
required path for validated structured inputs.

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
`artifacts.angularWorkspace`. Diagnostic artifacts support troubleshooting and validation;
they are not a substitute for execution.

| Artifact | Format | Storage path |
|---|---|---|
| Generated application files | TypeScript / HTML / SCSS / JSON | `artifacts.angularWorkspace` workspace root |
| oasdiff report | JSON or YAML | `build/` |
| ChangeSet | JSON | `build/` |
| Command execution and validation log | JSONL or text | `build/` |

---

## Functional Requirements

### FR-1: Change detection

- The builder must validate current project sources before comparison.
- The builder must compare all supported project-configuration keys and carry
  their changes in the `config` domain.
- The builder must detect schema changes using `oasdiff`.
- The builder must detect non-CRM changes by structurally diffing OpenUI
  document trees.
- If no previous schema is available, the OpenAPI domain must emit `create`
  changes for the candidate contract.

### FR-2: Command translation and execution

- The command sequence must be deterministic for the same inputs.
- Translation must apply dependency ordering for deterministic tool commands,
  any optional AI-guided SKILL commands, enforced gates, and terminal
  validation.
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

### FR-4: Initial-state force mode

- `--force start-from-scratch` overrides comparison results and executes the
  full deterministic initial-state command set plus any separately selected
  optional SKILL commands in dependency order.

### FR-5: OpenUI-only changes

- When the schema is unchanged but the OpenUI document changed, execute only
  the OpenUI-derived commands and required terminal validation.
- Schema-derived commands must not rerun unless triggered by a schema change.

### FR-6: Combined changes

- When both sources change, schema-derived commands are ordered before
  OpenUI-derived commands at the same dependency level.

### FR-7: Automation command execution

- Each selected SKILL command must run through the selected provider adapter
  with the specified canonical SKILL(s), sanitized command inputs, and
  `artifacts.angularWorkspace` as the generated-app workspace. The adapter
  returns normalized session evidence; it does not determine command or run
  acceptance.
- Each selected tool command must execute the corresponding deterministic tool
  contract with structured inputs and outputs. Direct deterministic execution
  must not open or require a provider session.
- Each selected gate must enforce its blocking check or lifecycle side effect
  before downstream commands continue.

### FR-8: Command and hook failure handling

- A failed tool command must halt execution and prevent dependent commands from
  starting.
- A failed command must report its identity, automation contract, error
  category, message, and structured details to the command output and run log.
- A failing pre- or post-execution hook must halt the build. A `session-stop`
  hook may only append warnings and must not change the run's exit code.
- The builder must not silently retry a failed command or hook.

### FR-9: Terminal validation

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
| **ChangeSet** | Domain-specific atomic changes and a computed summary used to select change commands. Its canonical schema is in `REQUIREMENTS.md` §4.2.9. | `REQUIREMENTS.md` §4.2.9 |
| **`app.openui.json`** | The generated app's OpenUI concrete UI document. | `ARCHITECTURE.md` §8.5 |
