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
- `e2e_enabling_documentation_plan.md:131` — planned `sdk.query()` per skill procedure.
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

## Proposed document-update plan

1. **Add a “Provider portability and evidence” section** to GENERATE_AI_AUTOMATIONS.md.
   - Declare the existing TOOL contract shape, procedure graph, structured errors, acceptance evidence, and terminal verification as provider-neutral.
   - State that a provider adapter owns session creation, prompt/skill loading, tool dispatch, hook enforcement, event normalization, cancellation/timeouts, and credential configuration.

2. **Replace the Claude-only assumption in Phase 5** of phased_implementation_plan.md.
   - Rename it to **“Orchestration flow and provider adapters.”**
   - Keep the Claude Agent SDK adapter as the first implementation target.
   - Add acceptance criteria requiring a stubbed adapter interface, so OpenAI, Gemini, and Copilot can be integrated without changing graph traversal semantics.

3. **Add an adapter capability matrix** in ARCHITECTURE.md and reference it from APP_BUILDER_REQUIREMENTS.md.
   - Rows: skill loading, tool calling, pre-tool gate, post-tool observation, stop/session teardown, structured result, timeout/cancellation.
   - Columns: Claude Agent SDK, OpenAI Agents/Responses, Gemini SDK/Antigravity, Copilot SDK.
   - Explicitly distinguish **native** hooks from **djng-enforced** hooks; the latter must remain authoritative for correctness.

4. **Revise hook language in GENERATE_AI_AUTOMATIONS.md.**
   - Preserve Claude Code event mappings as the Claude adapter mapping, not the normative hook definition.
   - Make `build_app` procedure-graph gates the cross-provider enforcement point.
   - Document OpenAI’s hook-manager pattern, Gemini decorator/wrapper pattern, and Copilot session-hook pattern as reference implementations learned from `shlomoa/ai`.

5. **Clarify skill/plugin portability.**
   - Define a canonical `djng` skill source and provider-specific packaging/rendering rules.
   - Avoid claiming that Claude `SKILL.md` frontmatter, `.claude-plugin/plugin.json`, or CLI slash invocation applies unchanged to other providers.
   - Add provider-package conformance tests analogous to `shlomoa/ai`’s provider-specific skill tests.

6. **Update backlog and verification documents.**
   - Replace the ambiguous “Claude Code Python SDK” wording in TODO.md with **Claude Agent SDK**.
   - Add adapter contract tests: successful session, unmet acceptance, timeout/context exhaustion, tool denial, post-tool failure, and teardown behavior for each provider adapter.
   - Keep one integration test suite per provider credential/runtime, plus provider-independent unit tests using stubs.
