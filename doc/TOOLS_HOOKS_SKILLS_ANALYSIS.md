# Tools, Hooks, Skills, and Plugins — Analysis

## Purpose

This document fulfils the research task described in issue [Research the use of tools
and hooks in addition to skills].

It provides:
1. A comparison table of the four Claude extensibility primitives — Tools (& Plugins),
   Hooks, and Skills — sourced from Claude documentation.
2. A targeted scan of `ARCHITECTURE.md` to identify current uses of SKILLS or
   'scripts' that are better served by Tools (& Plugins), Hooks, or Plugins
   respectively, with reasoning for each recommendation.

## Implementation status

The Tools recommendations in §2 below have been promoted into explicit,
normative tool contracts. See `doc/GENERATE_AI_AUTOMATIONS.md` §Tool Contracts
Catalog for the per-capability contracts (name, inputs, outputs, error
behavior, allowed invocation context) covering:

- `export_schema` — §2.1 of this document
- `oasdiff_diff` — §2.2 of this document
- `ng_openapi_gen` — §2.3 of this document
- `ngdj_create_workspace`, `ngdj_create_app` — §2.4 of this document
- `validate_openapi_schema` — §2.5 of this document

The Hooks recommendations in §3 below have been promoted into explicit,
normative hook contracts. See `doc/GENERATE_AI_AUTOMATIONS.md` §Hook Contracts
Catalog for the per-capability contracts (name, purpose, trigger event,
deterministic action, failure behavior, allowed wrapped tools, implementation
reference) covering:

- `pre-construction` — §3.5 of this document (contract validation gate)
- `migration-triggered` — §3.2 of this document (OpenAPI schema re-extraction)
- `breaking-change` — §3.1 of this document (gate on schema diff)
- `post-generation` — §3.3 of this document (verification logging)
- `session-stop` — §3.4 of this document (archiving and audit cleanup)

The Plugins recommendations in §4 below have been promoted into explicit,
normative plugin contracts. See `doc/GENERATE_AI_AUTOMATIONS.md` §Plugin
Contracts Catalog for the per-capability contracts (name, purpose, bundled
SKILLS / TOOLS / HOOKS, distribution, versioning, dependencies, installation,
implementation reference) covering:

- `djng-angular-construction` — §4.1 of this document
- `ngdj-scaffold` — §4.2 of this document
- `contract-lifecycle` — §4.3 of this document

References used:
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/hooks-guide
- https://code.claude.com/docs/en/plugins
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

---

## 1. Comparison Table — Tools, Hooks, Skills, Plugins

| Dimension | **Skills** | **Tools** | **Hooks** | **Plugins** |
|---|---|---|---|---|
| **What it is** | A reusable knowledge/procedure unit that teaches Claude *how* to carry out a specific construction task | An external callable function or service that Claude invokes to extend its reach | A shell script or callback triggered automatically at a lifecycle event | A distributable bundle that packages Skills, Tools (MCP configs), Hooks, and Agents together |
| **Primary purpose** | Encode domain know-how and multi-step task procedures for the agent to follow | Expose deterministic capabilities (APIs, CLI tools, file operations) the agent can call | Automate deterministic actions at defined points in the agent lifecycle without agent involvement | Share and distribute a cohesive set of capabilities across teams or projects |
| **Format** | `SKILL.md` with YAML frontmatter, markdown body, optional context/templates/examples directories | MCP server specification or Python/shell function registered via `.mcp.json` or `allowed-tools` | Shell script or function declared in Claude settings (`.claude/settings.json`) under a lifecycle event key | Directory with `plugin.json` manifest, `skills/`, `hooks/`, `mcp-servers/` subdirectories |
| **Invocation** | Invoked by the outer agent orchestrator based on task context; never directly by users | Called by the agent at its own discretion during task execution | Triggered automatically by Claude Code at a lifecycle event (not by the agent, not by the user) | Installed once; its contents (Skills, Hooks, Tools) then follow their individual invocation models |
| **Lifecycle events** | N/A — selected per agent session | N/A — called on demand by the agent | `PreToolUse` · `PostToolUse` · `UserPromptSubmit` · `Stop` | N/A — wraps other primitives |
| **AI involvement** | High — Claude interprets and applies the skill | Low — Claude only decides *when* to call the tool; the tool itself runs deterministically | None — lifecycle hooks run deterministically as plain scripts | None in the bundle itself; depends on what it packages |
| **Determinism** | Non-deterministic (AI-guided) | Deterministic (tool executes predictably) | Deterministic (script runs on event) | Depends on contents |
| **Token cost** | Medium–high (full SKILL.md loaded per session) | Low (only tool declaration loaded) | Zero (runs outside the context window) | Sum of packaged components |
| **Best for** | Multi-step generative work requiring AI judgment: generating, composing, or modifying code artifacts | Single bounded operations: schema extraction, schema diff, CLI generation, file I/O wrappers | Enforcement, validation gates, logging, cleanup, mandatory side-effects that must not be skipped | Distributing a complete, coherent capability set to other projects or teams |
| **Example** | "Generate an Angular feature page from an OpenAPI resource definition" | "Run `oasdiff` and return the diff as structured JSON" | "Block proceeding if `oasdiff` reports breaking changes (PreToolUse)" | "djng Angular construction plugin: bundles all 11 skills + schema tools + validation hooks" |

### Key distinctions to remember

- A **Skill** is AI-guided knowledge. Use it when the task requires judgment, iteration, or code authoring.
- A **Tool** is a deterministic callable. Use it when the agent needs to run a fixed command or query a system and get back a structured result.
- A **Hook** runs *outside* the agent's context window on lifecycle events. Use it to guarantee that certain deterministic actions (blocking checks, logging, cleanup) always run — even if the agent would not choose to invoke them.
- A **Plugin** is a packaging and distribution unit. Use it to ship a self-contained capability to another project or team.

---

## 2. ARCHITECTURE.md Scan — Candidates for Tools (& MCP Tools)

The following operations identified in `ARCHITECTURE.md` are currently described as
SKILLS-based or script-based work, but are in fact deterministic bounded operations
that are better expressed as **Tools** (registered MCP tools or `allowed-tools`
functions the agent calls directly).

### 2.1 OpenAPI Schema Extraction (`export_schema` command)

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §3.3 djng-o-1, §7.1 stage 1, §11.1 |
| **Current approach** | A Django management command (`export_schema`) that extracts the OpenAPI schema from DRF |
| **Why a Tool is better** | Schema extraction is a bounded, deterministic shell operation with a fixed output format. It does not require AI judgment. Exposing it as an MCP tool lets the agent call it on demand and receive the resulting schema path or content as a structured return value — eliminating any ambiguity about when extraction has occurred. |
| **Recommended form** | MCP tool wrapping `python manage.py export_schema`, returning the schema file path and a change-detected flag. |

### 2.2 Schema Diff and Change Detection (`oasdiff`)

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.1 stage 2, §11.2, §11.4, §17 |
| **Current approach** | Running `oasdiff` as an external CLI tool during the contract normalization stage |
| **Why a Tool is better** | Schema diffing is entirely deterministic. The agent needs structured output (breaking changes list, non-breaking changes list, version delta) to derive the procedure graph. As a registered MCP tool, `oasdiff` output can be returned as typed JSON that the agent reads, rather than the agent having to parse raw CLI output via Bash. |
| **Recommended form** | MCP tool wrapping `oasdiff` invocation, returning structured diff result with `breaking: []`, `non_breaking: []`, and `schema_changed: bool` fields. |

### 2.3 Angular TypeScript Client Generation (`ng-openapi-gen`)

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.1 stage 3, §11.2, §17 |
| **Current approach** | Running `ng-openapi-gen` as a generation step within or alongside the agent session |
| **Why a Tool is better** | TypeScript client generation from an OpenAPI schema is deterministic given fixed inputs. Registering `ng-openapi-gen` as a tool lets the agent call it with explicit input/output parameters and get back confirmation of generated file paths — without requiring a full SKILL to manage this step. |
| **Recommended form** | MCP tool wrapping `ng-openapi-gen --config <path>`, returning a list of generated file paths. |

### 2.4 Angular Workspace and Application Commands (`ngdj` CLI)

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §3.4 ngdj-o-1, §3.5 |
| **Current approach** | Described as `ngdj` commands for managing and assembling the Angular application (workspace, project layout, application layout) |
| **Why a Tool is better** | Workspace and application scaffold commands are deterministic schematics invocations. The agent only needs to call them with the right parameters. Exposing them as tools removes the need for a SKILL to manage how to invoke them and interpret their output. |
| **Recommended form** | MCP tools for each `ngdj` command: `ngdj_create_workspace`, `ngdj_create_app`, `ngdj_add_feature`, returning structured result objects. |

### 2.5 Contract Validation

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.1 stage 2, §7.3, §11.1 |
| **Current approach** | Validation is described as a construction-stage concern handled within the construction flow |
| **Why a Tool is better** | OpenAPI schema validation against the OAS 3.1 specification is deterministic and has a binary valid/invalid result with an error list. Registering a `validate_openapi_schema` tool means the agent gets back a structured validation report rather than needing to interpret raw validator output. |
| **Recommended form** | MCP tool wrapping an OpenAPI linter/validator (e.g. `spectral lint`), returning `{ valid: bool, errors: [] }`. |

---

## 3. ARCHITECTURE.md Scan — Candidates for Hooks

The following operations are deterministic enforcement or side-effect steps that must
always run at defined moments in the workflow. They do not require AI judgment and
are therefore better expressed as **Hooks** rather than SKILL steps or agent
instructions.

### 3.1 Breaking-Change Gate (PreToolUse on schema-diff tool)

**Promoted contract**: [`breaking-change`](GENERATE_AI_AUTOMATIONS.md#3-breaking-change--gate-on-schema-diff) in `doc/GENERATE_AI_AUTOMATIONS.md` §Hook Contracts Catalog. The contract is authoritative; the table below is historical analysis and may not match the promoted hook surface.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.1 stage 2, §11.1, §11.2 |
| **Current approach** | "Breaking changes must block downstream generation until explicitly acknowledged or resolved" — currently stated as an architectural rule enforced inside construction logic |
| **Why a Hook is better** | A `PreToolUse` hook on the schema-diff tool (or on any downstream generation tool) can inspect the diff result and exit non-zero to halt the agent session automatically if unacknowledged breaking changes are detected. This makes the gate deterministic and unavoidable, regardless of what the AI agent decides. |
| **Hook event** | `PreToolUse` on `ng-openapi-gen` tool or on the Angular generation tool |
| **Hook action** | Read `oasdiff` output; if `breaking` is non-empty and not acknowledged, print an error message and exit non-zero to block the tool invocation. |

### 3.2 Migration-Triggered Schema Extraction

**Promoted contract**: [`migration-triggered`](GENERATE_AI_AUTOMATIONS.md#2-migration-triggered--openapi-schema-re-extraction) in `doc/GENERATE_AI_AUTOMATIONS.md` §Hook Contracts Catalog.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §11.2 |
| **Current approach** | "Any datamodel change creating a Django database migration file (after makemigrations) will force an OpenAPI schema extraction" — currently an architectural rule with no specified enforcement mechanism |
| **Why a Hook is better** | A `PostToolUse` hook on the `makemigrations` tool (or a `UserPromptSubmit` hook that detects new migration files) can automatically trigger `export_schema` whenever a new migration is detected. This removes the human or agent responsibility of remembering to re-export. |
| **Hook event** | `PostToolUse` on `makemigrations` call or file-watch hook on `migrations/` directory |
| **Hook action** | If new `.py` migration files are detected, invoke `export_schema` to re-export and rotate the schema artifact; append a status record to `build/hook-log.jsonl` and exit 0 so downstream `breaking-change` and `pre-construction` hooks act on the rotated schema. |

### 3.3 Post-Generation Verification Logging

**Promoted contract**: [`post-generation`](GENERATE_AI_AUTOMATIONS.md#4-post-generation--verification-logging) in `doc/GENERATE_AI_AUTOMATIONS.md` §Hook Contracts Catalog.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.2, §7.3, §14.3 |
| **Current approach** | Verification is described as occurring throughout construction — "inspect emitted artifacts and validation results" — and relies on the agent doing this inspection |
| **Why a Hook is better** | A `PostToolUse` hook after each generation tool invocation (e.g. `ng-openapi-gen`, `ngdj` commands) can automatically run a lightweight structural check (e.g. TypeScript compilation check, file count check) and write a machine-readable log entry. This provides guaranteed, consistent logging independent of the agent's iteration decisions. |
| **Hook event** | `PostToolUse` on `ng-openapi-gen` and `ngdj_*` tools |
| **Hook action** | Run `tsc --noEmit` in the generated app workspace and append pass/fail result to `build/verification.log`. |

### 3.4 Session-End Cleanup and Audit (Stop)

**Promoted contract**: [`session-stop`](GENERATE_AI_AUTOMATIONS.md#5-session-stop--archiving-and-audit-cleanup) in `doc/GENERATE_AI_AUTOMATIONS.md` §Hook Contracts Catalog.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.2, §7.4 |
| **Current approach** | Not described — cleanup and build artifact management are implicit |
| **Why a Hook is better** | A `Stop` hook runs when the agent session ends, whether successfully or due to an error. It provides a guaranteed opportunity to archive the procedure graph output, clean up temporary files, and record session metadata (schema version, procedures completed, errors encountered) without depending on the agent to carry out these steps. |
| **Hook event** | `Stop` |
| **Hook action** | Archive `build/procedure-graph.*` to `build/history/<timestamp>/`; write session summary to `build/session-log.json`. |

### 3.5 Pre-Construction Contract Validation Gate

**Promoted contract**: [`pre-construction`](GENERATE_AI_AUTOMATIONS.md#1-pre-construction--contract-validation-gate) in `doc/GENERATE_AI_AUTOMATIONS.md` §Hook Contracts Catalog.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.1 stage 2, §11.1 |
| **Current approach** | "The exported schema should be stored as a durable build artifact so downstream agent-chain stages can consume it deterministically" and "Contract changes should be reviewed as part of normal API change management" |
| **Why a Hook is better** | A `PreToolUse` hook on any Angular generation tool can validate that the OpenAPI schema file exists, is valid OAS 3.1, and has been exported since the last model change. This makes the validation gate happen automatically before any generation step, rather than relying on the agent to decide to validate first. |
| **Hook event** | `PreToolUse` on `ng_openapi_gen`, `ngdj_create_workspace`, `ngdj_create_app`, and future `ngdj_*` generation tools |
| **Hook action** | Check schema file exists and modification timestamp is newer than last migration; invoke `validate_openapi_schema`; if any check fails, exit non-zero and print a descriptive error. |

---

## 4. ARCHITECTURE.md Scan — Candidates for Plugins

Plugins bundle Skills, Tools, Hooks, and MCP configs into a distributable, installable
unit. The following groupings in `ARCHITECTURE.md` represent coherent capability sets
that are natural candidates for packaging as **Plugins**.

### 4.1 djng Angular Construction Plugin

**Promoted contract**: [`djng-angular-construction`](GENERATE_AI_AUTOMATIONS.md#1-djng-angular-construction--angular-construction-bundle) in `doc/GENERATE_AI_AUTOMATIONS.md` §Plugin Contracts Catalog.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §2.5, §2.14, §3.3, §3.5 |
| **Current approach** | All construction capabilities (agent, SKILLS, `build_app` entry point, configuration) are bundled inside the `djng` repository but are not packaged in the Claude plugin format |
| **Why a Plugin is better** | The full set of 11 Angular construction Skills, the schema and generation Tools (§2 above), and the validation/enforcement Hooks (§3 above) together form a complete, coherent capability that any `djng`-backed project needs. Packaging them as a Claude plugin enables: (a) installation with a single command, (b) versioning independent of the Django package, (c) reuse across multiple generated-app projects without copying files. |
| **Plugin contents** | Skills: all 11 Angular SKILL.md files (`ng-workspace`, `ng-app`, `ng-api`, `ng-data-service`, `ng-field-component`, `ng-form-field`, `ng-component`, `ng-complex-component`, `ng-reactive-form`, `ng-page`, `ng-site`); Tools: `export_schema`, `oasdiff_diff`, `ng_openapi_gen`, `validate_openapi_schema`; Hooks: breaking-change gate (PreToolUse), migration-triggered extraction (PostToolUse), session cleanup (Stop). |

### 4.2 ngdj Angular Scaffold Plugin

**Promoted contract**: [`ngdj-scaffold`](GENERATE_AI_AUTOMATIONS.md#2-ngdj-scaffold--angular-schematics-bundle) in `doc/GENERATE_AI_AUTOMATIONS.md` §Plugin Contracts Catalog.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §2.6, §3.4 |
| **Current approach** | `ngdj` is a separate npm package providing Angular schematics and code generation templates, invoked by the agent as CLI commands |
| **Why a Plugin is better** | `ngdj`'s workspace, application, and code generation commands could be exposed as a plugin containing MCP tools for each schematic. This would let the agent call `ngdj` capabilities through structured tool calls rather than raw `Bash` invocations, with typed inputs and outputs. The plugin would be installed once per project and could be versioned alongside `ngdj`. |
| **Plugin contents** | Tools: `ngdj_create_workspace`, `ngdj_create_app`, `ngdj_add_feature`, `ngdj_add_component`, `ngdj_run_schematic`; MCP config pointing to the `ngdj` CLI MCP server. |

### 4.3 Contract Lifecycle Plugin

**Promoted contract**: [`contract-lifecycle`](GENERATE_AI_AUTOMATIONS.md#3-contract-lifecycle--openapi-contract-bundle) in `doc/GENERATE_AI_AUTOMATIONS.md` §Plugin Contracts Catalog.

| | |
|---|---|
| **Location in ARCHITECTURE.md** | §7.1 stages 1–2, §11.1, §11.2, §11.4 |
| **Current approach** | Contract lifecycle operations (export, validate, diff, version) are distributed across `djng` commands, `oasdiff` CLI, and agent-session instructions |
| **Why a Plugin is better** | The contract lifecycle forms a self-contained domain: export → validate → diff → version → gate. Packaging this domain as a plugin with its own tools and hooks makes the contract boundary explicit and reusable independently of the full Angular construction flow. Teams working only on the backend contract management layer could install this plugin without the full construction stack. |
| **Plugin contents** | Tools: `export_schema`, `validate_openapi_schema`, `oasdiff_diff`, `oasdiff_changelog`; Hooks: breaking-change PreToolUse gate, migration-triggered PostToolUse extraction. |

---

## 5. Summary Decision Guide

Use this table when deciding which primitive to apply to a new capability in `djng`:

| If the work… | Use |
|---|---|
| Requires AI judgment, iteration, or multi-step code authoring | **Skill** |
| Is a single deterministic command, API call, or file operation | **Tool** |
| Must run automatically at a lifecycle event, regardless of agent choices | **Hook** |
| Is a coherent set of capabilities intended for distribution or reuse across projects | **Plugin** |
| Is both deterministic and must be guaranteed to run at a specific event | **Hook** (wrapping a **Tool**) |
| Is a complete construction workflow for a team | **Plugin** (bundling **Skills** + **Tools** + **Hooks**) |

---

## References

[Claude Skills]: https://code.claude.com/docs/en/skills  
[Claude Hooks Guide]: https://code.claude.com/docs/en/hooks-guide  
[Claude Plugins]: https://code.claude.com/docs/en/plugins  
[Claude Tool Use]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
[ARCHITECTURE.md]: ARCHITECTURE.md  
[GENERATE_AI_AUTOMATIONS.md]: GENERATE_AI_AUTOMATIONS.md  
[APP_BUILDER_REQUIREMENTS.md]: APP_BUILDER_REQUIREMENTS.md  
