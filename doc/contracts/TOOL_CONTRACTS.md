# Tool contracts

This document specifies the canonical Tool contracts used by `djng` to build
and maintain Angular applications. The automation subsystem architecture,
primitive-selection policy, relationship cardinality, and naming crosswalk are
defined in `ARCHITECTURE.md` §§2.22 and 3.6. Exact internal module
organization, persistence, execution, adapter, and rendering realization are
defined in `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md`.

All `ngdj` command, option, and behavior facts used by these contracts follow
the upstream-source policy in `ARCHITECTURE.md` §2.6. This document defines
only `djng`-owned Tool contracts and does not redefine the underlying `ngdj`
schematic surface.

The sibling automation contract owners are [HOOK_CONTRACTS.md],
[PROVIDER_ADAPTER_CONTRACTS.md], [PLUGIN_CONTRACTS.md], and
[SKILL_CONTRACTS.md]. The canonical Change Model is defined in
[CHANGE_MODEL_CONTRACTS.md].

---

## Tools

Use TOOLS for deterministic operations that do not require AI judgment. In the
`djng` architecture, this includes schema export, schema diff, contract
validation, Angular/client generation wrappers, and similar bounded
construction operations.

Per-capability tool contracts are defined in the
[Tool Contracts Catalog](#tool-contracts-catalog) below. Each contract follows
the same fixed shape — **name, inputs, outputs, error behavior, allowed
invocation context** — so the agent, `build_app` command translator, and a
future MCP exposure layer all see the same surface.

### Tool contract shape

Every tool contract in this document **MUST** specify:

| Field | Meaning |
|---|---|
| **Name** | The stable identifier the agent and `build_app` use to call the tool. Matches the deterministic tool contract selected during command translation (see `doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Change Command Translation and Execution). |
| **Purpose** | One-sentence statement of what the tool does. Must be deterministic — no AI judgment inside the operation. |
| **Inputs** | Typed table of input keys, required/optional status, type, default, and description. Inputs are passed as a single structured object. |
| **Outputs** | Typed table of output keys returned on success. Outputs are returned as a single structured object so the agent and downstream tools can read them without parsing free-form text. |
| **Error behavior** | The exit-code or exception contract on failure, the structured error fields returned, and the failure categories the caller must distinguish (e.g. `invalid_input`, `missing_dependency`, `external_tool_failed`, `output_invalid`). |
| **Allowed invocation context** | Which automation primitives are permitted to invoke this tool: `build_app` (as a selected TOOL command), `HOOK` (as the wrapped action of a lifecycle hook), agent (as a direct callable inside a guided agent session), or CLI (as a `django-admin` command). |
| **Implementation reference** | Pointer to the concrete code or external CLI that backs the contract today, so the contract and the implementation can be kept aligned. |

Contracts are normative. An implementation that deviates from a documented
contract is a bug in the implementation, not in the contract.

### Criteria for a future `tools_creation/` workspace

Do not create a sibling `tools_creation/` folder just to mirror
`skill_creation/`. Introduce it only when tool work becomes a dedicated
authoring stream with its own operational cadence.

Use the following criteria:

- there are named tool contracts to author, not only candidate ideas or
  analysis notes
- tool work has shared authoring guidance distinct from skill authoring
- multiple tool specifications need split working files because keeping them
  only in `doc/` is becoming unwieldy
- tool implementation and verification are being reviewed as a coherent track
  rather than as scattered notes attached to skill work
- the shared material across tools is large enough to justify a dedicated
  working set and folder structure

Until those conditions are met, keep tool planning and design detail in the
umbrella documentation under `doc/`.

## Tool Contracts Catalog

This catalog defines the deterministic tool contracts referenced from
`doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Change-to-Automations Mapping. Each entry follows the
[tool contract shape](#tool-contract-shape) defined above.

The contracts are grouped by lifecycle stage so the command execution order is
visually obvious: **contract lifecycle** (export → validate → diff) precedes
**Angular generation wrappers** (`ng-openapi-gen`, `ngdj_*`).

## Configuration discovery

Tool contracts that operate on a generated app discover its
`django-angular3-<project_name>.json`; they do not accept a project-configuration
path. The project configuration supplies the project identity and artifact
locations, while static `django-angular3.json` supplies global `djng` tool
settings. `DJANGO_ANGULAR3` and `DjangoAngularSettings` are derived from the static
tool configuration. See `SPECIFICATIONS.md` §2 for the authoritative category and
lifecycle definitions.

### Contract lifecycle tools

#### 1. `openapi_schema_export` — schema extraction trigger

**Name**: `openapi_schema_export`

**Purpose**: Generate the current OpenAPI 3.1 schema from the configured DRF
project (via `drf-spectacular`) and persist it as a durable, versioned artifact
at the discovered `artifacts.openapiSchema` path. Rotates any
existing schema to its `.previous` counterpart before writing.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `format` | no | `"json"` \| `"yaml"` | `"json"` | Serialization format for the exported schema. |
| `dry_run` | no | boolean | `false` | When `true`, compute and report the destination and would-be-archived previous path, but do not modify disk. |
**Outputs**:

| Key | Type | Description |
|---|---|---|
| `destination` | string (path) | Absolute path to the freshly written current schema (`artifacts.openapiSchema`). |
| `previous_path` | string (path) \| null | Absolute path of the archived previous schema if one existed before the run, otherwise `null`. |
| `format` | `"json"` \| `"yaml"` | Format the schema was rendered in. |
| `bytes_written` | integer | Size of the written schema artifact in bytes. Omitted on `dry_run`. |
| `schema_changed` | boolean | `true` if the new schema differs from the rotated previous, `false` if they are byte-identical, `null` when there was no previous schema. |

**Error behavior**: Non-zero exit (CLI) / raised `ToolError` (programmatic).
Returns a structured error object `{ category, message, details }` where
`category` is one of:

- `invalid_input` — discovered configuration missing or malformed, or required
  values absent.
- `missing_dependency` — `drf-spectacular` not installed.
- `external_tool_failed` — DRF schema generation raised an exception.
- `output_invalid` — generated bytes failed sanity checks (empty document,
  missing `openapi` key).

The destination file is **never** left in a partially written state: on any
failure after rotation, the rotation is reversed so the previous schema is
restored.

**Allowed invocation context**: `build_app` (as a TOOL command preceding
schema-derived SKILL commands); HOOK (`post-tool` on `makemigrations`); CLI
(`django-admin export_schema`).

**Implementation reference**:
`django_angular3/management/commands/export_schema.py`;
`django_angular3.config.get_previous_schema_path()`.

#### 2. `validate_openapi_schema` — contract validation

**Name**: `validate_openapi_schema`

**Purpose**: Validate that a given OpenAPI artifact is a syntactically valid
OAS 3.1 document and conforms to the structural constraints required by
downstream Angular generation. Returns a structured pass/fail report — never a
free-form text blob.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `schema` | yes | string (path) | — | Absolute path to the OpenAPI artifact to validate (typically the output of `openapi_schema_export`). |
| `format` | no | `"json"` \| `"yaml"` \| `"auto"` | `"auto"` | How to parse the artifact. `auto` infers from extension. |
| `ruleset` | no | string (path) \| `"default"` | `"default"` | Optional path to a custom validation ruleset (e.g. a Spectral ruleset). |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `valid` | boolean | `true` if the artifact passes all checks. |
| `errors` | array of `{ code, message, path, severity }` | Structural or specification-conformance errors. Empty when `valid` is `true`. |
| `warnings` | array of `{ code, message, path }` | Non-blocking lint findings. |
| `openapi_version` | string | The `openapi` field value detected in the artifact. |
| `resource_count` | integer | Number of distinct resource schemas detected in `components.schemas`. |

**Error behavior**:

- Validation failures (`valid: false`) are **not** treated as tool errors:
  the tool returns its structured report and exits zero. The `build_app`
  command executor — or a `pre-tool` hook — decides whether to halt.
- A non-zero exit / raised `ToolError` is reserved for `category` values:
  `invalid_input` (schema path missing or unreadable),
  `missing_dependency` (validator binary not installed),
  `external_tool_failed` (validator crashed),
  `output_invalid` (validator returned an unparseable report).

**Allowed invocation context**: `build_app` (as a TOOL command after
`openapi_schema_export` and before any generation command); HOOK (`pre-tool` on
`angular_api_client_generate`, `angular_workspace_scaffold`, and
`angular_app_scaffold`); agent (callable inside a guided agent session that needs to re-verify a
hand-edited schema). Not a user-facing CLI command in the current release.

**Implementation reference**: planned wrapper over an OpenAPI 3.1 validator
(e.g. `spectral lint`) invoked from `django_angular3/validation.py`. Contract
must be honoured regardless of the chosen backing validator.

#### 3. `oasdiff_diff` — schema diff and change detection

**Name**: `oasdiff_diff`

**Purpose**: Run `oasdiff` against the current and previous OpenAPI artifacts
and return a structured diff result that `build_app` consumes to derive the
`ChangeSet`. The agent does not parse raw `oasdiff` output.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `current_schema` | yes | string (path) | — | Absolute path to the current OpenAPI artifact. |
| `previous_schema` | yes | string (path) | — | Absolute path to the previous OpenAPI artifact. |
| `report_path` | no | string (path) | `build/oasdiff-report.json` | Path where the raw `oasdiff` report is also archived for human inspection. |
| `format` | no | `"json"` \| `"yaml"` \| `"text"` | `"json"` | Format used for the archived raw report. The structured return value is always JSON-shaped. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `schema_changed` | boolean | `true` if any difference is detected. |
| `changes` | array of structured diff entries | Differences reported by `oasdiff`. |
| `affected_resources` | array of string | Distinct resource names touched by the diff. |
| `report_path` | string (path) | Where the raw `oasdiff` artifact was archived. |

`oasdiff_diff` does not classify changes into builder categories. `build_app`
maps its structured entries into atomic OpenAPI changes according to the
canonical Change Model in [CHANGE_MODEL_CONTRACTS.md] §2.

**Error behavior**: Non-zero exit / raised `ToolError` with `category` in
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.
A successful `oasdiff` invocation returns structured differences with exit
zero; a non-zero exit indicates tool failure, not a special change category.

**Allowed invocation context**: `build_app` (as the TOOL command feeding the
`ChangeSet`); agent (read-only diagnostic use inside a guided agent session
that needs to re-inspect a diff).

**Implementation reference**: `django_angular3/tools.py:ensure_oasdiff()` for
binary acquisition; planned `django_angular3.diff` wrapper that calls
`oasdiff` with the contract above and post-processes its JSON output.

### Angular generation wrapper tools

#### 4. `angular_api_client_generate` — typed Angular client generation

**Name**: `angular_api_client_generate`

**Purpose**: Run `ng-openapi-gen` against the current OpenAPI artifact inside
the generated Angular workspace to produce typed Angular API clients. Wraps
the existing `ng_openapi_gen` djng management command so the agent and
`build_app` command executor see a structured tool contract instead of raw CLI output.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `schema` | no | string (path) | `artifacts.openapiSchema` | Override path to the OpenAPI artifact to consume. |
| `dry_run` | no | boolean | `false` | When `true`, compute the generator command line and the expected output directory but do not invoke `ng-openapi-gen`. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `output_dir` | string (path) | Absolute path of the directory where generated client files were written. |
| `generated_files` | array of string (path) | All files written by this invocation, relative to `output_dir`. |
| `client_count` | integer | Number of distinct generated client classes. |
| `generator_version` | string | Version string reported by `ng-openapi-gen`. |
| `command` | string | The exact command line invoked (for audit and debug). |

**Error behavior**: Non-zero exit / raised `ToolError` with `category` in
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.

- `missing_dependency` covers the case where the generated workspace has not
  installed `ng-openapi-gen` locally. Per the repository principle, the tool
  **must not** download Angular packages at runtime: it instead surfaces a
  `missing_dependency` error directing the user to run the workspace install
  step.
- `output_invalid` is returned when the generator exits zero but writes no
  files or produces files that fail a TypeScript parse smoke check.

**Allowed invocation context**: `build_app` (as a TOOL command invoked
after `validate_openapi_schema` and before the `angular-api-integration` skill session); agent
(inside the `angular-api-integration` guided agent session when the SKILL needs to regenerate
the client during refinement). Not a HOOK target — generation is always
explicit. CLI (`django-admin ng_openapi_gen`).

**Implementation reference**:
`django_angular3/management/commands/ng_openapi_gen.py`;
`django_angular3/angular.py`.

#### 5. `angular_workspace_scaffold` — Angular workspace scaffold wrapper

**Name**: `angular_workspace_scaffold`

**Purpose**: Invoke the `ngdj` Angular workspace schematic to scaffold a fresh
workspace at `artifacts.angularWorkspace`. Wraps the existing `ng_new` djng management
command behind the structured tool contract used during direct execution.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `dry_run` | no | boolean | `false` | When `true`, validate inputs and report the resolved command line without creating the workspace. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `workspace_path` | string (path) | Absolute path to the created workspace root. |
| `package_manager` | `"npm"` \| `"yarn"` \| `"pnpm"` | Package manager configured for the workspace. |
| `angular_version` | string | Angular CLI version that performed the scaffold. |
| `command` | string | The exact command line invoked. |

**Error behavior**: Non-zero exit / raised `ToolError`. Categories:

- `invalid_input` — `artifacts.angularWorkspace` already contains a non-empty workspace,
  or `project.name` is not a valid Angular workspace identifier.
- `missing_dependency` — required package manager binary is not on `PATH`.
- `external_tool_failed` — `ng new` exited non-zero.
- `output_invalid` — the scaffold completed but `angular.json` is missing.

**Allowed invocation context**: `build_app` (as the foundational TOOL
command before the `angular-workspace-foundation` SKILL session, when the workspace does not
yet exist); CLI (`django-admin ng_new`). Not invocable from a HOOK —
workspace creation must be an explicit command.

**Implementation reference**:
`django_angular3/management/commands/ng_new.py`;
`django_angular3/angular.py`.

#### 6. `angular_app_scaffold` — Angular application scaffold wrapper

**Name**: `angular_app_scaffold`

**Purpose**: Invoke the `ngdj add` / `ng_gen_app` schematic to add the primary
Angular application into an existing workspace. Wraps the existing
`ng_gen_app` djng management command. The wrapper forwards `--ssr`,
`--zoneless`, and `--defaults` to the `angular-django2:material-app` schematic so the
generated application matches the Angular CLI `ng new` defaults.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `dry_run` | no | boolean | `false` | When `true`, validate inputs and report the resolved command line without modifying the workspace. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `app_path` | string (path) | Absolute path to the generated Angular application directory inside the workspace. |
| `app_name` | string | Name of the Angular application produced. |
| `command` | string | The exact command line invoked. |

**Error behavior**: Non-zero exit / raised `ToolError`. Categories:

- `invalid_input` — `artifacts.angularWorkspace` does not contain an Angular workspace, or
  an application with the same name already exists.
- `missing_dependency` — `ngdj` schematic package not installed in the
  workspace.
- `external_tool_failed` — schematic invocation exited non-zero.
- `output_invalid` — the schematic completed but the expected app directory
  is missing.

**Allowed invocation context**: `build_app` (as a TOOL command between the
`angular-workspace-foundation` and `angular-app-composition` skill sessions, when the application does not yet
exist); CLI (`django-admin ng_gen_app`). Not invocable from a HOOK.

**Implementation reference**:
`django_angular3/management/commands/ng_gen_app.py`;
`django_angular3/management/commands/ng_add.py`.

#### 7. `ngdj_add_feature` — Angular feature page and route scaffold

**Name**: `ngdj_add_feature`

**Purpose**: Create a deterministic feature area beneath the selected Angular
application's `features/` directory, including an initial standalone page
component, a feature route definition, and registration in the application
route tree. This is a djng wrapper contract; the current ngdj collection does
not expose a separate `feature` schematic.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `name` | yes | string | — | Kebab-case feature name. |
| `path` | no | string (relative path) | `src/app/features` | Application-relative parent directory for the feature area. |
| `project` | no | string | inferred from `project.name` | Angular project to modify. Required when inference is ambiguous. |
| `page_name` | no | string | value of `name` | Kebab-case initial page component name. |
| `route_path` | no | string | value of `name` | URL path segment registered for the feature. |
| `register_route` | no | boolean | `true` | Add the feature route to the application route tree. |
| `dry_run` | no | boolean | `false` | When `true`, validate inputs and return resolved paths and invocations without modifying the workspace. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `feature_path` | string (path) | Absolute path of the created feature area. |
| `page_component_path` | string (path) | Absolute path of the initial page component source. |
| `feature_routes_path` | string (path) | Absolute path of the feature route definition. |
| `app_routes_path` | nullable string (path) | Application route file updated when `register_route` is `true`; otherwise `null`. |
| `generated_files` | array of string (path) | Files created by this invocation, relative to `feature_path`. |
| `commands` | array of string | Exact ngdj command lines invoked. |

**Error behavior**: Non-zero exit / raised `ToolError` with `category` in
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.
`invalid_input` includes non-kebab-case names, paths outside the selected
application source root, an existing feature area, invalid page or route names,
or a requested route registration without an application route tree.
`output_invalid` applies when generation completes without the expected page
component or feature route definition.

**Allowed invocation context**: `build_app` (as a TOOL command), agent
(inside a guided Skill session), CLI. Not a HOOK target.

**Implementation reference**: planned djng wrapper that composes the
`angular-django2:component` schematic, writes the feature route definition,
and performs a syntax-aware application-route registration. Its contract
remains stable even if ngdj later provides a dedicated feature schematic.

#### 8. `ngdj_add_component` — standalone component scaffold

**Name**: `ngdj_add_component`

**Purpose**: Generate a standalone OnPush Angular component with ngdj's
embedding hooks at a deterministic project-relative path.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `name` | yes | string | — | Kebab-case component name. |
| `path` | no | string (relative path) | Angular CLI default | Project-relative destination directory. |
| `project` | no | string | inferred from `project.name` | Angular project to modify. |
| `dry_run` | no | boolean | `false` | When `true`, validate inputs and return the resolved invocation without modifying the workspace. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `component_path` | string (path) | Absolute path of the generated component directory. |
| `component_class` | string | Generated component class name. |
| `selector` | string | Generated component selector. |
| `generated_files` | array of string (path) | Files created by this invocation, relative to `component_path`. |
| `command` | string | Exact `angular-django2:component` command line invoked. |

**Error behavior**: Non-zero exit / raised `ToolError` with `category` in
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.
`invalid_input` includes a non-kebab-case name or a path outside the selected
application source root. `output_invalid` applies when the invocation succeeds
but does not create the expected component source and template.

**Allowed invocation context**: `build_app` (as a TOOL command), agent
(inside a guided Skill session), CLI. Not a HOOK target.

**Implementation reference**: the existing `ng_component` CLI wrapper in
`django_angular3/angular.py` and
`django_angular3/management/commands/ng_component.py` resolves
`ng generate angular-django2:component <name> --path=<path> --project=<project>`.
The structured Tool behavior and outputs in this contract remain planned.

#### 9. `ngdj_run_schematic` — controlled ngdj schematic runner

**Name**: `ngdj_run_schematic`

**Purpose**: Execute one explicitly allowlisted `angular-django2` schematic
with structured options, returning the resulting file delta rather than raw
Angular CLI output.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `schematic` | yes | string | — | Allowlisted ngdj schematic name, without the `angular-django2:` prefix. |
| `options` | no | object | `{}` | JSON-shaped schematic options, validated against the selected schematic schema. |
| `project` | no | string | inferred from `project.name` | Angular project to modify when the selected schematic supports it. |
| `dry_run` | no | boolean | `false` | When `true`, validate and return the invocation without modifying the workspace. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `schematic` | string | Canonical executed collection name (`angular-django2:<name>`). |
| `generated_files` | array of string (path) | Files created, changed, or removed by the invocation, relative to the workspace. |
| `command` | string | Exact command line invoked. |
| `warnings` | array of string | Non-fatal schematic warnings. |

**Error behavior**: Non-zero exit / raised `ToolError` with `category` in
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.
`invalid_input` includes a schematic outside the djng-maintained allowlist or
options that fail its schema. The tool MUST NOT accept arbitrary collection
names or execute package downloads at runtime.

**Allowed invocation context**: `build_app` (as a TOOL command), agent
(inside a guided Skill session), CLI. Not a HOOK target.

**Implementation reference**: planned djng wrapper invoking the workspace-local
`pnpm exec ng generate angular-django2:<schematic>` command. The allowlist is
derived from the supported ngdj collection version and is verified by contract
tests.

#### 10. `oasdiff_changelog` — human-readable schema-change report

**Name**: `oasdiff_changelog`

**Purpose**: Generate a durable human-readable changelog from a previous and a
current OpenAPI artifact, using the same schema pair consumed by `oasdiff_diff`.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `current_schema` | yes | string (path) | — | Absolute path to the current OpenAPI artifact. |
| `previous_schema` | yes | string (path) | — | Absolute path to the previous OpenAPI artifact. |
| `output_path` | no | string (path) | `build/openapi-changelog.md` | Destination for the generated Markdown changelog. |
| `format` | no | `"markdown"` \| `"html"` | `"markdown"` | Changelog serialization format. |
| `dry_run` | no | boolean | `false` | When `true`, validate inputs and report the resolved destination without writing. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `changelog_path` | string (path) | Absolute path of the written changelog. |
| `format` | `"markdown"` \| `"html"` | Serialization format used. |
| `schema_changed` | boolean | Whether the schema pair contains any change. |
| `command` | string | Exact `oasdiff` command line invoked. |

**Error behavior**: Non-zero exit / raised `ToolError` with `category` in
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.
`output_invalid` applies when `oasdiff` exits successfully but the requested
changelog file is empty or cannot be parsed as the requested format.

**Allowed invocation context**: `build_app` (as a TOOL command after
`oasdiff_diff`), agent (read-only contract-review assistance), CLI. Not a HOOK
target.

**Implementation reference**: planned wrapper around the installed `oasdiff`
CLI changelog capability. It must use the existing `ensure_oasdiff()` binary
resolution and archive output under the configured build directory.

### Contract compliance

- `build_app` MUST select the matching **Name** value above when translating a
  deterministic operation into an executable command. Free-form `Bash`
  invocations of these capabilities outside the documented tool-contract
  mechanism are not permitted.
- HOOKS that need to perform any of the operations above MUST do so by
  invoking the corresponding tool contract — not by calling the underlying
  binary directly — so error categories and structured outputs remain uniform
  across automation primitives.
- New deterministic capabilities added to `djng` MUST be documented here using
  the [tool contract shape](#tool-contract-shape) before they may appear as a
  selected TOOL command.

[APP_BUILDER_REQUIREMENTS.md]: ../requirements/APP_BUILDER_REQUIREMENTS.md
[CHANGE_MODEL_CONTRACTS.md]: CHANGE_MODEL_CONTRACTS.md
[HOOK_CONTRACTS.md]: HOOK_CONTRACTS.md
[PLUGIN_CONTRACTS.md]: PLUGIN_CONTRACTS.md
[PROVIDER_ADAPTER_CONTRACTS.md]: PROVIDER_ADAPTER_CONTRACTS.md
[SKILL_CONTRACTS.md]: SKILL_CONTRACTS.md
