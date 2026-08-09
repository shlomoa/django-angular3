# AI Knowledge Integration

## Findings

`shlomoa/ai` is private but authenticated access confirmed it contains tested examples for all four providers:

- **Claude**: Agent SDK `query`, MCP tools, native hooks, filesystem skills, `.claude-plugin`.
- **OpenAI/ChatGPT**: Responses API and `openai-agents`; local function-tool guard/hook manager and explicit skill-bundle loading.
- **Gemini/Antigravity**: `google-genai`, function tools, decorator-based local hook wrapping.
- **Copilot**: `github-copilot-sdk`, sessions, permission handlers, `on_pre_tool_use` / `on_post_tool_use`.

The transferable design is a **provider-neutral automation contract plus provider-specific adapters**. Hooks are particularly non-portable: Claude supports native lifecycle hooks; the other providers implement equivalent pre/post execution wrappers.

## Claude references in `djng`

There is **no implemented Claude SDK import, `query()` call, or orchestration adapter** in django_angular3; `claude-agent-sdk` is only a declared dependency. Current references are all configuration, plans, or architecture documentation:

- `pyproject.toml:33` — declares `claude-agent-sdk`.
- `TODO.md:184–201` — planned Claude Code Python SDK orchestration and failure modes.
- `e2e_enabling_documentation_plan.md:131` — planned `sdk.query()` per selected SKILL command.
- `doc/phased_implementation_plan.md:236–259` — Phase 5 is explicitly “Claude Agent SDK.”
- `doc/APP_BUILDER_REQUIREMENTS.md:436–560` — FR-8 requires a Claude Agent SDK call for each `skill-session`; glossary and non-functional requirements also name it.
- `doc/ARCHITECTURE.md:73–91, 758, 779–784` — Anthropic skill format, Claude Agent SDK as agent implementation, and upstream links.
- `doc/GENERATE_AI_AUTOMATIONS.md:24, 559–893, 916–1228, 1266–1324` — the largest concentration: Claude Code hook lifecycle/exit behavior, plugin manifest/installation model, SKILL format, `query(skills=…, allowedTools=…)`, and SDK/CLI differences.
- `doc/REQUIREMENTS.md:15, 957, 1037–1039` — Claude Skills and Agent SDK requirements/references.
- `doc/SKILL_AUTHORING_PLAN.md:90, 250–262` — Anthropic skill format and Claude Code/SDK docs.
- `doc/TEST_EXAMPLES.md:520` — Claude Code hook blocking example.
- `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md:9–10, 57–73, 224–225, 269–272` — Claude-derived comparison and plugin recommendations.
- `skill_creation/shared/skill-architecture.md:3, 48` and `skill_creation/skill-building.md:13` — Claude-oriented skill architecture/authoring wording.
- CLAUDE.md — only provider instructions; no API/SDK integration.

## Documents update plan

Execute the following items in order. Each item records its target documents,
required update, and the evidence required before it is complete. These updates
define the provider-portable architecture; they do not claim that an adapter is
already implemented.

### 1. **Define provider portability and evidence**
   - **Execution status:** Complete (documentation only; no provider adapter
      is implemented).
    - **Target:** `doc/GENERATE_AI_AUTOMATIONS.md`.
    - **Required update:** Add a *Provider portability and evidence* section
       that defines the TOOL contract shape, ordered command execution,
       structured errors, acceptance evidence, and terminal validation as
       provider-neutral. Define the provider-adapter boundary: session creation,
       prompt and skill loading, tool dispatch, hook enforcement, event
       normalization, cancellation and timeouts, and credential configuration.
    - **Acceptance evidence:** The section distinguishes the provider-neutral
       contract from provider adapters and does not prescribe any provider SDK as
       the normative construction interface.

### 2. **Plan provider-adapter orchestration**
    - **Execution status:** Complete (documentation planning only; no provider
       adapter is implemented).
    - **Target:** `doc/phased_implementation_plan.md` Phase 5.
    - **Required update:** Rename the phase to *Orchestration flow and provider
      adapters*. Require a stubbed adapter interface so OpenAI, Gemini, and
      Copilot adapters can be introduced without changing direct
      command-execution semantics.
    - **Acceptance evidence:** The phase identifies the adapter interface,
      provider-independent unit tests, and provider-runtime integration tests
      as separate verification layers.

### 3. **Record adapter capabilities and enforcement ownership**
   - **Execution status:** Complete (documentation only; no provider adapter
      is implemented).
    - **Targets:** `doc/ARCHITECTURE.md` and
       `doc/APP_BUILDER_REQUIREMENTS.md`.
    - **Required update:** Add an adapter capability matrix with rows for skill
       loading, tool calling, pre-tool gates, post-tool observation, stop/session
       teardown, structured results, and timeout/cancellation. Include columns
       for Claude Agent SDK, OpenAI Agents/Responses, Gemini SDK/Antigravity,
       and Copilot SDK. Distinguish provider-native hooks from `djng`-enforced
       hooks, with `djng` command-execution gates remaining authoritative for
       correctness.
    - **Acceptance evidence:** Both documents reference the same authority for
       the matrix and state that native provider hooks are adapter mechanisms,
       not independent correctness gates.

### 4. **Make hook terminology provider-portable**
   - **Execution status:** Complete (documentation only; no provider adapter
      is implemented).
    - **Target:** `doc/GENERATE_AI_AUTOMATIONS.md`.
    - **Required update:** Reframe Claude Code lifecycle events as the Claude
       adapter mapping rather than the normative Hook definition. Specify
       `build_app` command-execution gates as the cross-provider enforcement
       point. Record the validated reference patterns from `shlomoa/ai`:
       OpenAI local hook-manager, Gemini decorator/wrapper, and Copilot
       session-hook patterns.
    - **Acceptance evidence:** Every normative Hook requirement is expressible
       without a Claude-specific lifecycle event; Claude event names appear only
       in the Claude adapter mapping.

### 5. **Separate canonical skills from provider packaging**
   - **Execution status:** Complete (documentation only; no provider package
      or adapter is implemented).
    - **Targets:** `doc/GENERATE_AI_AUTOMATIONS.md`,
       `doc/SKILL_AUTHORING_PLAN.md`, and plugin planning documents.
    - **Required update:** Define a canonical `djng` skill source and
       provider-specific packaging/rendering rules. Do not claim that Claude
       `SKILL.md` frontmatter, `.claude-plugin/plugin.json`, or slash invocation
       applies unchanged to other providers. Specify provider-package conformance
       tests analogous to the provider-specific skill tests in `shlomoa/ai`.
    - **Acceptance evidence:** The canonical skill content has one source of
       truth, and every provider packaging format is identified as a derived
       adapter artifact.

### 6. **Align the backlog and verification strategy**
    - **Execution status:** In progress. Phase 5 of
       `doc/phased_implementation_plan.md` now specifies provider-independent
       adapter-contract tests and separate credential/runtime-gated integration
       suites. `TODO.md` and the remaining test-planning documents still need
       the corresponding backlog and verification updates.
    - **Targets:** `TODO.md`, `doc/phased_implementation_plan.md`, and relevant
       test-planning documents.
    - **Required update:** Replace the ambiguous “Claude Code Python SDK” term
       with **Claude Agent SDK**. Add adapter-contract test cases for successful
       sessions, unmet acceptance, timeout or context exhaustion, tool denial,
       post-tool failure, and teardown behavior. Specify provider-independent
       unit tests using stubs and one credential/runtime-gated integration suite
       per provider.
    - **Acceptance evidence:** The backlog tracks each adapter and its contract
       tests, while provider credentials are required only for provider-runtime
       integration suites.

---

## Code update plan

---
