# Automation Plan

## Purpose and boundary

Provider-neutral Tools, Hooks, Skills, adapters, and Plugins; their dependency-ordered implementation; and automation-specific acceptance.

Normative behavior remains owned by the referenced requirements,
specifications, contracts, architecture, and executable/configuration sources.
GitHub owns issue scope and tracking.

## Related domain plans

- [Construction Plan](CONSTRUCTION_PLAN.md)
- [Verification Plan](VERIFICATION_PLAN.md)

## Tools, Hooks, Skills, adapters, and Plugins

### Open backlog

- [ ] `doc/contracts/SKILL_CONTRACTS.md`, `doc/contracts/TOOL_CONTRACTS.md`, `doc/contracts/HOOK_CONTRACTS.md`, and `doc/contracts/PLUGIN_CONTRACTS.md` own the canonical Skill, Tool, Hook, and Plugin contracts. <!-- STEP7-0963a0a2fac4 -->
- [ ] Keep `skill_creation/` aligned with the canonical Skills catalog by following the cadence in `doc/SKILL_AUTHORING_PLAN.md` without duplicating normative contracts. <!-- STEP7-1b6577edc2dc -->
- [ ] `doc/contracts/PLUGIN_CONTRACTS.md` owns the canonical Plugin contracts. <!-- STEP7-d8f1aeb440c6 -->

### Implementation sequence

- Authoritative sources are the contracts in <!-- STEP7-db81b18fba54 -->
- This plan applies the primitive-selection policy defined in `doc/ARCHITECTURE.md` §3.6.3. <!-- STEP7-cd7cb510c282 -->
- The following already exist in the current workspace and are the starting point for this plan: <!-- STEP7-244b22b96a76 -->
- **CLI wrappers** (Django management commands): `export_schema`, `build_app`, <!-- STEP7-cfdbfe1ff3c4 -->
- `ng_new`, `ng_add`, `ng_config`, `ng_gen_app`, `ng_page`, `ng_component`, `ng_complex_component`, `ng_reactive_form`, `ng_site`, `ng_openapi_gen`, `ng_build`, `ng_workspace`, `ng_workspace_delete`, `ng_workspace_modify` (`django_angular3/management/commands/`). <!-- STEP7-3afcd0c47340 -->
- **oasdiff acquisition**: `django_angular3/tools.py:ensure_oasdiff()`. <!-- STEP7-616b278f5674 -->
- **Normative contract catalogs** for Tools, Hooks, and Plugins <!-- STEP7-3553167fc57e -->
- **build_app functional requirements** for traversal, failure handling, and <!-- STEP7-ba292c49b963 -->
- **Skill working copies** under `skill_creation/skills/` (split copies of the <!-- STEP7-dfd02a744b05 -->
- **Provider research evidence** in the private `shlomoa/ai` repository, <!-- STEP7-ab92c8417f09 -->
- **No provider orchestration implementation**: `django_angular3` has no <!-- STEP7-9646d470e48d -->
- What is *not* yet implemented and is therefore scheduled below: the deterministic tool wrappers, the lifecycle hook scripts, the direct command translation and execution that calls them, the SDK-driven Skill orchestration, terminal validation commands, and the plugin packaging. <!-- STEP7-969bf05201c3 -->
- **Goal**: Land the design alignment that lets implementation proceed against stable contracts. <!-- STEP7-584bb46bffd2 -->
- Promote Tools / Hooks / Plugins recommendations into normative contracts in <!-- STEP7-48f99ac4eb26 -->
- `doc/contracts/TOOL_CONTRACTS.md`, `doc/contracts/HOOK_CONTRACTS.md`, and `doc/contracts/PLUGIN_CONTRACTS.md` (done — see their Contracts Catalogs). <!-- STEP7-9dfe8ebdfa5f -->
- (`doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-8 and FR-9) (done). <!-- STEP7-ba8cda71a1ec -->
- Define every additional Tool contract that <!-- STEP7-cef54b011de1 -->
- The design and contract sources satisfy <!-- STEP7-ff1e628b2cda -->
- `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` AIR-1. <!-- STEP7-391cbeb13f15 -->
- This plan exists and references the contracts and FRs by name. <!-- STEP7-14d1e81dd2d5 -->
- **Work items** (one per Tool contract in `doc/contracts/TOOL_CONTRACTS.md` §Tool Contracts Catalog): <!-- STEP7-ae3c4444fb15 -->
- in `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` §§2–3. <!-- STEP7-f3998a7d7736 -->
- Implement every Tool contract in the catalog without redefining its identity, <!-- STEP7-6a9d2c546778 -->
- input, output, or error boundary here. <!-- STEP7-46ea2fee5395 -->
- AIR-NFR-2 in `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md`. <!-- STEP7-cd8248aa7ca1 -->
- Every implemented Tool passes its canonical contract-conformance checks and <!-- STEP7-e93ecc429a67 -->
- the applicable FR-7 and FR-8 checks in `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. <!-- STEP7-7e5c404e6205 -->
- Contract serialization, validation, deterministic ID/timestamp injection, <!-- STEP7-95afbbce44cc -->
- redaction, ordered JSONL events, metadata finalization, malformed prior events, and recorder-write failures. <!-- STEP7-f286a1e7d803 -->
- **Work items** (one per Hook contract in `doc/contracts/HOOK_CONTRACTS.md` §Hook Contracts Catalog): <!-- STEP7-07e6ce269fc7 -->
- Implement the Hook registry, dispatch, idempotency, and persistence mechanics <!-- STEP7-9873033a418a -->
- defined in `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` §§3–4. <!-- STEP7-daabd8d9358b -->
- Implement every Hook contract in the catalog without redefining its trigger, <!-- STEP7-66e10c67020a -->
- The implemented Hook registry and Hooks satisfy AIR-3 through AIR-5 in <!-- STEP7-96e9942e5e2b -->
- `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` and FR-8 in `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. <!-- STEP7-fbaf2bb984e0 -->
- execution, non-blocking `Post*` failure halts and records, `Stop` hook cannot change exit code. <!-- STEP7-41ba89e57a6c -->
- Registry scope, event ordering, idempotency, exception normalization, and <!-- STEP7-05ca26bd5270 -->
- equivalent normalized outcomes from provider-shaped lifecycle observations. <!-- STEP7-a56835ba9815 -->
- **Goal**: Make `build_app` translate changes into ordered commands and execute each command through the right primitive. <!-- STEP7-1d2daacdbca3 -->
- Implement the direct controller, execution context, Hook boundaries, and <!-- STEP7-e7b0be677eb6 -->
- validation integration defined in `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` §5. <!-- STEP7-2bbd5c42c542 -->
- Translate selected TOOL, HOOK, and SKILL contracts into ordered commands whose <!-- STEP7-b5fb48bfa4c9 -->
- contract names match the documented surfaces (FR-7). <!-- STEP7-3e364793716f -->
- Implement FR-3 dry-run behavior and FR-8 failure handling. <!-- STEP7-1d4cbcc1fe90 -->
- Integrate at `build_app` entry and error boundaries: create the execution <!-- STEP7-e7210516ddf3 -->
- Direct execution satisfies AIR-5 in <!-- STEP7-c62fe1e70767 -->
- `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` and FR-2, FR-3, FR-7, and FR-8 in `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. <!-- STEP7-8f20c02778fd -->
- invocation; post-tool halt; warning-only session stop; wrapper-exception and recorder-failure normalization; and absence of provider imports/network use. <!-- STEP7-c00dd316684e -->
- evidence while preserving existing Django command errors and exit behavior. <!-- STEP7-b694262f1573 -->
- Author each canonical Skill per `doc/SKILL_AUTHORING_PLAN.md` (plan, <!-- STEP7-f3d8206fd88c -->
- Keep `skill_creation/skills/` working copies aligned with the authoritative <!-- STEP7-59437800d439 -->
- `doc/contracts/SKILL_CONTRACTS.md` Skills Catalog. <!-- STEP7-47924c62d577 -->
- `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` §6. <!-- STEP7-827e20f4b57a -->
- pass/fail conditions, the tools used to verify them, and what "done" means locally. <!-- STEP7-8eebf79cfcc4 -->
- Skill authoring and runtime resolution satisfy AIR-1 and AIR-6 in <!-- STEP7-4f62cd16d96a -->
- `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` and FR-2 in `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. <!-- STEP7-13969132ef5f -->
- Skill-catalog-alignment check between `skill_creation/skills/` and <!-- STEP7-e3b50d6cc681 -->
- `doc/contracts/SKILL_CONTRACTS.md`. <!-- STEP7-e1283cb70b74 -->
- capability registration, provider isolation, and credential handling defined in `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` §7. <!-- STEP7-78d7871e8584 -->
- Implement adapters against that interface. The validated reference examples <!-- STEP7-cddb9e2717c4 -->
- in `shlomoa/ai` are: <!-- STEP7-1496bb5d3423 -->
- **Claude:** Agent SDK `query`, native hooks, filesystem skills, and plugins. <!-- STEP7-693cdc161855 -->
- **OpenAI:** Responses API / `openai-agents`, a local function-tool guard, and a hook manager. <!-- STEP7-e8e916bac78a -->
- **Gemini:** `google-genai`, function tools, and decorator/wrapper hooks. <!-- STEP7-c0682b03c673 -->
- **Copilot:** `github-copilot-sdk`, sessions, permission handlers, and pre-/post-tool hooks. <!-- STEP7-816f7b16b04c -->
- Apply AIR-5 enforcement ownership to every adapter implementation. <!-- STEP7-83340c91a5e3 -->
- Apply FR-3 and AIR-8 to keep dry runs provider-free. <!-- STEP7-a0f7d2532949 -->
- Keep provider selection internal until the configuration taxonomy assigns its <!-- STEP7-3eb71862cd8b -->
- public ownership. Deterministic-only runs require no adapter. <!-- STEP7-8454ec053897 -->
- Provider adapters and guided-session orchestration satisfy AIR-5 and AIR-7 <!-- STEP7-c9b541737c42 -->
- through AIR-9 in `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` and FR-7 and FR-8 in `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. <!-- STEP7-9dcd387045dd -->
- `doc/contracts/PROVIDER_ADAPTER_CONTRACTS.md` §Provider adapter contracts. <!-- STEP7-80a57601adec -->
- Credential- and runtime-gated integration suites per provider verify the <!-- STEP7-00670b6ff2ca -->
- redaction; optional-SDK import isolation; capability registration/rejection; local-vs-native lifecycle mappings; and proof that provider allow/deny or success signals cannot bypass a direct Hook or terminal-validation failure. <!-- STEP7-9e6564311efb -->
- Keep shared contract and capability coverage in <!-- STEP7-cc9438e99f21 -->
- Apply the provider adapter contracts in <!-- STEP7-cac8d76798f4 -->
- `doc/contracts/PROVIDER_ADAPTER_CONTRACTS.md` §Provider adapter contracts to both credential-free stubs and opted-in provider runtime suites. <!-- STEP7-fcdb50e6d5c5 -->
- **Goal**: Package the coherent capability sets through provider-specific distribution artifacts derived from the canonical `djng` Skills, Tools, and Hooks. <!-- STEP7-296d439156d2 -->
- **Work items** (one per Plugin contract in `doc/contracts/PLUGIN_CONTRACTS.md` §Plugin Contracts Catalog): <!-- STEP7-35674349b69a -->
- Implement every Plugin contract in the catalog without redefining its <!-- STEP7-fd10b8999220 -->
- identity or bundled capabilities here. <!-- STEP7-e4966a166b23 -->
- Implement the derived package rendering, generic manifest realization, and <!-- STEP7-06732df6c184 -->
- artifact storage defined in `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` §8. <!-- STEP7-6852ed0af1ef -->
- Cover canonical preservation and provider derivation in <!-- STEP7-41d281188104 -->
- Implement renderers incrementally with their adapters. <!-- STEP7-6f569ec2a530 -->
- Apply AIR-10 to provider installation and discovery. <!-- STEP7-3a981ddb0dd1 -->
- Packaging, distribution, and release evidence satisfy AIR-9 and AIR-10 in <!-- STEP7-1263bd5fba27 -->
- `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md`. <!-- STEP7-2543f93b0d2f -->
- required fields are preserved, manifests match exactly, and stale artifacts can be detected by provenance/hash. <!-- STEP7-b0c60ee915c8 -->
- Maintain one shared adapter contract matrix for stub and opted-in runtime <!-- STEP7-a6bdfc38c410 -->
- suites. Centralize prerequisite/skip checks, bound live Skills and Tool allowlists, and record only provider/SDK version plus normalized redacted outcomes—not prompts, conversations, headers, or credentials. <!-- STEP7-a310edb3c380 -->
- `doc/contracts/TOOL_CONTRACTS.md`, `doc/contracts/HOOK_CONTRACTS.md`, <!-- STEP7-569596b8e500 -->
- `doc/contracts/PLUGIN_CONTRACTS.md`, `doc/contracts/SKILL_CONTRACTS.md`, and `doc/contracts/PROVIDER_ADAPTER_CONTRACTS.md` — authoritative Tool / Hook / Plugin / Skill and provider-adapter contracts. <!-- STEP7-a6cce6b3c1dc -->
- `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md` — exact automation <!-- STEP7-afddc77e74ab -->
- module organization, persistence, execution, adapter, and rendering realization. <!-- STEP7-2dcdd233a9ba -->
- `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` — AIR-1…AIR-10 and <!-- STEP7-b02f182c103f -->
- AIR-NFR-1…AIR-NFR-3 for the automation subsystem. <!-- STEP7-ea89af0bccab -->
- `doc/requirements/APP_BUILDER_REQUIREMENTS.md` — FR-1…FR-10 (traversal, <!-- STEP7-fbbfa34764d2 -->
- `doc/ARCHITECTURE.md` — §2 automation primitive definitions, §7 construction and verification flow. <!-- STEP7-0323cc907509 -->
- `shlomoa/ai` — private, authenticated provider examples used as portability <!-- STEP7-213207e9bd57 -->

### Corrected current identities

- Canonical Skill authoring maps to the Automation plan's Skills work. <!-- STEP7-3c02e09b8ff6 -->

### Sequence structure

The source phase structure includes work-item, acceptance, and test
coverage blocks. Their substantive claims are rendered in this plan.

## Provider-neutral foundation

### Implementation sequence

- **Goal**: Establish provider-neutral result and evidence contracts, then implement deterministic tool wrappers so bounded operations return structured results instead of requiring raw CLI parsing. <!-- STEP7-067efeb856a7 -->
- Implement the provider-neutral foundation and evidence persistence defined <!-- STEP7-608cc6741333 -->
- Implement the provider-neutral result hand-off defined in the specification and governed by AIR-3 and AIR-5. <!-- STEP7-b9e40abf7dd6 -->
- The implemented foundation satisfies AIR-2 through AIR-4, AIR-NFR-1, and <!-- STEP7-ca1e18e19e0e -->
- context after project-config validation and finalize evidence on every normal or error exit. Preserve the current OpenUI-diff and `NotImplementedError` limitations until their owning work lands; foundation wiring must not imply complete execution. <!-- STEP7-ea88b1840746 -->
- Implement the executable catalog and provider-neutral resolver defined in <!-- STEP7-3213a38f3e91 -->
- Implement the provider-neutral adapter boundary, guided-session algorithm, <!-- STEP7-6c22067ba12e -->

## Dependency-ordered implementation phases

### Open backlog

- [ ] Complete the operation-support and canonical Tool decisions tracked by issue #57 for page, component, complex-component, reactive-form, and site concerns. Reconcile the crosswalk, Tool catalog, builder mapping, and phased plan before implementing issues #162 or #164. <!-- STEP7-5bcb5b8c2b4b -->
- [ ] Implement and verify provider-specific derived packages under Plugin packaging and distribution in this Automation plan. <!-- STEP7-661b278dbe57 -->

### Implementation sequence

- It fulfils the "phased implementation plan" deliverable of the *Architecture alignment — Phased implementation plan* issue. Contract changes identified while executing the plan are made only in the owning contract file under `doc/contracts/`. The full automation model is defined in `doc/ARCHITECTURE.md` §3.6. <!-- STEP7-97708fa5b165 -->
- Each phase lists its **goal**, its **dependencies** (what must land first), <!-- STEP7-5a2cc0d20bf7 -->
- Phases are ordered by dependency. A phase must not start while an upstream <!-- STEP7-c73f8e958d54 -->
- phase it is blocked on is unsatisfied — the same dependency-gating principle direct command execution enforces at runtime (`doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-2, FR-7). <!-- STEP7-446da3c1999f -->
- `doc/contracts/` and the requirements in `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` and `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. Exact automation realization is defined in `doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md`. This plan sequences those sources and does not redefine them. Where this plan disagrees with an authoritative source, update this plan to match. <!-- STEP7-5302299fa085 -->
- (`doc/contracts/TOOL_CONTRACTS.md`, `doc/contracts/HOOK_CONTRACTS.md`, and `doc/contracts/PLUGIN_CONTRACTS.md`). The catalogs define the primitives scheduled in Phases 1, 2, and 8; most carry an *Implementation reference* of "planned" because the backing artifact does not yet exist. The additional OpenUI wrapper contracts identified in `doc/requirements/APP_BUILDER_REQUIREMENTS.md` remain undefined and must be added before the corresponding operations can be claimed as supported. <!-- STEP7-f73ab95e9f66 -->
- validated through authenticated access: Claude Agent SDK `query`, MCP tools, native hooks, filesystem Skills, and `.claude-plugin`; OpenAI Responses API / `openai-agents` with local function-tool guards and hook management; Gemini `google-genai` function tools with decorator/wrapper hooks; and Copilot SDK sessions, permission handlers, and pre-/post-tool handlers. This evidence informs adapter mappings; it is not a runtime dependency or contract source. <!-- STEP7-839d6f244fe8 -->
- provider SDK import, session call, or adapter. The required `claude-agent-sdk` dependency is transitional until a Claude adapter exists and can own it as an optional extra. <!-- STEP7-54eb264aaba7 -->
- **Dependencies**: none. <!-- STEP7-9f25bdae134b -->
- Record this phased implementation plan (this document). <!-- STEP7-9e1dcc220136 -->
- `doc/requirements/APP_BUILDER_REQUIREMENTS.md` identifies as planned before claiming Phase 0 contract coverage (open). <!-- STEP7-4c5da1ae233e -->
- **Dependencies**: Phase 0. <!-- STEP7-bc3554bf70e7 -->
- **Goal**: Implement the deterministic enforcement and side-effect hooks so gates and mandatory side effects always run, independent of agent choices. <!-- STEP7-2742d208c411 -->
- **Dependencies**: Phase 1 (hooks wrap tool outputs). <!-- STEP7-a31e0de7f65b -->
- action, artifact, or failure consequence here. <!-- STEP7-9566fb176bd0 -->
- **Dependencies**: Phases 1–2. <!-- STEP7-266554bf78bb -->
- Execute in dependency order; TOOL commands call the Phase 1 tools and HOOK <!-- STEP7-4105471c23c6 -->
- boundaries apply the Phase 2 hooks. <!-- STEP7-011e91d36d43 -->
- **Dependencies**: Phase 3 (Skills run as selected AI-guided commands). <!-- STEP7-1ab6fa0eafaf -->
- Catalog validation for unique identifiers, valid dependencies, known <!-- STEP7-2fb5f5dd0d08 -->
- **Dependencies**: Phases 3–4. <!-- STEP7-da9c53771cb8 -->
- Package each provider SDK as an optional dependency extra. Move <!-- STEP7-21d8a3f2d6e7 -->
- `claude-agent-sdk` out of required dependencies only when the Claude adapter owns all consumers; add OpenAI, Gemini, and Copilot extras only with their adapters. <!-- STEP7-dc521f1b817d -->
- Skill resolution and dependency failures; close behavior on every path; <!-- STEP7-d53d7e9cf222 -->
- **Dependencies**: Phases 1–7 (a plugin bundles already-implemented primitives). <!-- STEP7-53521b5fa5d4 -->
- research evidence only; not a runtime dependency or normative source. <!-- STEP7-0cc35573b09c -->
- The Construction, Automation, Application Delivery, and Verification plans own their respective open backlogs; this Automation plan sequences only automation work. <!-- STEP7-3128f63863e4 -->

## Automation-specific acceptance

### Implementation sequence

- This document derives a phased implementation plan from the normative contracts in `doc/contracts/` and the requirements in `doc/requirements/AI_AUTOMATION_REQUIREMENTS.md` into an ordered, acceptance-gated sequence of implementation work. It also incorporates the provider-portability research and code-level implementation details formerly maintained in a separate AI knowledge integration plan, making this document the single sequencing authority for that work. <!-- STEP7-db9221a0201d -->
- the **work items**, **acceptance criteria** (the conditions that must hold before the phase is considered done), and **test / verification coverage**. <!-- STEP7-74cb9f5dca64 -->
- terminal verification (`doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-1…FR-10), including FR-8 (command and hook failure handling) and FR-9 (terminal verification contract). <!-- STEP7-8b51f5552669 -->
- Add build_app FRs for failure handling and terminal verification <!-- STEP7-187507ddf2f5 -->
- Record the local-to-global acceptance decision (Phase 7). <!-- STEP7-501635306551 -->
- **Test / verification coverage**: documentation review only — no code behaviour changes in this phase. <!-- STEP7-0f7c49a7cbfc -->
- Add the Phase 1 contract, evidence, and Tool tests listed below. <!-- STEP7-aa2f0088b4d0 -->
- Unit tests per tool: success path, each error `category`, and diagnostic dry-run output where applicable. <!-- STEP7-c54efc98e088 -->
- A contract-conformance test asserting each tool's output keys match its contract. <!-- STEP7-f20bfd01d32d -->
- Add the Phase 2 direct-dispatch and provider-event-mapping tests listed below. <!-- STEP7-b1b3a20a324b -->
- Per-hook tests: trigger event fires the hook, blocking hook halts command <!-- STEP7-a71c9ad11c4b -->
- Exit-code distinctness tests for hook and tool failures. <!-- STEP7-e14e54639011 -->
- Keep controller coverage in `tests/test_automation_execution.py` and focused <!-- STEP7-394434b9ab19 -->
- command-boundary coverage in a dedicated `build_app` test module. Do not add provider fixtures or adapter SDK stubs to this phase. <!-- STEP7-0872fa19c0a5 -->
- Direct controller tests: successful evidence; pre-tool block without Tool <!-- STEP7-52bee6541dd3 -->
- Focused `build_app` tests assert invalid input and schema-diff exits finalize <!-- STEP7-4c9400c3372c -->
- Command-translation determinism tests (same inputs → same command sequence). <!-- STEP7-d5a6ff3e560d -->
- Execution tests: dependency ordering, halt-on-failure, dependent-skip, exit-code mapping. <!-- STEP7-34bf010a962a -->
- Dry-run snapshot tests for the documented `TEST_EXAMPLES.md` scenarios. <!-- STEP7-08764635f5d7 -->
- **Goal**: Author the eleven Angular construction Skills as canonical `djng` skill content with per-skill acceptance criteria and provider-specific renderings. <!-- STEP7-eae61ad3c95a -->
- implementation + tests, build_app command integration, verification). <!-- STEP7-a12723934047 -->
- Cover catalog integrity in `tests/test_skill_catalog.py`. <!-- STEP7-ebf4c65d85a1 -->
- Define each Skill's local acceptance criteria during its Plan phase: the exact <!-- STEP7-1031bdc3e03b -->
- Per-skill component tests for the generated Angular artifacts. <!-- STEP7-1024c342bf9f -->
- Tool/Hook bindings, and complete acceptance criteria. <!-- STEP7-4015068cf5e1 -->
- **Goal**: Drive each selected AI-guided command through a provider adapter until its acceptance criteria are satisfied, without changing the direct command-execution semantics owned by `djng`. <!-- STEP7-3d80674ced57 -->
- Implement AIR-7 handling for an agent session that ends without sufficient acceptance evidence. <!-- STEP7-8455ecf41867 -->
- Provider-independent stub tests cover every outcome in <!-- STEP7-464ec679bada -->
- corresponding adapter against its provider SDK. These suites are separate from provider-independent unit tests and do not claim any adapter is implemented until it passes its own suite. <!-- STEP7-f7ff46d94694 -->
- `tests/test_adapter_contracts.py` and `tests/test_adapter_capabilities.py`. Put live suites under `tests/integration/adapters/`, one module per provider, and centralize prerequisite/skip behavior in one helper. <!-- STEP7-509259f84310 -->
- `tests/test_provider_rendering.py`. <!-- STEP7-1fa2e777866c -->
- Establish release controls: the credential-free Ruff/unittest/catalog <!-- STEP7-2d1193d833a2 -->
- baseline remains required; optional import/conformance tests run for affected adapters; live suites run only in approved secret-managed environments. Do not advertise an adapter until its dependency bounds, shared matrix, live runtime suite, capability metadata, and package conformance all pass. <!-- STEP7-6be0dc9bbe7f -->
- Plugin-manifest conformance tests (declared contents match the contract). <!-- STEP7-f3490b673870 -->
- Provider-package conformance and install / smoke tests against a generated-app workspace. <!-- STEP7-30aeda2a3ea4 -->
- Temporary-directory renderer tests proving canonical inputs are unchanged, <!-- STEP7-3cb765faad1b -->
- failure handling, terminal verification, and global acceptance). <!-- STEP7-0be43e769a86 -->

### Sequence structure

The source phase structure includes work-item, acceptance, and test
coverage blocks. Their substantive claims are rendered in this plan.

## Tracked GitHub issues

- [#58 — Execute governed construction through bounded SKILLS](https://github.com/shlomoa/django-angular3/issues/58) <!-- STEP7-778aa6127289 -->
- [#60 — Add iterative inspection, repair, retry, and refinement to construction](https://github.com/shlomoa/django-angular3/issues/60) <!-- STEP7-bf0180d779c7 -->
- [#139 — Implement provider-neutral automation foundation in phases](https://github.com/shlomoa/django-angular3/issues/139) <!-- STEP7-6deb7ccc591e -->
- [#156 — Phase 1: resolve executable-contract design decisions](https://github.com/shlomoa/django-angular3/issues/156) <!-- STEP7-f0203c9ee0bf -->
- [#157 — Phase 2: add provider-neutral automation contracts package](https://github.com/shlomoa/django-angular3/issues/157) <!-- STEP7-80d47d2be43c -->
- [#158 — Phase 3: implement durable provider-independent evidence recording](https://github.com/shlomoa/django-angular3/issues/158) <!-- STEP7-85a4c3ee70ce -->
- [#159 — Phase 4: add provider-neutral direct-execution primitives](https://github.com/shlomoa/django-angular3/issues/159) <!-- STEP7-636a87176d87 -->
- [#162 — Phase 7: implement deterministic TOOL contracts](https://github.com/shlomoa/django-angular3/issues/162) <!-- STEP7-3777350855ee -->
- [#163 — Phase 8: implement direct lifecycle HOOK contracts](https://github.com/shlomoa/django-angular3/issues/163) <!-- STEP7-0459532c0501 -->
- [#165 — Phase 10: implement guided-session adapter orchestration after direct execution](https://github.com/shlomoa/django-angular3/issues/165) <!-- STEP7-70434ec3cb0b -->

Issue bodies, status, timestamps, relationships, dependency lists, and
acceptance criteria are intentionally not copied into this plan.
