# Hook contracts

This document specifies the canonical lifecycle Hook contracts used by `djng`
to build and maintain Angular applications. The automation subsystem
architecture, primitive-selection policy, relationship cardinality, and naming
crosswalk are defined in `ARCHITECTURE.md` §§2.22 and 3.6. Exact internal
module organization, persistence, execution, adapter, and rendering
realization are defined in
`doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md`.

All `ngdj` command, option, and behavior facts used by these contracts follow
the upstream-source policy in `ARCHITECTURE.md` §2.6. This document defines
only `djng`-owned Hook contracts and does not redefine the underlying `ngdj`
schematic surface.

The sibling automation contract owners are [TOOL_CONTRACTS.md],
[PROVIDER_ADAPTER_CONTRACTS.md], [PLUGIN_CONTRACTS.md], and
[SKILL_CONTRACTS.md]. The canonical Change Model is defined in
[CHANGE_MODEL_CONTRACTS.md].

---

## Hooks

Use HOOKS for deterministic lifecycle enforcement points that must run whether
or not the agent would choose to do so. In the `djng` architecture, this
includes migration-triggered schema export,
pre-construction contract validation, post-generation verification logging, and
session-stop cleanup and audit behavior.

Per-capability hook contracts are defined in the
[Hook Contracts Catalog](#hook-contracts-catalog) below. Each contract follows
the same fixed shape — **name, purpose, trigger event, deterministic action,
failure behavior, allowed wrapped tools, implementation reference** — so
`build_app` command execution and every provider adapter see the same surface.

`build_app` direct command-execution gates are the authoritative enforcement
boundary. Provider-native hooks, handlers, and wrappers are adapter mechanisms
that normalize provider-runtime events into this contract; they cannot override
or bypass a failed `build_app` gate or terminal validation.

### Hook contract shape

Every hook contract in this document **MUST** specify:

| Field | Meaning |
|---|---|
| **Name** | The stable identifier the hook is registered under. It is used during direct `build_app` command execution and as the provider-adapter handler key. |
| **Purpose** | One-sentence statement of the lifecycle enforcement the hook guarantees. Must be deterministic — no AI judgment inside the hook itself. |
| **Trigger event** | The provider-neutral lifecycle family that fires the hook: `pre-tool`, `post-tool`, or `session-stop`. A `pre-tool` hook blocks its wrapped command before it runs; a `post-tool` hook validates it after it runs; a `session-stop` hook runs at teardown. Tool names referenced here MUST match a contract in the [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog) or an explicitly named external command. Provider mappings are defined in [Provider adapter hook mappings](PROVIDER_ADAPTER_CONTRACTS.md#provider-adapter-hook-mappings). |
| **Deterministic action** | Step-by-step description of what the hook does on the trigger event. The action must be reproducible — same inputs always produce the same outcome and side effects. When the hook performs a deterministic operation that already has a tool contract in [TOOL_CONTRACTS.md], it MUST invoke that contract by name rather than calling the underlying binary directly. |
| **Failure behavior** | What the hook does when its check fails or its action errors. MUST specify the cross-provider consequence (`pre-tool`: block; `post-tool`: halt further processing; `session-stop`: warn only), the `build_app` process exit code for direct execution, and the structured message written to stderr or to the durable artifact log. An adapter maps this consequence to its provider runtime. |
| **Allowed wrapped tools** | The tool contract names (from the [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog)) or external commands the hook may scope itself to. Hooks MUST NOT silently apply themselves to tools outside this list. |
| **Implementation reference** | Pointer to the concrete script or planned implementation that backs the contract, so the contract and the implementation can be kept aligned. |

Contracts are normative. An implementation that deviates from a documented
contract is a bug in the implementation, not in the contract.

#### Shape rationale

The seven fields describe the provider-neutral enforcement contract:

- **Name** and **Trigger event** identify a stable catalog key and lifecycle
  family. The command executor uses them to select a boundary before a tool,
  after a tool, or at teardown; adapters map that family to their provider's
  event, handler, or wrapper model.
- **Purpose** is required so that consumers of the catalog — the
  `build_app` command translator, reviewers, and future plugin authors —
  can verify at a glance what invariant a hook enforces without reading the
  implementation. It also makes the *deterministic* constraint explicit: a
  one-sentence purpose that requires AI judgment signals a misclassification
  (the capability belongs in a SKILL, not a HOOK).
- **Deterministic action** and **Allowed wrapped tools** constrain the hook's
  blast radius together. The action describes *what* the hook does step by
  step; the allowed-tools list declares *which tools* the hook may scope itself
  to through its adapter. Both fields are needed to validate a
  hook against its contract without executing it, and to detect if an
  implementation silently broadens its scope beyond the catalogued boundary.
- **Failure behavior** defines the authoritative block, halt, or warning
  consequence for `build_app` execution. Adapters preserve that consequence in
  their provider runtime, but do not define a competing acceptance decision.
- **Implementation reference** links the normative contract to the concrete
  backing artifact (script path, planned ticket, or external CLI) so that drift
  between the spec and the code is detectable during review. Without this
  field, a contract can become unanchored documentation with no path back to
  the running system.

## Hook Contracts Catalog

This catalog defines the lifecycle hook contracts referenced from
`doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Change-to-Automations Mapping. Each entry follows the
[hook contract shape](#hook-contract-shape) defined above.

The contracts use provider-neutral lifecycle families and are grouped by when
they fire relative to command execution:
**pre-construction gates** fire before generation commands; **mid-run
triggers** fire on backend events that invalidate prior artifacts;
**post-generation enforcement** fires after each generation tool; **session
lifecycle** fires when the agent session ends.

### Pre-construction gates

#### 1. `pre-construction` — contract validation gate

**Name**: `pre-construction`

**Purpose**: Guarantee that the OpenAPI schema artifact exists, is valid
OAS 3.1, and is at least as fresh as the latest Django migration before any
Angular generation tool is allowed to run.

**Trigger event**: `pre-tool` scoped to the Angular generation tools
`angular_api_client_generate`, `angular_workspace_scaffold`, `angular_app_scaffold`
(and any future generation tool contracts). Also runs as the very first gate of every
`build_app` invocation, before direct execution reaches any generation
command.

**Deterministic action**:

1. Read `artifacts.openapiSchema` from the discovered project configuration.
2. Assert the schema file exists and its modification timestamp is greater
   than or equal to the newest migration file under the configured Django
   apps' `migrations/` directories.
3. Invoke the `validate_openapi_schema` tool contract with the schema path.
4. If `valid: true`, allow the wrapped tool to run (exit 0).

**Failure behavior**:

- If the schema file is missing, stale, or `validate_openapi_schema` returns
  `valid: false`, write a structured error
  `{ hook: "pre-construction", category, message, schema_path, ... }` to
  stderr **and** to `build/hook-log.jsonl`, and block the wrapped tool.
- In `build_app`, hook failure MUST halt the run with this hook’s dedicated
  hook-failure exit code (distinct from FR-8 tool-failure exit codes).
- The hook MUST NOT attempt to auto-repair (e.g. it does not invoke
  `openapi_schema_export` itself); auto-extraction is the responsibility of the
  `migration-triggered` hook.

**Allowed wrapped tools**: `angular_api_client_generate`, `angular_workspace_scaffold`,
`angular_app_scaffold`, future generation tools.

**Implementation reference**: planned handler `hooks/pre-construction.sh`.
It wraps `validate_openapi_schema` via its tool contract and is registered by
the applicable provider adapter.

### Mid-run triggers

#### 2. `migration-triggered` — OpenAPI schema re-extraction

**Name**: `migration-triggered`

**Purpose**: Guarantee that whenever a new Django migration file is produced,
the OpenAPI schema artifact is re-exported so downstream construction always
sees a contract that matches the current data model.

**Trigger event**: `post-tool` scoped to any tool invocation that runs
`python manage.py makemigrations` (e.g. a `bash` tool call detected by the
`makemigrations` substring in its command).

**Deterministic action**:

1. Enumerate the migration files added or modified during the wrapped tool
   call by listing the contents of each app's `migrations/` directory and
   comparing against the pre-call snapshot captured by the hook runner.
2. If the set is non-empty, invoke the `openapi_schema_export` tool contract;
  it discovers the project's `django-angular3-<project_name>.json` configuration.
3. Append a `{ hook: "migration-triggered", migrations: [...], destination,
   previous_path, schema_changed }` record to `build/hook-log.jsonl`.
4. Exit 0 regardless of `schema_changed`; the `pre-construction` hook will
  validate the rotated schema before generation.

**Failure behavior**:

- If `openapi_schema_export` returns a non-success error object, write
  `{ hook: "migration-triggered", category, message, details }` to stderr
  and to `build/hook-log.jsonl`, and exit non-zero.
- A non-zero exit does **not** roll back the `makemigrations` result (the
  migration files remain on disk) but does halt the agent session so the
  human operator can repair the schema-extraction failure before any
  Angular generation proceeds.

**Allowed wrapped tools**: any tool invocation that calls
`manage.py makemigrations`. The hook MUST NOT fire for unrelated tool calls.

**Implementation reference**: planned handler `hooks/migration-triggered.sh`.
It wraps `openapi_schema_export` via its tool contract and is registered by
the applicable provider adapter.

### Post-generation enforcement

#### 3. `post-generation` — verification logging

**Name**: `post-generation`

**Purpose**: Guarantee that every Angular generation tool invocation is
followed by a deterministic structural check whose pass/fail result is
recorded to a machine-readable log, regardless of whether the agent would
choose to re-inspect the output.

**Trigger event**: `post-tool` scoped to `angular_api_client_generate`,
`angular_workspace_scaffold`, `angular_app_scaffold`, and any future
generation tool contract.

**Deterministic action**:

1. Read the wrapped tool's structured output (e.g. the `generated_files`
   array returned by `angular_api_client_generate`) from the run's artifact location.
2. Run a lightweight structural check appropriate to the wrapped tool:
   - For `angular_api_client_generate`: `tsc --noEmit` in the generated app workspace
     (`artifacts.angularWorkspace`).
   - For `angular_workspace_scaffold` / `angular_app_scaffold`: assert the expected
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

**Allowed wrapped tools**: `angular_api_client_generate`, `angular_workspace_scaffold`,
`angular_app_scaffold`, future generation tools.

**Implementation reference**: planned handler `hooks/post-generation.sh`,
registered by the applicable provider adapter.

### Session lifecycle

#### 4. `session-stop` — archiving and audit cleanup

**Name**: `session-stop`

**Purpose**: Guarantee that, whenever a `build_app`-driven agent session
ends — successfully, by user interrupt, or by error — the run's durable
artifacts are archived and a session summary is recorded.

**Trigger event**: `session-stop`. Fires exactly once per agent session,
unconditionally.

**Deterministic action**:

1. Read a stable session timestamp `YYYYMMDDTHHMMSSZ` from a durable location (e.g. `build/session-timestamp.txt`); if missing, compute it and persist it so retries reuse the same value.
2. Move (not copy) `build/command-execution.*`, `build/oasdiff-report.json`,
   `build/verification.log`, and `build/hook-log.jsonl` into
   `build/history/<timestamp>/`. Missing artifacts are silently skipped.
3. Write (or update) a session summary
  `{ hook: "session-stop", timestamp, schema_version, commands_completed,
  commands_failed, hook_failures, exit_code }` to
   `build/session-log.json` (append to the JSON array on disk only if an entry for this `timestamp` does not already exist).
4. Exit 0.

**Failure behavior**:

- A `session-stop` hook cannot block the session from ending; failure is
  recorded only.
- If archiving fails (e.g. disk full, permission error), write
  `{ hook: "session-stop", category, message, details }` to stderr and to
  whatever portion of `build/session-log.json` is still writable, then
  return a warning outcome. The warning does not retroactively change the
  session outcome.
- The hook MUST be idempotent: re-running it after a partial failure must
  not duplicate archived artifacts or session summary entries.

**Allowed wrapped tools**: not applicable — `session-stop` is not scoped to a tool.

**Implementation reference**: planned handler `hooks/session-stop.sh`,
registered by the applicable provider adapter.

### Provider adapter hook mappings

Provider-native lifecycle mappings for the families above are owned by
[Provider adapter hook mappings](PROVIDER_ADAPTER_CONTRACTS.md#provider-adapter-hook-mappings)
in [PROVIDER_ADAPTER_CONTRACTS.md]. An adapter maps a lifecycle family into its
provider runtime without changing the authoritative `build_app` consequence
defined here.

### Contract compliance

- `build_app` MUST apply an enforced command boundary whose `hook` equals one
  of the **Name** values above: before a wrapped command for `pre-tool` hooks,
  after it for `post-tool` hooks, and at session teardown for `session-stop`.
  Ad-hoc
  `Bash` invocations of the actions above outside the hook mechanism are not
  permitted.
- HOOKS that need to perform a deterministic operation also covered by the
  [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog) MUST do so
  by invoking the corresponding tool contract — not by calling the underlying
  binary directly — so error categories and structured outputs remain uniform.
- New lifecycle enforcement points added to `djng` MUST be documented here
  using the [hook contract shape](#hook-contract-shape) before they may
  appear as an enforced command boundary or be registered through a provider
  adapter.

[CHANGE_MODEL_CONTRACTS.md]: CHANGE_MODEL_CONTRACTS.md
[PLUGIN_CONTRACTS.md]: PLUGIN_CONTRACTS.md
[PROVIDER_ADAPTER_CONTRACTS.md]: PROVIDER_ADAPTER_CONTRACTS.md
[SKILL_CONTRACTS.md]: SKILL_CONTRACTS.md
[TOOL_CONTRACTS.md]: TOOL_CONTRACTS.md
