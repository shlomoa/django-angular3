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

> **Implementation status:** `handle()` loads the project configurations, derives
> the ChangeSet (project configuration, OpenAPI and OpenUI; the static-configuration
> lane is not detected), translates it with `translate_changes` and, with
> `--dry-run`, prints the ordered steps with their wrapper commands and resolved
> parameters. OpenUI and OpenAPI changes get their steps from the
> ngdj command mapping (§Change-to-command mapping). Without `--dry-run` the steps run
> in order through their wrappers (§Step execution), halt at the first failure and
> leave `build-evidence.json` in `--output`; `--force` is refused, not honored. The
> `export_schema` wrapper has no invocation builder, so a schema export step is refused,
> and a data service step cannot run until its `resource` is defined
> ([shlomoa/django-angular3#207](https://github.com/shlomoa/django-angular3/issues/207)). Previous-configuration discovery, the
> static-configuration change lane, the implementation of the deterministic TOOL
> commands, hooks, and terminal validation are not implemented. This document
> specifies the target behavior; it must not be read as a claim that those target
> behaviors are already available.

### Build algorithm

`build_app` builds the generated app; it does not emit a build plan or a
procedure graph. For every run it performs this ordered algorithm:

1. Validate the discovered project configuration, static tool configuration,
  OpenAPI schema, and OpenUI document.
2. Identify the difference between the previous and current project
  configurations.
3. Identify the difference between the previous and current OpenAPI schemas.
4. Identify the structural difference between the previous and current OpenUI
   document trees, including each node's `id`, `type`, `attrs`, and parent
   relation. The order of identified siblings is not significant (see
   `doc/contracts/CHANGE_MODEL_CONTRACTS.md` §2.2).
5. Translate the identified change sets into the required change commands.
6. Execute those commands against the generated-app workspace.
7. Validate the generated outputs and the resulting integrated application.

The comparison inputs determine what changes; command execution performs those
changes; validation decides whether the build succeeded. A command failure or
failed validation halts the build and surfaces the failure through Django's
normal command error reporting.

### Provider adapters and enforcement ownership

`doc/ARCHITECTURE.md` §3.6.1.1 is the authoritative provider-adapter capability
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
| Current project configuration | `--current-config <path>`, otherwise discovered `django-angular3-<project_name>.json` | JSON | Discovery and filename realization are defined in `doc/specifications/SPECIFICATIONS.md` §2.2. |
| Current OpenAPI schema | `artifacts.openapiSchema` | YAML or JSON (OAS 3.x) | The current schema version. |
| Previous project configuration | `--previous-config <path>`, otherwise the current configuration path with `.json` replaced by `.previous.json` | JSON | Resolves its own artifact selectors independently of the current configuration. A missing previous configuration starts a build from scratch. |
| Previous OpenAPI schema | `artifacts.openapiSchema` from the previous project configuration | YAML or JSON (OAS 3.x) | Baseline contract selected by the previous configuration. Absent on a first run; the OpenAPI domain emits `create` changes for the candidate contract. `export_schema` produces the baseline file by rotating the current schema to its `.previous` counterpart (`api.json` → `api.previous.json`) before it writes the new one; the previous project configuration selects that rotated file through its own `artifacts.openapiSchema`. `build_app` does not discover the rotated file by naming convention. |
| Current `app.openui.json` | `artifacts.openuiSpecification` | JSON (`openui.schema.json`) | OpenUI concrete UI document selected for the candidate build. |
| Previous `app.openui.json` | `artifacts.openuiSpecification` from the previous project configuration | JSON (`openui.schema.json`) | Baseline OpenUI document selected by the previous configuration. Absent on a first run; the OpenUI domain emits `create` changes for the candidate document. |

Each project configuration resolves its own artifact selectors relative to its
location. The current configuration selects the candidate OpenAPI and OpenUI
documents; the previous configuration selects their baselines. The
`--previous-config` argument remains a project-configuration input and no
separate `--previous-openui` argument or `.previous` OpenUI filename convention
is defined. `artifacts.openuiSpecification` does not name the document format
or the ChangeSet domain. `app.openui.json` is the generated-app filename
convention. Its concrete-document role, grammar, and catalog relationship are
defined by the
[OpenUI artifact-role SSOT](https://github.com/shlomoa/openui-spec/blob/main/spec/README.md#41-specification-artifacts);
djng owns only the configured input path and its build-stage handling. See
`doc/ARCHITECTURE.md` §2.8.1 and §8.5.

The OpenUI stage gate validates each configured canonical JSON document through
`openui-spec` before comparison, selector resolution, or wrapper selection.
The accepted document is the deterministic JSON-first input to the upstream
ngdj compiler, which applies the three-layer construction model defined in
`doc/ARCHITECTURE.md` §3.4.1. `djng` owns Python-side validation and wrapper
selection, not OpenUI parsing rules, selectors, or ngdj compiler behavior.

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
configuration categories are in `doc/specifications/SPECIFICATIONS.md` §2.1;
discovery and baseline-path realization are defined in §2.2.

---

## Change Derivation

The canonical Change Model, including `Change`, the four domains, identity
rules, baseline/candidate semantics, and the complete `ChangeSet` schema, is
defined in `doc/contracts/CHANGE_MODEL_CONTRACTS.md` §2. This section defines how `build_app`
applies that model.

For every run, the builder must compare the accepted baseline and candidate
normalized semantic state, emit atomic `create`, `delete`, `update`, or `move`
changes, and then translate those changes to commands. A missing baseline emits
`create` changes for the candidate state. An empty atomic-change list means
there are no changes in that domain. Coarse category strings and an ad-hoc
per-domain `type` field are not part of the builder contract.

| Domain | Builder derivation requirement |
|---|---|
| `static_config` | Compare only validated static-configuration fields. |
| `project_config` | Compare project identity and all artifact selectors. Record selector changes separately from changes in selected OpenAPI or OpenUI content. |
| `openapi` | Parse structured `oasdiff` output into atomic contract changes. Preserve complete contract identity and source diff evidence before deriving resource hints. |
| `openui` | Compare declared OpenUI node identities, attributes, and parent relations; reordering identified siblings is not a change (`CHANGE_MODEL_CONTRACTS.md` §2.2). Missing, duplicate, or invalid node identities fail validation. |

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
All underlying `ngdj` command and behavior facts follow the upstream-source
policy in `doc/ARCHITECTURE.md` §3.4; this document defines only djng command
selection and composition.
Tool and hook names remain distinct from CLI wrapper command names, as defined
by the automation naming layers in `doc/ARCHITECTURE.md` §3.6.4. Contract identity
and command-composition cardinalities are defined in `doc/ARCHITECTURE.md` §3.6.2;
this document selects and composes those contracts but does not redefine them.
In particular, an OpenUI wrapper may receive only a validated canonical
document and spec-defined selectors, component types, and attributes; it must
not introduce custom behavioral selectors or a duplicate parser.

| Construction concern | Primitive | Tool contract | Hook contract | Direct-build role |
|---|---|---|---|---|
| Schema export from DRF | TOOL | `openapi_schema_export` | — | Produce the current OpenAPI artifact when required. |
| Schema validation | TOOL | `validate_openapi_schema` | — | Validate the schema before construction. |
| Pre-construction validation | HOOK | — | `pre-construction` | Block Angular generation until required inputs are valid. |
| Schema diff | TOOL | `oasdiff_diff` | — | Derive schema changes. |
| Angular workspace scaffold | TOOL | `angular_workspace_scaffold` | — | Create the workspace for a first build. |
| Angular app scaffold | TOOL | `angular_app_scaffold` | — | Create the primary Angular application. |
| Typed Angular client generation | TOOL | `angular_api_client_generate` | — | Generate the typed API client. |
| Data service | TOOL | `ngdj_add_data_service` | — | Generate the typed data service of an API resource. |
| Standalone component | TOOL | `ngdj_add_component` | — | Generate a component from an OpenUI element. |
| Complex component | TOOL | `ngdj_add_complex_component` | — | Generate an advanced component from an OpenUI element. |
| Reactive form | TOOL | `ngdj_add_reactive_form` | — | Generate a typed form from an OpenUI `Form` element. |
| Routed page | TOOL | `ngdj_add_page` | — | Generate a page from an OpenUI page element. |
| Optional interpretive refinement | SKILL | — | — | Handle only selected work that structured inputs and deterministic schematics do not fully specify. |
| Post-generation verification | HOOK | — | `post-generation` | Record and enforce per-command structural checks. |
| Session-end audit | HOOK | — | `session-stop` | Archive run information and write a session summary. |

### Change-to-command mapping

| Source atomic change | Selected command category | Mode |
|---|---|---|
| Initial-domain `create` | Workspace, application, API-integration, data-service, and required OpenUI commands | create |
| `project_config` `create` or `update` of `project.name` or `artifacts.angularWorkspace` | Project-level workspace and application foundation commands | matching operation |
| `project_config` `create` or `update` of `artifacts.openapiSchema` or `artifacts.openuiSpecification` | No construction command; the selected OpenAPI or OpenUI content is compared by its own domain, and the terminal validation gate checks the new source | — |
| `project_config` `delete` or `move` | Unsupported; fails explicitly (`move` is reserved) | — |
| `static_config` `create` or `update` of a setting in the table below | The command that consumes the setting | matching operation |
| `static_config` `create` or `update` of a setting that changes no construction output | No construction command; the terminal validation gate runs | — |
| `static_config` `delete` or `move`, or a subject not in the table | Unsupported; fails explicitly | — |
| `openapi` `create` of a path | `angular_api_client_generate`, then `ngdj_add_data_service` for the new resource | create |
| `openapi` `create` of a schema | `angular_api_client_generate` | create |
| Any other `openapi` change: an operation, or the `update` or `delete` of a path or schema | Unsupported while ngdj's `data-service` is create-only; fails explicitly with the upstream mapping's reason and gap issue | — |
| `openui` change whose element resolves to a root node type of the upstream command mapping, with a `supported` status for its operation | The Tool of that node type in the table below | matching operation |
| `openui` change inside an `embedded` node type | The Tool of its root node type, with the root's operation status | update |
| `openui` change whose operation is `partial` or `unsupported` in the mapping, or whose command has no djng Tool | Unsupported; fails explicitly with the mapping's reason and gap issue, or "no wrapper" | — |

A static setting selects the command that consumes it. `create` appears for an initial
build or a new setting, and has the same translation as `update`:

| Static setting | Consumed by | Step | Stage |
|---|---|---|---|
| `drfSpectacular.settings.*` | schema export | `openapi_schema_export` | 0 |
| `angular.workspace.*` (`packageManager`, `style`, `routing`) | workspace defaults, reapplied by the workspace modification wrapper | `angular-workspace-foundation` | 1 |
| `tool.ngAddPackage` | the ngdj registration, repeated by the same wrapper | `angular-workspace-foundation` | 1 |
| `angular.application.*` (`ssr`, `zoneless`) | application generation | `angular-app-composition` | 2 |
| `ngOpenApiGen.*` (`serviceSuffix`, `modelIndex`) | the derived `ng-openapi-gen.json` | `angular_api_client_generate` | 3 |
| `angular.build.*`, `oasdiff.*`, `tool.executables.*` | the build gate, the diff output and the executable lookup | none | — |

The workspace and application steps use Skill-layer names, as the project-config steps
do, because no Tool contract modifies a workspace or application. A schema export does
not by itself change the OpenAPI subjects: any resulting difference in the schema comes
from the `openapi` Changes.

Every `openapi` change regenerates the typed client from the changed schema. Whether
`data-service` supports an operation is read from the upstream command mapping, as for
OpenUI. The OpenUI commands that depend on an API subject come from the `openui`
Changes of the same ChangeSet; `build_app` does not derive that dependency from the API
subject. The ngdj `openapi-setup` schematic (`ng_openapi_setup`) has no dedicated Tool;
the generic `ngdj_run_schematic` Tool can run it. The translators give no step for it yet, and
a first build needs it before `angular_api_client_generate`.

`build_app` loads the mapping only when the ChangeSet has an `openui` or `openapi`
Change, from `<angularWorkspace>/node_modules/<package>/schematics/`, where the package is
the one `tool.ngAddPackage` names. It must be installed at the pinned version, so the steps
of a workspace that does not exist yet cannot be derived for these Changes; `build_app` reports
that the package must be installed. `--dry-run` prints the ordered steps without running
them.

The upstream command mapping (`schematics/command-mapping.json` of the installed
`angular-django2` package, `ARCHITECTURE.md` §3.4) owns which node type is compiled by
which command and which operations that command supports; `build_app` reads it at run
time and does not keep a copy. `build_app` owns the Tool selection:

| Root node type | ngdj command | Tool contract | Stage |
|---|---|---|---|
| `Application` | `material-app` | `angular_app_scaffold` | 2 |
| `SurfaceContainers` (no overlay child) | `component` | `ngdj_add_component` | 7 |
| `SurfaceContainers` (with an overlay child) | `complex-component` | `ngdj_add_complex_component` | 8 |
| `Form` | `reactive-form` | `ngdj_add_reactive_form` | 9 |
| `DashboardPage`, `EmptyPage` | `page` | `ngdj_add_page` | 10 |

A change inside an `embedded` node type is an `update` of the root node that compiles it
(a navigation or route change is an `Application` update). A change at a root node type
element itself is a `create` or `delete`; a change inside it is an `update`. Node types
compiled by `form-field`, `field-component`, `tabs`, `dialog`, `stepper`, `table`,
`html` or `link` (whose update runs through the workspace modification wrapper) have
no djng Tool yet and fail as "no Tool", and so does a node type the mapping does not
cover. The `SurfaceContainers` condition and the choice of `material-app` for
`Application` are decided by `build_app`, not by the mapping. With the
mapping of `angular-django2` 0.7.0 only `create` is supported for most node types:
`update` is supported for `Application`, `html` and `link`, `complex-component` is
`partial`, and every other `update` and every `delete` fails explicitly. A Tool step
receives the `document` and `node_id` of its element.

Unsupported changes must fail explicitly; `build_app` must not silently omit them.

### Step execution

A step produced by translation names a Tool contract or a Skill name. `build_app` bridges
it to its operator wrapper through the crosswalk of `ARCHITECTURE.md` §3.6.4.1
(`django_angular3/step_bridge.py` keeps a copy that a test compares with the table) and
resolves the wrapper's options from the project configuration and the ngdj command
mapping. A step therefore carries its concern key, wrapper (`command`), ngdj command and
`parameters`. No site identifier comes from ngdj, and each option must be a parameter of
the step's ngdj command in the mapping.

| Option | Resolved from |
|---|---|
| `document`, `node_id` | The OpenUI element the step compiles; `document` is workspace-relative |
| `name` | The element `id`, dasherized as ngdj does |
| `target_path` | `src/app/features/<name>` for a page, `src/app/features` for a complex component |
| `project`, `app_name` | `project.name` |

A document that lies outside the Angular workspace is copied to
`<workspace>/.django-angular3/` before the first step that reads it, never in a dry run.
The final `last-check` gate runs `ng_build` until the terminal validation commands exist.

`--dry-run` resolves the steps and prints them; it runs no wrapper and writes no file. A real
run refuses steps with an unresolved option before anything runs. It then executes the
steps level by level (by `exec_order`) and, within a level, in list order; the first
failing call halts the run, the remaining steps are recorded as skipped and `build_app`
exits with a `CommandError` naming the step. The evidence
(`<output>/build-evidence.json`, written after a failure too) holds every step with its
status and each call's argv, exit code and output, and the pinned `tool.ngAddPackage` and
the mapping and OpenUI spec versions of the mapping the steps used.

### Execution order

Commands must satisfy this dependency order:

```
1  angular_workspace_scaffold       (TOOL; foundation)
2  angular_app_scaffold             (TOOL; depends on 1)
3  angular_api_client_generate      (TOOL; depends on 2)
```

Stage `0` is the schema export (`openapi_schema_export`); the remaining stages are `4`
data service (`ngdj_add_data_service`), `7` component,
`8` complex component, `9` reactive form and `10` page, as in the table above, and `12`
last validation; `5`, `6` and `11` are unassigned. A deterministic `ngdj` operation
without a Tool contract in `TOOL_CONTRACTS.md` is not added to this order and is not
claimed as supported by `build_app`.

An optional matching `angular-*-composition` SKILL command may follow its
deterministic TOOL command only when the selected work is genuinely
underspecified or requires interpretive refinement. It is not part of the
required path for validated structured inputs.

Project-level foundation commands are selected once per command and operation,
not once per `project_config` subject: on a first run `project.name` and
`artifacts.angularWorkspace` are both created, and each of those commands
appears once, with every contributing subject listed in its target and reason.
Steps from other domains are not merged.

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
- The builder must detect OpenUI document changes by structurally diffing OpenUI
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
- Specific integration acceptance work remains tracked in the
  [Verification Plan](../plan/VERIFICATION_PLAN.md#terminal-and-global-acceptance).

### FR-10: Global generated-app acceptance

- Local acceptance by an individual Skill session is necessary but not
  sufficient for global generated-app acceptance.
- After all selected deterministic commands and Skill sessions complete,
  terminal validation must apply a global acceptance gate to the composed
  application.
- The gate must verify cross-Skill interface consistency, including the types
  and signatures exchanged across generated API-client, data-service, and UI
  boundaries.
- The gate must verify that the generated Angular client remains aligned with
  the exported OpenAPI contract.
- The gate must include runtime smoke coverage proving that the composed
  application starts and that its required main flows run.
- A run must fail global acceptance when any global check fails, even when
  every individual Skill passed its local acceptance criteria.

---

## Non-Functional Requirements

- Change derivation and command translation must complete in under 30 seconds
  for typical schema and OpenUI document sizes, excluding `oasdiff` execution.
- The builder must be testable with mock oasdiff output so oasdiff does not
  need to be installed for the test suite.
- Dry-run command previews must be available for CI inspection without modifying
  the generated-app workspace.

---

## Terminology

Authoritative terminology is defined in `doc/ARCHITECTURE.md` §§2 and 19. The
canonical `ChangeSet` boundary is defined in `doc/contracts/CHANGE_MODEL_CONTRACTS.md` §2.3.
