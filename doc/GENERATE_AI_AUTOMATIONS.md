Design the AI automation subsystem used by `djng` to build and maintain
Angular applications.

This document defines how `djng` uses four automation primitives together:

- **SKILLS** for AI-guided construction and integration work
- **TOOLS** for deterministic callable operations
- **HOOKS** for lifecycle enforcement and mandatory side effects
- **PLUGINS** for packaging and distributing coherent capability bundles

It also specifies the detailed SKILL catalog used for the AI-guided layer of
Angular construction and integration.

# Glossary

For authoritative definitions see `ARCHITECTURE.md` §2 and §19.

| Term | Definition | See |
|---|---|---|
| **AI automations** | The full automation model used by `djng`: SKILLS, TOOLS, HOOKS, and PLUGINS working together for bounded construction and integration. The subject of this document. | `TOOLS_HOOKS_SKILLS_ANALYSIS.md`, `ARCHITECTURE.md` |
| **`djng`** | The `django-angular3` solution — this repository, the Django package, and the tool. Contains the agent, the AI automation subsystem, `build_app`, and all configuration files. | `ARCHITECTURE.md` §2.5 |
| **`ngdj`** | The `angular-django2` companion Angular package. Provides the Angular-side schematics and templates invoked by the agent during construction. | `ARCHITECTURE.md` §2.6 |
| **`build_app`** | The `djng` Django management command. Entry point that drives the agent through the procedure graph. | `APP_BUILDER_REQUIREMENTS.md` |
| **the agent** | The agentic orchestrator bundled in `djng`. At implementation level, driven by the Claude Agent SDK. | `ARCHITECTURE.md` §2.16 |
| **SKILLS** | Bounded AI skills (`SKILL.md` files) bundled in `djng` that guide the agent within each guided agent session. One primitive family in the automation model defined here. | `ARCHITECTURE.md` §2.14 |
| **TOOLS** | Deterministic callable capabilities that expose bounded operations to the agent without requiring AI judgment inside the operation itself. | `TOOLS_HOOKS_SKILLS_ANALYSIS.md` |
| **HOOKS** | Deterministic lifecycle-triggered automations that enforce gates, logging, cleanup, and other mandatory side effects outside the agent context window. | `TOOLS_HOOKS_SKILLS_ANALYSIS.md` |
| **PLUGINS** | Packaging and distribution bundles that group coherent SKILLS, TOOLS, HOOKS, and related agent capabilities for reuse across projects or teams. | `TOOLS_HOOKS_SKILLS_ANALYSIS.md` |
| **guided agent session** | A single agent session in which the agent carries out one procedure, guided by the specified SKILL(s). | `ARCHITECTURE.md` §2.13 |

---

# AI Automation Architecture

This document defines the automation subsystem at four primitive levels. The
detailed item-by-item specifications in this file are currently most complete
for SKILLS, while TOOLS, HOOKS, and PLUGINS are defined here through
boundaries, selection policy, and architectural responsibilities.

## Primitive families

- **SKILLS** handle AI-guided generation, modification, and integration work
  that requires judgment, iteration, or code authoring.
- **TOOLS** handle deterministic commands, validations, file operations, and
  other bounded capabilities that the agent can call directly.
- **HOOKS** handle deterministic lifecycle enforcement points that must run
  regardless of agent choice.
- **PLUGINS** package coherent bundles of SKILLS, TOOLS, HOOKS, and related
  agent capabilities for reuse and distribution.

## Primitive-selection policy

Use the following policy when deciding which automation primitive to apply:

| If the work… | Use |
|---|---|
| Requires AI judgment, iteration, or multi-step code authoring | **SKILL** |
| Is a single deterministic command, API call, validation, or file operation | **TOOL** |
| Must always run at a lifecycle event regardless of agent choice | **HOOK** |
| Is a reusable bundle of capabilities intended for distribution | **PLUGIN** |
| Is deterministic and must be guaranteed at a lifecycle event | **HOOK** wrapping a **TOOL** |

This policy is distilled from `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` and is the
selection rule for the automation model described in this document.

## Tools

Use TOOLS for deterministic operations that do not require AI judgment. In the
`djng` architecture, this includes schema export, schema diff, contract
validation, Angular/client generation wrappers, and similar bounded
construction operations.

Per-capability tool contracts for the deterministic operations identified in
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` are defined in the
[Tool Contracts Catalog](#tool-contracts-catalog) below. Each contract follows
the same fixed shape — **name, inputs, outputs, error behavior, allowed
invocation context** — so the agent, the procedure-graph builder, and a future
MCP exposure layer all see the same surface.

### Tool contract shape

Every tool contract in this document **MUST** specify:

| Field | Meaning |
|---|---|
| **Name** | The stable identifier the agent uses to call the tool. Matches the `tool` field of a `tool` procedure node in the procedure graph (see `APP_BUILDER_REQUIREMENTS.md` §Procedure Graph). |
| **Purpose** | One-sentence statement of what the tool does. Must be deterministic — no AI judgment inside the operation. |
| **Inputs** | Typed table of input keys, required/optional status, type, default, and description. Inputs are passed as a single structured object. |
| **Outputs** | Typed table of output keys returned on success. Outputs are returned as a single structured object so the agent and downstream tools can read them without parsing free-form text. |
| **Error behavior** | The exit-code or exception contract on failure, the structured error fields returned, and the failure categories the caller must distinguish (e.g. `invalid_input`, `missing_dependency`, `external_tool_failed`, `output_invalid`). |
| **Allowed invocation context** | Which automation primitives are permitted to invoke this tool: `build_app` (as a `tool` procedure), `HOOK` (as the wrapped action of a lifecycle hook), agent (as a direct callable inside a guided agent session), or CLI (as a `django-admin` command). |
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
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §2 and from `APP_BUILDER_REQUIREMENTS.md`
§Change-to-Automations Mapping. Each entry follows the
[tool contract shape](#tool-contract-shape) defined above.

The contracts are grouped by lifecycle stage so the procedure-graph order is
visually obvious: **contract lifecycle** (export → validate → diff) precedes
**Angular generation wrappers** (`ng-openapi-gen`, `ngdj_*`).

### Contract lifecycle tools

#### 1. `export_schema` — schema extraction trigger

**Name**: `export_schema`

**Purpose**: Generate the current OpenAPI 3.1 schema from the configured DRF
project (via `drf-spectacular`) and persist it as a durable, versioned artifact
at the path declared by `openapi.source` in `django-angular3.json`. Rotates any
existing schema to its `.previous` counterpart before writing.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `config` | yes | string (path) | — | Absolute path to the `django-angular3.json` project config. |
| `format` | no | `"json"` \| `"yaml"` | `"json"` | Serialization format for the exported schema. |
| `dry_run` | no | boolean | `false` | When `true`, compute and report the destination and would-be-archived previous path, but do not modify disk. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `destination` | string (path) | Absolute path to the freshly written current schema (`openapi.source`). |
| `previous_path` | string (path) \| null | Absolute path of the archived previous schema if one existed before the run, otherwise `null`. |
| `format` | `"json"` \| `"yaml"` | Format the schema was rendered in. |
| `bytes_written` | integer | Size of the written schema artifact in bytes. Omitted on `dry_run`. |
| `schema_changed` | boolean | `true` if the new schema differs from the rotated previous, `false` if they are byte-identical, `null` when there was no previous schema. |

**Error behavior**: Non-zero exit (CLI) / raised `ToolError` (programmatic).
Returns a structured error object `{ category, message, details }` where
`category` is one of:

- `invalid_input` — config path missing, malformed JSON, or required keys
  absent.
- `missing_dependency` — `drf-spectacular` not installed.
- `external_tool_failed` — DRF schema generation raised an exception.
- `output_invalid` — generated bytes failed sanity checks (empty document,
  missing `openapi` key).

The destination file is **never** left in a partially written state: on any
failure after rotation, the rotation is reversed so the previous schema is
restored.

**Allowed invocation context**: `build_app` (as a `tool` procedure preceding
schema-derived skill sessions); HOOK (PostToolUse on `makemigrations`, per
`TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3.2); CLI
(`django-admin export_schema <config>`).

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
| `schema` | yes | string (path) | — | Absolute path to the OpenAPI artifact to validate (typically the output of `export_schema`). |
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
  the tool returns its structured report and exits zero. The procedure-graph
  caller (`build_app`) — or a PreToolUse hook — decides whether to halt.
- A non-zero exit / raised `ToolError` is reserved for `category` values:
  `invalid_input` (schema path missing or unreadable),
  `missing_dependency` (validator binary not installed),
  `external_tool_failed` (validator crashed),
  `output_invalid` (validator returned an unparseable report).

**Allowed invocation context**: `build_app` (as a `tool` procedure after
`export_schema` and before any generation procedure); HOOK (PreToolUse on
`ng_openapi_gen` and `ngdj_*` tools, per `TOOLS_HOOKS_SKILLS_ANALYSIS.md`
§3.5); agent (callable inside a guided agent session that needs to re-verify a
hand-edited schema). Not a user-facing CLI command in the current release.

**Implementation reference**: planned wrapper over an OpenAPI 3.1 validator
(e.g. `spectral lint`) invoked from `django_angular3/validation.py`. Contract
must be honoured regardless of the chosen backing validator.

#### 3. `oasdiff_diff` — schema diff and change detection

**Name**: `oasdiff_diff`

**Purpose**: Run `oasdiff` against the current and previous OpenAPI artifacts
and return a structured diff result that the procedure-graph builder consumes
to derive the `ChangeSet`. The agent does not parse raw `oasdiff` output.

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
| `breaking` | array of `{ resource, path, code, message }` | Breaking changes detected by `oasdiff`. Empty when no breaking changes. |
| `non_breaking` | array of `{ resource, path, code, message }` | Non-breaking changes detected. |
| `affected_resources` | array of string | Distinct resource names touched across both `breaking` and `non_breaking`. |
| `change_type` | `"no-change"` \| `"add-things"` \| `"remove-things"` \| `"replace-things"` \| `"breaking"` | Pre-classified change type matching the values defined in `APP_BUILDER_REQUIREMENTS.md` §Change Classification Summary. |
| `report_path` | string (path) | Where the raw `oasdiff` artifact was archived. |

**Error behavior**: Non-zero exit / raised `ToolError` with `category` in
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.
A successful `oasdiff` invocation that reports breaking changes is **not** an
error — it returns the populated `breaking` array with exit zero. The
breaking-change gate (HOOK or `build_app`) interprets the structured output.

**Allowed invocation context**: `build_app` (as the `tool` procedure feeding
the `ChangeSet`); HOOK (wrapped by the PreToolUse breaking-change gate from
`TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3.1); agent (read-only diagnostic use inside
a guided agent session that needs to re-inspect a diff).

**Implementation reference**: `django_angular3/tools.py:ensure_oasdiff()` for
binary acquisition; planned `django_angular3.diff` wrapper that calls
`oasdiff` with the contract above and post-processes its JSON output.

### Angular generation wrapper tools

#### 4. `ng_openapi_gen` — typed Angular client generation

**Name**: `ng_openapi_gen`

**Purpose**: Run `ng-openapi-gen` against the current OpenAPI artifact inside
the generated Angular workspace to produce typed Angular API clients. Wraps
the existing `ng_openapi_gen` djng management command so the agent and
procedure graph see a structured tool contract instead of raw CLI output.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `config` | yes | string (path) | — | Absolute path to the `django-angular3.json` project config. The schema location and `angular.output` workspace are read from this file. |
| `schema` | no | string (path) | value of `openapi.source` from `config` | Override path to the OpenAPI artifact to consume. |
| `generator_config` | no | string (path) | derived from `config` | Override path to the `ng-openapi-gen` configuration JSON. |
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

**Allowed invocation context**: `build_app` (as a `tool` procedure invoked
after `validate_openapi_schema` and before the `ng-api` skill session); agent
(inside the `ng-api` guided agent session when the SKILL needs to regenerate
the client during refinement). Not a HOOK target — generation is always
explicit. CLI (`django-admin ng_openapi_gen <config>`).

**Implementation reference**:
`django_angular3/management/commands/ng_openapi_gen.py`;
`django_angular3/angular.py`.

#### 5. `ngdj_create_workspace` — Angular workspace scaffold wrapper

**Name**: `ngdj_create_workspace`

**Purpose**: Invoke the `ngdj` Angular workspace schematic to scaffold a fresh
workspace at `angular.output`. Wraps the existing `ng_new` djng management
command behind the structured tool contract used by the procedure graph.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `config` | yes | string (path) | — | Absolute path to the `django-angular3.json` project config. `angular.output`, `project.name`, and the `angular.workspace.*` keys are read from this file. |
| `dry_run` | no | boolean | `false` | When `true`, compute and report the planned command line but do not create the workspace. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `workspace_path` | string (path) | Absolute path to the created workspace root. |
| `package_manager` | `"npm"` \| `"yarn"` \| `"pnpm"` | Package manager configured for the workspace. |
| `angular_version` | string | Angular CLI version that performed the scaffold. |
| `command` | string | The exact command line invoked. |

**Error behavior**: Non-zero exit / raised `ToolError`. Categories:

- `invalid_input` — `angular.output` already contains a non-empty workspace,
  or `project.name` is not a valid Angular workspace identifier.
- `missing_dependency` — required package manager binary is not on `PATH`.
- `external_tool_failed` — `ng new` exited non-zero.
- `output_invalid` — the scaffold completed but `angular.json` is missing.

**Allowed invocation context**: `build_app` (as the foundational `tool`
procedure before the `ng-workspace` skill session, when the workspace does not
yet exist); CLI (`django-admin ng_new <config>`). Not invocable from a HOOK —
workspace creation must be an explicit graph node.

**Implementation reference**:
`django_angular3/management/commands/ng_new.py`;
`django_angular3/angular.py`.

#### 6. `ngdj_create_app` — Angular application scaffold wrapper

**Name**: `ngdj_create_app`

**Purpose**: Invoke the `ngdj add` / `ng_gen_app` schematic to add the primary
Angular application into an existing workspace. Wraps the existing
`ng_gen_app` djng management command.

**Inputs**:

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `config` | yes | string (path) | — | Absolute path to the `django-angular3.json` project config. `app.name`, `angular.output`, and the `angular.app.*` keys are read from this file. |
| `dry_run` | no | boolean | `false` | When `true`, compute and report the planned command line but do not modify the workspace. |

**Outputs**:

| Key | Type | Description |
|---|---|---|
| `app_path` | string (path) | Absolute path to the generated Angular application directory inside the workspace. |
| `app_name` | string | Name of the Angular application produced. |
| `command` | string | The exact command line invoked. |

**Error behavior**: Non-zero exit / raised `ToolError`. Categories:

- `invalid_input` — `angular.output` does not contain an Angular workspace, or
  an application with the same name already exists.
- `missing_dependency` — `ngdj` schematic package not installed in the
  workspace.
- `external_tool_failed` — schematic invocation exited non-zero.
- `output_invalid` — the schematic completed but the expected app directory
  is missing.

**Allowed invocation context**: `build_app` (as a `tool` procedure between the
`ng-workspace` and `ng-app` skill sessions, when the application does not yet
exist); CLI (`django-admin ng_gen_app <config>`). Not invocable from a HOOK.

**Implementation reference**:
`django_angular3/management/commands/ng_gen_app.py`;
`django_angular3/management/commands/ng_add.py`.

### Contract compliance

- The procedure-graph builder in `build_app` MUST emit a `tool` node whose
  `tool` field equals one of the **Name** values above when scheduling a
  deterministic operation. Free-form `Bash` invocations of these capabilities
  outside the `tool` node mechanism are not permitted.
- HOOKS that need to perform any of the operations above MUST do so by
  invoking the corresponding tool contract — not by calling the underlying
  binary directly — so error categories and structured outputs remain uniform
  across automation primitives.
- New deterministic capabilities added to `djng` MUST be documented here using
  the [tool contract shape](#tool-contract-shape) before they may appear as a
  `tool` procedure in the graph.

## Hooks

Use HOOKS for deterministic lifecycle enforcement points that must run whether
or not the agent would choose to do so. In the `djng` architecture, this
includes breaking-change gates, migration-triggered schema export,
pre-construction contract validation, post-generation verification logging, and
session-stop cleanup and audit behavior.

Per-capability hook contracts for the lifecycle enforcement points identified
in `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3 are defined in the
[Hook Contracts Catalog](#hook-contracts-catalog) below. Each contract follows
the same fixed shape — **name, purpose, trigger event, deterministic action,
failure behavior, allowed wrapped tools, implementation reference** — so the
procedure-graph builder, the `build_app` traversal, and a future Claude Code
`settings.json` exposure layer all see the same surface.

### Hook contract shape

Every hook contract in this document **MUST** specify:

| Field | Meaning |
|---|---|
| **Name** | The stable identifier the hook is registered under. Matches the `hook` field of a `gate` (or equivalent enforced-boundary) procedure node in the procedure graph, and the script/handler key in a Claude Code `settings.json` lifecycle event. |
| **Purpose** | One-sentence statement of the lifecycle enforcement the hook guarantees. Must be deterministic — no AI judgment inside the hook itself. |
| **Trigger event** | The lifecycle event that fires the hook. One of the Claude Code events (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`) and, when applicable, the specific tool name(s) it is scoped to. Tool names referenced here MUST match a contract in the [Tool Contracts Catalog](#tool-contracts-catalog) or an explicitly-named external command. |
| **Deterministic action** | Step-by-step description of what the hook does on the trigger event. The action must be reproducible — same inputs always produce the same outcome and side effects. When the hook performs a deterministic operation that already has a tool contract above, it MUST invoke that contract by name rather than calling the underlying binary directly. |
| **Failure behavior** | What the hook does when its check fails or its action errors. MUST specify: the exit code returned (zero = allow, non-zero = block for `Pre*` hooks; non-zero = log for `Post*`/`Stop` hooks), the structured message written to stderr or to the durable artifact log, and whether the hook's failure halts the agent session, blocks the wrapped tool, or only records an audit entry. |
| **Allowed wrapped tools** | The tool contract names (from the [Tool Contracts Catalog](#tool-contracts-catalog)) or external commands the hook may scope itself to. Hooks MUST NOT silently apply themselves to tools outside this list. |
| **Implementation reference** | Pointer to the concrete script or planned implementation that backs the contract, so the contract and the implementation can be kept aligned. |

Contracts are normative. An implementation that deviates from a documented
contract is a bug in the implementation, not in the contract.

#### Shape rationale

The seven fields are derived directly from the Claude Code hooks execution
model (see [Hooks reference — Claude Code docs](https://docs.anthropic.com/en/docs/claude-code/hooks)):

- **Name** and **Trigger event** map one-to-one onto Claude Code's
  `settings.json` hook registration. Each entry under a lifecycle event key
  (`PreToolUse`, `PostToolUse`, `Stop`) requires a stable identifier and an
  explicit event-plus-matcher declaration. Separating the *name* (the catalog
  key used in `gate` nodes and `settings.json` keys) from the *trigger event*
  (the runtime event that fires it) lets multiple hooks share the same event
  without name collision and lets the catalog be queried by either dimension.
- **Purpose** is required so that consumers of the catalog — the
  procedure-graph builder, `build_app` reviewers, and future plugin authors —
  can verify at a glance what invariant a hook enforces without reading the
  implementation. It also makes the *deterministic* constraint explicit: a
  one-sentence purpose that requires AI judgment signals a misclassification
  (the capability belongs in a SKILL, not a HOOK).
- **Deterministic action** and **Allowed wrapped tools** constrain the hook's
  blast radius together. The action describes *what* the hook does step by
  step; the allowed-tools list declares *which tools* the hook may scope itself
  to via Claude Code's `matcher` field. Both fields are needed to validate a
  hook against its contract without executing it, and to detect if an
  implementation silently broadens its matcher beyond the catalogued boundary.
- **Failure behavior** captures Claude Code's exit-code protocol: `Pre*` hooks
  use exit code `2` to block the wrapped tool (Claude Code surfaces the stderr
  message as the block reason and does not invoke the tool); `Post*` hooks that
  exit non-zero record a structured error but cannot undo the already-completed
  tool action; `Stop` hooks that exit non-zero may warn but must not abort the
  session abruptly. Documenting exit codes, message destinations, and
  halt-vs-warn semantics per hook prevents each implementer from inventing
  their own convention and enables automated compliance checks.
- **Implementation reference** links the normative contract to the concrete
  backing artifact (script path, planned ticket, or external CLI) so that drift
  between the spec and the code is detectable during review. Without this
  field, a contract can become unanchored documentation with no path back to
  the running system.

## Hook Contracts Catalog

This catalog defines the lifecycle hook contracts referenced from
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3 and from `APP_BUILDER_REQUIREMENTS.md`
§Change-to-Automations Mapping. Each entry follows the
[hook contract shape](#hook-contract-shape) defined above.

The contracts are grouped by when they fire relative to the procedure graph:
**pre-construction gates** fire before generation procedures; **mid-run
triggers** fire on backend events that invalidate prior artifacts;
**post-generation enforcement** fires after each generation tool; **session
lifecycle** fires when the agent session ends.

### Pre-construction gates

#### 1. `pre-construction` — contract validation gate

**Name**: `pre-construction`

**Purpose**: Guarantee that the OpenAPI schema artifact exists, is valid
OAS 3.1, and is at least as fresh as the latest Django migration before any
Angular generation tool is allowed to run. Implements the gate described in
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3.5.

**Trigger event**: `PreToolUse` scoped to the Angular generation tools
`ng_openapi_gen`, `ngdj_create_workspace`, `ngdj_create_app` (and any future
`ngdj_*` tool contract). Also runs as the very first `gate` procedure of every
`build_app` invocation, before the procedure-graph traversal reaches any
generation procedure.

**Deterministic action**:

1. Read `openapi.source` from `django-angular3.json`.
2. Assert the schema file exists and its modification timestamp is greater
   than or equal to the newest migration file under the configured Django
   apps' `migrations/` directories.
3. Invoke the `validate_openapi_schema` tool contract with the schema path.
4. If `valid: true`, allow the wrapped tool to run (exit 0).

**Failure behavior**:

- If the schema file is missing, stale, or `validate_openapi_schema` returns
  `valid: false`, write a structured error
  `{ hook: "pre-construction", category, message, schema_path, ... }` to
  stderr **and** to `build/hook-log.jsonl`, and exit non-zero.
- A non-zero exit blocks the wrapped tool invocation and halts the
  `build_app` run with the dedicated hook-failure exit code (distinct from
  both `breaking-change` block and from FR-9 tool-failure exit codes).
- The hook MUST NOT attempt to auto-repair (e.g. it does not invoke
  `export_schema` itself); auto-extraction is the responsibility of the
  `migration-triggered` hook.

**Allowed wrapped tools**: `ng_openapi_gen`, `ngdj_create_workspace`,
`ngdj_create_app`, future `ngdj_*` generation tools.

**Implementation reference**: planned shell script
`hooks/pre-construction.sh`, registered under the `PreToolUse` key of the
project's Claude Code `settings.json`. Wraps `validate_openapi_schema` via
its tool contract.

### Mid-run triggers

#### 2. `migration-triggered` — OpenAPI schema re-extraction

**Name**: `migration-triggered`

**Purpose**: Guarantee that whenever a new Django migration file is produced,
the OpenAPI schema artifact is re-exported so downstream construction always
sees a contract that matches the current data model. Implements the trigger
described in `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3.2.

**Trigger event**: `PostToolUse` scoped to any tool invocation that runs
`python manage.py makemigrations` (e.g. a `bash` tool call detected by the
`makemigrations` substring in its command), and a filesystem watch hook on
the configured Django apps' `migrations/` directories for non-tool migration
file creation.

**Deterministic action**:

1. Enumerate the migration files added or modified during the wrapped tool
   call (`git status --porcelain` against `migrations/` is sufficient since
   the workspace is git-controlled per `ARCHITECTURE.md`).
2. If the set is non-empty, invoke the `export_schema` tool contract with
   the project's `django-angular3.json` config path.
3. Append a `{ hook: "migration-triggered", migrations: [...], destination,
   previous_path, schema_changed }` record to `build/hook-log.jsonl`.
4. Exit 0 regardless of `schema_changed`; downstream `breaking-change` and
   `pre-construction` hooks will act on the rotated schema.

**Failure behavior**:

- If `export_schema` returns a non-success error object, write
  `{ hook: "migration-triggered", category, message, details }` to stderr
  and to `build/hook-log.jsonl`, and exit non-zero.
- A non-zero exit does **not** roll back the `makemigrations` result (the
  migration files remain on disk) but does halt the agent session so the
  human operator can repair the schema-extraction failure before any
  Angular generation proceeds.

**Allowed wrapped tools**: any tool invocation that calls
`manage.py makemigrations`. The hook MUST NOT fire for unrelated tool calls.

**Implementation reference**: planned shell script
`hooks/migration-triggered.sh`, registered under the `PostToolUse` key of
the project's Claude Code `settings.json`. Wraps `export_schema` via its
tool contract.

#### 3. `breaking-change` — gate on schema diff

**Name**: `breaking-change`

**Purpose**: Block any downstream Angular generation as soon as `oasdiff_diff`
reports breaking changes, unless the run was started with
`--acknowledge-breaking`. Implements the gate described in
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3.1 and the FR-4 builder behavior in
`doc/APP_BUILDER_REQUIREMENTS.md`.

**Trigger event**: `PreToolUse` scoped to `ng_openapi_gen` and any
`ngdj_*` generation tool. Also runs as the `gate` procedure that consumes
the structured output of the `oasdiff_diff` `tool` procedure in the
procedure graph.

**Deterministic action**:

1. Read the most recent `oasdiff_diff` tool output (a structured
   `{ breaking: [], non_breaking: [], schema_changed: bool }` object) from
   the run's durable artifact location (`build/oasdiff-report.json`).
2. If `breaking` is empty, exit 0 (allow the wrapped tool).
3. If `breaking` is non-empty and the run carries an
   `acknowledge_breaking: true` flag (set via `--acknowledge-breaking`),
   write an audit entry
   `{ hook: "breaking-change", decision: "acknowledged", breaking: [...] }`
   to `build/hook-log.jsonl` and exit 0.
4. Otherwise, write a structured error
   `{ hook: "breaking-change", category: "breaking_changes_unacknowledged",
   breaking: [...] }` to stderr and to `build/hook-log.jsonl`, and exit
   non-zero with the dedicated breaking-change exit code defined in
   `APP_BUILDER_REQUIREMENTS.md` FR-4.

**Failure behavior**:

- A non-zero exit blocks the wrapped tool and halts the `build_app` run.
- The hook MUST surface the exact `breaking` array so the operator can
  decide whether to re-run with `--acknowledge-breaking` or revise the
  backend contract.
- The hook MUST NOT consume `oasdiff` raw CLI output directly; it consumes
  only the structured contract output of `oasdiff_diff`.

**Allowed wrapped tools**: `ng_openapi_gen`, `ngdj_create_workspace`,
`ngdj_create_app`, future `ngdj_*` generation tools.

**Implementation reference**: planned shell script
`hooks/breaking-change.sh`, registered under the `PreToolUse` key of the
project's Claude Code `settings.json`. Consumes `oasdiff_diff` tool output.

### Post-generation enforcement

#### 4. `post-generation` — verification logging

**Name**: `post-generation`

**Purpose**: Guarantee that every Angular generation tool invocation is
followed by a deterministic structural check whose pass/fail result is
recorded to a machine-readable log, regardless of whether the agent would
choose to re-inspect the output. Implements the enforcement described in
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3.3.

**Trigger event**: `PostToolUse` scoped to `ng_openapi_gen`,
`ngdj_create_workspace`, `ngdj_create_app`, and any future `ngdj_*`
generation tool contract.

**Deterministic action**:

1. Read the wrapped tool's structured output (e.g. the `generated_files`
   array returned by `ng_openapi_gen`) from the run's artifact location.
2. Run a lightweight structural check appropriate to the wrapped tool:
   - For `ng_openapi_gen`: `tsc --noEmit` in the generated app workspace
     (`angular.output`).
   - For `ngdj_create_workspace` / `ngdj_create_app`: assert the expected
     workspace/app directories and files exist on disk.
3. Append a verification entry
   `{ hook: "post-generation", tool, pass: bool, details, generated_files,
   timestamp }` to `build/verification.log`.

**Failure behavior**:

- If the structural check fails, write the verification entry with
  `pass: false` and exit non-zero. A non-zero exit halts the `build_app`
  run via the dedicated hook-failure exit code so the failure cannot be
  silently swallowed by the agent loop.
- The hook MUST always write the log entry even on success, so the audit
  trail is complete.
- The hook MUST NOT modify or "fix" the generated artifacts; repair is the
  responsibility of a subsequent guided agent session per
  `ARCHITECTURE.md` §7.2.

**Allowed wrapped tools**: `ng_openapi_gen`, `ngdj_create_workspace`,
`ngdj_create_app`, future `ngdj_*` generation tools.

**Implementation reference**: planned shell script
`hooks/post-generation.sh`, registered under the `PostToolUse` key of the
project's Claude Code `settings.json`.

### Session lifecycle

#### 5. `session-stop` — archiving and audit cleanup

**Name**: `session-stop`

**Purpose**: Guarantee that, whenever a `build_app`-driven agent session
ends — successfully, by user interrupt, or by error — the run's durable
artifacts are archived and a session summary is recorded. Implements the
cleanup described in `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §3.4.

**Trigger event**: `Stop`. Fires exactly once per agent session,
unconditionally.

**Deterministic action**:

1. Compute a session timestamp `YYYYMMDDTHHMMSSZ`.
2. Move (not copy) `build/procedure-graph.*`, `build/oasdiff-report.json`,
   `build/verification.log`, and `build/hook-log.jsonl` into
   `build/history/<timestamp>/`. Missing artifacts are silently skipped.
3. Write a session summary
   `{ hook: "session-stop", timestamp, schema_version, procedures_completed,
   procedures_failed, hook_failures, exit_code }` to
   `build/session-log.json` (append to the JSON array on disk).
4. Exit 0.

**Failure behavior**:

- A `Stop` hook cannot block the session from ending; failure is recorded
  only.
- If archiving fails (e.g. disk full, permission error), write
  `{ hook: "session-stop", category, message, details }` to stderr and to
  whatever portion of `build/session-log.json` is still writable, then
  exit non-zero. The non-zero exit code is surfaced by Claude Code as a
  post-session warning but does not retroactively change the session
  outcome.
- The hook MUST be idempotent: re-running it after a partial failure must
  not duplicate archived artifacts or session summary entries.

**Allowed wrapped tools**: not applicable — `Stop` is not scoped to a tool.

**Implementation reference**: planned shell script `hooks/session-stop.sh`,
registered under the `Stop` key of the project's Claude Code
`settings.json`.

### Contract compliance

- The procedure-graph builder in `build_app` MUST emit a `gate` (or
  equivalent enforced-boundary) node whose `hook` field equals one of the
  **Name** values above when scheduling a lifecycle enforcement procedure.
  Ad-hoc `Bash` invocations of the actions above outside the hook/gate
  mechanism are not permitted.
- HOOKS that need to perform a deterministic operation also covered by the
  [Tool Contracts Catalog](#tool-contracts-catalog) MUST do so by invoking
  the corresponding tool contract — not by calling the underlying binary
  directly — so error categories and structured outputs remain uniform.
- New lifecycle enforcement points added to `djng` MUST be documented here
  using the [hook contract shape](#hook-contract-shape) before they may
  appear as a `gate` procedure in the graph or be registered in any
  project's Claude Code `settings.json`.

## Plugins

Use PLUGINS to package coherent bundles of SKILLS, TOOLS, and HOOKS for reuse
or distribution. In the `djng` architecture, candidate bundles include the
djng Angular construction capability, the ngdj scaffold capability, and the
contract lifecycle capability.

## Skills

The formal skill format used here is defined by Anthropic — see `ARCHITECTURE.md` §20: [Claude Skills] (conceptual overview), [Claude Code Skills] (CLI-side reference: extended frontmatter, invocation control, dynamic context injection), and [Claude Agent SDK Skills] (SDK-side discovery and invocation). This section describes the project-specific application of that format; for the authoritative skill-format reference, consult the upstream documents.

All skill specifications in this document follow the **Agent Skills** format — reusable capabilities invoked explicitly by `build_app` via the Claude Agent SDK `query(skills=[...])` option, or by users via `/<skill-name>` in the Claude Code CLI.

### Directory Structure

Each skill lives in its own directory under `.claude/skills/`:

```
.claude/skills/<skill-name>/
  SKILL.md          # Main skill specification with YAML frontmatter
  context/          # Optional context files loaded at instruction level
  templates/        # Optional template files for code generation
  examples/         # Optional example files demonstrating usage
```

### YAML Frontmatter

Every `SKILL.md` file begins with YAML frontmatter that defines skill metadata:

```yaml
---
name: <skill-name>
description: <capability statement, third person, no I/you>
when_to_use: <"Use when build_app dispatches X, or when a user runs /<skill-name> to do Y">
user-invocable: false
context: fork
agent: <subagent type if context: fork is set; usually general-purpose, Explore, or Plan>
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

**Dual-mode requirement.** These skills are used both by direct CLI invocation (a user types `/<skill-name>` in Claude Code) and by `build_app` via the Claude Agent SDK (`query(skills=[...], allowedTools=[...])`). The `allowed-tools` frontmatter field is honored by the CLI but **not** by the SDK — `build_app` must mirror the same tool list in its `query()` `allowedTools` option. The canonical tool list per skill in this document is the source of truth for both surfaces. See `ARCHITECTURE.md` §2.14 references to [Claude Code Skills] and [Claude Agent SDK Skills] for the authoritative field reference.

#### Field Definitions

- **`name`**: Unique identifier for the skill (matches directory name)
- **`description`**: Brief description used by outer agent for skill matching and invocation
- **`user-invocable`**: Always `false` for these skills — invoked by outer agent, not by users directly
- **`context`**: Always `fork` — each skill execution runs in an isolated context
- **`allowed-tools`**: List of Claude Code tools the skill is permitted to use during execution

### Skill loading model

At session start, the skill loader preloads only the YAML frontmatter (`name`, `description`, `when_to_use`) of every discovered SKILL.md into the model's context. When a skill is invoked — by the user typing `/<name>` in CLI mode, or by `build_app` selecting it via `query(skills=[...])` in SDK mode — the SKILL.md body loads. Supporting files (shared references, templates, scripts) live on the filesystem and are read by Claude on demand via the Read tool when SKILL.md links to them. Scripts are executed via Bash; their source is never loaded as context.

**Token strategy.** Keep SKILL.md body under ~500 lines (per [Claude Skills Best Practices]). Move detailed reference material into separate files in the same skill directory and link to them. Files that Claude does not need to read incur no token cost.

### Progressive disclosure of supporting files

Per the formal skill format ([Claude Code Skills], [Claude Agent SDK Skills]), SKILL.md preloads only its YAML frontmatter (`name`, `description`, optionally `when_to_use`) into the session at startup. The body of SKILL.md loads when the skill is invoked. Supporting files (shared references, templates, scripts) live on the filesystem and are read on demand by Claude via the Read tool when SKILL.md links to them. Scripts in `scripts/` are executed via Bash; their source is never loaded as context.

#### Referencing supporting files

Use standard markdown links from SKILL.md to point at supporting files. Keep references one level deep so Claude reads them in full (deeply nested references can lead to partial reads):

```markdown
## Conventions
See [angular-conventions.md](../shared/angular-conventions.md) — read this before scaffolding.

## Templates
Use the template at `templates/component.ts.tpl` — read and adapt for the output file.
```

#### Dynamic context injection (CLI only)

For dynamic context injected at load time, the Claude Code CLI supports shell-command interpolation via the `` !`<command>` `` syntax. The Claude Agent SDK does not perform this preprocessing — under SDK invocation, Claude must use the Bash tool explicitly when shell output is needed inline.

### Invocation Model

Within the broader automation model, SKILLS are used by the agent within
guided agent sessions, not invoked by users directly:

1. **Procedure graph construction**: `build_app` derives a procedure graph from
   schema and config changes. Each node specifies which SKILL(s) apply and what
   inputs to provide.
2. **Guided agent session**: For each procedure node, `build_app` makes a Claude
   Agent SDK `query()` call with the relevant SKILL(s) enabled and the procedure
   inputs as the prompt. The agent carries out the construction work, using the
   SKILL's knowledge to guide its actions — invoking ngdj schematics, reading
   and writing files, and verifying results.
3. **Next procedure**: `build_app` proceeds to the next procedure node in
   dependency order until all procedures are complete.

**Key Principle**: SKILLS are composable knowledge units within the broader
automation model. Multiple SKILLS may be enabled for a single guided agent
session when a procedure composes capabilities from several skills.

**Implementation note**: Higher-level documents (`APP_BUILDER_REQUIREMENTS.md`,
`ARCHITECTURE.md`) use the abstract term "Claude Agent SDK call" to describe a
guided agent session. In the Claude Agent SDK, this is implemented as a `query()`
call. This document uses `query()` to refer to that concrete function.

### Canonical SKILL.md Template Structure

Every `SKILL.md` file follows this structure:

```markdown
---
name: <skill-name>
description: <capability statement, third person, no I/you>
when_to_use: <"Use when build_app dispatches X, or when a user runs /<skill-name> to do Y">
user-invocable: false
context: fork
agent: <subagent type>
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# <Skill Display Name>

## Purpose

Brief statement of what this skill does and when to use it.

## Modes

All skills support three operational modes:

### Create
Generate the artifact from scratch when it doesn't exist.

**Input Requirements**:
- List required inputs for creation

**Process**:
1. Step-by-step creation process
2. Including validation
3. And error handling

**Output**:
- Description of created artifacts

### Modify
Update an existing artifact with changes.

**Input Requirements**:
- List required inputs for modification

**Process**:
1. Step-by-step modification process
2. Including validation
3. And error handling

**Output**:
- Description of modified artifacts

### Delete
Remove the artifact completely.

**Input Requirements**:
- List required inputs for deletion

**Process**:
1. Step-by-step deletion process
2. Including cleanup
3. And verification

**Output**:
- Confirmation of deletion

## Context Files

- See [shared-context-file.md](../shared/shared-context-file.md) — replace with the actual filename when this skill needs the shared content.

## Templates

- `templates/template-name.ts` — description of template purpose
- `templates/another-template.html` — description of template purpose

## Validation

Steps to validate successful execution of the skill.

## Error Handling

Common errors and their resolution strategies.

## Dependencies

List any skills that must be executed before this skill (e.g., workspace must exist before creating an app).

## Examples

Brief examples demonstrating typical usage patterns.
```

This canonical structure ensures consistency across all 11 skills and provides clear guidance for both outer agent invocation and skill implementation.

# Skill Shared Context Files

Shared context files are reference documents stored in `.claude/skills/shared/`
that multiple skills read on demand. They eliminate duplication by
centralising conventions, patterns, and integration rules that apply across
many skills in the skill layer of the broader automation model.

Each skill references a shared file using a standard markdown link with a one-level-up relative path. From inside a skill directory at `.claude/skills/<skill-name>/SKILL.md`:

```markdown
See [angular-conventions.md](../shared/angular-conventions.md) — when this skill needs shared Angular conventions.
```

## `angular-conventions.md`

**Path**: `.claude/skills/shared/angular-conventions.md`

**Contents**:

- **Standalone components**: All components use `standalone: true`; no NgModules are generated. Imports are declared directly in the component decorator.
- **Signals**: State management uses Angular signals (`signal()`, `computed()`, `effect()`). Avoid `BehaviorSubject` and `Observable`-based state where signals suffice.
- **SCSS & Material theming**: Component stylesheets use `.scss`. Global theme tokens (palette, typography, density) are defined once in the workspace theme file and consumed via `mat.get-theme-color()` / `mat.get-theme-typography()` mixins.
- **Naming conventions**: Files follow `<name>.<type>.ts` (e.g., `user-list.component.ts`). Classes follow PascalCase (e.g., `UserListComponent`). Selectors follow `app-<name>` (e.g., `app-user-list`).
- **Imports**: Use Angular's `inject()` function for dependency injection. Barrel files (`index.ts`) are generated for each feature directory.
- **Testing patterns**: Unit tests use Jest with Angular Testing Library. Each component test file follows `<name>.component.spec.ts`. Services use `TestBed` with `HttpClientTestingModule` for HTTP dependencies.

**Referenced by**:
- Angular Material app boiler plate
- Angular Material small field level component generation
- Angular Material form field generation
- Angular component generation
- Angular Material complex component generation
- Angular Material reactive form generation
- Angular Material page generation
- Angular Material site generation

## `angular-material-patterns.md`

**Path**: `.claude/skills/shared/angular-material-patterns.md`

**Contents**:

- **MatTable page**: Standard data-table layout using `<mat-table>`, `MatPaginatorModule`, `MatSortModule`, and a `MatProgressSpinnerModule` loading overlay. Data source is a `MatTableDataSource` bound to a signal-based service.
- **MatCard form**: Form contained within a `<mat-card>` with `<mat-card-header>`, `<mat-card-content>`, and `<mat-card-actions>`. Uses `ReactiveFormsModule` with `FormBuilder`.
- **MatSidenav shell**: Application shell with `<mat-sidenav-container>`, a collapsible `<mat-sidenav>` for navigation, and `<mat-sidenav-content>` for the router outlet.
- **Dialog pattern**: Dialogs are opened via `MatDialog.open()`, receive data through `MAT_DIALOG_DATA`, and return results via `MatDialogRef.close()`.
- **Snackbar pattern**: User feedback is delivered through `MatSnackBar.open()` with a duration of 3000 ms and a dismiss action.

**Referenced by**:
- Angular Material app boiler plate
- Angular Material small field level component generation
- Angular Material form field generation
- Angular Material complex component generation
- Angular Material reactive form generation
- Angular Material page generation
- Angular Material site generation

## `openapi-integration.md`

**Path**: `.claude/skills/shared/openapi-integration.md`

**Contents**:

- **oasdiff — schema diff and change detection**: `oasdiff` is run by `build_app` during the Change Derivation phase, before any skill is invoked. Skills receive the resulting `ChangeSet` as procedure input (see `APP_BUILDER_REQUIREMENTS.md` §"Change Derivation"). Skills must **not** re-run `oasdiff`.
- **ng-openapi-gen output paths**: Generated files are placed in `src/app/api/` by default. The output directory is configured in `ng-openapi-gen.json` at the workspace root.
- **Service naming**: Each OpenAPI tag produces one Angular service named `<Tag>ApiService` (e.g., tag `Users` → `UsersApiService`). Import from `src/app/api/services/<tag>-api.service.ts`.
- **Import patterns**: Models are imported from `src/app/api/models/<model-name>.ts`. The barrel export at `src/app/api/models.ts` re-exports all models.
- **Do-not-edit rule**: All files inside `src/app/api/` are auto-generated and **must not be edited manually**. Re-run `ng-openapi-gen` to regenerate after schema changes.

**Referenced by**:
- Angular API generation
- Angular data model Service
- Angular Material complex component generation
- Angular Material page generation
- Angular Material site generation

# Skill Templates

Template files are reusable Angular code scaffolds stored in `.claude/skills/<skill-name>/templates/` that skills reference during code generation. Each template provides a complete, working example following the conventions defined in the Shared Context Files section.

Skills reference these templates by relative path. Claude reads the file via the Read tool when the skill instructs it to use the scaffold:

```markdown
Use the template at `templates/component.ts.tpl` — read and adapt for the output file.
```

## Template 1: Standalone Component (`.ts` + `.html` + `.scss`)

**Files**: `component.ts.tpl`, `component.html.tpl`, `component.scss.tpl`

**Used by**:
- Angular Material small field level component generation (skill 5)
- Angular Material form field generation (skill 6)
- Angular component generation (skill 7)
- Angular Material complex component generation (skill 8)

### `component.ts.tpl`

```typescript
import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-{{COMPONENT_NAME_KEBAB}}',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
  ],
  templateUrl: './{{COMPONENT_NAME_KEBAB}}.component.html',
  styleUrl: './{{COMPONENT_NAME_KEBAB}}.component.scss'
})
export class {{COMPONENT_NAME_PASCAL}}Component {
  // Input signals
  title = input<string>('');
  data = input<any>(null);

  // Output signals
  itemClicked = output<void>();

  handleClick(): void {
    this.itemClicked.emit();
  }
}
```

### `component.html.tpl`

```html
<mat-card>
  <mat-card-header>
    <mat-card-title>{{ title() }}</mat-card-title>
  </mat-card-header>

  <mat-card-content>
    @if (data()) {
      <p>{{ data() }}</p>
    } @else {
      <p>No data available</p>
    }
  </mat-card-content>

  <mat-card-actions>
    <button mat-raised-button color="primary" (click)="handleClick()">
      Action
    </button>
  </mat-card-actions>
</mat-card>
```

### `component.scss.tpl`

```scss
@use '@angular/material' as mat;

:host {
  display: block;

  mat-card {
    margin: 1rem 0;

    mat-card-header {
      background-color: mat.get-theme-color(primary, 50);
      padding: 1rem;
      margin: -1rem -1rem 1rem -1rem;
    }

    mat-card-title {
      color: mat.get-theme-color(primary, 700);
      font-weight: mat.get-theme-typography(headline-6, font-weight);
    }

    mat-card-actions {
      padding: 0 1rem 1rem;
    }
  }
}
```

## Template 2: ControlValueAccessor Boilerplate

**File**: `form-field.ts.tpl`

**Used by**:
- Angular Material form field generation (skill 6)

```typescript
import { Component, input, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-{{FIELD_NAME_KEBAB}}',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './{{FIELD_NAME_KEBAB}}.component.html',
  styleUrl: './{{FIELD_NAME_KEBAB}}.component.scss',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => {{FIELD_NAME_PASCAL}}Component),
      multi: true
    }
  ]
})
export class {{FIELD_NAME_PASCAL}}Component implements ControlValueAccessor {
  // Input properties
  label = input<string>('');
  placeholder = input<string>('');

  // Internal state
  value: string = '';
  disabled: boolean = false;

  // Callbacks
  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  // ControlValueAccessor implementation
  writeValue(value: string): void {
    this.value = value || '';
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  // Value change handler
  onValueChange(value: string): void {
    this.value = value;
    this.onChange(value);
    this.onTouched();
  }
}
```

## Template 3: Typed Reactive `FormGroup<>`

**File**: `reactive-form.ts.tpl`

**Used by**:
- Angular Material reactive form generation (skill 9)

```typescript
import { Component, inject, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';

// Typed form interface
interface {{FORM_NAME_PASCAL}}Form {
  name: FormControl<string>;
  email: FormControl<string>;
  description: FormControl<string>;
}

@Component({
  selector: 'app-{{FORM_NAME_KEBAB}}-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatProgressBarModule,
  ],
  templateUrl: './{{FORM_NAME_KEBAB}}-form.component.html',
  styleUrl: './{{FORM_NAME_KEBAB}}-form.component.scss'
})
export class {{FORM_NAME_PASCAL}}FormComponent {
  private fb = inject(FormBuilder);

  // Signals
  loading = signal(false);

  // Outputs
  formSubmit = output<any>();
  formCancel = output<void>();

  // Typed FormGroup
  form: FormGroup<{{FORM_NAME_PASCAL}}Form> = this.fb.group({
    name: this.fb.control('', { nonNullable: true, validators: [Validators.required, Validators.minLength(2)] }),
    email: this.fb.control('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
    description: this.fb.control('', { nonNullable: true, validators: [Validators.maxLength(500)] }),
  });

  onSubmit(): void {
    if (this.form.valid && !this.loading()) {
      this.loading.set(true);
      this.formSubmit.emit(this.form.getRawValue());
    }
  }

  onCancel(): void {
    this.form.reset();
    this.formCancel.emit();
  }

  // Server-side validation error handler
  setServerErrors(errors: Record<string, string[]>): void {
    Object.entries(errors).forEach(([field, messages]) => {
      const control = this.form.get(field);
      if (control) {
        control.setErrors({ server: messages.join(', ') });
      }
    });
  }
}
```

## Template 4: `MatTable` + Paginator + Sort Page

**Files**: `list-page.ts.tpl`, `list-page.html.tpl`

**Used by**:
- Angular Material page generation (skill 10)

### `list-page.ts.tpl`

```typescript
import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { {{RESOURCE_NAME_PASCAL}} } from '../../api/models/{{RESOURCE_NAME_KEBAB}}';
import { {{RESOURCE_NAME_PASCAL}}Service } from '../../services/{{RESOURCE_NAME_KEBAB}}.service';

@Component({
  selector: 'app-{{RESOURCE_NAME_KEBAB}}-list',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatProgressBarModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './{{RESOURCE_NAME_KEBAB}}-list.component.html',
  styleUrl: './{{RESOURCE_NAME_KEBAB}}-list.component.scss'
})
export class {{RESOURCE_NAME_PASCAL}}ListComponent implements OnInit {
  private router = inject(Router);
  private {{RESOURCE_NAME_CAMEL}}Service = inject({{RESOURCE_NAME_PASCAL}}Service);

  // Signals
  items = signal<{{RESOURCE_NAME_PASCAL}}[]>([]);
  loading = signal(false);
  totalCount = signal(0);
  pageSize = signal(10);
  pageIndex = signal(0);

  // Data source
  dataSource = computed(() => {
    const ds = new MatTableDataSource(this.items());
    return ds;
  });

  // Table configuration
  displayedColumns: string[] = ['id', 'name', 'status', 'createdAt', 'actions'];

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading.set(true);
    this{{RESOURCE_NAME_CAMEL}}Service
      .list(this.pageIndex(), this.pageSize())
      .subscribe({
        next: (response) => {
          this.items.set(response.results);
          this.totalCount.set(response.count);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
        }
      });
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.loadData();
  }

  onSortChange(sort: Sort): void {
    // Implement sorting logic
    this.loadData();
  }

  onRowClick(item: {{RESOURCE_NAME_PASCAL}}): void {
    this.router.navigate(['/{{RESOURCE_NAME_KEBAB}}', item.id]);
  }

  onCreate(): void {
    this.router.navigate(['/{{RESOURCE_NAME_KEBAB}}/new']);
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource().filter = filterValue.trim().toLowerCase();
  }
}
```

### `list-page.html.tpl`

```html
<div class="list-container">
  <div class="list-header">
    <h1>{{RESOURCE_NAME_TITLE}}s</h1>
    <button mat-raised-button color="primary" (click)="onCreate()">
      <mat-icon>add</mat-icon>
      New {{RESOURCE_NAME_TITLE}}
    </button>
  </div>

  @if (loading()) {
    <mat-progress-bar mode="indeterminate"></mat-progress-bar>
  }

  <mat-form-field appearance="outline" class="filter-field">
    <mat-label>Filter</mat-label>
    <input matInput (keyup)="applyFilter($event)" placeholder="Search...">
    <mat-icon matSuffix>search</mat-icon>
  </mat-form-field>

  <div class="table-container">
    <table mat-table [dataSource]="dataSource()" matSort (matSortChange)="onSortChange($event)">

      <ng-container matColumnDef="id">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>ID</th>
        <td mat-cell *matCellDef="let item">{{ item.id }}</td>
      </ng-container>

      <ng-container matColumnDef="name">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Name</th>
        <td mat-cell *matCellDef="let item">{{ item.name }}</td>
      </ng-container>

      <ng-container matColumnDef="status">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Status</th>
        <td mat-cell *matCellDef="let item">{{ item.status }}</td>
      </ng-container>

      <ng-container matColumnDef="createdAt">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Created</th>
        <td mat-cell *matCellDef="let item">{{ item.createdAt | date:'short' }}</td>
      </ng-container>

      <ng-container matColumnDef="actions">
        <th mat-header-cell *matHeaderCellDef>Actions</th>
        <td mat-cell *matCellDef="let item">
          <button mat-icon-button (click)="onRowClick(item)">
            <mat-icon>visibility</mat-icon>
          </button>
        </td>
      </ng-container>

      <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
      <tr mat-row *matRowDef="let row; columns: displayedColumns;"
          (click)="onRowClick(row)"
          class="clickable-row"></tr>
    </table>
  </div>

  <mat-paginator
    [length]="totalCount()"
    [pageSize]="pageSize()"
    [pageIndex]="pageIndex()"
    [pageSizeOptions]="[5, 10, 25, 50]"
    (page)="onPageChange($event)"
    showFirstLastButtons>
  </mat-paginator>
</div>
```

## Template 5: `MatSidenav` App Shell

**Files**: `app-shell.ts.tpl`, `app-shell.html.tpl`

**Used by**:
- Angular Material site generation (skill 11)

### `app-shell.ts.tpl`

```typescript
import { Component, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { toSignal } from '@angular/core/rxjs-interop';

interface NavItem {
  label: string;
  route: string;
  icon: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  private breakpointObserver = inject(BreakpointObserver);
  private router = inject(Router);

  // Responsive layout
  isHandset = toSignal(
    this.breakpointObserver.observe([Breakpoints.Handset]),
    { initialValue: { matches: false } }
  );

  isMobile = computed(() => this.isHandset().matches);
  sidenavMode = computed(() => this.isMobile() ? 'over' : 'side');
  sidenavOpened = signal(true);

  // Navigation items
  navItems: NavItem[] = [
    { label: 'Dashboard', route: '/dashboard', icon: 'dashboard' },
    { label: 'Users', route: '/users', icon: 'people' },
    { label: 'Settings', route: '/settings', icon: 'settings' },
  ];

  toggleSidenav(): void {
    this.sidenavOpened.set(!this.sidenavOpened());
  }

  navigate(route: string): void {
    this.router.navigate([route]);
    if (this.isMobile()) {
      this.sidenavOpened.set(false);
    }
  }
}
```

### `app-shell.html.tpl`

```html
<mat-sidenav-container class="app-container">
  <mat-sidenav
    [mode]="sidenavMode()"
    [opened]="sidenavOpened()"
    class="app-sidenav">

    <div class="sidenav-header">
      <h2>{{APP_NAME}}</h2>
    </div>

    <mat-nav-list>
      @for (item of navItems; track item.route) {
        <a mat-list-item (click)="navigate(item.route)">
          <mat-icon matListItemIcon>{{ item.icon }}</mat-icon>
          <span matListItemTitle>{{ item.label }}</span>
        </a>
      }
    </mat-nav-list>
  </mat-sidenav>

  <mat-sidenav-content>
    <mat-toolbar color="primary" class="app-toolbar">
      <button mat-icon-button (click)="toggleSidenav()">
        <mat-icon>menu</mat-icon>
      </button>
      <span class="toolbar-spacer"></span>
      <button mat-icon-button>
        <mat-icon>account_circle</mat-icon>
      </button>
    </mat-toolbar>

    <div class="content-container">
      <router-outlet></router-outlet>
    </div>
  </mat-sidenav-content>
</mat-sidenav-container>
```

## Template 6: Service + `catchError` + `MatSnackBar`

**File**: `service.ts.tpl` (intended resource path for the `ng-data-service` skill template)

**Used by**:
- Angular data model Service (skill 4)

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { MatSnackBar } from '@angular/material/snack-bar';
import { {{RESOURCE_NAME_PASCAL}} } from '../api/models/{{RESOURCE_NAME_KEBAB}}';
import { {{RESOURCE_NAME_PASCAL}}ApiService } from '../api/services/{{RESOURCE_NAME_KEBAB}}-api.service';

@Injectable({
  providedIn: 'root'
})
export class {{RESOURCE_NAME_PASCAL}}Service {
  private http = inject(HttpClient);
  private snackBar = inject(MatSnackBar);
  private apiService = inject({{RESOURCE_NAME_PASCAL}}ApiService);

  /**
   * List all resources with pagination
   */
  list(page: number = 0, pageSize: number = 10): Observable<{ results: {{RESOURCE_NAME_PASCAL}}[]; count: number }> {
    return this.apiService
      .list{{RESOURCE_NAME_PASCAL}}s({ page: page + 1, pageSize })
      .pipe(
        map((response) => ({
          results: response.results || [],
          count: response.count || 0
        })),
        catchError((error) => this.handleError(error, 'Failed to load {{RESOURCE_NAME_KEBAB}}s'))
      );
  }

  /**
   * Get a single resource by ID
   */
  get(id: number): Observable<{{RESOURCE_NAME_PASCAL}}> {
    return this.apiService
      .get{{RESOURCE_NAME_PASCAL}}({ id })
      .pipe(
        catchError((error) => this.handleError(error, 'Failed to load {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Create a new resource
   */
  create(data: Partial<{{RESOURCE_NAME_PASCAL}}>): Observable<{{RESOURCE_NAME_PASCAL}}> {
    return this.apiService
      .create{{RESOURCE_NAME_PASCAL}}({ body: data })
      .pipe(
        map((response) => {
          this.showSuccess('{{RESOURCE_NAME_TITLE}} created successfully');
          return response;
        }),
        catchError((error) => this.handleError(error, 'Failed to create {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Update an existing resource
   */
  update(id: number, data: Partial<{{RESOURCE_NAME_PASCAL}}>): Observable<{{RESOURCE_NAME_PASCAL}}> {
    return this.apiService
      .update{{RESOURCE_NAME_PASCAL}}({ id, body: data })
      .pipe(
        map((response) => {
          this.showSuccess('{{RESOURCE_NAME_TITLE}} updated successfully');
          return response;
        }),
        catchError((error) => this.handleError(error, 'Failed to update {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Delete a resource
   */
  delete(id: number): Observable<void> {
    return this.apiService
      .delete{{RESOURCE_NAME_PASCAL}}({ id })
      .pipe(
        map(() => {
          this.showSuccess('{{RESOURCE_NAME_TITLE}} deleted successfully');
        }),
        catchError((error) => this.handleError(error, 'Failed to delete {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Handle HTTP errors and display user-friendly messages
   */
  private handleError(error: HttpErrorResponse, fallbackMessage: string): Observable<never> {
    let errorMessage = fallbackMessage;

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else if (error.status === 0) {
      // Network error
      errorMessage = 'Network error. Please check your connection.';
    } else if (error.status >= 400 && error.status < 500) {
      // Client error (validation, authentication, etc.)
      errorMessage = error.error?.message || error.error?.detail || fallbackMessage;
    } else if (error.status >= 500) {
      // Server error
      errorMessage = 'Server error. Please try again later.';
    }

    this.showError(errorMessage);
    return throwError(() => error);
  }

  /**
   * Display success message
   */
  private showSuccess(message: string): void {
    this.snackBar.open(message, 'Dismiss', {
      duration: 3000,
      horizontalPosition: 'end',
      verticalPosition: 'top',
      panelClass: ['success-snackbar']
    });
  }

  /**
   * Display error message
   */
  private showError(message: string): void {
    this.snackBar.open(message, 'Dismiss', {
      duration: 5000,
      horizontalPosition: 'end',
      verticalPosition: 'top',
      panelClass: ['error-snackbar']
    });
  }
}
```

# Skills Catalog

This section breaks down the skills subset of the automation model into the
different skills.

Each skill will include:
- A building script(s).
- A description of the skill, including when to use it and how to use it.
  - Optionally additional details about the skill or sub section, in seperate md files.
- Template files.
Each script will have the following modes:
- Create: from zero, the object didn't exist before.
- Modify: Modify a given object
- Delete: Delete the object

The mode to apply to each object is determined by running `oasdiff` against the previous and current OpenAPI schema. `oasdiff` output identifies which API resources, operations, and models were added (→ Create), changed (→ Modify), or removed (→ Delete), driving the correct skill mode for each affected object.

## Angular Material workspace boiler plate

**Skill Name**: `ng-workspace`

### YAML Frontmatter

```yaml
---
name: ng-workspace
description: Create, modify, or delete an Angular Material workspace with modern conventions (standalone components, signals, SCSS theming)
when_to_use: Use when build_app dispatches a workspace-creation or workspace-modification procedure node, or when a user runs /ng-workspace to scaffold or update an Angular workspace from django-angular3.json.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-workspace` skill manages the creation, modification, and deletion of Angular workspaces configured with Angular Material, following modern Angular conventions (standalone components, signals, SCSS theming). This is the foundation skill that must be executed before any app-level or component-level skills can be invoked.

### Inputs

All inputs are read from `django-angular3.json` passed as the procedure input.

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `angular.output` | yes | string | — | Absolute path where the workspace will be created |
| `project.name` | yes | string | — | Name of the workspace |
| `angular.workspace.packageManager` | no | `npm` \| `yarn` \| `pnpm` | `pnpm` | Package manager to use |
| `angular.workspace.style` | no | `css` \| `scss` \| `sass` \| `less` | `scss` | Stylesheet format |
| `angular.workspace.routing` | no | boolean | `true` | Whether to include routing |

### Mode: Create

Generate an Angular Material workspace from scratch when it doesn't exist.

#### Input Requirements

- **`angular.output`**: Must not already exist or must be an empty directory
- **`project.name`**: Valid workspace name (lowercase, hyphenated)
- **`angular.workspace.packageManager`**: Valid package manager executable must be available in PATH
- **`angular.workspace.style`**: Must be a valid Angular CLI stylesheet option
- **`angular.workspace.routing`**: Boolean flag

#### Pre-flight Checks

Before creating the workspace, verify:

1. `angular.output` directory does not exist or is empty
2. Node.js version meets Angular's requirements (currently Node 18.19+ or 20.11+ or 22.0+)
3. Sufficient disk space is available (minimum 500MB recommended)

Package manager availability and Angular CLI access are validated by the `ng_new` djng wrapper.

#### Process (Create Mode)

1. **Create workspace via djng wrapper**:
   ```bash
   django-admin ng_new django-angular3.json --dry-run
   ```
   Review the dry-run output (the previewed command invocation). When `ng_new` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_new django-angular3.json
   ```

2. **Install Angular Material via djng wrapper**:
   ```bash
   django-admin ng_add django-angular3.json --dry-run
   ```
   When `ng_add` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_add django-angular3.json
   ```

   > **Note**: `ng_new` and `ng_add` are not in `command_allowlist` by default — they plan dry-runs unless the allowlist is explicitly broadened. See `django_angular3/settings.py`.

3. **Configure custom Material theme**:
   - Read the generated `src/styles.scss`
   - Replace default theme imports with custom theme configuration using Material 3 token-based theming
   - Define palette variables: `$primary`, `$accent`, `$warn`
   - Apply theme to core, typography, and density

4. **Update `angular.json` configuration**:
   - Set `inlineStyleLanguage` to `scss`
   - Enable source maps for development
   - Configure build optimization for production
   - Add Material prebuilt CSS path if needed

5. **Create `.editorconfig`** (if not present):
   - Standard Angular formatting rules
   - 2-space indentation for TS/HTML/SCSS
   - UTF-8 charset
   - Insert final newline

6. **Create `.prettierrc.json`** (optional but recommended):
   - Configure Prettier for consistent formatting
   - Single quotes, 2-space indent, trailing commas

7. **Update `tsconfig.json` with strict mode**:
   - Enable `strict: true`
   - Enable `strictNullChecks: true`
   - Enable `noImplicitAny: true`
   - Enable `skipLibCheck: true`

8. **Install additional development dependencies**:
   ```bash
   pnpm install --save-dev @angular-eslint/builder @angular-eslint/eslint-plugin @angular-eslint/eslint-plugin-template @angular-eslint/schematics @angular-eslint/template-parser
   ```

9. **Initialize ESLint configuration** (uses locally installed Angular CLI — no download):
   ```bash
   pnpm exec ng add @angular-eslint/schematics --skip-confirmation
   ```

10. **Create initial Git commit** (if not skipped):
    ```bash
    git add .
    git commit -m "chore: initialize Angular Material workspace with modern conventions"
    ```

#### Expected Output

After successful execution, the workspace directory contains:

```
<angular.output>/
├── .angular/                    # Angular cache directory
├── .editorconfig               # Editor configuration
├── .gitignore                  # Git ignore rules
├── .prettierrc.json            # Prettier configuration
├── angular.json                # Angular workspace configuration
├── node_modules/               # Installed dependencies
├── package.json                # NPM package manifest
├── pnpm-lock.yaml              # pnpm lock file (default package manager)
├── README.md                   # Project readme
├── tsconfig.json               # TypeScript configuration
├── tsconfig.app.json           # App-specific TS config
├── tsconfig.spec.json          # Test-specific TS config
├── .eslintrc.json              # ESLint configuration
└── src/
    ├── index.html              # Main HTML file
    ├── main.ts                 # Application entry point
    ├── styles.scss             # Global styles with Material theme
    ├── app/
    │   ├── app.component.ts    # Root component (standalone)
    │   ├── app.component.html  # Root template
    │   ├── app.component.scss  # Root styles
    │   ├── app.component.spec.ts # Root tests
    │   ├── app.config.ts       # Application configuration
    │   └── app.routes.ts       # Application routes (if routing enabled)
    └── assets/                 # Static assets
```

**Key characteristics**:
- All components are standalone (no NgModules)
- Material theming configured with custom SCSS theme
- ESLint configured for Angular projects
- TypeScript strict mode enabled
- Routing configured if requested

### Mode: Modify

Update an existing workspace with configuration changes, package updates, or new tooling.

> **Note**: `build_app` does not trigger `ng-workspace` Modify mode during normal operation — `django-angular3.json` is always read as current and its changes are not tracked. Modify mode is available for manual invocation via `--force`.

#### Input Requirements

- **`angular.output`**: Must exist and contain a valid Angular workspace (check for `angular.json`)
- **`modificationTarget`** (enum): Type of modification to perform:
  - `add-package`: Add NPM package(s)
  - `update-packages`: Update existing packages to latest versions
  - `update-angular`: Update Angular framework to latest version
  - `change-build-config`: Modify `angular.json` build configuration
  - `upgrade-typescript`: Upgrade TypeScript version
  - `reconfigure-material`: Change Material theme or configuration
  - `add-eslint-rule`: Add or modify ESLint rules
- **`modificationDetails`** (object): Details specific to the modification type

#### Process (Modify Mode)

**For `add-package` modifications**:
1. Verify workspace exists
2. Install package(s) using package manager: `<packageManager> install <packageName>`
3. Update imports in relevant files if needed
4. Run tests to verify compatibility
5. Commit changes: `git add . && git commit -m "chore: add <packageName>"`

**For `update-packages` modifications**:
1. Verify `angular.output` exists and contains `angular.json`
2. Update all packages: `pnpm update`
3. Run build: `django-admin ng_build django-angular3.json`
4. Run tests: `pnpm exec ng test --watch=false`
5. Fix any breaking changes
6. Commit changes: `git add . && git commit -m "chore: update dependencies"`

**For `update-angular` modifications**:
1. Verify `angular.output` exists and contains `angular.json`
2. Run Angular update: `pnpm exec ng update @angular/core @angular/cli @angular/material`
3. Review migration messages
4. Run build and tests: `django-admin ng_build django-angular3.json` and `pnpm exec ng test --watch=false`
5. Fix any breaking changes or deprecated API usage
6. Commit changes: `git add . && git commit -m "chore: update Angular to v<version>"`

**For `change-build-config` modifications**:
1. Verify `angular.output` exists and contains `angular.json`
2. Read `angular.json` using Read tool
3. Apply requested configuration changes using Edit tool
4. Validate JSON syntax
5. Test build: `django-admin ng_build django-angular3.json`
6. Commit changes: `git add angular.json && git commit -m "chore: update build configuration"`

**For `reconfigure-material` modifications**:
1. Verify `angular.output` exists and contains `angular.json`
2. Update `src/styles.scss` with new theme configuration using Edit tool
3. Test build: `django-admin ng_build django-angular3.json`
4. Verify Material components render correctly
5. Commit changes: `git add . && git commit -m "style: update Material theme"`

**For `add-eslint-rule` modifications**:
1. Verify `angular.output` exists and ESLint is configured
2. Read `.eslintrc.json` using Read tool
3. Add or modify rules using Edit tool
4. Run linter: `pnpm exec ng lint`
5. Fix any new violations
6. Commit changes: `git add . && git commit -m "chore: update ESLint rules"`

#### Output

- Modified workspace with requested changes applied
- All builds and tests passing
- Git commit created documenting the modification

### Mode: Delete

Remove the workspace directory completely, typically when starting fresh is simpler than extensive modification.

#### Input Requirements

- **`angular.output`**: Must exist and contain a valid Angular workspace (check for `angular.json`)

#### Process (Delete Mode)

1. **Remove workspace via djng wrapper**:
   ```bash
   django-admin ng_workspace_delete django-angular3.json --dry-run
   ```
   Review the dry-run output (the previewed command invocation). When `ng_workspace_delete` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_workspace_delete django-angular3.json
   ```
   The wrapper removes the directory cross-platform via `shutil.rmtree`.

   > **Note**: `ng_workspace_delete` is not in `command_allowlist` by default. See `django_angular3/settings.py`.

2. **Verify deletion**: Confirm `angular.output` directory no longer exists.

#### Output

- Workspace directory removed
- Deletion confirmed

### Supporting Files

#### Context Files

This skill references the following shared context files:

- [angular-conventions.md](../shared/angular-conventions.md) — Conventions for standalone components, signals, SCSS theming, naming, imports, and testing patterns.

#### Template Files

This skill does not use template files directly, as it relies on Angular CLI schematics for code generation. However, it configures the workspace to use the templates defined in the Templates section when subsequent skills (like `ng-component` or `ng-page`) are invoked.

### Validation

#### Post-Creation Validation

After creating a workspace, verify:

1. **Directory structure exists**:
   ```bash
   [ -f <angular.output>/angular.json ] && echo "✓ Workspace created"
   ```

2. **Dependencies installed**:
   ```bash
   [ -d <angular.output>/node_modules ] && echo "✓ Dependencies installed"
   ```

3. **Build succeeds**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   Expected: Build completes without errors

4. **Tests pass**:
   ```bash
   pnpm exec ng test --watch=false
   ```
   Expected: All tests pass

5. **Dev server starts**:
   ```bash
   pnpm exec ng serve --port 4200
   ```
   Expected: Server starts and application loads at `http://localhost:4200`

6. **Material is configured**:
   - Check `package.json` contains `@angular/material`
   - Check `src/styles.scss` contains Material theme imports
   - Verify Material components can be imported in app component

#### Post-Modification Validation

After modifying a workspace, verify:

1. **Build still succeeds**: `django-admin ng_build django-angular3.json`
2. **Tests still pass**: `pnpm exec ng test --watch=false`
3. **Linter passes**: `pnpm exec ng lint` (if ESLint configured)
4. **No TypeScript errors**: `django-admin ng_build django-angular3.json` (production configuration)

### Error Handling

#### Common Errors and Resolutions

**Error**: `ng: command not found`
- **Cause**: Angular CLI not installed in workspace `node_modules`
- **Resolution**: Re-run `django-admin ng_new django-angular3.json` to recreate the workspace with all dependencies

**Error**: `EACCES: permission denied`
- **Cause**: Insufficient permissions to create directory or install packages
- **Resolution**: Check directory permissions

**Error**: Dependency conflict during `pnpm install`
- **Cause**: Conflicting package versions
- **Resolution**: Resolve dependency versions manually or use `--force` flag

**Error**: `Schematic "ng-add" not found in collection "@angular/material"`
- **Cause**: Material package issue or version mismatch
- **Resolution**: Install Material manually and configure theme manually

**Error**: `The serve command requires to be run in an Angular project`
- **Cause**: Not in workspace root directory
- **Resolution**: Verify `angular.output` in `django-angular3.json` is correct and points to a directory containing `angular.json`

**Error**: Workspace directory already exists and is not empty
- **Cause**: Target directory contains files
- **Resolution**: Use Delete mode first, or choose a different directory

### Dependencies

**Prerequisites**:
- Node.js (v18.19+ or v20.11+ or v22.0+)
- pnpm package manager
- Git (for version control)
- Sufficient disk space (500MB+)
- djng installed with `ng_new`, `ng_add`, `ng_build`, `ng_workspace_delete` wrappers available

**No skill dependencies**: This is the foundational skill. All other Angular skills depend on this skill being executed first to create the workspace.

**Dependent skills** (must have workspace before using):
- `ng-app` — Angular Material app boiler plate
- `ng-api-gen` — Angular API generation
- All component, form, page, and site generation skills

### Examples

#### Example 1: Create New Workspace

**Input** (from `django-angular3.json`):
- `project.name`: `"my-shop"`
- `angular.output`: `"/home/user/projects/my-shop"`
- `angular.workspace.packageManager`: `"pnpm"`
- `angular.workspace.style`: `"scss"`
- `angular.workspace.routing`: `true`

**Execution**:
1. Run `django-admin ng_new django-angular3.json`
2. Run `django-admin ng_add django-angular3.json`
3. Configure custom SCSS theme
4. Install ESLint with `pnpm exec ng add @angular-eslint/schematics`
5. Create initial commit

**Output**: Workspace created at `/home/user/projects/my-shop` with Material configured

#### Example 2: Update Angular Version

**Input** (from `django-angular3.json`):
- `project.name`: `"my-shop"`
- `angular.output`: `"/home/user/projects/my-shop"`

**Execution**:
1. Run `pnpm exec ng update @angular/core @angular/cli @angular/material`
2. Review and apply migrations
3. Run `django-admin ng_build django-angular3.json` and `pnpm exec ng test --watch=false`
4. Commit changes

**Output**: Angular updated to latest version with all migrations applied

#### Example 3: Delete Workspace

**Input** (from `django-angular3.json`):
- `project.name`: `"my-shop"`
- `angular.output`: `"/home/user/projects/my-shop"`

Procedure-level input: `confirmDelete: true`

**Execution**:
1. Run `django-admin ng_workspace_delete django-angular3.json` (when in `command_allowlist`)
2. Confirm `angular.output` directory no longer exists

**Output**: Workspace deleted

## Angular Material app boiler plate

```yaml
---
name: ng-app
description: Manage Angular Material application within a workspace - create app structure with Material theme, modify providers and routing, or delete app
when_to_use: Use when build_app dispatches an app-creation, app-modification, or app-deletion procedure node, or when a user runs /ng-app to scaffold or update an Angular Material application inside an existing workspace.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

Generate and manage Angular Material applications within an existing Angular workspace. This skill creates a complete application scaffold with Material Design theming, standalone component architecture, proper directory structure, and routing configuration. Use this skill after the workspace has been created but before generating individual components or pages.

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular Material application inside the workspace with complete directory structure, theme configuration, and standalone bootstrap setup.

**Input Requirements** (all from `django-angular3.json`):
- `project.name` (required): Name of the application
- `angular.output` (required): Absolute path to the Angular workspace root directory
- `angular.workspace.prefix` (optional): Component selector prefix (defaults to `app`)
- `angular.workspace.routing` (optional): Whether to include routing configuration (defaults to `true`)

Note: `standalone: true` is a fixed Angular convention and is not configurable.

**Process**:

1. **Validate workspace exists**
   - Check that `angular.output` exists and contains `angular.json`
   - Verify workspace is initialized and valid
   - Confirm `project.name` doesn't already exist in workspace

2. **Generate application scaffold via djng wrapper**:
   ```bash
   django-admin ng_gen_app django-angular3.json --dry-run
   ```
   When `ng_gen_app` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_gen_app django-angular3.json
   ```

   > **Note**: `ng_gen_app` is not in `command_allowlist` by default. See `django_angular3/settings.py`.

3. **Create standard directory structure**
   - Create `projects/<project.name>/src/app/core/` - Core services and guards
   - Create `projects/<project.name>/src/app/shared/components/` - Shared components
   - Create `projects/<project.name>/src/app/shared/pipes/` - Shared pipes
   - Create `projects/<project.name>/src/app/features/` - Feature modules/routes
   - Create barrel exports (`index.ts`) in each directory

4. **Wire Angular Material theme**
   - Angular Material is already installed at the workspace level by `ng-workspace`.
   - Update `projects/<project.name>/src/styles.scss` with app-level theme configuration using Edit tool:
     ```scss
     @use '@angular/material' as mat;
     @include mat.core();

     $primary: mat.define-palette(mat.$indigo-palette);
     $accent: mat.define-palette(mat.$pink-palette, A200, A100, A400);
     $warn: mat.define-palette(mat.$red-palette);

     $theme: mat.define-light-theme((
       color: (
         primary: $primary,
         accent: $accent,
         warn: $warn,
       ),
       typography: mat.define-typography-config(),
       density: 0,
     ));

     @include mat.all-component-themes($theme);

     html, body { height: 100%; }
     body { margin: 0; font-family: Roboto, "Helvetica Neue", sans-serif; }
     ```

5. **Set up standalone bootstrap configuration**
   - Create/update `projects/<project.name>/src/app/app.config.ts`:
     ```typescript
     import { ApplicationConfig } from '@angular/core';
     import { provideRouter } from '@angular/router';
     import { provideAnimations } from '@angular/platform-browser/animations';
     import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
     import { routes } from './app.routes';

     export const appConfig: ApplicationConfig = {
       providers: [
         provideRouter(routes),
         provideAnimations(),
         provideHttpClient(withInterceptorsFromDi()),
       ]
     };
     ```

   - Update `projects/<project.name>/src/main.ts` to use standalone bootstrap:
     ```typescript
     import { bootstrapApplication } from '@angular/platform-browser';
     import { AppComponent } from './app/app.component';
     import { appConfig } from './app/app.config';

     bootstrapApplication(AppComponent, appConfig)
       .catch((err) => console.error(err));
     ```

6. **Generate application shell using template**
   - Use `templates/app-shell.ts.tpl` to create root `AppComponent`
   - Use `templates/app-shell.html.tpl` for component template
   - Replace `{{APP_NAME}}` placeholder with actual app name
   - Create responsive navigation shell with Material sidenav

7. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

**Output**:
- Complete Angular Material application created in `projects/<project.name>/`
- Directory structure with `core/`, `shared/`, `features/` folders
- Material theme configured in `styles.scss`
- Standalone bootstrap with `app.config.ts`
- Application shell with responsive navigation
- Entry added to `angular.json` for the new application

#### Modify

Update an existing Angular Material application with changes to providers, global styles, or routing configuration.

**Input Requirements**:
- `project.name` (from `django-angular3.json`, required): Name of the existing application to modify
- `angular.output` (from `django-angular3.json`, required): Absolute path to the Angular workspace
- `modifications` (from procedure inputs, required): Object describing changes to make:
  - `providers`: Array of provider configurations to add/remove
  - `styles`: CSS/SCSS rules to add to global styles
  - `routes`: Route definitions to register (lazy-loaded or eager)
  - `dependencies`: NPM packages to add/remove

**Process**:

1. **Validate application exists**
   - Verify `projects/<project.name>/` exists
   - Check `angular.json` contains configuration for `<project.name>`
   - Confirm application is using standalone architecture

2. **Update providers in app.config.ts**
   - Read existing `projects/<project.name>/src/app/app.config.ts`
   - Parse provider array
   - Add new providers to the `providers` array:
     ```typescript
     // Example: Adding authentication provider
     import { provideAuth } from './core/auth';

     export const appConfig: ApplicationConfig = {
       providers: [
         // ... existing providers
         provideAuth({ apiUrl: environment.apiUrl }),
       ]
     };
     ```
   - Remove specified providers if requested
   - Maintain formatting and import statements

3. **Update global styles**
   - Read `projects/<project.name>/src/styles.scss`
   - Append new styles to end of file (or update existing theme if modifying theme)
   - Example modifications:
     ```scss
     // Custom utility classes
     .full-width { width: 100%; }
     .center-content { display: flex; justify-content: center; align-items: center; }

     // Custom Material overrides
     .mat-mdc-card { border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
     ```

4. **Register lazy routes**
   - Read `projects/<project.name>/src/app/app.routes.ts`
   - Add new route definitions:
     ```typescript
     import { Routes } from '@angular/router';

     export const routes: Routes = [
       { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
       {
         path: 'dashboard',
         loadComponent: () => import('./features/dashboard/dashboard.component')
           .then(m => m.DashboardComponent)
       },
       // ... new routes added here
     ];
     ```
   - Maintain route ordering and guard configurations

5. **Update dependencies**
   - If `dependencies` specified:
     ```bash
     pnpm install <package>@<version>
     # or
     pnpm uninstall <package>
     ```

6. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

**Output**:
- Updated `app.config.ts` with new providers
- Modified `styles.scss` with additional styles or theme changes
- Updated `app.routes.ts` with new route registrations
- Updated `package.json` and `node_modules` if dependencies changed
- Confirmation of successful modification with list of changes made

#### Delete

Remove an Angular Material application completely from the workspace, including all source files and configuration.

**Input Requirements** (all from `django-angular3.json`):
- `project.name` (required): Name of the application to delete
- `angular.output` (required): Absolute path to the Angular workspace

**Process**:

1. **Validate application exists**
   - Verify `<angular.output>/projects/<project.name>/` exists
   - Check `angular.json` contains configuration for `<project.name>`
   - Confirm no other applications depend on this one

2. **Remove application directory** using Bash tool:
   ```bash
   rm -rf <angular.output>/projects/<project.name>
   ```

3. **Update `angular.json`** using Read and Edit tools:
   - Remove entry from `projects` object for `<project.name>`
   - Remove any build configurations, serve targets, and test targets
   - Update default project if this was the default

4. **Clean up dependencies (optional)**:
   - Check if Angular Material is used by other apps
   - If this was the only app using Material, optionally remove:
     ```bash
     pnpm uninstall @angular/material @angular/cdk
     ```

5. **Verify workspace integrity**: Read `angular.json` and confirm it is valid JSON with no remaining references to `<project.name>`.

**Output**:
- Application directory `projects/<project.name>/` removed
- Entry removed from `angular.json`
- Workspace remains valid and functional
- Confirmation message listing what was deleted

### Context Files

See [angular-conventions.md](../shared/angular-conventions.md)

See [angular-material-patterns.md](../shared/angular-material-patterns.md)

### Templates

- `app-shell.ts.tpl` — Root AppComponent with Material sidenav navigation shell, responsive breakpoint handling, and routing outlet
- `app-shell.html.tpl` — MatSidenav container template with toolbar, navigation list, and content area
- `app.config.ts.tpl` — Standalone application configuration with standard providers (router, animations, HTTP client)
- `app.routes.ts.tpl` — Initial route configuration with empty routes array and typed Routes import

### Validation

Steps to validate successful execution of the skill:

1. **Verify directory structure**
   ```bash
   ls -la projects/<project.name>/src/app/
   # Should contain: core/, shared/, features/, app.component.ts, app.config.ts, app.routes.ts
   ```

2. **Verify Material theme is wired**
   ```bash
   cat projects/<project.name>/src/styles.scss | grep "@angular/material"
   # Should contain Material theme imports and configuration
   ```

3. **Verify standalone bootstrap**
   ```bash
   cat projects/<project.name>/src/main.ts | grep "bootstrapApplication"
   # Should use bootstrapApplication() not platformBrowserDynamic()
   ```

4. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   Expected: Build completes without errors

5. **Serve and verify**:
   ```bash
   pnpm exec ng serve <project.name>
   ```
   Navigate to `http://localhost:4200` and verify Material components render

### Error Handling

Common errors and their resolution strategies:

**Error**: Application with name `<project.name>` already exists
- **Cause**: Attempting to create an app with a name that's already in use
- **Resolution**: Use Delete mode first, or choose a different app name

**Error**: `Workspace path does not contain angular.json`
- **Cause**: Invalid workspace path or workspace not initialized
- **Resolution**: Verify workspace path is correct; if needed, run workspace creation skill first

**Error**: `Cannot find module '@angular/material'`
- **Cause**: Angular Material not installed or installation failed
- **Resolution**: Run `django-admin ng_add django-angular3.json` to install Material at workspace level

**Error**: `Compilation failed: Cannot find module './app/app.config'`
- **Cause**: Standalone bootstrap not properly configured
- **Resolution**: Verify `app.config.ts` exists and is properly imported in `main.ts`

**Error**: `SCSS compilation failed`
- **Cause**: Invalid SCSS syntax in theme configuration
- **Resolution**: Validate SCSS syntax in `styles.scss`; ensure `@use` statements are at the top

**Error**: `Port 4200 is already in use`
- **Cause**: Another application is already running on default port
- **Resolution**: Stop other dev servers or use `pnpm exec ng serve <project.name> --port=4201`

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1) — Workspace must exist before creating an application within it
2. **Node.js and npm** — Required to run Angular CLI commands
3. **Angular CLI** — Must be installed globally or in workspace (`@angular/cli`)

Optional dependencies:

- If using OpenAPI integration, **Angular API generation** (Skill 3) should be executed after app creation
### Examples

**Example 1: Create a new admin dashboard application**

```typescript
// Inputs from django-angular3.json:
//   project.name = "admin-dashboard"
//   angular.output = "/workspace/my-project"
// Procedure-level: prefix = "admin"

// Executes:
// 1. django-admin ng_gen_app django-angular3.json
// 2. Creates core/, shared/, features/ directories
// 3. Configures theme in projects/admin-dashboard/src/styles.scss
// 4. Sets up app.config.ts with providers
// 5. Generates responsive nav shell from app-shell templates
// 6. django-admin ng_build django-angular3.json

// Output: Application ready at projects/admin-dashboard/
```

**Example 2: Modify existing app to add authentication provider**

```typescript
// Inputs from django-angular3.json:
//   project.name = "admin-dashboard"
//   angular.output = "/workspace/my-project"
// Procedure-level: add provideAuth provider + styles

// Executes:
// 1. Reads projects/admin-dashboard/src/app/app.config.ts
// 2. Adds import: import { provideAuth } from './core/auth';
// 3. Adds to providers: provideAuth({ apiUrl: 'https://api.example.com' })
// 4. Appends custom styles to projects/admin-dashboard/src/styles.scss
// 5. django-admin ng_build django-angular3.json

// Output: Updated app.config.ts and styles.scss
```

**Example 3: Register lazy-loaded feature route**

```typescript
// Inputs from django-angular3.json:
//   project.name = "admin-dashboard"
//   angular.output = "/workspace/my-project"

// Executes:
// 1. Reads projects/admin-dashboard/src/app/app.routes.ts
// 2. Adds new route definition to routes array
// 3. django-admin ng_build django-angular3.json

// Output: Updated app.routes.ts with new lazy route
```

**Example 4: Delete an application**

```typescript
// Inputs from django-angular3.json:
//   project.name = "old-admin"
//   angular.output = "/workspace/my-project"
// Procedure-level: confirm = true

// Executes:
// 1. Verifies projects/old-admin/ exists
// 2. Removes: rm -rf projects/old-admin
// 3. Updates angular.json to remove "old-admin" project entry

// Output: Application "old-admin" removed from workspace
```

## Angular API generation

```yaml
---
name: ng-api
description: Generate TypeScript API client code from an OpenAPI specification using ng-openapi-gen.
when_to_use: Use when build_app dispatches an api-generation procedure node (initial generation or schema-change regeneration), or when a user runs /ng-api to regenerate API clients after OpenAPI schema changes.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---
```

### Purpose

Generate TypeScript API client code (services and models) from OpenAPI specifications using the ng-openapi-gen tool. This skill creates strongly-typed Angular services that wrap HTTP endpoints defined in the OpenAPI schema, producing `*ApiService` files organized by OpenAPI tags and corresponding TypeScript model interfaces.

### Modes

#### Create

Generate API client code from an OpenAPI specification when it doesn't exist.

**Input Requirements**:
- `openapi.source` (from `django-angular3.json`, required): Path to the current OpenAPI specification file (JSON or YAML)
- `angular.output` (from `django-angular3.json`, required): Angular workspace root (used to locate `ng-openapi-gen.json`)

Output path is configured in `ng-openapi-gen.json` at the workspace root; breaking-change detection is already performed by `build_app` before invoking this skill.

**Process**:
1. **Preflight validation**:
   - Verify `openapi.source` file exists and is well-formed JSON or YAML
   - Check `ng-openapi-gen` is installed in workspace: `pnpm list ng-openapi-gen`
   - Check for `ng-openapi-gen.json` at `angular.output` root
2. **Configuration setup** (if `ng-openapi-gen.json` doesn't exist):
   - Create `ng-openapi-gen.json` at workspace root with:
     ```json
     {
       "$schema": "node_modules/ng-openapi-gen/ng-openapi-gen-schema.json",
       "input": "<openapi.source>",
       "output": "src/app/api",
       "ignoreUnusedModels": false
     }
     ```
3. **Run generation** via djng wrapper (`ng_openapi_gen` is in `command_allowlist` by default):
   ```bash
   django-admin ng_openapi_gen django-angular3.json
   ```
4. **Verify output**:
   - Confirm `services/` directory populated with `*-api.service.ts` files
   - Confirm `models/` directory populated with model TypeScript interfaces
   - Check for `models.ts` and `services.ts` barrel export files
5. **Report results**:
   - List all generated `*ApiService` files (one per OpenAPI tag)
   - Report count of generated models
   - Output any warnings from ng-openapi-gen

**Output**:
- Generated TypeScript services in `<output_path>/services/`
- Generated TypeScript model interfaces in `<output_path>/models/`
- Barrel exports at `<output_path>/models.ts` and `<output_path>/services.ts`
- Base API configuration file at `<output_path>/base-service.ts`

#### Modify

Regenerate API client code after OpenAPI specification changes.

**Input Requirements**:
- `openapi.source` (from `django-angular3.json`, required): Path to the updated OpenAPI specification file
- `angular.output` (from `django-angular3.json`, required): Angular workspace root

Breaking-change detection is already performed by `build_app` before invoking this skill. The `oasdiff_report` is available in the ChangeSet passed as procedure input.

**Process**:
1. **Verify existing generation**:
   - Confirm `ng-openapi-gen.json` config exists at `angular.output`
   - Confirm output directory exists with previous generation
2. **Clean previous generation** (optional):
   - ng-openapi-gen handles incremental updates, but removed endpoints/models may leave orphaned files
3. **Re-run generation** via djng wrapper:
   ```bash
   django-admin ng_openapi_gen django-angular3.json
   ```
4. **Diff analysis**:
   - Identify new, modified, and removed services and models by comparing directory contents before and after
5. **Report changes**:
   - List added, modified, and removed services and models
   - Warn about any orphaned files requiring manual cleanup

**Output**:
- Updated TypeScript services reflecting spec changes
- Updated TypeScript models reflecting schema changes
- Change summary report

**Important**: Never hand-edit generated files in `<output_path>/`. Always regenerate via this skill.

#### Delete

Remove generated API client code directory; invoke Create mode to regenerate.

**Input Requirements**:
- `angular.output` (from `django-angular3.json`, required): Angular workspace root (output path is read from `ng-openapi-gen.json`)

**Process**:
1. **Verify target**:
   - Read `ng-openapi-gen.json` to determine `output` path
   - Confirm output directory exists and contains ng-openapi-gen generated structure (`services/`, `models/`, barrel exports)
2. **Warn if non-generated files present**
3. **Remove directory** using Bash tool:
   ```bash
   rm -rf <output_path>
   ```
4. **Retain `ng-openapi-gen.json`** for subsequent regeneration via Create mode

**Output**:
- Removed output directory
- Confirmation message

### Context Files

See [openapi-integration.md](../shared/openapi-integration.md)

### Supporting Files

- `ng-openapi-gen.json` — Configuration file for ng-openapi-gen tool (created if doesn't exist)
- OpenAPI specification file (external input, not part of skill)

### Validation

**Post-Create/Modify Validation**:
1. **Directory structure check**:
   ```bash
   ls -la <output_path>/services/
   ls -la <output_path>/models/
   ```
   - Verify `services/` directory contains at least one `*-api.service.ts` file per OpenAPI tag
   - Verify `models/` directory populated with `.ts` model files
2. **Barrel exports check**:
   ```bash
   cat <output_path>/models.ts
   cat <output_path>/services.ts
   ```
   - Confirm barrel files exist and contain re-exports
3. **TypeScript compilation check**:
   ```bash
   pnpm exec tsc --noEmit --project tsconfig.json
   ```
   - Confirm generated files compile without errors
4. **Service naming validation**:
   - Each OpenAPI tag should produce exactly one `<Tag>ApiService`
   - Service file names follow kebab-case: `<tag>-api.service.ts`
   - Service class names follow PascalCase: `<Tag>ApiService`

### Error Handling

**Common Errors**:

1. **OpenAPI spec not found**:
   - Error: `ENOENT: no such file or directory`
   - Resolution: Verify `openapi_source_path` is correct; check file exists

2. **Invalid OpenAPI spec**:
   - Error: `OpenAPI schema validation failed`
   - Resolution: Validate spec using `django-admin validate-project django-angular3.json` or an online validator

3. **ng-openapi-gen not installed**:
   - Error: `command not found: ng-openapi-gen`
   - Resolution: Install via `pnpm install --save-dev ng-openapi-gen`

4. **Generation errors**:
   - Error: Various ng-openapi-gen errors during generation
   - Resolution: Check stderr output; common issues include:
     - Unsupported OpenAPI features
     - Circular references in schemas
     - Invalid TypeScript identifiers from spec

5. **TypeScript compilation errors after generation**:
   - Error: Compilation failures in generated code
   - Resolution: Usually indicates OpenAPI spec issue or ng-openapi-gen version incompatibility; check ng-openapi-gen documentation for supported OpenAPI versions

### Dependencies

**Required Skills**:
- Angular Material workspace boilerplate must exist (workspace with `package.json` and Angular CLI)

**Required Tools**:
- `oasdiff` — used by `build_app` for change derivation before invoking this skill; not called by the skill directly
- `ng-openapi-gen` npm package installed in workspace (`pnpm install --save-dev ng-openapi-gen`)
- Angular workspace with TypeScript configuration

**Optional Dependencies**:
- OpenAPI specification linting tools for validation

### Examples

**Example 1: Initial API generation**
```markdown
Input (from django-angular3.json):
- openapi.source: "spec/openapi.yaml"
- angular.output: "/path/to/workspace"

Process:
1. Verify spec/openapi.yaml exists
2. Create ng-openapi-gen.json config
3. Run: django-admin ng_openapi_gen django-angular3.json
4. Report generated files

Output:
Generated 3 API services:
- src/app/api/services/users-api.service.ts (UsersApiService)
- src/app/api/services/posts-api.service.ts (PostsApiService)
- src/app/api/services/comments-api.service.ts (CommentsApiService)

Generated 8 models in src/app/api/models/
Barrel exports created
```

**Example 2: Regeneration after spec update**
```markdown
Input:
- openapi_source_path: "spec/openapi.yaml" (updated)

Process:
1. Detect existing ng-openapi-gen.json
2. Re-run generation
3. Analyze changes

Output:
Changes detected:
- New service: AuthApiService
- Modified models: User (added 'role' field), Post (changed 'content' to optional)
- No removed services
```

**Example 3: Clean regeneration**
```markdown
Input:
- output_path: "src/app/api"

Process:
1. Delete mode: Remove src/app/api/
2. Auto-invoke Create mode with previous config

Output:
Cleaned and regenerated API client code
```

## Angular data model Service

```yaml
---
name: ng-data-service
description: Create, modify, or delete Angular data services that wrap generated `<Resource>ApiService` clients with typed `Observable` methods, snack-bar feedback, and focused unit tests.
when_to_use: Use when build_app dispatches a data-service procedure node for a resource that has generated <Resource>ApiService code, or when a user runs /ng-data-service to wrap a generated API client with typed Observables and snack-bar feedback.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-data-service` skill manages handwritten Angular data services that sit on top of generated `*ApiService` clients from the `ng-api` skill. It creates or updates a resource-specific service that centralises API calls, wraps errors with `catchError`, reports failures through `MatSnackBar`, preserves typed `Observable<>` return values, and maintains a matching unit spec.

### Inputs

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path (used to locate the workspace)
- `project.name`: Project name (used to resolve the application directory)

Procedure-level input (provided by `build_app` when invoking this skill):
- `resource_name` (string): Resource name used to resolve the generated `<Resource>ApiService` and related model types

**Resource Mapping**:
- `resource_name` maps to `<Resource>ApiService` generated by the `ng-api` skill
- Service file names follow Angular conventions such as `features/<resource>/services/<resource>.service.ts`
- Shared services that are reused across features may instead live in `core/services/<resource>.service.ts`

### Modes

#### Create

Generate a new Angular data service and unit spec when a resource already has generated OpenAPI client code.

**Input Requirements**:
- `resource_name` (string): Name of the resource to wrap
- Optional placement hint indicating feature-local service (`features/<resource>/services/`) or shared service (`core/services/`)

**Process**:
1. **Pre-flight validation**:
   - Verify the Angular workspace exists
   - Verify the generated `<Resource>ApiService` exists and is importable
   - Identify the generated model and request/response types needed for method signatures
2. **Choose placement**:
   - Use `features/<resource>/services/` when the service belongs to one feature area
   - Use `core/services/` when the same wrapper is shared by multiple features
3. **Scaffold the service**:
   - Create `<resource>.service.ts` from `templates/service.ts.tpl`
   - Inject the generated `<Resource>ApiService` and `MatSnackBar`
   - Add one wrapper method per generated API method
   - Preserve typed `Observable<>` return values for every wrapper
   - Wrap each API call with `catchError(...)` and route user-facing failures through `MatSnackBar`
   - Add success notifications for state-changing wrappers such as create, update, patch, and delete operations; do not add them for read-only list, get, or search methods
4. **Add focused tests**:
   - Create `<resource>.service.spec.ts` beside the service
   - Configure `TestBed` with `HttpClientTestingModule`
   - Mock or spy on `<Resource>ApiService` and `MatSnackBar`
   - Verify wrapped methods delegate correctly, preserve return types, and surface error handling behavior
5. **Report generated artifacts**:
   - List the created `.service.ts` and `.spec.ts` files
   - Summarise wrapped API methods

**Output**:
- New Angular data service at `features/<resource>/services/<resource>.service.ts` or `core/services/<resource>.service.ts`
- Matching unit spec at the same location with `.spec.ts` suffix
- Wrapped methods for each generated `<Resource>ApiService` endpoint

#### Modify

Update an existing Angular data service when generated API methods or service behavior changes.

**Input Requirements**:
- `resource_name` (string): Name of the resource whose service should be updated
- Description of the required change, such as added/removed endpoints, caching changes, or updated error-handling rules

**Process**:
1. Locate the existing `<resource>.service.ts` and `.spec.ts`
2. Reconcile the wrapper surface with the current `<Resource>ApiService`
   - Add wrapper methods for new generated API methods
   - Remove wrapper methods that no longer have generated counterparts
3. Apply requested behavioral updates
   - Change caching strategy where required
   - Update `catchError` logic and snack-bar messaging
   - Adjust mapping logic while keeping typed `Observable<>` returns intact
4. Update the spec to match the service changes
   - Add or remove tests for wrapped methods
   - Update caching and error-handling assertions
5. Report the modified methods and any removed wrappers

**Output**:
- Updated `<resource>.service.ts`
- Updated `<resource>.service.spec.ts`
- Change summary covering wrapped methods, caching, and error handling

#### Delete

Remove a handwritten Angular data service and its associated unit spec.

**Input Requirements**:
- `resource_name` (string): Name of the resource whose service should be removed

**Process**:
1. Locate the target `<resource>.service.ts` in `features/<resource>/services/` or `core/services/`
2. Verify the paired `<resource>.service.spec.ts` file exists if tests were generated
3. Remove both files
4. Check for any now-stale barrel exports (`index.ts` re-export files) or imports; remove them automatically when the deleted service is the only matching export or when a grep check confirms there are no remaining imports, otherwise report the required manual follow-up

**Output**:
- Removed `<resource>.service.ts`
- Removed `<resource>.service.spec.ts`
- Confirmation of deleted artifacts and any follow-up cleanup notes

### Context Files

See [openapi-integration.md](../shared/openapi-integration.md)

### Supporting Files

- `templates/service.ts.tpl` — Service scaffold that wraps generated `<Resource>ApiService` methods with typed `Observable<>` returns and shared error handling
- `context/openapi-integration.md` — Guidance for locating generated OpenAPI services, models, and import paths

### Validation

**Post-Create/Modify Validation**:
1. **Compile check**:
   ```bash
   pnpm exec tsc --noEmit --project tsconfig.json
   ```
   - Confirm the service and spec compile with the generated API imports
2. **Spec run**:
   ```bash
   pnpm exec ng test --watch=false --include='**/<resource>.service.spec.ts'
   ```
   - Confirm the targeted service spec passes
3. **Manual review**:
   - Verify every generated `<Resource>ApiService` method that should be exposed has a matching wrapper
   - Verify `catchError` and `MatSnackBar` behavior are present on error paths

### Error Handling

**Common Errors**:

1. **Generated API service missing**:
   - Error: `<Resource>ApiService` cannot be resolved
   - Resolution: Run the `ng-api` skill first, then retry this skill

2. **Wrong service placement**:
   - Error: Service created in a feature folder but needed across the application
   - Resolution: Move the wrapper to `core/services/` and update imports

3. **Untyped wrapper methods**:
   - Error: Service methods return `Observable<any>` or lose generated model typing
   - Resolution: Reuse the generated request/response types from the OpenAPI client and restore explicit `Observable<>` signatures

4. **Spec not aligned with wrapper behavior**:
   - Error: Tests no longer cover all wrapped methods or error paths
   - Resolution: Update `<resource>.service.spec.ts` whenever methods, caching, or snack-bar behavior changes

### Dependencies

**Required Skills**:
- `ng-workspace` for the Angular workspace structure
- `ng-api` for the generated `<Resource>ApiService` dependency

**Required Tools/Libraries**:
- Angular workspace with TypeScript configuration
- Angular HTTP client testing support via `HttpClientTestingModule`
- Angular Material `MatSnackBar`

### Examples

**Example 1: Create a feature-local data service**
```markdown
Input:
- resource_name: "orders"

Process:
1. Verify OrdersApiService exists from ng-api generation
2. Create features/orders/services/orders.service.ts
3. Wrap each OrdersApiService method with typed Observable returns and catchError
4. Create features/orders/services/orders.service.spec.ts using HttpClientTestingModule

Output:
- features/orders/services/orders.service.ts
- features/orders/services/orders.service.spec.ts
```

**Example 2: Modify wrapper behavior after API regeneration**
```markdown
Input:
- resource_name: "users"
- change: "Add wrapper for new deactivate endpoint and update cache invalidation"

Process:
1. Compare UsersApiService methods with users.service.ts
2. Add deactivate wrapper and cache updates
3. Update error handling and spec coverage

Output:
- Updated users.service.ts
- Updated users.service.spec.ts
```

## Angular Material small field level component generation

```yaml
---
name: ng-field-component
description: Create, modify, or delete Angular Material small field-level components with typed input/output signals, Material imports, and ARIA accessibility
when_to_use: Use when build_app dispatches a small-field-component procedure node, or when a user runs /ng-field-component to scaffold a small reusable Material field-level component (badge, chip, button-with-icon, status indicator, etc.).
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

Generate and manage small, reusable Angular Material field-level components (e.g., custom buttons, chips, badges, status indicators, icons with tooltips). These are lightweight standalone components that use Angular signals for inputs/outputs, import only required Material modules, include ARIA attributes for accessibility, and utilize modern control flow syntax (`@if`/`@for`). Unlike form fields (skill 6) which implement `ControlValueAccessor`, these components are simple presentational or interactive elements used within larger components or pages.

### Modes

All skills support three operational modes:

#### Create

Generate a standalone Angular Material small field-level component from scratch with typed signals, Material imports, ARIA attributes, and test harness.

**Input Requirements**:

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path
- `project.name`: Application name within the workspace

Procedure-level inputs (provided by `build_app`):
- `componentName` (string, required): Name of the component in kebab-case (e.g., `status-badge`, `action-button`)
- `placement` (string, required): Where to place the component:
  - `shared` — Place in `projects/<project.name>/src/app/shared/components/` (for reusable components)
  - `feature/<feature-name>` — Place in `projects/<project.name>/src/app/features/<feature-name>/components/` (for feature-specific components)
- `componentType` (string, optional): Type of component to scaffold. Defaults to `generic`:
  - `button` — Action button with icon support
  - `chip` — Material chip with removable option
  - `badge` — Status or notification badge
  - `icon-tooltip` — Icon with Material tooltip
  - `generic` — Basic component scaffold
- `materialModules` (array, optional): List of Material modules to import (e.g., `['MatButtonModule', 'MatIconModule']`). Auto-selected based on `componentType` if not provided

**Process**:

1. **Validate prerequisites**:
   - Read `angular.output` and `project.name` from `django-angular3.json`
   - Verify workspace exists at `angular.output` and contains `angular.json`
   - Verify application `<project.name>` exists in `projects/<project.name>/`
   - Confirm workspace uses standalone component architecture
   - Validate `componentName` follows naming conventions (lowercase, hyphenated)
   - Check component doesn't already exist at target path

2. **Determine target directory**:
   - If `placement` is `shared`:
     - Target: `projects/<project.name>/src/app/shared/components/<componentName>/`
   - If `placement` is `feature/<feature-name>`:
     - Target: `projects/<project.name>/src/app/features/<feature-name>/components/<componentName>/`
   - Create directory if it doesn't exist:
     ```bash
     mkdir -p <targetDirectory>
     ```

3. **Generate component TypeScript file** using `templates/component.ts.tpl`:
   - Create `<componentName>.component.ts` with:
     - `@Component` decorator with `standalone: true`
     - Typed input signals using `input<T>()` with appropriate types
     - Typed output signals using `output<T>()` with appropriate types
     - Import only required Material modules based on `componentType` or `materialModules`
     - Import `CommonModule` for built-in directives
     - Component class with PascalCase naming: `<ComponentName>Component`
     - Selector: `app-<component-name>`
   - Placeholders to replace:
     - `{{COMPONENT_NAME_KEBAB}}` → e.g., `status-badge`
     - `{{COMPONENT_NAME_PASCAL}}` → e.g., `StatusBadge`
   - Customize based on `componentType`:
     - **button**: Add `MatButtonModule`, `MatIconModule`; input for `label`, `icon`, `disabled`; output for `clicked`
     - **chip**: Add `MatChipsModule`; input for `label`, `removable`; output for `removed`
     - **badge**: Add `MatBadgeModule`, `MatIconModule`; input for `count`, `color`
     - **icon-tooltip**: Add `MatIconModule`, `MatTooltipModule`; input for `icon`, `tooltip`
     - **generic**: Add `MatCardModule`, `MatButtonModule`; basic input/output signals

4. **Generate component HTML template** using `templates/component.html.tpl`:
   - Create `<componentName>.component.html` with:
     - Material component markup based on `componentType`
     - Use `@if` for conditional rendering (not `*ngIf`)
     - Use `@for` for list rendering (not `*ngFor`)
     - Add ARIA attributes: `aria-label`, `role`, `aria-describedby`, etc.
     - Bind to signals using signal call syntax: `{{ title() }}`
     - Event bindings to component methods
   - Ensure accessibility:
     - Add `role` attributes where appropriate
     - Add `aria-label` for icon-only buttons
     - Add `tabindex` for keyboard navigation
     - Add `aria-hidden="true"` for decorative elements

5. **Generate component SCSS file** using `templates/component.scss.tpl`:
   - Create `<componentName>.component.scss` with:
     - `:host` selector for component-level styles
     - Material theme token usage via `mat.get-theme-color()` and `mat.get-theme-typography()`
     - No hardcoded colors or typography (use theme tokens)
     - Responsive sizing using relative units
   - Example structure:
     ```scss
     @use '@angular/material' as mat;

     :host {
       display: inline-block;

       .component-wrapper {
         // Use theme tokens
         color: mat.get-theme-color(primary, 700);
         background: mat.get-theme-color(primary, 50);
       }
     }
     ```

6. **Generate component spec file**:
   - Create `<componentName>.component.spec.ts` with:
     - Angular Testing Library setup (if available) or ComponentFixture
     - Material test harness imports (e.g., `MatButtonHarness`)
     - Test suite structure:
       - `should create` test
       - Input signal tests (verify signals update correctly)
       - Output signal tests (verify events emit correctly)
       - Material component interaction tests using harnesses
       - ARIA attribute tests
     - Example test structure:
       ```typescript
       import { ComponentFixture, TestBed } from '@angular/core/testing';
       import { HarnessLoader } from '@angular/cdk/testing';
       import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';
       import { MatButtonHarness } from '@angular/material/button/testing';
       import { StatusBadgeComponent } from './status-badge.component';

       describe('StatusBadgeComponent', () => {
         let component: StatusBadgeComponent;
         let fixture: ComponentFixture<StatusBadgeComponent>;
         let loader: HarnessLoader;

         beforeEach(async () => {
           await TestBed.configureTestingModule({
             imports: [StatusBadgeComponent]
           }).compileComponents();

           fixture = TestBed.createComponent(StatusBadgeComponent);
           component = fixture.componentInstance;
           loader = TestbedHarnessEnvironment.loader(fixture);
           fixture.detectChanges();
         });

         it('should create', () => {
           expect(component).toBeTruthy();
         });

         it('should display input signal value', () => {
           fixture.componentRef.setInput('status', 'active');
           fixture.detectChanges();
           // Test implementation
         });

         it('should emit output signal on interaction', async () => {
           const button = await loader.getHarness(MatButtonHarness);
           // Test implementation
         });
       });
       ```

7. **Update barrel export** (if in shared directory):
   - Read `projects/<project.name>/src/app/shared/components/index.ts`
   - If file doesn't exist, create it
   - Add export: `export * from './<componentName>/<componentName>.component';`
   - Maintain alphabetical ordering

8. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Confirm build completes without errors
   - Check for TypeScript errors

9. **Run component tests**:
   ```bash
   pnpm exec ng test <project.name> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Confirm all tests pass

**Output**:
- Complete standalone component created at target directory:
  - `<componentName>.component.ts` — Component TypeScript with typed signals
  - `<componentName>.component.html` — Template with ARIA attributes and modern control flow
  - `<componentName>.component.scss` — Styles using Material theme tokens
  - `<componentName>.component.spec.ts` — Test suite with Material test harnesses
- Updated barrel export in `index.ts` (if applicable)
- Compilation verification successful
- Tests passing
- Confirmation message with component location and usage example

#### Modify

Update an existing Angular Material small field-level component by adding/removing inputs/outputs, updating template, or modifying styles.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName` (string, required): Name of the existing component to modify
- `placement` (string, required): Current placement location (`shared` or `feature/<feature-name>`)
- `modifications` (object, required): Changes to apply:
  - `addInputs`: Array of input signals to add with type information
    - Format: `[{ name: 'newInput', type: 'string', default: "''" }]`
  - `removeInputs`: Array of input signal names to remove
  - `addOutputs`: Array of output signals to add with type information
    - Format: `[{ name: 'newAction', type: 'void' }]`
  - `removeOutputs`: Array of output signal names to remove
  - `updateTemplate`: HTML string to replace or modify template sections
  - `updateStyles`: SCSS rules to add or modify
  - `addMaterialModules`: Array of Material module names to import
  - `removeMaterialModules`: Array of Material module names to remove

**Process**:

1. **Validate component exists**:
   - Determine target directory from `placement`
   - Verify component files exist:
     - `<componentName>.component.ts`
     - `<componentName>.component.html`
     - `<componentName>.component.scss`
     - `<componentName>.component.spec.ts`

2. **Modify TypeScript component**:
   - If `addInputs` specified:
     - Read `<componentName>.component.ts`
     - Add new input signals to component class:
       ```typescript
       newInput = input<string>(''); // with default value
       ```
     - Add TypeScript imports if needed for new types
   - If `removeInputs` specified:
     - Remove input signal declarations
     - Search template for usage and warn if still referenced
   - If `addOutputs` specified:
     - Add new output signals:
       ```typescript
       newAction = output<void>();
       ```
     - Add corresponding emit methods if needed
   - If `removeOutputs` specified:
     - Remove output signal declarations
     - Search template for event bindings and remove
   - If `addMaterialModules` specified:
     - Add imports to `imports` array in `@Component` decorator
     - Add import statement at top of file
   - If `removeMaterialModules` specified:
     - Remove from `imports` array
     - Remove import statement (if no longer used)
     - Warn if template still uses removed module components

3. **Modify HTML template**:
   - If `updateTemplate` specified:
     - Read `<componentName>.component.html`
     - Apply template modifications:
       - Add new elements
       - Update existing elements
       - Remove elements
     - Ensure ARIA attributes remain present
     - Verify modern control flow syntax (`@if`/`@for`)
     - Update signal bindings if inputs changed

4. **Modify SCSS styles**:
   - If `updateStyles` specified:
     - Read `<componentName>.component.scss`
     - Append new styles or modify existing selectors
     - Ensure theme token usage (no hardcoded colors)
     - Maintain `:host` selector pattern

5. **Update tests**:
   - Read `<componentName>.component.spec.ts`
   - Add tests for new inputs/outputs
   - Update existing tests if template/behavior changed
   - Remove tests for removed inputs/outputs
   - Ensure Material test harness usage updated

6. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

7. **Run updated tests**:
   ```bash
   pnpm exec ng test <project.name> --watch=false --include='**/<componentName>.component.spec.ts'
   ```

**Output**:
- Modified component files with requested changes
- Updated tests reflecting new behavior
- Compilation successful
- All tests passing
- Change summary listing what was modified

#### Delete

Remove an Angular Material small field-level component completely, including all files and references.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName` (string, required): Name of the component to delete
- `placement` (string, required): Current placement location
- `confirmDelete` (boolean, required): Safety confirmation (must be `true`)

**Process**:

1. **Validate component exists**:
   - Determine target directory from `placement`
   - Verify component directory exists

2. **Check for component usage**:
   - Search for imports of the component across the application:
     ```bash
     cd projects/<project.name>/src/app
     grep -r "import.*<ComponentName>Component" --include="*.ts"
     ```
   - If component is imported anywhere, list usage locations and warn:
     - "Component is used in X file(s). Remove imports before deletion or use --force flag."
   - For `--force` mode, automatically remove imports from detected files

3. **Remove from barrel exports**:
   - If component was in `shared/components/`:
     - Read `projects/<project.name>/src/app/shared/components/index.ts`
     - Remove export line: `export * from './<componentName>/<componentName>.component';`
   - If component was in feature directory, check for feature-level barrel exports

4. **Delete component directory**:
   ```bash
   rm -rf <targetDirectory>/<componentName>
   ```

5. **Remove from any imports arrays** (if referenced in other components):
   - Search for component usage in `imports` arrays
   - Remove from component imports
   - This step only executes if `--force` flag used or no usages found

6. **Verify compilation after deletion**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Confirm build succeeds (no broken imports)

7. **Run tests**:
   ```bash
   pnpm exec ng test <project.name> --watch=false
   ```
   - Confirm no failing tests due to missing component

**Output**:
- Component directory removed
- Barrel exports updated
- All component imports removed from codebase
- Compilation successful
- Confirmation message with deletion summary

### Context Files

See [angular-conventions.md](../shared/angular-conventions.md)

See [angular-material-patterns.md](../shared/angular-material-patterns.md)

### Templates

- `component.ts.tpl` — Standalone component TypeScript scaffold with typed input/output signals, Material imports, and signal-based state management
- `component.html.tpl` — Component template with Material components, ARIA attributes, and modern control flow (`@if`/`@for`)
- `component.scss.tpl` — Component styles using Material theme tokens and `:host` selector pattern

### Validation

Steps to validate successful execution of the skill:

**Post-Create Validation**:
1. **Verify directory structure**:
   ```bash
   ls -la <targetDirectory>/<componentName>/
   ```
   - Should contain: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`

2. **Verify component is standalone**:
   ```bash
   grep "standalone: true" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should return match

3. **Verify signal usage**:
   ```bash
   grep -E "input<|output<" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find typed input/output signals

4. **Verify ARIA attributes**:
   ```bash
   grep -E "aria-|role=" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should find ARIA attributes in template

5. **Verify modern control flow**:
   ```bash
   grep -E "@if|@for" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should use `@if`/`@for` (not `*ngIf`/`*ngFor`)

6. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Should complete without errors

7. **Run specs**:
   ```bash
   pnpm exec ng test <project.name> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Should pass all tests

8. **Check Material test harness usage**:
   ```bash
   grep "Harness" <targetDirectory>/<componentName>/<componentName>.component.spec.ts
   ```
   - Should find Material test harness imports and usage

**Post-Modify Validation**:
1. **Verify requested changes applied**:
   - Check TypeScript file for added/removed inputs/outputs
   - Check template for updated markup
   - Check styles for new SCSS rules

2. **Compile and test** (same as create mode steps 6-7)

**Post-Delete Validation**:
1. **Verify component removed**:
   ```bash
   [ ! -d <targetDirectory>/<componentName> ] && echo "Component deleted"
   ```

2. **Verify no broken imports**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Should compile successfully

### Error Handling

Common errors and their resolution strategies:

**Error**: `Component <componentName> already exists`
- **Cause**: Attempting to create a component with a name that already exists
- **Resolution**: Use Modify mode to update existing component, or Delete mode first, or choose a different name

**Error**: Application `<project.name>` not found in workspace
- **Cause**: `project.name` in `django-angular3.json` does not match any project in the workspace
- **Resolution**: Verify `angular.output` contains `angular.json` and the application exists in `projects/`

**Error**: `Invalid placement path: feature/<feature-name> does not exist`
- **Cause**: Feature directory doesn't exist
- **Resolution**: Create feature directory first or use `placement: 'shared'`

**Error**: `Component name must be in kebab-case`
- **Cause**: Component name uses PascalCase, camelCase, or contains invalid characters
- **Resolution**: Convert name to kebab-case (e.g., `MyComponent` → `my-component`)

**Error**: `Material module <ModuleName> not found`
- **Cause**: Specified Material module doesn't exist or isn't installed
- **Resolution**: Verify Material is installed (`@angular/material` in `package.json`) and module name is correct

**Error**: `Compilation failed: Cannot find name '<SignalName>'`
- **Cause**: Signal used in template but not declared in component
- **Resolution**: Verify all template bindings correspond to declared input/output signals

**Error**: `Component is still imported in X files`
- **Cause**: Attempting to delete component that's still in use
- **Resolution**: Remove imports from listed files first, or use `--force` flag to auto-remove

**Error**: `Tests failing after modification`
- **Cause**: Tests not updated to reflect component changes
- **Resolution**: Update test file to match new component inputs/outputs/behavior

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1) — Workspace must exist with Angular Material installed
2. **Angular Material app boilerplate** (Skill 2) — Application must exist in workspace with proper directory structure

Optional dependencies:

- None — This skill is independent and can be executed once workspace and app exist

Dependent skills (use this skill before):

- **Angular Material form field generation** (Skill 6) — May use field components as building blocks
- **Angular component generation** (Skill 7) — May compose field components into larger components
- **Angular Material page generation** (Skill 10) — Pages may use field components

### Examples

**Example 1: Create a status badge component in shared**

Input from `django-angular3.json`: `angular.output = "/workspace/my-project"`, `project.name = "admin-dashboard"`

```json
{
  "mode": "create",
  "componentName": "status-badge",
  "placement": "shared",
  "componentType": "badge",
  "materialModules": ["MatBadgeModule", "MatIconModule"]
}
```

**Execution**:
1. Validate workspace and app exist
2. Create directory: `projects/admin-dashboard/src/app/shared/components/status-badge/`
3. Generate TypeScript component with:
   - Input: `status = input<'active' | 'inactive' | 'pending'>('active')`
   - Input: `count = input<number>(0)`
   - Output: `clicked = output<void>()`
4. Generate HTML template:
   ```html
   <div class="status-badge"
        [class.active]="status() === 'active'"
        [class.inactive]="status() === 'inactive'"
        [class.pending]="status() === 'pending'"
        role="status"
        [attr.aria-label]="'Status: ' + status()">
     @if (count() > 0) {
       <mat-icon [matBadge]="count()" matBadgeColor="warn">notifications</mat-icon>
     } @else {
       <mat-icon>check_circle</mat-icon>
     }
   </div>
   ```
5. Generate SCSS with theme tokens
6. Generate spec with Material test harness
7. Update `shared/components/index.ts`: `export * from './status-badge/status-badge.component';`
8. Compile and test

**Output**: Status badge component created at `projects/admin-dashboard/src/app/shared/components/status-badge/`

**Example 2: Create an action button in a feature**

```json
{
  "mode": "create",
  "componentName": "export-button",
  "placement": "feature/reports",
  "componentType": "button"
}
```

**Execution**:
1. Create directory: `projects/admin-dashboard/src/app/features/reports/components/export-button/`
2. Generate component with:
   - Input: `label = input<string>('Export')`
   - Input: `icon = input<string>('download')`
   - Input: `disabled = input<boolean>(false)`
   - Output: `clicked = output<void>()`
3. Generate template with Material button, icon, and ARIA attributes
4. Compile and test

**Output**: Export button component created in reports feature

**Example 3: Modify existing component to add new input**

```json
{
  "mode": "modify",
  "componentName": "status-badge",
  "placement": "shared",
  "modifications": {
    "addInputs": [
      { "name": "size", "type": "'small' | 'medium' | 'large'", "default": "'medium'" }
    ],
    "updateStyles": ".status-badge.small { font-size: 12px; }\n.status-badge.large { font-size: 20px; }"
  }
}
```

**Execution**:
1. Read existing component files
2. Add to TypeScript: `size = input<'small' | 'medium' | 'large'>('medium')`
3. Update HTML: Add `[class.small]="size() === 'small'"` and `[class.large]="size() === 'large'"`
4. Append SCSS rules for size variants
5. Update tests to verify size input
6. Compile and test

**Output**: Status badge component updated with size variants

**Example 4: Delete component**

```json
{
  "mode": "delete",
  "componentName": "old-badge",
  "placement": "shared",
  "confirmDelete": true
}
```

**Execution**:
1. Check for usage (find no imports)
2. Remove from `shared/components/index.ts`
3. Delete directory: `projects/admin-dashboard/src/app/shared/components/old-badge/`
4. Verify compilation succeeds

**Output**: Component deleted successfully

## Angular Material form field generation

```yaml
---
name: ng-form-field
description: Create, modify, or delete Angular Material form field components implementing ControlValueAccessor for seamless reactive forms integration with validation and error handling
when_to_use: Use when build_app dispatches a form-field-component procedure node, or when a user runs /ng-form-field to scaffold a Material form-field component that implements ControlValueAccessor for reactive forms.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

Generate and manage Angular Material form field components that implement `ControlValueAccessor` for seamless integration with Angular reactive forms. These components wrap Material form field elements (`MatFormField`, `MatInput`, `MatSelect`, `MatDatepicker`, `MatAutocomplete`, `MatTextarea`) with custom validation, error messages, labels, hints, and disabled state handling. Unlike simple field-level components (skill 5) which are presentational, form field components implement the full `ControlValueAccessor` interface (`writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`) and provide `NG_VALUE_ACCESSOR`, enabling them to work as custom form controls within `FormGroup` and `FormControl` contexts.

### Modes

All skills support three operational modes:

#### Create

Generate a standalone Angular Material form field component implementing `ControlValueAccessor` with Material form field wrapper, validation support, and test harness.

**Input Requirements**:

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path
- `project.name`: Application name within the workspace

Procedure-level inputs:
- `componentName` (string, required): Name of the form field component in kebab-case (e.g., `email-input`, `date-picker`, `country-select`)
- `placement` (string, required): Where to place the component:
  - `shared` — Place in `projects/<project.name>/src/app/shared/form-fields/` (for reusable form fields)
  - `feature/<feature-name>` — Place in `projects/<project.name>/src/app/features/<feature-name>/form-fields/` (for feature-specific form fields)
- `fieldType` (enum, required): Type of input field to scaffold:
  - `input` — Text input field (default, supports type="text|number|email|password|tel|url")
  - `textarea` — Multi-line text area
  - `select` — Dropdown select with options
  - `datepicker` — Material datepicker with date input
  - `autocomplete` — Material autocomplete with filtering
- `inputType` (string, optional): HTML input type for `fieldType: 'input'` (default: `'text'`). Options: `text`, `number`, `email`, `password`, `tel`, `url`
- `valueType` (string, optional): TypeScript type for the form control value (default: `string`). Common types: `string`, `number`, `Date`, `boolean`, or custom types
- `validators` (array, optional): List of Angular validators to include (e.g., `['required', 'email', 'minLength', 'maxLength', 'pattern']`). These generate corresponding error message blocks in the template

**Process**:

1. **Validate prerequisites**:
   - Read `angular.output` and `project.name` from `django-angular3.json`
   - Verify workspace exists at `angular.output` and contains `angular.json`
   - Verify application `<project.name>` exists in `projects/<project.name>/`
   - Confirm workspace uses standalone component architecture
   - Validate `componentName` follows naming conventions (lowercase, hyphenated)
   - Check component doesn't already exist at target path

2. **Determine target directory**:
   - If `placement` is `shared`:
     - Target: `projects/<project.name>/src/app/shared/form-fields/<componentName>/`
   - If `placement` is `feature/<feature-name>`:
     - Target: `projects/<project.name>/src/app/features/<feature-name>/form-fields/<componentName>/`
   - Create directory if it doesn't exist:
     ```bash
     mkdir -p <targetDirectory>
     ```

3. **Generate component TypeScript file** using `templates/form-field.ts.tpl`:
   - Create `<componentName>.component.ts` with:
     - `@Component` decorator with `standalone: true`
     - Implement `ControlValueAccessor` interface with:
       - `writeValue(value: T): void` — Write new value to the component
       - `registerOnChange(fn: (value: T) => void): void` — Register callback for value changes
       - `registerOnTouched(fn: () => void): void` — Register callback for touch events
       - `setDisabledState(isDisabled: boolean): void` — Handle disabled state
     - Provide `NG_VALUE_ACCESSOR` in `providers` array using `forwardRef`
     - Import Material modules based on `fieldType`:
       - **input/textarea**: `MatFormFieldModule`, `MatInputModule`, `ReactiveFormsModule`, `CommonModule`
       - **select**: Add `MatSelectModule`
       - **datepicker**: Add `MatDatepickerModule`, `MatNativeDateModule`
       - **autocomplete**: Add `MatAutocompleteModule`
     - Input signals for configuration:
       - `label = input<string>('')` — Field label text
       - `placeholder = input<string>('')` — Placeholder text
       - `hint = input<string>('')` — Hint text below field
       - `required = input<boolean>(false)` — Required indicator
       - For **select**: `options = input<Array<{value: T, label: string}>>([])`
       - For **datepicker**: `minDate = input<Date | null>(null)`, `maxDate = input<Date | null>(null)`
       - For **autocomplete**: `options = input<Array<T>>([])`, `displayFn = input<(value: T) => string>(() => String)`
     - Internal state properties:
       - `value: T` — Current value
       - `disabled: boolean` — Disabled state
       - `onChange: (value: T) => void` — Change callback
       - `onTouched: () => void` — Touch callback
     - Value change handler:
       - `onValueChange(value: T): void` — Called on user input, propagates to form control
     - Component class with PascalCase naming: `<ComponentName>Component`
     - Selector: `app-<component-name>`
   - Placeholders to replace:
     - `{{FIELD_NAME_KEBAB}}` → e.g., `email-input`
     - `{{FIELD_NAME_PASCAL}}` → e.g., `EmailInput`
     - `{{VALUE_TYPE}}` → e.g., `string`, `number`, `Date`

4. **Generate component HTML template** using `templates/form-field.html.tpl`:
   - Create `<componentName>.component.html` with:
     - Wrap input in `<mat-form-field>` with `appearance="outline"`
     - Add `<mat-label>` bound to `label()` signal
     - Add appropriate input element based on `fieldType`:
       - **input**: `<input matInput [type]="inputType" [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled" [placeholder]="placeholder()">`
       - **textarea**: `<textarea matInput [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled" [placeholder]="placeholder()"></textarea>`
       - **select**: `<mat-select [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled">` with `@for (option of options(); track option.value)` for options
       - **datepicker**: `<input matInput [matDatepicker]="picker" [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled" [min]="minDate()" [max]="maxDate()">` with `<mat-datepicker #picker></mat-datepicker>`
       - **autocomplete**: `<input matInput [matAutocomplete]="auto" [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled">` with `<mat-autocomplete #auto="matAutocomplete">`
     - Add `<mat-hint>` bound to `hint()` signal
     - Add `<mat-error>` blocks for each validator:
       - **required**: `@if (formControl?.hasError('required')) { <mat-error>This field is required</mat-error> }`
       - **email**: `@if (formControl?.hasError('email')) { <mat-error>Please enter a valid email</mat-error> }`
       - **minlength**: `@if (formControl?.hasError('minlength')) { <mat-error>Minimum length is {{ formControl.errors?.['minlength'].requiredLength }}</mat-error> }`
       - **maxlength**: `@if (formControl?.hasError('maxlength')) { <mat-error>Maximum length is {{ formControl.errors?.['maxlength'].requiredLength }}</mat-error> }`
       - **pattern**: `@if (formControl?.hasError('pattern')) { <mat-error>Invalid format</mat-error> }`
     - Note: Error messages require access to parent form control. Pass via input: `formControl = input<FormControl | null>(null)`
     - Use modern control flow (`@if`, `@for`) instead of `*ngIf`, `*ngFor`
     - Add ARIA attributes: `[attr.aria-required]="required()"`, `[attr.aria-invalid]="formControl?.invalid && formControl?.touched"`

5. **Generate component SCSS file** using `templates/component.scss.tpl`:
   - Create `<componentName>.component.scss` with:
     - `:host` selector with `display: block; width: 100%;`
     - Material theme token usage for colors
     - Responsive sizing
   - Example structure:
     ```scss
     @use '@angular/material' as mat;

     :host {
       display: block;
       width: 100%;

       mat-form-field {
         width: 100%;
       }
     }
     ```

6. **Generate component spec file**:
   - Create `<componentName>.component.spec.ts` with:
     - Import `ReactiveFormsModule` and `FormControl` for testing
     - Import Material test harnesses: `MatFormFieldHarness`, `MatInputHarness` (or appropriate harness for field type)
     - Test suite structure:
       - **should create** — Component initialization test
       - **ControlValueAccessor tests**:
         - `writeValue()` should update internal value
         - `registerOnChange()` should register callback
         - `registerOnTouched()` should register callback
         - `setDisabledState()` should disable/enable input
         - Value changes should call `onChange` callback
         - Blur events should call `onTouched` callback
       - **Reactive forms integration test**:
         - Create `FormControl` and bind to component
         - Set value via form control, verify component updates
         - Change value in component, verify form control updates
         - Set form control to disabled, verify component disables
       - **Validation tests** (if validators specified):
         - Test error messages display correctly
         - Test required validation
         - Test specific validators (email, minLength, etc.)
       - **Material harness tests**:
         - Use `MatFormFieldHarness` to verify label, hint, error display
         - Use input harness to interact with input programmatically
     - Example test structure:
       ```typescript
       import { ComponentFixture, TestBed } from '@angular/core/testing';
       import { ReactiveFormsModule, FormControl, Validators } from '@angular/forms';
       import { HarnessLoader } from '@angular/cdk/testing';
       import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';
       import { MatFormFieldHarness } from '@angular/material/form-field/testing';
       import { MatInputHarness } from '@angular/material/input/testing';
       import { EmailInputComponent } from './email-input.component';
       import { NoopAnimationsModule } from '@angular/platform-browser/animations';

       describe('EmailInputComponent', () => {
         let component: EmailInputComponent;
         let fixture: ComponentFixture<EmailInputComponent>;
         let loader: HarnessLoader;

         beforeEach(async () => {
           await TestBed.configureTestingModule({
             imports: [
               EmailInputComponent,
               ReactiveFormsModule,
               NoopAnimationsModule
             ]
           }).compileComponents();

           fixture = TestBed.createComponent(EmailInputComponent);
           component = fixture.componentInstance;
           loader = TestbedHarnessEnvironment.loader(fixture);
           fixture.detectChanges();
         });

         it('should create', () => {
           expect(component).toBeTruthy();
         });

         it('should implement ControlValueAccessor writeValue', () => {
           component.writeValue('test@example.com');
           expect(component.value).toBe('test@example.com');
         });

         it('should call onChange when value changes', () => {
           const onChangeSpy = jasmine.createSpy('onChange');
           component.registerOnChange(onChangeSpy);

           component.onValueChange('new@example.com');

           expect(onChangeSpy).toHaveBeenCalledWith('new@example.com');
         });

         it('should integrate with reactive forms', async () => {
           const formControl = new FormControl('initial@example.com');

           // Bind component to form control
           component.writeValue(formControl.value);
           component.registerOnChange((value) => formControl.setValue(value, { emitEvent: false }));

           // Test form -> component
           formControl.setValue('updated@example.com');
           component.writeValue(formControl.value);
           expect(component.value).toBe('updated@example.com');

           // Test component -> form
           component.onValueChange('changed@example.com');
           expect(formControl.value).toBe('changed@example.com');
         });

         it('should display error messages using harness', async () => {
           const formControl = new FormControl('', Validators.required);
           component.formControl = () => formControl;
           formControl.markAsTouched();
           fixture.detectChanges();

           const formField = await loader.getHarness(MatFormFieldHarness);
           const errors = await formField.getTextErrors();

           expect(errors).toContain('This field is required');
         });

         it('should disable input when setDisabledState is called', async () => {
           component.setDisabledState(true);
           fixture.detectChanges();

           const input = await loader.getHarness(MatInputHarness);
           expect(await input.isDisabled()).toBe(true);
         });
       });
       ```

7. **Update barrel export** (if placement is `shared` or feature has barrel file):
   - Append to `shared/form-fields/index.ts` or `features/<feature-name>/form-fields/index.ts`:
     ```typescript
     export * from './<componentName>/<componentName>.component';
     ```

8. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Verify build succeeds with no errors

9. **Run specs**:
   ```bash
   pnpm exec ng test <project.name> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Verify all tests pass

**Output**:
- Component files created: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`
- Component implements `ControlValueAccessor` interface
- Component integrated with reactive forms via `NG_VALUE_ACCESSOR`
- Validation and error handling configured
- Material form field wrapper with label, hint, error messages
- Test harness tests passing
- Barrel export updated
- Compilation successful

#### Modify

Update an existing form field component to change input type, add/remove validators, update error messages, or modify configuration.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName` (string, required): Name of the form field component to modify
- `placement` (string, required): Where the component is located (`shared` or `feature/<feature-name>`)
- `modifications` (object, required): Specifies what to modify:
  - `changeFieldType` (enum, optional): Change to different field type (`input` | `textarea` | `select` | `datepicker` | `autocomplete`)
  - `changeInputType` (string, optional): Change HTML input type (for `fieldType: 'input'`)
  - `changeValueType` (string, optional): Change TypeScript value type (requires updating generics throughout)
  - `addValidators` (array, optional): Add validators and corresponding error messages
  - `removeValidators` (array, optional): Remove validators and error message blocks
  - `updateErrorMessages` (object, optional): Map of validator names to new error message templates
  - `addInputSignals` (array, optional): Add new input signals (e.g., `[{ name: 'maxLength', type: 'number', default: '100' }]`)
  - `updateStyles` (string, optional): Additional SCSS to append

**Process**:

1. **Validate prerequisites**:
   - Verify component exists at target path
   - Read existing component files to understand current structure
   - Verify requested modifications are compatible with current implementation

2. **Apply modifications based on modification type**:

   **If `changeFieldType` specified**:
   - This is a significant change requiring updates to TypeScript, HTML, and imports
   - Read current component TypeScript file
   - Update imports:
     - Remove old Material module imports (e.g., `MatInputModule` if changing from `input`)
     - Add new Material module imports based on new `fieldType`
   - Update template file completely:
     - Replace input element markup with new field type markup
     - Preserve existing `@if` error blocks
     - Update bindings to match new field type requirements
   - Update spec file:
     - Change harness imports to match new field type
     - Update test interactions to use correct harness methods

   **If `addValidators` specified**:
   - For each validator in list:
     - Add corresponding `<mat-error>` block to HTML template
     - Use modern `@if` syntax with `formControl?.hasError('validatorName')`
     - Use appropriate error message template:
       - `required`: "This field is required"
       - `email`: "Please enter a valid email"
       - `minlength`: "Minimum length is {{requiredLength}}"
       - `maxlength`: "Maximum length is {{requiredLength}}"
       - `min`: "Minimum value is {{min}}"
       - `max`: "Maximum value is {{max}}"
       - `pattern`: "Invalid format"
   - Update spec file to add tests for new validators

   **If `removeValidators` specified**:
   - For each validator in list:
     - Remove corresponding `<mat-error>` block from HTML template
     - Remove validator tests from spec file

   **If `updateErrorMessages` specified**:
   - For each validator in map:
     - Find and replace the error message text in the `<mat-error>` block
     - Preserve the `@if` condition structure

   **If `addInputSignals` specified**:
   - For each signal to add:
     - Add signal declaration to TypeScript: `<name> = input<<type>>(<default>)`
     - Add binding to HTML template where appropriate
     - Update spec tests to verify new input signal

   **If `updateStyles` specified**:
   - Append provided SCSS to `.component.scss` file
   - Ensure no duplicate selectors

3. **Update spec file**:
   - Add tests for any new functionality
   - Update existing tests if behavior changed
   - Ensure all ControlValueAccessor tests still pass

4. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

5. **Run specs**:
   ```bash
   pnpm exec ng test <project.name> --watch=false --include='**/<componentName>.component.spec.ts'
   ```

**Output**:
- Component files updated with requested modifications
- All tests passing
- Compilation successful
- Changes documented in commit message

#### Delete

Remove a form field component completely from the codebase, including all related files and imports.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName` (string, required): Name of the form field component to delete
- `placement` (string, required): Where the component is located (`shared` or `feature/<feature-name>`)
- `confirmDelete` (boolean, required): Explicit confirmation flag to prevent accidental deletion
- `force` (boolean, optional): Force deletion even if component is still imported elsewhere (default: `false`)

**Process**:

1. **Validate prerequisites**:
   - Verify component exists at target path
   - Confirm `confirmDelete` is `true`

2. **Check for component usage**:
   - Search for imports of the component across codebase:
     ```bash
     grep -r "from.*<componentName>.component" projects/<project.name>/src/
     ```
   - If imports found and `force` is `false`:
     - Return error listing files that import the component
     - Require user to remove imports first or use `force: true`

3. **Remove from barrel exports**:
   - If `placement` is `shared`:
     - Remove export line from `shared/form-fields/index.ts`
   - If `placement` is `feature/<feature-name>`:
     - Remove export line from `features/<feature-name>/form-fields/index.ts` (if exists)

4. **Delete component directory**:
   - Determine target directory based on `placement`
   - Delete entire directory:
     ```bash
     rm -rf <targetDirectory>/<componentName>/
     ```

5. **Remove from any imports arrays** (if `force: true` and usages found):
   - Search for component usage in component `imports` arrays
   - Remove from component imports
   - This is a potentially breaking change, so log all modified files

6. **Verify compilation after deletion**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Confirm build succeeds (no broken imports)

7. **Run tests**:
   ```bash
   pnpm exec ng test <project.name> --watch=false
   ```
   - Confirm no failing tests due to missing component

**Output**:
- Component directory removed
- Barrel exports updated
- All component imports removed from codebase (if `force: true`)
- Compilation successful
- Confirmation message with deletion summary

### Context Files

See [angular-conventions.md](../shared/angular-conventions.md)

See [angular-material-patterns.md](../shared/angular-material-patterns.md)

### Templates

- `form-field.ts.tpl` — ControlValueAccessor TypeScript scaffold with `writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`, `NG_VALUE_ACCESSOR` provider, and typed signals
- `form-field.html.tpl` — Material form field template with `<mat-form-field>`, appropriate input element based on field type, label, hint, and error message blocks
- `component.scss.tpl` — Component styles using Material theme tokens and `:host` selector pattern

### Validation

Steps to validate successful execution of the skill:

**Post-Create Validation**:
1. **Verify directory structure**:
   ```bash
   ls -la <targetDirectory>/<componentName>/
   ```
   - Should contain: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`

2. **Verify ControlValueAccessor implementation**:
   ```bash
   grep "implements ControlValueAccessor" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should return match

3. **Verify NG_VALUE_ACCESSOR provider**:
   ```bash
   grep "NG_VALUE_ACCESSOR" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find provider configuration with `forwardRef`

4. **Verify required CVA methods**:
   ```bash
   grep -E "writeValue|registerOnChange|registerOnTouched|setDisabledState" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find all four interface methods

5. **Verify Material form field wrapper**:
   ```bash
   grep "<mat-form-field" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should find `<mat-form-field>` wrapper

6. **Verify error message blocks**:
   ```bash
   grep -E "@if.*hasError.*mat-error" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should find error handling with modern `@if` syntax

7. **Verify signal usage**:
   ```bash
   grep -E "input<|output<" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find typed input signals for label, placeholder, hint, etc.

8. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Should complete without errors

9. **Run specs**:
   ```bash
   pnpm exec ng test <project.name> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Should pass all tests including CVA tests

10. **Check Material test harness usage**:
    ```bash
    grep "FormFieldHarness" <targetDirectory>/<componentName>/<componentName>.component.spec.ts
    ```
    - Should find Material form field test harness imports and usage

**Post-Modify Validation**:
1. **Verify requested changes applied**:
   - Check TypeScript file for updated field type, validators, or signals
   - Check template for new error message blocks
   - Check styles for new SCSS rules

2. **Compile and test** (same as create mode steps 8-9)

**Post-Delete Validation**:
1. **Verify component removed**:
   ```bash
   [ ! -d <targetDirectory>/<componentName> ] && echo "Component deleted"
   ```

2. **Verify no broken imports**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Should compile successfully

### Error Handling

Common errors and their resolution strategies:

**Error**: `Component <componentName> already exists`
- **Cause**: Attempting to create a component with a name that already exists
- **Resolution**: Use Modify mode to update existing component, or Delete mode first, or choose a different name

**Error**: Application `<project.name>` not found in workspace
- **Cause**: `project.name` in `django-angular3.json` does not match any project in the workspace
- **Resolution**: Verify `angular.output` contains `angular.json` and the application exists in `projects/`

**Error**: `Invalid placement path: feature/<feature-name> does not exist`
- **Cause**: Feature directory doesn't exist
- **Resolution**: Create feature directory first or use `placement: 'shared'`

**Error**: `Component name must be in kebab-case`
- **Cause**: Component name uses PascalCase, camelCase, or contains invalid characters
- **Resolution**: Convert name to kebab-case (e.g., `EmailInput` → `email-input`)

**Error**: `Material module <ModuleName> not found`
- **Cause**: Specified Material module doesn't exist or isn't installed
- **Resolution**: Verify Material is installed (`@angular/material` in `package.json`) and module name is correct

**Error**: `NG_VALUE_ACCESSOR provider not found`
- **Cause**: Component missing `NG_VALUE_ACCESSOR` provider configuration
- **Resolution**: Add provider object with `provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Component), multi: true`

**Error**: `ControlValueAccessor interface not fully implemented`
- **Cause**: Missing one or more required interface methods
- **Resolution**: Ensure all four methods are implemented: `writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`

**Error**: `Cannot read formControl in template`
- **Cause**: `formControl` input signal not declared or not passed from parent
- **Resolution**: Add `formControl = input<FormControl | null>(null)` to component and pass from parent template

**Error**: `Compilation failed: Type mismatch in writeValue`
- **Cause**: Value type doesn't match declared `valueType`
- **Resolution**: Ensure all CVA methods use consistent generic type parameter

**Error**: `Tests failing: onChange not called`
- **Cause**: Value change handler not calling registered `onChange` callback
- **Resolution**: Ensure `onValueChange` method calls `this.onChange(value)` and `this.onTouched()`

**Error**: `Component is still imported in X files`
- **Cause**: Attempting to delete component that's still in use
- **Resolution**: Remove imports from listed files first, or use `force: true` flag to auto-remove

**Error**: `Validator error messages not displaying`
- **Cause**: Parent form control not passed to component or not marked as touched
- **Resolution**: Pass form control via input and ensure `markAsTouched()` is called on blur

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1) — Workspace must exist with Angular Material installed
2. **Angular Material app boilerplate** (Skill 2) — Application must exist in workspace with proper directory structure

Optional dependencies:

- None — This skill is independent and can be executed once workspace and app exist

Dependent skills (use this skill before):

- **Angular Material reactive form generation** (Skill 9) — Forms use form field components as custom controls
- **Angular Material page generation** (Skill 10) — Pages may include forms with custom form fields
- **Angular component generation** (Skill 7) — Complex components may compose form fields

### Examples

**Example 1: Create an email input form field in shared**

Input from `django-angular3.json`: `angular.output = "/workspace/my-project"`, `project.name = "admin-dashboard"`

```json
{
  "mode": "create",
  "componentName": "email-input",
  "placement": "shared",
  "fieldType": "input",
  "inputType": "email",
  "valueType": "string",
  "validators": ["required", "email"]
}
```

**Execution**:
1. Validate workspace and app exist
2. Create directory: `projects/admin-dashboard/src/app/shared/form-fields/email-input/`
3. Generate TypeScript component with:
   - Implements `ControlValueAccessor`
   - Provides `NG_VALUE_ACCESSOR`
   - Imports: `MatFormFieldModule`, `MatInputModule`, `ReactiveFormsModule`, `CommonModule`
   - Input signals: `label`, `placeholder`, `hint`, `required`, `formControl`
   - CVA methods: `writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`
   - Value type: `string`
4. Generate HTML template:
   ```html
   <mat-form-field appearance="outline">
     <mat-label>{{ label() }}</mat-label>
     <input matInput
            type="email"
            [(ngModel)]="value"
            (ngModelChange)="onValueChange($event)"
            (blur)="onTouched()"
            [disabled]="disabled"
            [placeholder]="placeholder()"
            [attr.aria-required]="required()"
            [attr.aria-invalid]="formControl()?.invalid && formControl()?.touched">
     @if (hint()) {
       <mat-hint>{{ hint() }}</mat-hint>
     }
     @if (formControl()?.hasError('required')) {
       <mat-error>This field is required</mat-error>
     }
     @if (formControl()?.hasError('email')) {
       <mat-error>Please enter a valid email address</mat-error>
     }
   </mat-form-field>
   ```
5. Generate SCSS with `:host` and theme tokens
6. Generate spec with CVA tests and Material harness tests
7. Update `shared/form-fields/index.ts`: `export * from './email-input/email-input.component';`
8. Compile and test

**Output**: Email input form field component created at `projects/admin-dashboard/src/app/shared/form-fields/email-input/`

**Example 2: Create a country select form field in a feature**

```json
{
  "mode": "create",
  "componentName": "country-select",
  "placement": "feature/users",
  "fieldType": "select",
  "valueType": "string",
  "validators": ["required"]
}
```

**Execution**:
1. Create directory: `projects/admin-dashboard/src/app/features/users/form-fields/country-select/`
2. Generate component with:
   - Field type: `select`
   - Input signal: `options = input<Array<{value: string, label: string}>>([])`
   - CVA implementation for `string` value type
   - Imports: `MatFormFieldModule`, `MatSelectModule`, `ReactiveFormsModule`, `CommonModule`
3. Generate template with:
   ```html
   <mat-form-field appearance="outline">
     <mat-label>{{ label() }}</mat-label>
     <mat-select [(ngModel)]="value"
                 (ngModelChange)="onValueChange($event)"
                 (blur)="onTouched()"
                 [disabled]="disabled"
                 [placeholder]="placeholder()">
       @for (option of options(); track option.value) {
         <mat-option [value]="option.value">{{ option.label }}</mat-option>
       }
     </mat-select>
     @if (formControl()?.hasError('required')) {
       <mat-error>Please select a country</mat-error>
     }
   </mat-form-field>
   ```
4. Compile and test

**Output**: Country select form field component created in users feature

**Example 3: Create a date picker form field with min/max date**

```json
{
  "mode": "create",
  "componentName": "birth-date-picker",
  "placement": "feature/users",
  "fieldType": "datepicker",
  "valueType": "Date",
  "validators": ["required"]
}
```

**Execution**:
1. Create directory: `projects/admin-dashboard/src/app/features/users/form-fields/birth-date-picker/`
2. Generate component with:
   - Field type: `datepicker`
   - Input signals: `minDate = input<Date | null>(null)`, `maxDate = input<Date | null>(null)`
   - CVA implementation for `Date` value type
   - Imports: `MatFormFieldModule`, `MatInputModule`, `MatDatepickerModule`, `MatNativeDateModule`, `ReactiveFormsModule`, `CommonModule`
3. Generate template with:
   ```html
   <mat-form-field appearance="outline">
     <mat-label>{{ label() }}</mat-label>
     <input matInput
            [matDatepicker]="picker"
            [(ngModel)]="value"
            (ngModelChange)="onValueChange($event)"
            (blur)="onTouched()"
            [disabled]="disabled"
            [placeholder]="placeholder()"
            [min]="minDate()"
            [max]="maxDate()">
     <mat-datepicker-toggle matSuffix [for]="picker"></mat-datepicker-toggle>
     <mat-datepicker #picker></mat-datepicker>
     @if (formControl()?.hasError('required')) {
       <mat-error>Birth date is required</mat-error>
     }
   </mat-form-field>
   ```
4. Compile and test

**Output**: Birth date picker form field component created in users feature

**Example 4: Modify existing form field to add validator**

```json
{
  "mode": "modify",
  "componentName": "email-input",
  "placement": "shared",
  "modifications": {
    "addValidators": ["maxlength"],
    "addInputSignals": [
      { "name": "maxLength", "type": "number", "default": "100" }
    ]
  }
}
```

**Execution**:
1. Read existing `email-input.component.ts`
2. Add input signal: `maxLength = input<number>(100)`
3. Read existing `email-input.component.html`
4. Add error block after existing error blocks:
   ```html
   @if (formControl()?.hasError('maxlength')) {
     <mat-error>Maximum length is {{ formControl()?.errors?.['maxlength'].requiredLength }}</mat-error>
   }
   ```
5. Update spec file to add test for maxlength validator
6. Compile and test

**Output**: Email input form field updated with maxlength validation

**Example 5: Change field type from input to textarea**

```json
{
  "mode": "modify",
  "componentName": "description-input",
  "placement": "shared",
  "modifications": {
    "changeFieldType": "textarea"
  }
}
```

**Execution**:
1. Read existing `description-input.component.ts`
2. Verify imports already include `MatInputModule` (works for both input and textarea)
3. Read existing `description-input.component.html`
4. Replace `<input matInput>` with `<textarea matInput rows="5"></textarea>`
5. Preserve all existing attributes, bindings, and error blocks
6. Update spec file harness tests (MatInputHarness works for both)
7. Compile and test

**Output**: Description input changed from single-line input to multi-line textarea

**Example 6: Delete form field component**

```json
{
  "mode": "delete",
  "componentName": "old-phone-input",
  "placement": "shared",
  "confirmDelete": true
}
```

**Execution**:
1. Check for usage (find no imports)
2. Remove from `shared/form-fields/index.ts`
3. Delete directory: `projects/admin-dashboard/src/app/shared/form-fields/old-phone-input/`
4. Verify compilation succeeds

**Output**: Form field component deleted successfully

## Angular component generation

**Skill Name**: `ng-component`

### YAML Frontmatter

```yaml
---
name: ng-component
description: Create, modify, or delete Angular Material components (display, container, or dialog types) with standalone architecture and Material theming
when_to_use: Use when build_app dispatches a component procedure node for display, container, or dialog types, or when a user runs /ng-component to scaffold a standalone Angular Material component.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-component` skill manages the creation, modification, and deletion of Angular components within an existing Angular Material application. Components are generated following modern Angular conventions (standalone components, signals, Material Design patterns) and can be one of three types: **display** (presentational with Material layout), **container** (smart component with service injection and Observable data binding), or **dialog** (Material dialog with data injection and action buttons). This skill should be used after the workspace and application have been created.

### Inputs

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path
- `project.name`: Application name within the workspace

Procedure-level inputs:
- **`componentName`** (string, required): Name of the component in kebab-case (e.g., `user-profile`, `product-card`)
- **`targetPath`** (string, required): Relative path from app source directory where component will be created (e.g., `src/app/features/users`, `src/app/shared/components`)
- **`type`** (enum, required): Component type (`display` | `container` | `dialog`)

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular component from scratch when it doesn't exist.

**Input Requirements**:
- `componentName`: Must be valid kebab-case identifier (lowercase, hyphenated)
- `targetPath`: Must be valid directory path within the application
- `type`: Must be one of: `display`, `container`, or `dialog`

**Pre-flight Checks**:

Before creating the component, verify:

1. Read `angular.output` and `project.name` from `django-angular3.json`
2. Workspace exists at `angular.output` and contains `angular.json`
3. Target directory exists or can be created
4. Component with same name doesn't already exist at target path

**Process (Create Mode)**:

The creation process varies based on component `type`:

##### Type: Display

**Display components** are presentational components that receive data via input signals and emit events via output signals. They use Material Card layout with structured header, content, and actions sections.

1. **Generate component scaffold**:
   ```bash
   pnpm exec ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<project.name>
   ```

2. **Replace component TypeScript file** using `templates/component-display.ts.tpl`:
   ```typescript
   import { Component, input, output } from '@angular/core';
   import { CommonModule } from '@angular/common';
   import { MatCardModule } from '@angular/material/card';
   import { MatButtonModule } from '@angular/material/button';

   @Component({
     selector: 'app-{{COMPONENT_NAME_KEBAB}}',
     standalone: true,
     imports: [
       CommonModule,
       MatCardModule,
       MatButtonModule,
     ],
     templateUrl: './{{COMPONENT_NAME_KEBAB}}.component.html',
     styleUrl: './{{COMPONENT_NAME_KEBAB}}.component.scss'
   })
   export class {{COMPONENT_NAME_PASCAL}}Component {
     // Input signals
     title = input<string>('');
     subtitle = input<string>('');
     data = input<any>(null);

     // Output signals
     actionClicked = output<void>();

     handleAction(): void {
       this.actionClicked.emit();
     }
   }
   ```

3. **Replace component template** using `templates/component-display.html.tpl`:
   ```html
   <mat-card>
     <mat-card-header>
       <mat-card-title>{{ title() }}</mat-card-title>
       @if (subtitle()) {
         <mat-card-subtitle>{{ subtitle() }}</mat-card-subtitle>
       }
     </mat-card-header>

     <mat-card-content>
       @if (data()) {
         <p>{{ data() }}</p>
       } @else {
         <p>No data available</p>
       }
     </mat-card-content>

     <mat-card-actions align="end">
       <button mat-button (click)="handleAction()">
         Action
       </button>
     </mat-card-actions>
   </mat-card>
   ```

4. **Replace component styles** using `templates/component-display.scss.tpl`:
   ```scss
   @use '@angular/material' as mat;

   :host {
     display: block;

     mat-card {
       mat-card-header {
         background-color: mat.get-theme-color(primary, 50);
         padding: 1rem;
         margin: -1rem -1rem 1rem -1rem;
       }

       mat-card-title {
         color: mat.get-theme-color(primary, 700);
         font-weight: mat.get-theme-typography(headline-6, font-weight);
       }

       mat-card-subtitle {
         color: mat.get-theme-color(primary, 500);
       }

       mat-card-content {
         padding: 1rem;
       }

       mat-card-actions {
         padding: 0.5rem 1rem 1rem;
       }
     }
   }
   ```

5. **Replace placeholders**:
   - Replace `{{COMPONENT_NAME_KEBAB}}` with `componentName` (e.g., `user-profile`)
   - Replace `{{COMPONENT_NAME_PASCAL}}` with PascalCase version (e.g., `UserProfile`)

##### Type: Container

**Container components** are smart components that inject services, manage state, and interact with backend APIs. They use `toSignal()` to convert Observables to signals for reactive data binding.

1. **Generate component scaffold** (same as display):
   ```bash
   pnpm exec ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<project.name>
   ```

2. **Replace component TypeScript file** using `templates/component-container.ts.tpl`:
   ```typescript
   import { Component, inject } from '@angular/core';
   import { CommonModule } from '@angular/common';
   import { toSignal } from '@angular/core/rxjs-interop';
   import { MatCardModule } from '@angular/material/card';
   import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
   import { MatButtonModule } from '@angular/material/button';

   @Component({
     selector: 'app-{{COMPONENT_NAME_KEBAB}}',
     standalone: true,
     imports: [
       CommonModule,
       MatCardModule,
       MatProgressSpinnerModule,
       MatButtonModule,
     ],
     templateUrl: './{{COMPONENT_NAME_KEBAB}}.component.html',
     styleUrl: './{{COMPONENT_NAME_KEBAB}}.component.scss'
   })
   export class {{COMPONENT_NAME_PASCAL}}Component {
     // Inject services using inject() function
     // private dataService = inject(DataService);

     // Convert Observable to signal using toSignal()
     // data = toSignal(this.dataService.getData$(), { initialValue: null });
     // loading = toSignal(this.dataService.loading$(), { initialValue: false });

     handleRefresh(): void {
       // Trigger data refresh
       // this.dataService.refresh();
     }
   }
   ```

3. **Replace component template** using `templates/component-container.html.tpl`:
   ```html
   <mat-card>
     <mat-card-header>
       <mat-card-title>{{COMPONENT_NAME_TITLE}}</mat-card-title>
     </mat-card-header>

     <mat-card-content>
       @if (loading()) {
         <div class="loading-spinner">
           <mat-spinner diameter="40"></mat-spinner>
         </div>
       } @else if (data()) {
         <!-- Display data here -->
         <p>{{ data() }}</p>
       } @else {
         <p>No data available</p>
       }
     </mat-card-content>

     <mat-card-actions align="end">
       <button mat-button (click)="handleRefresh()">
         Refresh
       </button>
     </mat-card-actions>
   </mat-card>
   ```

4. **Replace component styles** using `templates/component-container.scss.tpl`:
   ```scss
   @use '@angular/material' as mat;

   :host {
     display: block;

     mat-card {
       mat-card-content {
         min-height: 200px;
         position: relative;

         .loading-spinner {
           display: flex;
           justify-content: center;
           align-items: center;
           height: 200px;
         }
       }
     }
   }
   ```

5. **Replace placeholders**:
   - Replace `{{COMPONENT_NAME_KEBAB}}` with `componentName` (e.g., `user-list`)
   - Replace `{{COMPONENT_NAME_PASCAL}}` with PascalCase version (e.g., `UserList`)
   - Replace `{{COMPONENT_NAME_TITLE}}` with Title Case version (e.g., `User List`)

##### Type: Dialog

**Dialog components** are Material dialogs that receive data via `MAT_DIALOG_DATA` injection and close with results via `MatDialogRef`. They include confirm and cancel action buttons.

1. **Generate component scaffold** (same as display):
   ```bash
   pnpm exec ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<project.name>
   ```

2. **Replace component TypeScript file** using `templates/component-dialog.ts.tpl`:
   ```typescript
   import { Component, inject } from '@angular/core';
   import { CommonModule } from '@angular/common';
   import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
   import { MatButtonModule } from '@angular/material/button';
   import { MatFormFieldModule } from '@angular/material/form-field';
   import { MatInputModule } from '@angular/material/input';

   export interface {{COMPONENT_NAME_PASCAL}}DialogData {
     title: string;
     message: string;
   }

   @Component({
     selector: 'app-{{COMPONENT_NAME_KEBAB}}',
     standalone: true,
     imports: [
       CommonModule,
       MatDialogModule,
       MatButtonModule,
       MatFormFieldModule,
       MatInputModule,
     ],
     templateUrl: './{{COMPONENT_NAME_KEBAB}}.component.html',
     styleUrl: './{{COMPONENT_NAME_KEBAB}}.component.scss'
   })
   export class {{COMPONENT_NAME_PASCAL}}Component {
     // Inject dialog data and dialog reference
     data = inject<{{COMPONENT_NAME_PASCAL}}DialogData>(MAT_DIALOG_DATA);
     dialogRef = inject(MatDialogRef<{{COMPONENT_NAME_PASCAL}}Component>);

     onCancel(): void {
       this.dialogRef.close();
     }

     onConfirm(): void {
       this.dialogRef.close({ confirmed: true });
     }
   }
   ```

3. **Replace component template** using `templates/component-dialog.html.tpl`:
   ```html
   <h2 mat-dialog-title>{{ data.title }}</h2>

   <mat-dialog-content>
     <p>{{ data.message }}</p>
   </mat-dialog-content>

   <mat-dialog-actions align="end">
     <button mat-button (click)="onCancel()">Cancel</button>
     <button mat-raised-button color="primary" (click)="onConfirm()">
       Confirm
     </button>
   </mat-dialog-actions>
   ```

4. **Replace component styles** using `templates/component-dialog.scss.tpl`:
   ```scss
   @use '@angular/material' as mat;

   :host {
     display: block;

     mat-dialog-content {
       min-width: 300px;
       padding: 1.5rem 1rem;
     }

     mat-dialog-actions {
       padding: 0.5rem 1rem 1rem;
     }
   }
   ```

5. **Replace placeholders**:
   - Replace `{{COMPONENT_NAME_KEBAB}}` with `componentName` (e.g., `confirm-delete`)
   - Replace `{{COMPONENT_NAME_PASCAL}}` with PascalCase version (e.g., `ConfirmDelete`)

**Output (all types)**:
- Component files created at `<targetPath>/<componentName>/`:
  - `<componentName>.component.ts` - Component class
  - `<componentName>.component.html` - Component template
  - `<componentName>.component.scss` - Component styles
  - `<componentName>.component.spec.ts` - Component unit tests
- Confirmation message with component location and next steps

#### Modify

Update an existing Angular component with changes to template, services, or type conversion.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName`: Must reference existing component
- `targetPath`: Must point to existing component directory
- `modifications` (required): Object describing changes to make:
  - `template`: HTML changes to apply to template
  - `services`: Array of service injections to add/remove
  - `convertType`: New component type to convert to (`display` | `container` | `dialog`)
  - `styles`: SCSS rules to add or modify

**Process**:

1. **Validate component exists**:
   - Verify `<targetPath>/<componentName>/<componentName>.component.ts` exists
   - Verify component follows standalone architecture
   - Read existing component files

2. **Apply template modifications**:
   - If `modifications.template` specified:
     - Read existing `<componentName>.component.html`
     - Apply requested template changes using Edit tool
     - Preserve Material component usage and new control flow syntax (`@if`, `@for`)

3. **Add or remove service injections**:
   - If `modifications.services` specified:
     - Read existing component TypeScript file
     - For each service to add:
       ```typescript
       // Add import at top of file
       import { ServiceName } from './path/to/service';

       // Add injection in component class
       private serviceName = inject(ServiceName);
       ```
     - For each service to remove:
       - Remove injection line
       - Remove import if no longer used
     - Update template if service methods were used

4. **Convert component type**:
   - If `modifications.convertType` specified:
     - Backup current component files
     - Apply type-specific template from Create mode process
     - Preserve existing input/output signals where applicable
     - Update imports based on new type requirements
     - Notify user of manual adjustments needed

5. **Apply style modifications**:
   - If `modifications.styles` specified:
     - Read existing `<componentName>.component.scss`
     - Append new styles or update existing rules
     - Maintain Material theme token usage (`mat.get-theme-color()`)

6. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

**Output**:
- Updated component files at `<targetPath>/<componentName>/`
- List of modifications applied
- Compilation confirmation

#### Delete

Remove an Angular component completely, including all files and references in parent components or routes.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName`: Must reference existing component to delete
- `targetPath`: Must point to existing component directory
- `confirm` (required): Boolean confirmation flag (must be `true`)

**Process**:

1. **Validate component exists**:
   - Verify `<targetPath>/<componentName>/` directory exists
   - Check for any imports or references to this component

2. **Search for component references**:
   ```bash
   grep -r "{{COMPONENT_NAME_PASCAL}}Component" --include="*.ts" --include="*.html"
   grep -r "app-{{COMPONENT_NAME_KEBAB}}" --include="*.html"
   ```

3. **Remove component from imports/routes**:
   - For each file that imports the component:
     - Remove import statement
     - Remove from component imports array (if used)
     - Remove from route definitions (if lazy-loaded)
   - For each template that uses the component:
     - Remove component selector usage
     - Notify user of template references to be updated manually

4. **Delete component directory**:
   ```bash
   rm -rf <targetPath>/<componentName>
   ```

5. **Update barrel exports** (if applicable):
   - If `<targetPath>/index.ts` exists:
     - Remove export statement for deleted component

6. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

**Output**:
- Component directory removed
- List of files that referenced the component (requiring manual cleanup)
- Confirmation of deletion

### Context Files

See [angular-conventions.md](../shared/angular-conventions.md)

See [angular-material-patterns.md](../shared/angular-material-patterns.md)

### Templates

- `component-display.ts.tpl` — Display component TypeScript with input/output signals, Material Card layout
- `component-display.html.tpl` — Display component template with MatCard, header, content, and actions
- `component-display.scss.tpl` — Display component styles using Material theme tokens
- `component-container.ts.tpl` — Container component TypeScript with service injection and `toSignal()` usage
- `component-container.html.tpl` — Container component template with loading spinner and data display
- `component-container.scss.tpl` — Container component styles with loading state
- `component-dialog.ts.tpl` — Dialog component TypeScript with `MAT_DIALOG_DATA` and `MatDialogRef`
- `component-dialog.html.tpl` — Dialog component template with title, content, and action buttons
- `component-dialog.scss.tpl` — Dialog component styles

### Validation

Steps to validate successful execution of the skill:

1. **Verify component files exist**:
   ```bash
   ls -la <targetPath>/<componentName>/
   # Should contain: *.component.ts, *.component.html, *.component.scss, *.component.spec.ts
   ```

2. **Verify standalone architecture**:
   ```bash
   cat <targetPath>/<componentName>/<componentName>.component.ts | grep "standalone: true"
   # Should return standalone: true in decorator
   ```

3. **Verify correct type implementation**:
   - For `display`: Check for input/output signals, no service injections
   - For `container`: Check for service injection with `inject()`, `toSignal()` usage
   - For `dialog`: Check for `MAT_DIALOG_DATA` and `MatDialogRef` injections

4. **Verify Material imports**:
   ```bash
   cat <targetPath>/<componentName>/<componentName>.component.ts | grep "@angular/material"
   # Should contain Material module imports appropriate for type
   ```

5. **Verify SCSS uses theme tokens**:
   ```bash
   cat <targetPath>/<componentName>/<componentName>.component.scss | grep "mat.get-theme-color"
   # Should use Material theme functions, not hardcoded colors
   ```

6. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   # Should complete without errors
   ```

7. **Run unit tests**:
   ```bash
   pnpm exec ng test <project.name> --include='**/<componentName>.component.spec.ts'
   # Should pass with no failures
   ```

### Error Handling

Common errors and their resolution strategies:

**Error**: `Component <componentName> already exists at <targetPath>`
- **Cause**: Attempting to create a component that already exists
- **Resolution**: Use Modify mode to update existing component, or Delete mode first to recreate

**Error**: `Target path does not exist: <targetPath>`
- **Cause**: Invalid or non-existent target directory
- **Resolution**: Create target directory first or use valid path within app structure

**Error**: `Invalid component name: <componentName>`
- **Cause**: Component name doesn't follow kebab-case convention
- **Resolution**: Provide valid kebab-case name (lowercase, hyphenated)

**Error**: `Cannot find module '@angular/material/<module>'`
- **Cause**: Required Material module not installed
- **Resolution**: Ensure Angular Material is installed in the application (`ng add @angular/material`)

**Error**: `Compilation failed: Type 'WritableSignal<T>' is not assignable`
- **Cause**: Incorrect signal usage or TypeScript version mismatch
- **Resolution**: Verify Angular version is 17+ which supports signals natively

**Error**: `SCSS compilation failed: Undefined function 'mat.get-theme-color'`
- **Cause**: Material theme not properly configured or SCSS not using `@use` syntax
- **Resolution**: Ensure `styles.scss` contains Material theme setup with `@use '@angular/material' as mat;`

**Error**: `Dialog component not opening`
- **Cause**: Dialog component not properly registered or MatDialog service not provided
- **Resolution**: Verify `provideAnimations()` is in app.config.ts providers array

**Error**: `No provider for MAT_DIALOG_DATA`
- **Cause**: Dialog component used outside of MatDialog.open() context
- **Resolution**: Only instantiate dialog components via `MatDialog.open()`, not directly in templates

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1 - ng-workspace) — Workspace must exist
2. **Angular Material app boilerplate** (Skill 2 - ng-app) — Application must exist before creating components
3. **Angular CLI** — Must be installed and accessible
4. **Angular Material** — Must be installed in the target application

Optional dependencies:

- **Angular API generation** (Skill 3 - ng-api-gen) — If component needs to consume API services
- **Angular data model Service** (Skill 4) — If container component needs data service injection

### Examples

**Example 1: Create a display component for product card**

```typescript
// Inputs from django-angular3.json: angular.output, project.name = "admin-dashboard"
// Procedure-level:
{
  componentName: "product-card",
  targetPath: "src/app/shared/components",
  type: "display"
}

// Executes:
// 1. pnpm exec ng generate component src/app/shared/components/product-card --standalone --project=admin-dashboard
// 2. Replaces files using component-display templates
// 3. Replaces {{COMPONENT_NAME_KEBAB}} with "product-card"
// 4. Replaces {{COMPONENT_NAME_PASCAL}} with "ProductCard"
// 5. django-admin ng_build django-angular3.json

// Output: Display component created at src/app/shared/components/product-card/
// Usage: <app-product-card [title]="product.name" [data]="product" (actionClicked)="onBuy()" />
```

**Example 2: Create a container component for user list**

```typescript
// Inputs from django-angular3.json: angular.output, project.name
// Procedure-level:
{
  componentName: "user-list",
  targetPath: "src/app/features/users",
  type: "container"
}

// Executes:
// 1. pnpm exec ng generate component src/app/features/users/user-list --standalone --project=<project.name>
// 2. Replaces files using component-container templates
// 3. Adds service injection placeholder comments
// 4. Adds toSignal() usage examples
// 5. django-admin ng_build django-angular3.json

// Output: Container component created at src/app/features/users/user-list/
// Next step: Inject UserService and bind data using toSignal()
```

**Example 3: Create a dialog component for confirmation**

```typescript
// Inputs from django-angular3.json: angular.output, project.name
// Procedure-level:
{
  componentName: "confirm-delete",
  targetPath: "src/app/shared/dialogs",
  type: "dialog"
}

// Executes:
// 1. pnpm exec ng generate component src/app/shared/dialogs/confirm-delete --standalone --project=<project.name>
// 2. Replaces files using component-dialog templates
// 3. Adds MAT_DIALOG_DATA and MatDialogRef injections
// 4. Adds cancel and confirm action buttons
// 5. django-admin ng_build django-angular3.json

// Output: Dialog component created at src/app/shared/dialogs/confirm-delete/
// Usage: this.dialog.open(ConfirmDeleteComponent, { data: { title: 'Delete?', message: 'Are you sure?' } })
```

**Example 4: Modify existing component to add service injection**

```typescript
// Inputs from django-angular3.json: angular.output, project.name
// Procedure-level:
{
  componentName: "user-list",
  targetPath: "src/app/features/users",
  modifications: {
    services: [
      {
        action: "add",
        serviceName: "UserService",
        importPath: "../../core/services/user.service",
        binding: "users$ = toSignal(this.userService.getUsers$(), { initialValue: [] })"
      }
    ]
  }
}

// Executes:
// 1. Reads src/app/features/users/user-list/user-list.component.ts
// 2. Adds: import { UserService } from '../../core/services/user.service';
// 3. Adds: private userService = inject(UserService);
// 4. Adds: users$ = toSignal(this.userService.getUsers$(), { initialValue: [] });
// 5. django-admin ng_build django-angular3.json

// Output: Component updated with UserService injection and signal binding
```

**Example 5: Delete a component and clean up references**

```typescript
// Inputs from django-angular3.json: angular.output, project.name
// Procedure-level:
{
  componentName: "old-widget",
  targetPath: "src/app/shared/components",
  confirm: true
}

// Executes:
// 1. Searches for references to OldWidgetComponent in codebase
// 2. Removes component from parent component imports (if found)
// 3. Deletes: rm -rf src/app/shared/components/old-widget
// 4. Updates: src/app/shared/components/index.ts (removes export)
// 5. django-admin ng_build django-angular3.json

// Output: Component deleted. Manual cleanup needed in:
//   - src/app/pages/dashboard/dashboard.component.html (remove <app-old-widget>)
```

## Angular Material complex component generation

**Skill Name**: `ng-complex-component`

### YAML Frontmatter

```yaml
---
name: ng-complex-component
description: Create, modify, or delete Angular Material complex components with theme mixins, nested child components, content projection, and CDK overlay integration
when_to_use: Use when build_app dispatches a complex-component procedure node, or when a user runs /ng-complex-component to scaffold a Material component requiring theme mixins, content projection, child components, or CDK overlay integration.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-complex-component` skill manages Angular Material components that go beyond a single standalone component scaffold. It is used when a component needs one or more advanced composition features: a dedicated theme mixin, nested child components, typed content projection slots, or CDK overlay behavior. The skill keeps the component aligned with the simpler `ng-component` conventions while expanding the generated structure to cover public API documentation, theming integration, and multi-file component composition.

### Inputs

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path
- `project.name`: Application name within the workspace

Procedure-level inputs:
- **`componentName`** (string, required): Component name in kebab-case (e.g., `user-menu`, `filter-builder`)
- **`targetPath`** (string, required): Relative path from app source directory where the component directory will be created
- **`features`** (array, required): List of advanced features to enable. Allowed values:
  - `mixins`
  - `nested`
  - `projection`
  - `cdk-overlay`

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular Material complex component from scratch.

**Input Requirements**:
- `componentName` must be valid kebab-case
- `targetPath` must resolve inside the Angular application source tree
- `features` must contain one or more supported feature flags

**Pre-flight Checks**:

Before creating the component, verify:

1. Read `angular.output` and `project.name` from `django-angular3.json`
2. `angular.json` exists under `angular.output`
3. Angular Material and `@angular/cdk` are installed when `cdk-overlay` is requested
4. The target component directory does not already exist
5. Root theme entrypoint (typically `src/styles.scss`) exists and is writable when `mixins` is requested

**Process (Create Mode)**:

1. **Generate the parent standalone component scaffold**:
   ```bash
   pnpm exec ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<project.name>
   ```

2. **Replace the generated parent component** with a Material-oriented complex component implementation that:
   - uses standalone imports
   - keeps Angular Material imports explicit
   - adds a top-level JSDoc block documenting the public API:
     - inputs
     - outputs
     - projection slots
   - exposes only the supported public surface

3. **Apply feature: `mixins`**:
   - Create `_<componentName>-theme.scss` in the component directory
   - Define a named mixin for the component theme contract, for example:
     ```scss
     @use '@angular/material' as mat;

     @mixin <componentName>-theme($theme) {
       .app-<componentName> {
         color: mat.get-theme-color($theme, primary, 500);
       }
     }
     ```
   - Update the application theme entrypoint (`styles.scss`) to import and include the mixin
   - Keep theme styling in the mixin file instead of duplicating theme token logic inline

4. **Apply feature: `nested`**:
   - Generate child components inside `<targetPath>/<componentName>/`
   - Use focused names for child components such as `header`, `content`, `actions`, or domain-specific names like `filter-panel` and `result-summary`
   - Import the generated child components into the parent component `imports` array
   - Keep the parent component responsible for composition and high-level orchestration only

5. **Apply feature: `projection`**:
   - Add one or more projection slots using explicit selectors:
     ```html
     <ng-content select="[slot=title]"></ng-content>
     <ng-content select="[slot=actions]"></ng-content>
     ```
   - Create typed marker directives for each supported slot so the public API is discoverable and template usage is constrained
   - Document each slot in the parent component JSDoc block

6. **Apply feature: `cdk-overlay`**:
   - Use Angular CDK overlay primitives, not ad hoc DOM manipulation
   - Inject and use:
     - `Overlay`
     - `OverlayRef`
     - `ComponentPortal`
   - Keep overlay creation, attachment, disposal, and teardown inside the parent component or a tightly scoped helper service/provider
   - Register only the providers needed for the generated overlay behavior

7. **Generate tests and support files consistent with the selected features**:
   - Parent component spec remains at `<componentName>.component.spec.ts`
   - Child component specs are generated when nested components are created
   - Overlay-enabled components verify attach/detach behavior at the unit level when spec coverage is present in the workspace

**Output**:
- Parent component directory created at `<targetPath>/<componentName>/`
- Parent component files:
  - `<componentName>.component.ts`
  - `<componentName>.component.html`
  - `<componentName>.component.scss`
  - `<componentName>.component.spec.ts`
- Optional feature files:
  - `_<componentName>-theme.scss`
  - child component directories under `<componentName>/`
  - typed slot directives
  - overlay-specific providers or support files when required

#### Modify

Update an existing complex component by adding advanced composition features without rebuilding the entire component.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName` must reference an existing component directory
- `targetPath` must point to a valid existing path
- `features` must describe the feature(s) to add or expand

**Process**:

1. Read the current parent component, template, styles, tests, and any existing child components
2. Preserve the existing public API unless the requested change explicitly expands it
3. For requested modifications:
   - **Add mixin**:
     - create `_<componentName>-theme.scss` if missing
     - extract theme-specific rules into the mixin
     - add the import/include in `styles.scss`
   - **Extract child**:
     - move a cohesive template region into a child component inside `<componentName>/`
     - add the child component to the parent `imports`
     - keep existing bindings flowing through typed inputs/outputs
   - **Add projection slot**:
     - add a new `<ng-content select="...">` slot
     - add the corresponding typed directive
     - extend the parent JSDoc block with the new slot contract
4. Re-run a compile check after modifications

**Output**:
- Existing component updated in place
- Public API documentation refreshed
- Theme, child component, or slot support added without deleting unaffected files

#### Delete

Remove a complex component and its advanced integrations completely.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `componentName` must reference an existing complex component
- `targetPath` must resolve to the existing component directory
- `confirm` (required): Must be `true`

**Process**:

1. Verify the component directory exists and identify all references
2. Remove the full component directory tree:
   ```bash
   rm -rf <targetPath>/<componentName>
   ```
3. If `mixins` was enabled:
   - remove the theme mixin import from `styles.scss`
   - remove the `@include` statement for the component theme mixin
4. If `cdk-overlay` was enabled:
   - remove CDK overlay-specific providers or helper registrations introduced for the component
   - remove overlay portal imports that are now unused
5. Remove any parent-level imports, route references, or barrel exports that still reference the component or extracted children
6. Re-run a compile check to ensure all references were removed

**Output**:
- Component directory tree removed
- Theme mixin usage removed from `styles.scss`
- CDK providers and imports cleaned up
- Remaining manual cleanup locations reported if unrelated templates still reference the deleted selectors

### Context Files

See [angular-conventions.md](../shared/angular-conventions.md)

See [angular-material-patterns.md](../shared/angular-material-patterns.md)

### Templates

None

### Validation

Steps to validate successful execution of the skill:

1. **Verify the complex component directory structure**:
   ```bash
   ls -la <targetPath>/<componentName>/
   ```
   - Should include the parent component files
   - Should include child directories or `_<componentName>-theme.scss` when requested

2. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Should complete without TypeScript, template, or styling errors

3. **Theme injection verified**:
   ```bash
   grep -n "<componentName>-theme" src/styles.scss
   ```
   - Should show the mixin import/include when `mixins` is enabled
   - Should return no matches after Delete mode cleanup

4. **Projection slot verification**:
   ```bash
   grep -n '<ng-content select="' <targetPath>/<componentName>/<componentName>.component.html
   ```
   - Should show explicit projection slots when `projection` is enabled

5. **Nested component verification**:
   ```bash
   grep -n "imports:" <targetPath>/<componentName>/<componentName>.component.ts
   ```
   - Parent component should import generated child components when `nested` is enabled

6. **CDK overlay verification**:
   ```bash
   grep -E "Overlay|OverlayRef|ComponentPortal" <targetPath>/<componentName>/<componentName>.component.ts
   ```
   - Should show CDK overlay primitives when `cdk-overlay` is enabled

### Error Handling

Common errors and their resolution strategies:

**Error**: `Unsupported complex component feature: <feature>. Supported features are: mixins, nested, projection, cdk-overlay`
- **Cause**: The `features` list contains an unknown value
- **Resolution**: Restrict the feature list to `mixins`, `nested`, `projection`, and `cdk-overlay`

**Error**: `Theme entrypoint not found`
- **Cause**: `styles.scss` could not be located for theme mixin registration
- **Resolution**: Verify the workspace uses a writable global theme entrypoint before enabling `mixins`

**Error**: `Projection slot selector already exists`
- **Cause**: Attempting to add a duplicate slot
- **Resolution**: Reuse the existing slot or choose a different selector/directive name

**Error**: `Cannot find module '@angular/cdk/overlay'`
- **Cause**: CDK overlay support is requested but Angular CDK is not available
- **Resolution**: Install or restore Angular CDK before enabling `cdk-overlay`

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1 - ng-workspace)
2. **Angular Material app boilerplate** (Skill 2 - ng-app)
3. **Angular component generation** (Skill 7 - ng-component) conventions should already be understood and available for reuse

### Examples

**Example 1: Create a themed complex component with nested children**

Input from `django-angular3.json`: `angular.output = "/workspace/my-project"`, `project.name = "admin-dashboard"`

```json
{
  "componentName": "user-menu",
  "targetPath": "src/app/shared/components",
  "features": ["mixins", "nested", "projection"]
}
```

**Example 2: Add overlay behavior to an existing complex component**

```json
{
  "componentName": "filter-builder",
  "targetPath": "src/app/features/search",
  "features": ["cdk-overlay"]
}
```

## ng-reactive-form

```yaml
---
name: ng-reactive-form
description: Create, modify, or delete Angular Material reactive forms with typed FormGroup, FormBuilder scaffolding, Material form fields, server-side validation error handling, and comprehensive specs
when_to_use: Use when build_app dispatches a reactive-form procedure node, or when a user runs /ng-reactive-form to scaffold a typed Material reactive form with FormBuilder, validation, and server-error handling.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-reactive-form` skill manages Angular reactive form components that use typed `FormGroup<>` interfaces, `FormBuilder` for control creation, Angular Material form fields (`MatFormField`), and integrate with data services for submission. These forms implement loading states with `MatProgressBar`, handle server-side validation errors by calling `setErrors()` on individual controls, wire submit actions to data service methods, and provide cancel handlers for navigation or output events. Forms can operate in create mode (empty initial values), edit mode (pre-populated from resource), or both modes (dynamic based on route parameters).

### Inputs

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path
- `project.name`: Application name within the workspace

Procedure-level inputs:
- `formName` (string, required): Name of the form component in kebab-case (e.g., `user-profile`, `order-create`, `product-edit`)
- `targetPath` (string, required): Relative path from app source where form should be placed (e.g., `features/users/forms`, `shared/forms`)
- `mode` (enum, required): Form operational mode:
  - `create` — Form for creating new resources (empty initial values)
  - `edit` — Form for editing existing resources (pre-populated from resource)
  - `both` — Form supporting both create and edit based on route parameters or input
- `resourceName` (string, optional): Name of the resource this form operates on. If provided, the skill will:
  - Inspect generated API models from `ng-api` output to derive field types
  - Create typed `FormGroup<>` interface matching the model structure
  - Wire submit to corresponding data service method (e.g., `createUser()`, `updateUser()`)
  - If not provided, form fields must be manually specified

### Modes

#### Create

Generate a new Angular reactive form component from scratch with typed `FormGroup<>`, Material form fields, validation, loading state, server error handling, and comprehensive spec tests.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `formName` (string): Form component name in kebab-case
- `targetPath` (string): Target directory relative to app source
- `mode` (enum): `create`, `edit`, or `both`
- `resourceName` (string, optional): Resource name for API integration

**Process**:

1. **Pre-flight validation**:
   - Read `angular.output` and `project.name` from `django-angular3.json`
   - Verify workspace exists at `angular.output` and contains `angular.json`
   - Verify application `<project.name>` exists in `projects/<project.name>/`
   - Validate `formName` follows naming conventions (lowercase, hyphenated)
   - Check form component doesn't already exist at `targetPath/<formName>/`
   - If `resourceName` is provided:
     - Verify generated API models exist from `ng-api` skill output
     - Verify corresponding data service exists from `ng-data-service` skill
     - Extract field names and types from the resource model

2. **Determine target directory**:
   - Resolve full path: `projects/<project.name>/src/app/<targetPath>/<formName>/`
   - Create directory if it doesn't exist:
     ```bash
     mkdir -p <targetDirectory>
     ```

3. **Inspect resource model** (if `resourceName` provided):
   - Locate generated model at `src/app/api/models/<resource-name>.ts`
   - Parse model interface to extract:
     - Field names (convert to camelCase for form controls)
     - Field types (string, number, boolean, Date, custom types)
     - Optional vs required fields (use `?` indicator)
     - Nested objects (flatten to form controls or create nested `FormGroup`)
   - Map TypeScript types to appropriate validators:
     - `string` fields → `Validators.required`, `Validators.minLength()`, `Validators.maxLength()`
     - `email` or `*Email` fields → `Validators.email`
     - `number` fields → `Validators.required`, `Validators.min()`, `Validators.max()`
     - `Date` fields → `Validators.required`
     - Optional fields → omit `Validators.required`

4. **Generate TypeScript file** using `templates/reactive-form.ts.tpl`:
   - Create `<formName>.component.ts` with:
     - `@Component` decorator with `standalone: true`
     - Typed form interface:
       ```typescript
       interface {{FORM_NAME_PASCAL}}Form {
         fieldName: FormControl<string>;
         anotherField: FormControl<number>;
         optionalField: FormControl<string | null>;
       }
       ```
     - Component class with PascalCase: `{{FORM_NAME_PASCAL}}Component`
     - Selector: `app-{{FORM_NAME_KEBAB}}-form`
     - Import required Material modules:
       - `MatFormFieldModule`, `MatInputModule`, `MatButtonModule`
       - `MatCardModule` (for form container)
       - `MatProgressBarModule` (for loading state)
       - Additional modules based on field types (e.g., `MatSelectModule`, `MatDatepickerModule`)
     - Import `ReactiveFormsModule`, `CommonModule`
     - Inject `FormBuilder` using `inject()` function
     - If `resourceName` provided: Inject corresponding data service (e.g., `UsersService`)
     - Signals for state management:
       - `loading = signal(false)` — Loading state during form submission
       - `serverErrors = signal<Record<string, string[]> | null>(null)` — Server validation errors
     - Outputs:
       - `formSubmit = output<FormValue>()` — Emitted on successful submission (for parent component handling)
       - `formCancel = output<void>()` — Emitted when user cancels
     - Typed `FormGroup`:
       ```typescript
       form: FormGroup<{{FORM_NAME_PASCAL}}Form> = this.fb.group({
         fieldName: this.fb.control('', {
           nonNullable: true,
           validators: [Validators.required, Validators.minLength(2)]
         }),
         numberField: this.fb.control(0, {
           nonNullable: true,
           validators: [Validators.required, Validators.min(0)]
         }),
         optionalField: this.fb.control<string | null>(null)
       });
       ```
     - **Mode: Create** — Form starts with empty values
     - **Mode: Edit** — Add input signal:
       ```typescript
       initialValue = input<ResourceModel | null>(null);

       ngOnInit(): void {
         if (this.initialValue()) {
           this.form.patchValue(this.initialValue()!);
         }
       }
       ```
     - **Mode: Both** — Detect based on `initialValue` presence:
       ```typescript
       isEditMode = computed(() => this.initialValue() !== null);
       ```
     - `onSubmit()` method:
       - Check `form.valid` and `!loading()`
       - Set `loading(true)`
       - If data service integrated:
         - Call service method based on mode (e.g., `createUser()` or `updateUser()`)
         - Subscribe to result
         - On success: Reset loading, emit `formSubmit` output or navigate
         - On error: Set loading to false, call `setServerErrors()`
       - If no service: Emit `formSubmit.emit(this.form.getRawValue())`
     - `onCancel()` method:
       - Reset form: `this.form.reset()`
       - Emit `formCancel.emit()`
     - `setServerErrors(errors: Record<string, string[]>)` method:
       - Iterate over error object
       - For each field, call `control.setErrors({ server: messages.join(', ') })`
       - Update `serverErrors` signal for display
   - Placeholders to replace:
     - `{{FORM_NAME_KEBAB}}` → e.g., `user-profile`
     - `{{FORM_NAME_PASCAL}}` → e.g., `UserProfile`
     - `{{RESOURCE_NAME_PASCAL}}` → e.g., `User` (if resource provided)
     - `{{SERVICE_NAME_PASCAL}}` → e.g., `UsersService` (if resource provided)

5. **Generate HTML template** using `templates/reactive-form.html.tpl`:
   - Create `<formName>.component.html` with:
     - Wrap form in `<mat-card>` with header and actions
     - `<mat-card-header>` with title (e.g., "Create User" or "Edit User")
     - `<mat-progress-bar>` with `@if (loading())` for loading state
     - `<form [formGroup]="form" (ngSubmit)="onSubmit()">` with `<mat-card-content>`
     - One `<mat-form-field>` per form control:
       ```html
       <mat-form-field appearance="outline">
         <mat-label>Field Label</mat-label>
         <input matInput formControlName="fieldName" placeholder="Enter value">
         @if (form.get('fieldName')?.hasError('required') && form.get('fieldName')?.touched) {
           <mat-error>This field is required</mat-error>
         }
         @if (form.get('fieldName')?.hasError('minlength')) {
           <mat-error>Minimum length is {{ form.get('fieldName')?.errors?.['minlength'].requiredLength }}</mat-error>
         }
         @if (form.get('fieldName')?.hasError('server')) {
           <mat-error>{{ form.get('fieldName')?.errors?.['server'] }}</mat-error>
         }
       </mat-form-field>
       ```
     - Use modern control flow (`@if`, `@for`) instead of `*ngIf`, `*ngFor`
     - `<mat-card-actions>` with two buttons:
       ```html
       <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || loading()">
         @if (isEditMode()) { Update } @else { Create }
       </button>
       <button mat-button type="button" (click)="onCancel()" [disabled]="loading()">
         Cancel
       </button>
       ```

6. **Generate SCSS file** using `templates/component.scss.tpl`:
   - Create `<formName>.component.scss` with:
     - `:host` selector with `display: block;`
     - Material theme token usage
     - Form field spacing and layout
     - Example structure:
       ```scss
       @use '@angular/material' as mat;

       :host {
         display: block;

         mat-card {
           max-width: 600px;
           margin: 0 auto;
         }

         mat-form-field {
           width: 100%;
           margin-bottom: 16px;
         }

         mat-card-actions {
           display: flex;
           gap: 8px;
           justify-content: flex-end;
         }
       }
       ```

7. **Generate spec file**:
   - Create `<formName>.component.spec.ts` with:
     - Import `ReactiveFormsModule`, `NoopAnimationsModule`
     - Mock data service (if integrated) using Jest spy
     - Test suite structure:
       - **should create** — Component initialization test
       - **Form initialization tests**:
         - Form should be invalid when empty (if required fields exist)
         - Form should initialize with correct control names
         - Form controls should have correct initial validators
       - **Mode: Create tests**:
         - Initial form values should be empty/default
         - Submit should call create method on data service
       - **Mode: Edit tests**:
         - `patchValue()` should populate form with initial values
         - Submit should call update method on data service
       - **Validation state transition tests**:
         - Form should transition from invalid to valid when required fields filled
         - Individual control errors should appear/disappear correctly
         - `form.invalid` should disable submit button
       - **Submit flow with mocked service**:
         - Successful submit: loading true → service called → loading false → output emitted
         - Failed submit with server errors: `setServerErrors()` called → control errors set
       - **Loading state tests**:
         - Loading state should disable submit button
         - Progress bar should display when loading
       - **Cancel flow**:
         - Cancel should reset form
         - Cancel should emit `formCancel` output
       - **Server-side validation error tests**:
         - `setServerErrors()` should set errors on matching controls
         - Server errors should display in `<mat-error>` blocks
     - Example test:
       ```typescript
       it('should handle successful form submission', fakeAsync(() => {
         const mockService = TestBed.inject(UsersService);
         const createSpy = jest.spyOn(mockService, 'createUser').mockReturnValue(
           of({ id: 1, name: 'Test User', email: 'test@example.com' })
         );

         component.form.patchValue({
           name: 'Test User',
           email: 'test@example.com'
         });

         component.onSubmit();
         expect(component.loading()).toBe(true);

         tick();

         expect(createSpy).toHaveBeenCalledWith({ name: 'Test User', email: 'test@example.com' });
         expect(component.loading()).toBe(false);
       }));

       it('should handle server validation errors', () => {
         const serverErrors = {
           email: ['Email already exists'],
           name: ['Name is too short']
         };

         component.setServerErrors(serverErrors);

         expect(component.form.get('email')?.hasError('server')).toBe(true);
         expect(component.form.get('email')?.errors?.['server']).toBe('Email already exists');
         expect(component.form.get('name')?.hasError('server')).toBe(true);
       });
       ```

8. **Wire to data service** (if `resourceName` provided):
   - Add route parameter handling for edit mode:
     - Inject `ActivatedRoute` and `Router`
     - Load resource data based on route params
     - Example:
       ```typescript
       private route = inject(ActivatedRoute);
       private usersService = inject(UsersService);

       ngOnInit(): void {
         const id = this.route.snapshot.paramMap.get('id');
         if (id) {
           this.usersService.getUser(+id).subscribe(user => {
             this.form.patchValue(user);
           });
         }
       }
       ```

9. **Report generated artifacts**:
   - List created files:
     - `<formName>.component.ts`
     - `<formName>.component.html`
     - `<formName>.component.scss`
     - `<formName>.component.spec.ts`
   - Summarise form fields and validators
   - Note integration with data service (if applicable)

**Output**:
- New reactive form component at `projects/<project.name>/src/app/<targetPath>/<formName>/`
- Four files: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`
- Typed `FormGroup<>` interface matching resource model (if provided)
- Integration with data service for submit/cancel actions (if provided)
- Loading state with `MatProgressBar`
- Server-side validation error handling with `setErrors()`
- Comprehensive unit tests covering validation state transitions and submit flow

#### Modify

Update an existing reactive form component to add/remove fields, change validators, update submit target, or adjust behavior.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `formName` (string): Name of the form to modify
- `targetPath` (string): Current location of form component
- Description of changes:
  - Fields to add/remove (with types and validators)
  - Validator changes for existing fields
  - Submit target changes (different service method or navigation)
  - Mode changes (create ↔ edit ↔ both)

**Process**:
1. Locate existing form component files:
   - Find `<formName>.component.ts`, `.html`, `.scss`, `.spec.ts`
   - Verify all files exist and are readable
2. **Add fields**:
   - Update typed form interface with new field types
   - Add new `FormControl` to `form` definition with appropriate validators
   - Add corresponding `<mat-form-field>` to template with error handling
   - Update spec tests to cover new fields
3. **Remove fields**:
   - Remove field from typed form interface
   - Remove `FormControl` from `form` definition
   - Remove `<mat-form-field>` from template
   - Remove field-specific tests from spec
4. **Change validators**:
   - Update validator array in `FormControl` definition
   - Update corresponding `<mat-error>` blocks in template
   - Update validation tests in spec
5. **Update submit target**:
   - Change injected service if switching resources
   - Update service method call in `onSubmit()` (e.g., `createUser()` → `createOrder()`)
   - Update mock service in spec tests
6. **Mode transitions**:
   - **Create → Edit**: Add `initialValue` input signal, add `ngOnInit()` with `patchValue()`
   - **Edit → Create**: Remove `initialValue` input, remove `ngOnInit()` patching logic
   - **Create/Edit → Both**: Add `isEditMode` computed signal, update button text with conditional
7. **Re-generate spec tests** for modified sections
8. Report modified files and changes

**Output**:
- Updated `<formName>.component.ts` with modified form definition
- Updated `<formName>.component.html` with added/removed fields
- Updated `<formName>.component.spec.ts` with matching test coverage
- Change summary documenting field additions/removals and validator updates

#### Delete

Remove a reactive form component and clean up references (route configurations, parent component imports).

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- `formName` (string): Name of the form to delete
- `targetPath` (string): Location of form component

**Process**:
1. Locate form component directory: `projects/<project.name>/src/app/<targetPath>/<formName>/`
2. Verify all component files exist:
   - `<formName>.component.ts`
   - `<formName>.component.html`
   - `<formName>.component.scss`
   - `<formName>.component.spec.ts`
3. Search for references:
   - Check for route definitions importing this component
   - Check for parent components using this form in their templates
   - Check for barrel exports (`index.ts`) re-exporting this component
4. Remove all four component files:
   ```bash
   rm -rf projects/<project.name>/src/app/<targetPath>/<formName>/
   ```
5. Remove stale imports and references:
   - If component is used in routes: Remove route entry or comment with TODO for manual cleanup
   - If barrel export exists: Remove export line from `index.ts`
   - If parent component imports: Report manual cleanup required (cannot automatically determine replacement)
6. Report deleted files and any follow-up manual cleanup needed

**Output**:
- Removed form component directory and all files
- Confirmation of deletion
- List of references that require manual cleanup (routes, parent component usage)

### Context Files

See [angular-conventions.md](../shared/angular-conventions.md)
See [angular-material-patterns.md](../shared/angular-material-patterns.md)
See [openapi-integration.md](../shared/openapi-integration.md)

### Supporting Files

- `templates/reactive-form.ts.tpl` — Typed reactive form scaffold with `FormGroup<>`, `FormBuilder`, loading state, and server error handling
- `templates/reactive-form.html.tpl` — Material form template with `MatCard`, `MatFormField` per control, progress bar, and submit/cancel buttons
- `context/angular-conventions.md` — Angular standalone component patterns, signals, dependency injection
- `context/openapi-integration.md` — Resource model location and import patterns for deriving form field types

### Validation

**Post-Create/Modify Validation**:

1. **Compile check**:
   ```bash
   pnpm exec tsc --noEmit --project tsconfig.json
   ```
   - Confirm form component compiles with typed `FormGroup<>` interface
   - Verify Material module imports are correct
   - Verify data service integration (if applicable) compiles

2. **Spec run**:
   ```bash
   pnpm exec ng test --watch=false --include='**/<formName>.component.spec.ts'
   ```
   - Confirm form spec passes
   - Verify validation state transition tests
   - Verify submit flow tests with mocked service

3. **Manual review**:
   - Verify form fields match resource model (if provided)
   - Verify `setServerErrors()` method handles server validation correctly
   - Verify loading state disables submit button
   - Verify `form.invalid` disables submit button
   - Test form interactively in running application

### Error Handling

**Common Errors**:

1. **Generated model not found**:
   - Error: Cannot resolve resource model for form field derivation
   - Resolution: Run `ng-api` skill first to generate OpenAPI models, then retry

2. **Data service missing**:
   - Error: Cannot inject data service for submit integration
   - Resolution: Run `ng-data-service` skill to create service wrapper, then retry

3. **Form control type mismatch**:
   - Error: TypeScript compilation fails due to form control type not matching model field type
   - Resolution: Verify model field types, adjust `FormControl<Type>` definitions to match

4. **Server error handling not working**:
   - Error: Server validation errors don't display in form
   - Resolution: Verify `setServerErrors()` is called in error handler, verify field names match form control names

5. **Spec tests fail after field changes**:
   - Error: Tests reference old field names or validators
   - Resolution: Regenerate spec tests to match current form definition

### Dependencies

**Required Skills** (must execute before this skill):

1. **ng-workspace** (Skill 1) — Workspace must exist with Angular Material installed
2. **ng-app** (Skill 2) — Application must exist in workspace with proper directory structure

**Optional Dependencies** (enhance functionality if present):

- **ng-api** (Skill 3) — If `resourceName` provided, generated models are used to derive typed `FormGroup<>` fields
- **ng-data-service** (Skill 4) — If `resourceName` provided, data service is injected for submit integration
- **ng-form-field** (Skill 6) — Custom form field components can be used in place of standard `MatFormField` inputs

**Dependent Skills** (use this skill before):

- **ng-page** (Skill 10) — Pages include forms with routing integration and navigation
- **ng-component** (Skill 7) — Container components may include reactive forms as child components

### Examples

**Example 1: Create a user profile form with API integration**

Input from `django-angular3.json`: `angular.output = "/workspace/my-app"`, `project.name = "admin-dashboard"`

```json
{
  "formName": "user-profile",
  "targetPath": "features/users/forms",
  "mode": "both",
  "resourceName": "user"
}
```

**Process**:
1. Inspect `src/app/api/models/user.ts` for field types
2. Create typed form interface:
   ```typescript
   interface UserProfileForm {
     firstName: FormControl<string>;
     lastName: FormControl<string>;
     email: FormControl<string>;
     phoneNumber: FormControl<string | null>;
   }
   ```
3. Generate form with validators derived from model
4. Wire submit to `UsersService.createUser()` or `UsersService.updateUser()` based on mode
5. Add `isEditMode` computed signal for button text

**Output**:
- `features/users/forms/user-profile/user-profile.component.ts` (with typed form and service integration)
- `features/users/forms/user-profile/user-profile.component.html` (with Material fields and loading state)
- `features/users/forms/user-profile/user-profile.component.scss` (with form layout)
- `features/users/forms/user-profile/user-profile.component.spec.ts` (with validation and submit tests)

**Example 2: Create a simple contact form without API integration**

```json
{
  "formName": "contact",
  "targetPath": "shared/forms",
  "mode": "create"
}
```

**Process**:
1. No `resourceName` provided, manually define form fields
2. Create form with standard fields (name, email, message)
3. No data service integration, emit `formSubmit` output for parent handling
4. Parent component subscribes to `formSubmit` and handles submission

**Output**:
- `shared/forms/contact/contact.component.ts` (with typed form and output event)
- `shared/forms/contact/contact.component.html` (with Material fields)
- `shared/forms/contact/contact.component.scss` (with form layout)
- `shared/forms/contact/contact.component.spec.ts` (with validation tests)

**Example 3: Modify existing form to add a new field**

```markdown
Input from django-angular3.json: angular.output, project.name = "admin-dashboard"
- formName: "product-edit"
- targetPath: "features/products/forms"
- change: "Add 'category' select field with dropdown options"

Process:
1. Locate existing `product-edit.component.ts`
2. Add `category: FormControl<string>` to form interface
3. Add form control with required validator
4. Add `<mat-form-field>` with `<mat-select>` to template
5. Update spec tests to cover category field validation

Output:
- Updated `product-edit.component.ts`
- Updated `product-edit.component.html`
- Updated `product-edit.component.spec.ts`
```

## Angular Material page generation

**Skill Name**: `ng-page`

### YAML Frontmatter

```yaml
---
name: ng-page
description: Create, modify, or delete Angular Material pages with lazy standalone routing, sidenav navigation, and authenticated route guard support
when_to_use: Use when build_app dispatches a page procedure node, or when a user runs /ng-page to scaffold a Material page with lazy routing, sidenav navigation, and authentication guards.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-page` skill manages top-level Angular Material pages inside an existing feature area. It covers page scaffolding, route registration, optional sidenav navigation, and page-specific layout patterns for common application screens. Use this skill after the Angular workspace and app exist, and after supporting skills such as data services, shared components, and reactive forms are available when the requested page depends on them.

### Inputs

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path
- `project.name`: Application name within the workspace

Procedure-level inputs:
- **`pageName`** (string, required): Page component name in kebab-case (for example `users-list`, `order-detail`, `team-dashboard`)
- **`routePath`** (string, required): Route path segment to register in the feature route file (for example `users`, `orders/:id`, `dashboard`)
- **`pageType`** (enum, required): Page type (`list` | `detail` | `dashboard` | `workflow`)
- **`featureName`** (string, required): Feature area that owns the route and page files (for example `users`, `orders`, `admin`)

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular Material page from scratch, register it in the feature route tree, and wire navigation when the page is top-level.

**Input Requirements**:
- `pageName` must be a valid kebab-case component/page identifier
- `routePath` must be valid for the target feature route file
- `pageType` must be one of: `list`, `detail`, `dashboard`, `workflow`
- `featureName` must map to an existing feature directory

**Pre-flight Checks**:
1. Verify the feature route file exists
2. Verify a page with the same name does not already exist
3. Verify required supporting skills exist for the requested page type:
   - `list`/`detail`: data service available if page is resource-backed
   - `workflow`: reactive form support available for form steps
4. Identify whether the page is top-level and should appear in the sidenav
5. Identify whether the page requires authentication and a `CanActivate` guard reference

**Process (Create Mode)**:

1. **Create the standalone page component** in the feature page directory using the appropriate template files.
2. **Generate the page layout based on `pageType`**:

   ##### Type: List

   Create a resource list page using:
   - `MatTable` for rows and displayed columns
   - `MatPaginator` for pagination
   - `MatSort` for sortable column headers
   - `MatProgressBar` for loading state
   - Row click navigation to the matching detail page
   - A `"New"` button that routes to the create form/workflow page

   ##### Type: Detail

   Create a single-resource detail page using:
   - `MatCard` layout for the record summary and sections
   - Read-only presentation of one resource
   - Edit and delete actions in the card action area

   ##### Type: Dashboard

   Create a summary dashboard using:
   - A responsive grid of `MatCard` widgets
   - Summary metrics, shortcuts, or status blocks per card

   ##### Type: Workflow

   Create a multi-step workflow page using:
   - `MatStepper` for sequential workflow steps
   - Reactive form step components or inline reactive form groups for each step
   - Next/back/submit actions aligned to the stepper flow

3. **Register the feature route**:
   - Add a lazy standalone route entry in the feature route file
   - Use `loadComponent` rather than eager imports
   - Example:
     ```typescript
     {
       path: '<routePath>',
       loadComponent: () =>
         import('./pages/<pageName>/<pageName>.component').then(
           (m) => m.<PageName>Component
         ),
       canActivate: [authGuard],
     }
     ```
   - Add the `CanActivate` guard reference when the page is authenticated

4. **Update sidenav navigation**:
   - If the page is top-level, add a `MatNavList` item in the app or feature sidenav
   - Link the nav item to the new route

5. **Report generated artifacts**:
   - `<feature>/pages/<pageName>/<pageName>.component.ts`
   - `<feature>/pages/<pageName>/<pageName>.component.html`
   - Route entry added to the feature route file
   - Sidenav item added when applicable

**Output**:
- New standalone page component registered with `loadComponent`
- Page layout matching the requested Angular Material page type
- Optional authenticated route guard reference
- Optional top-level sidenav navigation item

#### Modify

Update an existing page to change its visible structure or route protection without rebuilding the feature from scratch.

**Supported Modifications**:
- Add or remove table columns on `list` pages
- Change the applied `CanActivate` guard for authenticated pages
- Update the page layout (for example card sections, widget arrangement, step content)

**Process**:
1. Locate the existing page component and its feature route entry
2. Apply the requested page-specific layout change:
   - `list`: add/remove displayed columns, update table header/cell definitions
   - `detail`: adjust `MatCard` sections or action placement
   - `dashboard`: update card grid composition
   - `workflow`: update step order, form step wiring, or button flow
3. Update the route definition if the guard changes
4. Update sidenav metadata if navigation label or visibility changes
5. Re-run compile validation

**Output**:
- Updated page component files
- Updated feature route definition when required
- Updated navigation entry when required

#### Delete

Remove a page and clean up routing and navigation references.

**Input Requirements**:
- Existing `pageName`
- Existing `featureName`
- Explicit confirmation before removal

**Process**:
1. Remove the standalone page component files
2. Remove the matching route from the feature route file
3. Remove the `MatNavList` item when the page is top-level
4. Check for remaining references from related pages (for example list-to-detail links)
5. Re-run compile validation

**Output**:
- Removed page component
- Removed route registration
- Removed sidenav navigation item when applicable

### Context Files

See [angular-material-patterns.md](../shared/angular-material-patterns.md) — Material design patterns for table pages, sidenav shells, card forms, dialogs, and snackbars.

Each shared file is referenced by a standard markdown link with a one-level-up relative path (e.g. `../shared/angular-material-patterns.md`). The shared files live at `.claude/skills/shared/`, sibling to each skill directory.

### Supporting Files

- `templates/list-page.ts.tpl` — Standalone Angular Material list-page TypeScript scaffold
- `templates/list-page.html.tpl` — Angular Material list-page template with table and loading state
- `../shared/angular-material-patterns.md` — Repo-facing path for the same shared Material context referenced above.

List-page templates act as the canonical scaffold for page generation. Detail, dashboard, and workflow pages are fully supported by the mode definitions above. Those non-list page types are generated from the documented mode rules and shared context even when dedicated template files are not listed separately in this section.

### Validation

**Post-Create/Modify/Delete Validation**:

1. **Route reachable**:
   - Start or inspect the application route tree and confirm the new or modified route is registered correctly
   - For lazy routes, verify `loadComponent` points at the generated standalone page component

2. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Confirm the page component, route file, and optional sidenav changes compile without errors

### Error Handling

**Common Errors**:

1. **Feature route file not found**:
   - Resolution: create or identify the owning feature route file before generating the page

2. **Authenticated page missing guard reference**:
   - Resolution: import and register the correct `CanActivate` guard in the route entry

3. **Workflow page missing reactive form dependencies**:
   - Resolution: run the `ng-reactive-form` skill first for the required step forms (see Dependencies below), then retry page generation

### Dependencies

**Required Skills**:

1. **ng-workspace** — Workspace and Angular Material foundation must exist
2. **ng-app** — Application shell and route structure must exist

**Common Upstream Skills**:

- **ng-data-service** — Needed for resource-backed list/detail pages
- **ng-component** — Useful for reusable dashboard widgets and nested page content
- **ng-reactive-form** — Needed for workflow steps and create/edit form flows

### Examples

**Example 1: Create a top-level users list page**

```json
{
  "pageName": "users-list",
  "routePath": "users",
  "pageType": "list",
  "featureName": "users"
}
```

**Process**:
1. Create a standalone list page with `MatTable`, `MatPaginator`, `MatSort`, and `MatProgressBar`
2. Add row-click navigation to the user detail route
3. Add a `"New"` button to route to the create workflow/form
4. Register the page in the users feature routes with `loadComponent`
5. Add a `MatNavList` item because the page is top-level

**Example 2: Create an authenticated workflow page**

```json
{
  "pageName": "order-checkout",
  "routePath": "checkout",
  "pageType": "workflow",
  "featureName": "orders"
}
```

**Process**:
1. Create a standalone `MatStepper` page backed by reactive form steps
2. Register the route with `loadComponent`
3. Add `CanActivate` guard reference for authenticated checkout access
4. Validate that the route is reachable and the app still compiles

## Angular Material site generation

**Skill Name**: `ng-site`

### YAML Frontmatter

```yaml
---
name: ng-site
description: Orchestrate Angular Material site generation across app shell, routing, OpenAPI clients, pages, forms, theme, and auth infrastructure
when_to_use: Use when build_app dispatches a site-composition procedure node (initial site generation or navigation/theme change), or when a user runs /ng-site to orchestrate site-level generation across app shell, routing, OpenAPI clients, pages, forms, theme, and auth infrastructure.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-site` skill coordinates complete Angular Material site generation for an application that already has an Angular workspace and app scaffold available. It acts as an orchestrator across app shell creation, route setup, OpenAPI client generation, page generation, reactive form generation, Material theming, and application-wide auth wiring. Use this skill when the agent needs to build or reshape the overall site structure rather than a single page or form in isolation.

### Inputs

Read from `django-angular3.json`:
- `angular.output`: Angular workspace root path
- `project.name`: Application name within the workspace
- `openapi.source`: Path to the OpenAPI source used by `ng-api` for client generation

Procedure-level inputs:
- **`uiSpecPath`** (string, optional): Path to a UI specification directory, typically under `spec/ui/`, used to discover pages, navigation structure, and forms
- **`defaults`** (object, optional): Fallback definitions to use when no UI spec is provided, such as default pages, route prefixes, or auth requirements

### Modes

All skills support three operational modes:

#### Create

Create a complete Angular Material site by orchestrating the existing Angular generation skills in the correct order and then wiring shared site-level infrastructure.

**Input Requirements**:
- `angular.output` must point to an existing Angular workspace
- `uiSpecPath` is optional; when provided it should point at the UI spec root or `spec/ui/`
- `openapi.source` is optional; when provided it should resolve to a valid OpenAPI document

**Process (Create Mode)**:

1. **Verify workspace and app exist before orchestration**
   - Read `angular.output` and `project.name` from `django-angular3.json`
   - Confirm `angular.output` exists and contains `angular.json`
   - Confirm the target Angular application already exists in the workspace
   - If either the workspace or application is missing, stop and instruct the caller to run `ng-workspace` first and then `ng-app`

2. **Read UI spec when provided**
   - If `uiSpecPath` is supplied, read `spec/ui/` (or the supplied equivalent) to determine:
     - top-level pages
     - route structure
     - navigation labels
     - workflow or form-backed screens
   - If no UI spec is provided, derive a minimal default site map from `defaults` or create a small starter set such as `home`, `dashboard`, and one authenticated workflow page

3. **Create the application shell**
   - Create or update `app.component.ts` as the Material site shell
   - Use `MatSidenav`, `MatToolbar`, `MatNavList`, and `RouterOutlet` for the top-level layout
   - Create or update the root route configuration in `app.routes.ts`
   - Ensure the shell exposes a stable place for feature navigation and authenticated child routes

4. **Invoke `ng-api` when an OpenAPI source is available**
   - If `openapi.source` is present in `django-angular3.json`, pass through to `ng-api` and generate or refresh Angular API clients before page or form generation
   - Reuse the generated models and services as the typed foundation for resource-backed pages and forms

5. **Invoke `ng-page` for each site page**
   - For every page discovered from the UI spec, invoke `ng-page` in sequence
   - If no UI spec exists, invoke `ng-page` for the default page set
   - Pass through page type, route path, feature ownership, authentication needs, and navigation metadata

6. **Invoke `ng-reactive-form` for each form definition**
   - For every form discovered in the UI spec, invoke `ng-reactive-form`
   - Prefer generated OpenAPI models when available
   - Attach generated forms to the relevant workflow or detail pages after form generation completes

7. **Set up the Material theme in `styles.scss`**
   - Create or update the application `styles.scss` file with Angular Material theme setup
   - Ensure the site-level styles cover shell layout, sidenav sizing, toolbar spacing, and global typography

8. **Set up `AuthGuard` in `core/guards/`**
   - Create or update `core/guards/auth.guard.ts`
   - Use the guard for authenticated routes discovered from the UI spec or required by defaults
   - Register guard references in the root or feature route tree as needed

9. **Set up an HTTP interceptor in `core/interceptors/` for CSRF**
   - Create or update a CSRF-focused interceptor under `core/interceptors/`
   - Register it in the app-wide HTTP client configuration
   - Ensure generated API traffic and reactive form submissions use the shared CSRF handling path

10. **Compile verification**
    - Run a full compile check after orchestration completes
    - Confirm the site shell, routing, generated pages, generated forms, auth guard, interceptor, and theme wiring build cleanly together

**Output**:
- Site-level `app.component.ts` shell with `MatSidenav` layout
- Root route configuration wired for generated pages and auth protection
- Generated OpenAPI clients when `openapi.source` is provided in `django-angular3.json`
- Generated Angular Material pages for each discovered or default page
- Generated reactive forms for each discovered form definition
- Global Material theme in `styles.scss`
- `AuthGuard` under `core/guards/`
- CSRF HTTP interceptor under `core/interceptors/`

#### Modify

Update an existing Angular Material site without regenerating the entire application.

**Supported Modification Variants**:
- **Theme** — update Material palettes, typography, density, or global shell styles in `styles.scss`
- **Navigation** — update `MatSidenav` items, labels, grouping, or top-level layout behavior in `app.component.ts`
- **Routing** — add, remove, reorder, or protect routes in the root route configuration and connected feature routes
- **Auth** — update `AuthGuard` behavior, route protection coverage, or CSRF interceptor registration

**Process**:
1. Identify the requested modification variant: `theme`, `navigation`, `routing`, or `auth`
2. Read the current app shell, root routes, styles, guard, and interceptor files
3. Apply only the requested site-level modification:
   - `theme`: update the Material theme definition and global layout styling
   - `navigation`: update sidenav structure, nav labels, route bindings, or shell responsiveness
   - `routing`: update root route composition, lazy route entries, redirects, and guard references
   - `auth`: update `AuthGuard`, protected route coverage, and CSRF interceptor/provider wiring
4. Re-run compile validation and a dry-run build

**Output**:
- Updated site-level shell, routes, theme, and/or auth infrastructure
- Change summary showing which site-wide concern was modified

#### Delete

Remove the Angular application that owns the generated site from the workspace.

**Input Requirements**:

Read from `django-angular3.json`: `angular.output`, `project.name`

Procedure-level inputs:
- Explicit confirmation before removal

**Process**:
1. Confirm the target application exists in the workspace
2. Remove the site by invoking the equivalent `ng-app` delete flow for the application
3. Remove site-level files that are unique to the app, including shell, routes, theme, guards, and interceptors if they are not shared elsewhere
4. Confirm the workspace remains valid after app removal

**Output**:
- Angular application removed from the workspace
- Site-specific shell, route, theme, and auth artifacts removed with the app

### Context Files

See [angular-conventions.md](../shared/angular-conventions.md)
See [angular-material-patterns.md](../shared/angular-material-patterns.md)
See [openapi-integration.md](../shared/openapi-integration.md)

### Supporting Files

- `templates/app-shell.ts.tpl` — Root site shell template used for `app.component.ts` generation with `MatSidenav` layout
- `context/angular-conventions.md` — Angular standalone application and DI conventions for app shell and route orchestration
- `context/angular-material-patterns.md` — Material sidenav, toolbar, navigation, and theme guidance used by the generated site shell
- `context/openapi-integration.md` — OpenAPI client generation and usage guidance for `ng-api`-driven pages and forms

### Validation

**Post-Create/Modify/Delete Validation**:

1. **Full compile**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   - Confirm the complete generated site compiles successfully

2. **Dry-run build**:
   ```bash
   django-angular3 ng_build django-angular3.json --dry-run
   ```
   - Confirm the dry-run build preview is valid without executing a full deployment build

3. **Manual route review**:
   - Confirm the app shell exposes the expected navigation structure
   - Confirm authenticated routes reference `AuthGuard`
   - Confirm forms and API-backed pages are reachable from the generated route tree

### Error Handling

**Common Errors**:

1. **Workspace or app missing**:
   - Resolution: run `ng-workspace` first, then `ng-app`, before invoking `ng-site`

2. **UI spec missing or incomplete**:
   - Resolution: fall back to defaults or stop and request a valid `spec/ui/` source when page/form inference is required

3. **OpenAPI source unavailable**:
   - Resolution: skip `ng-api` orchestration when no OpenAPI source is provided, or request a valid source path before generating resource-backed pages/forms

4. **Dependent page or form skill unavailable**:
   - Resolution: ensure `ng-page` and `ng-reactive-form` are available before site orchestration, then retry the failed step

5. **Auth or interceptor wiring fails compile validation**:
   - Resolution: review route guard imports, HTTP provider registration, and CSRF header handling before rerunning validation

### Dependencies

**Required Skills**:

1. **ng-workspace** — Angular workspace must exist before site orchestration starts
2. **ng-app** — Target Angular application must already exist so the site shell has a home

**Orchestrated Skills**:

- **ng-api** — Generates OpenAPI clients when `openapi_source_path` is provided
- **ng-page** — Generates each page discovered from the UI spec or defaults
- **ng-reactive-form** — Generates each form discovered from the UI spec

**Common Supporting Skills**:

- **ng-complex-component** — Useful when generated pages need richer reusable widgets inside dashboards or workflows

### Examples

**Example 1: Create a site from UI spec and OpenAPI**

Input from `django-angular3.json`: `angular.output = "/workspace/admin-portal"`, `project.name = "admin-portal"`, `openapi.source = "spec/openapi.yaml"`

```json
{
  "uiSpecPath": "spec/ui/"
}
```

**Process**:
1. Verify the workspace and app already exist
2. Read `spec/ui/` to discover pages and forms
3. Create the Material app shell and root routes
4. Invoke `ng-api`
5. Invoke `ng-page` for each discovered page
6. Invoke `ng-reactive-form` for each discovered form
7. Wire theme, `AuthGuard`, CSRF interceptor, and compile validation

**Example 2: Modify site navigation**

Input from `django-angular3.json`: `angular.output = "/workspace/admin-portal"`, `project.name = "admin-portal"`

```json
{
  "change": "navigation"
}
```

**Process**:
1. Read the existing app shell and root route tree
2. Update the `MatSidenav` navigation entries and bindings
3. Re-run compile validation and dry-run build

---

# Skill building

To create a skill from scratch with the skill-creator, I need roughly four things from you. Only the first two are required upfront; the rest can be built together.

**1. Intent — required, conversational**

Three short answers:
- What should the skill enable Claude to do? (the capability)
- When should it trigger? (user phrases, file types, contexts — this becomes the `description` field, which is what actually decides whether the skill fires)
- What's the expected output? (a file, a code change, a report, etc.)

Free-form prose is fine; I'll ask follow-ups to fill the gaps.

**2. Domain detail — required, format flexible**

Whatever a competent practitioner would need to do the task by hand. Concretely: the input shape (file paths, schemas, structured data, free text), the output shape (exact format, extensions, naming, directory layout), conventions or style rules the output must follow, edge cases (missing input, conflicts, partial state), and dependencies on other skills or artifacts.

The highest-bandwidth form here is a sample: an example input, a hand-written "good" output, or an existing spec doc. Much better than describing in prose. `GENERATE_AI_AUTOMATIONS.md` is exactly this kind of input — a structured spec.

**3. Bundled resources — optional**

Anything that should live inside the skill folder so the skill doesn't reinvent it on every run: scripts in `scripts/` for deterministic steps, long reference docs in `references/` loaded on demand, and assets in `assets/` (templates, fixtures, icons). If you don't have these, I draft them as part of skill creation.

**4. Evaluation setup — optional but recommended when outputs are verifiable**

Two or three realistic test prompts (what a real user would actually type), any input files those prompts need, and a rough sense of what "right" looks like — I turn that into assertions. For subjective outputs (writing style, design feel) we skip assertions and rely on your review of the rendered results.

---
