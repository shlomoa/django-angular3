# Provider adapter contracts

This document specifies the canonical provider-adapter contracts used by `djng`
to run automation primitives on a provider runtime, including the provider
lifecycle mappings for the Hook contracts defined in [HOOK_CONTRACTS.md]. The
automation subsystem architecture, primitive-selection policy, relationship
cardinality, and naming crosswalk are defined in `ARCHITECTURE.md` §§2.22 and
3.6. Exact internal module organization, persistence, execution, adapter, and
rendering realization are defined in
`doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md`.

The sibling automation contract owners are [TOOL_CONTRACTS.md],
[HOOK_CONTRACTS.md], [PLUGIN_CONTRACTS.md], and [SKILL_CONTRACTS.md]. The
canonical Change Model is defined in [CHANGE_MODEL_CONTRACTS.md].

---

## Provider adapter hook mappings

Each adapter maps the provider-neutral lifecycle families defined in
[HOOK_CONTRACTS.md] without changing their authoritative `build_app`
consequence:

| Provider adapter | `pre-tool` / `post-tool` mapping | `session-stop` mapping |
|---|---|---|
| Claude Agent SDK | Native `PreToolUse` / `PostToolUse` hooks registered in Claude Code `settings.json` | Native `Stop` hook in `settings.json` |
| OpenAI Agents / Responses | Local function-tool guard and hook manager | Adapter-managed session teardown |
| Gemini SDK / Antigravity | Decorator or wrapper around function-tool execution | Adapter-managed session teardown |
| Copilot SDK | `on_pre_tool_use` / `on_post_tool_use` hooks and permission handlers | Adapter-managed session teardown |

## Provider adapter contracts

Every provider adapter implements the provider-neutral interface defined by
this contract and returns normalized results. Adapter conformance is governed
by the following outcome matrix:

| Case | Adapter outcome | Required `build_app` behavior |
|---|---|---|
| Successful session | Returns acceptance evidence satisfying the selected Skill's criteria. | Advance only after recording the normalized evidence. |
| Unmet acceptance | Ends without sufficient acceptance evidence. | Halt, emit a structured `unmet_acceptance` error, and do not select a dependent command. |
| Timeout or context exhaustion | Returns the normalized timeout or context-exhaustion failure. | Halt, preserve diagnostics in the durable run record, and do not retry or advance implicitly. |
| Tool denial | Reports that the provider denied a requested Tool or permission. | Surface a structured `tool_denied` error and halt at the denied boundary. |
| Post-tool failure | The Tool succeeds but the normalized `post-tool` Hook outcome fails. | Halt with the Hook-failure result and do not treat the successful Tool result as acceptance. |
| Teardown | `session-stop` records a successful or warning-only cleanup outcome. | Record the outcome; a warning-only teardown failure does not change an already determined run result. |

Provider-independent conformance stubs MUST implement only the
provider-neutral adapter interface. They MUST NOT require credentials, network
access, or a provider SDK.

An opted-in provider runtime suite applies the same outcome matrix to the real
adapter when that provider's explicit credential and SDK prerequisites are
available. In addition to the shared assertions, it verifies provider-specific
Skill loading, Tool dispatch, lifecycle mapping, result normalization,
cancellation and timeout mapping, and teardown. If the explicit runtime
prerequisites are absent, the suite is skipped without prompting for or
exposing credentials.

[CHANGE_MODEL_CONTRACTS.md]: CHANGE_MODEL_CONTRACTS.md
[HOOK_CONTRACTS.md]: HOOK_CONTRACTS.md
[PLUGIN_CONTRACTS.md]: PLUGIN_CONTRACTS.md
[SKILL_CONTRACTS.md]: SKILL_CONTRACTS.md
[TOOL_CONTRACTS.md]: TOOL_CONTRACTS.md
