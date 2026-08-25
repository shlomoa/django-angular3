# AI Knowledge Integration

## Findings

`shlomoa/ai` is private but authenticated access confirmed it contains tested examples for all four providers:

- **Claude**: Agent SDK `query`, MCP tools, native hooks, filesystem skills, `.claude-plugin`.
- **OpenAI/ChatGPT**: Responses API and `openai-agents`; local function-tool guard/hook manager and explicit skill-bundle loading.
- **Gemini/Antigravity**: `google-genai`, function tools, decorator-based local hook wrapping.
- **Copilot**: `github-copilot-sdk`, sessions, permission handlers, `on_pre_tool_use` / `on_post_tool_use`.

The transferable design is a **provider-neutral automation contract plus provider-specific adapters**. Hooks are particularly non-portable: Claude supports native lifecycle hooks; the other providers implement equivalent pre/post execution wrappers.

## Provider-specific references in `djng`

There is **no implemented provider SDK import, `query()` call, or orchestration
adapter** in `django_angular3`. `claude-agent-sdk` remains a declared
transitional dependency; Code Plan Step 2.5 moves it to a Claude optional extra
only after a Claude adapter exists.

The provider-neutral architecture is authoritative in
`doc/GENERATE_AI_AUTOMATIONS.md`, `doc/ARCHITECTURE.md`, and
`doc/phased_implementation_plan.md`. Remaining Claude references are limited
to one of the following non-normative roles:

- the Claude column in the adapter capability matrix and Claude adapter test
   row;
- the documented Claude adapter mapping for native lifecycle events;
- the planned Claude rendering of canonical Skills and Plugins, including
   `SKILL.md`, `.claude-plugin`, and `query()` details; or
- historical research evidence from `shlomoa/ai` and Claude documentation.

These references do not select a provider, define cross-provider Hook behavior,
or determine `build_app` command or run acceptance. `CLAUDE.md` remains only a
provider-instruction file; it does not integrate an SDK.


## Code update plan

Implement this plan in order. Each step preserves the existing rule that
direct `build_app` command execution, deterministic TOOL results, HOOK gates,
and terminal validation decide correctness. A provider adapter may report or
normalize an agent-session result; it must never become the authority that
accepts a generated application.

### 1. **Implement provider-neutral portability and evidence foundation**

**Status: Not started.** This step establishes only the common contracts and
durable evidence required by later TOOL, HOOK, execution, and provider-adapter
work. It does not implement a Claude, OpenAI, Gemini, or Copilot adapter, does
not make network calls, and does not change the selected construction commands.

#### 1.1. **Create a provider-neutral automation package.**
    - Add `django_angular3/automation/__init__.py` and keep it free of provider
       SDK imports.
    - Add `django_angular3/automation/contracts.py` using standard-library
       frozen dataclasses and explicit type aliases; do not introduce a runtime
       validation dependency solely for these internal contracts.
    - Define the stable, serializable contract objects required by later steps:
       - `StructuredError`: `category`, `message`, `details`, and an optional
          underlying exit code. Categories must begin with the documented TOOL
          categories: `invalid_input`, `missing_dependency`,
          `external_tool_failed`, and `output_invalid`.
       - `ToolInvocation` and `ToolResult`: canonical TOOL name, invocation ID,
          normalized inputs or outputs, success state, and structured error.
       - `HookOutcome`: canonical Hook name, provider-neutral lifecycle family
          (`pre-tool`, `post-tool`, or `session-stop`), applicability, block/halt/
          warn consequence, and optional structured error.
       - `AcceptanceEvidence`: command ID, criterion identifier, pass/fail state,
          referenced TOOL/HOOK outcomes, and a compact evidence summary.
       - `CommandOutcome` and `RunOutcome`: direct-command status, final exit
          status, acceptance evidence, warnings, and failures.
    - Give every object a deterministic `to_dict()` representation and a
       corresponding parsing/validation constructor. Serialization must contain
       no secrets, raw credential values, or provider request headers.
    - Define identifier and timestamp generation at the execution boundary so
       tests can supply deterministic values.

#### 1.2. **Implement durable, provider-independent evidence recording.**
    - Add `django_angular3/automation/evidence.py` with an `EvidenceRecorder`
       that writes append-only JSON Lines records below the selected build output
       directory.
    - Use one run-scoped metadata record and one ordered event stream. The
       metadata records the run ID, discovered project-config path, selected
       change inputs, start/end timestamps, and final `RunOutcome`; event records
       contain only serialized `ToolResult`, `HookOutcome`, and
       `AcceptanceEvidence` objects.
    - Create the build directory with `pathlib`; write UTF-8 JSON with stable
       keys; flush each completed record so a halted build retains inspectable
       evidence. Treat recorder write failures as a structured direct-execution
       failure rather than silently continuing.
    - Keep the recorder dependency-injected. `validation.py`, command wrappers,
       and later adapters receive a recorder or a no-op recorder; they must not
       open ad-hoc provider-specific logs.
    - Do not yet prescribe a final artifact filename in public configuration.
       Use an internal, documented default below `--output` and make later
       `build_app` execution work responsible for exposing any stable CLI output
       contract.

#### 1.3. **Add a deterministic direct-execution boundary.**
    - Add `django_angular3/automation/execution.py` with small synchronous
       orchestration helpers rather than an asynchronous framework. Existing
       Django command wrappers and `subprocess` use are synchronous.
    - Define an execution context containing the discovered `ProjectConfig`,
       build-output path, run ID, dry-run flag, acknowledgement flags, and
       `EvidenceRecorder`.
    - Define a `run_tool` boundary that accepts a canonical TOOL name and a
       callable wrapper, converts expected failures and unexpected exceptions to
       `ToolResult`/`StructuredError`, records the result, and never invokes a
       provider SDK.
    - Define `apply_pre_tool_hooks`, `apply_post_tool_hooks`, and
       `apply_session_stop_hooks` boundaries that consume and return
       `HookOutcome` objects. The initial implementation may register no concrete
       hooks, but it must enforce the documented consequences: `pre-tool` blocks
       before execution, `post-tool` halts later direct commands, and
       `session-stop` records warning-only cleanup outcomes.
    - Require the execution boundary to stop dependency-ordered direct commands
       after a block, halt, or terminal-validation failure. It must never accept
       a command merely because a future agent/provider session reports success.

#### 1.4. **Integrate the foundation at existing ownership points without changing
    planner scope.**
    - Update `django_angular3/management/commands/build_app.py` only at its
       command entry/error boundaries: create the execution context after
      project-config validation, record input-validation and schema-diff
      results, and finalize the run outcome on every normal or error exit.
    - Keep the existing schema/config planning, OpenUI-diff gap, and
       `NotImplementedError` execution limitation explicit. This step must not
       silently turn generated command strings into direct execution or claim
       that the full build planner now works.
    - Add narrow recorder integration points to `validation.py` only after its
       public validation functions have returned their normal diagnostics. Do not
       change OpenAPI/OpenUI validation authority, message wording, or return
       types.
    - Leave `angular.py`, `config.py`, management command argument shapes, and
       all provider SDK dependencies unchanged in this step.

#### 1.5. **Specify the evidence-to-acceptance hand-off for future adapters.**
    - Add a protocol in `automation/contracts.py` for a future adapter session
       result to yield `AcceptanceEvidence` or `StructuredError`; it must not
       accept a generated app or directly mutate a `RunOutcome`.
    - Require future adapter results to reference the run ID and the selected
       canonical Skill/command ID, but prohibit them from writing directly to the
       evidence event stream. `build_app` records the normalized result through
       `EvidenceRecorder` after applying its direct TOOL/HOOK gates.
    - Document in code docstrings that actual adapter interfaces, provider skill
       loading, credential discovery, cancellation, and timeout mapping belong to
       Code Plan Step 2 and later; this foundation intentionally has no provider
       selection setting.

#### 1.6. **Add focused provider-independent tests.**
    - Add `tests/test_automation_contracts.py` for round-trip serialization,
       invalid error categories, deterministic supplied IDs/timestamps, and the
       prohibition on secret-bearing fields in serialized evidence.
    - Add `tests/test_automation_evidence.py` using `TemporaryDirectory` under
       the repository test workspace convention. Cover ordered JSONL events,
       metadata finalization after success and failure, malformed prior event
       handling, and recorder-write failure conversion to `StructuredError`.
    - Add `tests/test_automation_execution.py` with local stub TOOL and HOOK
       callables. Cover: successful direct command evidence; `pre-tool` block
       without calling the TOOL; `post-tool` halt after a successful TOOL;
       warning-only `session-stop`; wrapper exception normalization; and no
       provider import or network use.
    - Extend the focused `build_app` tests (create a dedicated test module if
       none exists) to assert that invalid project input and schema-diff results
       finalize an evidence record while preserving current command errors/exit
       behavior.
    - Do not add provider-runtime tests, credential fixtures, or adapter stubs
       that simulate provider SDK APIs in this step. Those belong to the
       provider-adapter implementation and verification steps.

#### 1.7. **Verify the foundation and define completion evidence.**
    - Run `ruff format django_angular3 tests` and
       `ruff check django_angular3 tests`.
    - Run the new focused automation tests, the affected `build_app` tests, and
       then `python -m unittest discover -s tests -p 'test*.py'`.
    - Run `django-admin build_app --dry-run` in a generated-app-compatible test
       configuration and inspect that its evidence is machine-readable, excludes
      secrets, and records validation and schema-diff outcomes without executing
       selected construction commands.
    - Mark this code-plan step complete only when the provider-neutral contracts
       and recorder are covered by credential-free tests, direct `build_app`
       remains the sole gate authority, and no production module imports a
       provider SDK outside a future provider-adapter package.

### 2. **Implement provider-adapter orchestration**

**Status: Not started.** Begin this step only after Code Plan Step 1 supplies
the provider-neutral contracts, recorder, and direct-execution boundaries. This
step introduces the adapter interface and the orchestration seam used for
AI-guided commands; it does not move deterministic TOOL, HOOK, dependency, or
terminal-validation authority out of `build_app`.

#### 2.1. **Define the adapter package and stable interface.**
   - Add `django_angular3/automation/adapters/__init__.py` and
      `django_angular3/automation/adapters/base.py`. The base module must
      import only the provider-neutral contracts from Step 1 and Python standard
      library typing primitives; it must not import a provider SDK.
   - Define a `ProviderAdapter` protocol or abstract base class with explicit
      synchronous lifecycle methods that match the repository's current Django
      command execution model:
      1. `create_session(request) -> SessionHandle`
      2. `load_skills(session, canonical_skills) -> None`
      3. `run_skill_command(session, command, context) -> AdapterSessionResult`
      4. `cancel_session(session, reason) -> AdapterSessionResult | None`
      5. `close_session(session) -> AdapterSessionResult | None`
   - Define immutable request/result contracts alongside the interface:
      - `SessionRequest`: run ID, command ID, canonical Skill names, sanitized
        prompt/context, allowed canonical TOOL names, timeout/cancellation
        policy, and a reference to the current evidence recorder.
      - `SessionHandle`: opaque provider/session identifier and adapter name;
        it must not expose provider client objects to `build_app`.
      - `AdapterSessionResult`: normalized completion state, optional
        `AcceptanceEvidence`, optional `StructuredError`, provider event
        summary, and warning-only teardown information.
      - `AdapterErrorCategory`: at minimum `unmet_acceptance`, `timeout`,
        `context_exhausted`, `tool_denied`, `provider_unavailable`,
        `cancelled`, and `provider_protocol_error`. Map provider exceptions to
        these categories without leaking credential values or raw requests.
   - Establish one result rule: an adapter may return evidence that a guided
      session completed, but only `build_app` may record its final acceptance
      after direct TOOL/HOOK gates and terminal validation have passed.

#### 2.2. **Create a canonical Skill loading boundary.**
   - Add `django_angular3/automation/skills.py` as a provider-neutral resolver
      for canonical Skill names and their contract-defined inputs, outputs,
      dependencies, and acceptance criteria. Do not use a provider-native
      `SKILL.md` file, `.claude/` filesystem layout, slash command, or plugin
      manifest as the source of truth.
   - Resolve canonical Skill metadata from the generated/maintained catalog
      representation selected during Code Plan Step 5. Until that representation
      exists in executable form, expose a small registry interface and use
      test-owned fixtures rather than parsing Markdown at runtime.
   - Validate that each selected Skill exists, its declared dependencies have
      completed, and its requested TOOLS are known to the direct execution
      boundary before a session request is created. Return a
      `StructuredError(category="invalid_input")` for invalid selections.
   - Give each adapter an explicit renderer hook that converts canonical Skill
      metadata to its native representation. Rendering belongs inside the
      adapter; the orchestrator never branches on Claude frontmatter, OpenAI
      function schemas, Gemini decorator metadata, or Copilot session syntax.

#### 2.3. **Implement the guided-session orchestrator.**
   - Add `django_angular3/automation/orchestrator.py` with a small
      `GuidedSessionOrchestrator` that is constructed with a `ProviderAdapter`,
      canonical Skill resolver, Step 1 execution context, and evidence recorder.
   - For each AI-guided command selected by the existing change-to-command
      translation, the orchestrator must:
      1. Confirm dependency order and prior direct-command outcomes.
      2. Resolve canonical Skills and build a sanitized `SessionRequest`.
      3. Create the provider session and load the rendered Skills.
      4. Dispatch only the provider session; deterministic TOOL calls continue
         through Step 1's direct execution boundary.
      5. Normalize the session completion into `AdapterSessionResult`.
      6. Record the normalized session event through `EvidenceRecorder`.
      7. Require non-empty, contract-matching acceptance evidence before
         allowing the next selected command.
      8. Close the provider session in a `finally` path and record a warning or
         structured teardown failure without masking an earlier build failure.
   - The orchestrator must halt on unmet acceptance, timeout, context
      exhaustion, tool denial, provider protocol error, or a failing post-tool
      Hook. It must not retry automatically in the first implementation;
      retry policy is a later, explicit architecture decision.
   - Extend `automation/execution.py` only with a narrow `run_guided_command`
      call point. `run_tool` and HOOK dispatch remain callable without an
      adapter, and a provider result cannot directly mark a `CommandOutcome`
      successful.

#### 2.4. **Integrate orchestration into `build_app` incrementally.**
   - Add an explicit internal execution mode for selected AI-guided commands;
      keep existing deterministic command translation and dry-run output
      inspectable before any provider session can start.
   - In `django_angular3/management/commands/build_app.py`, invoke the guided
      session orchestrator only after configuration validation, change
      derivation, dependency selection, and applicable pre-tool gates have
      succeeded. Continue to halt through Django `CommandError`/documented
      exit behavior when the normalized result is unsuccessful.
   - Keep `--dry-run` provider-free: it validates and renders the planned
      canonical Skill/command selection but must not create sessions, resolve
      credentials, import provider SDKs, mutate the generated-app workspace, or
      write provider artifacts.
   - Add an internal adapter factory/registry keyed by a provider identifier,
      but initially register only test stubs. Do not add a public provider CLI
      option or configuration field until the configuration taxonomy work in
      `TODO.md` item 0 defines its ownership and selection mechanism.
   - Preserve current partial-build limitations: OpenUI structural diffing,
      complete direct wrapper execution, and terminal verification remain
      separate prerequisites. Adapter orchestration must expose unsupported
      selected work explicitly instead of silently omitting it.

#### 2.5. **Add provider-adapter implementations behind optional dependencies.**
   - Keep the base `django-angular3` install provider-neutral. Move
      `claude-agent-sdk` from the required dependency list to a named optional
      extra only when its existing consumers have been migrated to the Claude
      adapter; add separate optional extras for OpenAI, Gemini, and Copilot
      SDKs when their adapters are introduced.
   - Implement one adapter at a time in isolated modules:
      - `claude.py`: map Agent SDK `query`, filesystem Skill rendering, native
        hooks, and session completion to the base contracts.
      - `openai.py`: map Responses/Agents sessions and the local function-tool
        guard/hook manager to the base contracts.
      - `gemini.py`: map `google-genai` function tools and decorator/wrapper
        lifecycle behavior to the base contracts.
      - `copilot.py`: map Copilot sessions, permission handlers, and pre/post
        tool handlers to the base contracts.
   - Each module may import only its own optional SDK. Import failures must be
      converted by the factory to
      `StructuredError(category="missing_dependency")`, with installation
      guidance that names the relevant extra but never a credential value.
   - Add no credentials to source control, test fixtures, build evidence, or
      command output. A future adapter reads credentials only through its
      provider-approved runtime mechanism; credential discovery is local to the
      adapter and absent credentials skip its runtime suite.

#### 2.6. **Normalize provider lifecycle behavior without delegating gates.**
   - Implement adapter-local mappings from provider events to the canonical
      lifecycle families defined in Code Plan Step 1:
      - Claude native hooks map to `pre-tool`, `post-tool`, and `session-stop`.
      - OpenAI's local guard/hook manager maps to `pre-tool`/`post-tool`; its
        session finalizer maps to `session-stop`.
      - Gemini's decorator/wrapper maps to `pre-tool`/`post-tool`; its session
        finalizer maps to `session-stop`.
      - Copilot pre/post handlers and permission decisions map to
        `pre-tool`/`post-tool`; its session finalizer maps to `session-stop`.
   - Route every normalized outcome through Step 1's hook/execution boundary
      and evidence recorder. A provider's native block, permission denial, or
      post-tool exception is additional session evidence; it cannot replace a
      required direct `build_app` gate.
   - Normalize provider cancellation, timeout, and context-exhaustion signals
      to the base error categories. Retain provider diagnostic identifiers only
      in redacted `details` fields suitable for durable evidence.

#### 2.7. **Build the credential-free adapter contract test suite first.**
   - Add `tests/test_adapter_contracts.py` using a configurable in-memory
      `StubProviderAdapter` that implements the base interface without a
      provider SDK, network connection, or credentials.
   - Test the Phase 5 matrix against the stub: successful session advances only
      after evidence; unmet acceptance halts; timeout/context exhaustion halts
      with the normalized category; tool denial surfaces at the direct boundary;
      post-tool failure halts after a successful TOOL; and warning-only teardown
      is recorded without changing an already determined result.
   - Add tests for Skill resolution failure, dependency ordering, session close
      in success/error/cancellation paths, error redaction, and proof that
      `--dry-run` never instantiates an adapter.
   - Test adapter registration/import behavior separately: an absent optional
      SDK yields `missing_dependency`, and importing one provider adapter does
      not import any other provider SDK.

#### 2.8. **Add one runtime-gated integration suite per implemented adapter.**
   - Create provider-specific test modules only with the corresponding adapter,
      for example `tests/integration/adapters/test_claude.py`. Keep them
      separate from the unittest suite that verifies the provider-neutral
      contract.
   - Gate every suite on both an explicit opt-in test selector and the
      provider's runtime prerequisites. If either is absent, skip with a clear
      reason; never prompt for or print credentials. Do not request credentials
      through agent/user interaction tools.
   - Each live suite verifies the same shared contract matrix plus the
      provider-specific rendering, session startup, TOOL dispatch or denial,
      lifecycle mapping, cancellation/timeout mapping, structured result
      normalization, and teardown path.
   - Mark an adapter implemented only after its credential-free contract suite
      and its own opted-in runtime suite pass. Passing the stub suite alone is
      not implementation evidence.

#### 2.9. **Verify incrementally and define completion evidence.**
   - After the base interface/orchestrator, run Ruff and all provider-neutral
      automation tests plus the full unittest suite. Do not run live provider
      tests as part of the default verification path.
   - For each adapter, run its optional-dependency import tests, then its
      opted-in credential/runtime suite in an environment configured by the
      provider owner. Record only redacted evidence and test outcomes.
   - Run relevant `django-admin build_app --dry-run` and controlled non-dry-run
      tests in a generated-app-compatible Django configuration. Confirm that
      direct TOOL/HOOK/terminal validation failures still halt even if the
      provider reports a successful session.
   - Mark this code-plan step complete only when a test stub exercises the
      base interface without provider dependencies, each implemented adapter
      passes both verification layers, and no provider-specific code bypasses
      the Step 1 execution/evidence boundary.

### 3. **Implement adapter capabilities and enforcement ownership**

**Status: Not started.** Begin this step after the base adapter interface in
Code Plan Step 2 exists. It turns the architectural capability matrix into
executable metadata and checks. It does not use metadata as a substitute for
direct `build_app` gates.

#### 3.1. **Represent capabilities as provider-neutral adapter metadata.**
   - Add `django_angular3/automation/adapters/capabilities.py` with immutable
      `AdapterCapabilities` data owned by each adapter implementation.
   - Model the capability rows from `ARCHITECTURE.md` §2.12.1 explicitly:
      canonical Skill loading, TOOL calling, pre-tool handling, post-tool
      observation, session-stop/teardown, structured results, and
      timeout/cancellation.
   - Represent whether an adapter offers a native mechanism or a local mapping
      for each lifecycle capability. Capability metadata describes what the
      adapter can normalize; it must not claim that a provider-native mechanism
      is itself an authoritative `djng` gate.
   - Add a stable adapter identifier and display name. Do not hard-code SDK
      package names, credentials, or endpoint values into shared capability
      metadata.

#### 3.2. **Require adapter declarations at registration time.**
   - Extend the Step 2 adapter registry/factory so every registered adapter
      exposes `capabilities()` and is rejected if required result,
      cancellation, or teardown normalization is absent.
   - Validate that a requested guided command does not require an unavailable
      adapter capability. Return a normalized `missing_dependency` or
      `invalid_input` error that names the canonical capability, not a raw SDK
      exception.
   - Permit deterministic-only `build_app` runs without any adapter
      registration. Do not make an adapter a prerequisite for schema diffing,
      wrapper execution, HOOK gates, or terminal validation.
   - Keep adapter capability selection internal until the configuration
      taxonomy defines a public, owned provider-selection configuration field.

#### 3.3. **Encode gate ownership in the execution API.**
   - Update `automation/execution.py` so `run_tool`, pre-tool Hook dispatch,
      post-tool Hook dispatch, dependency checks, and terminal validation are
      invoked only by the direct execution controller.
   - Pass adapters a restricted session context containing canonical command
      inputs and an allowlist of TOOL contract names. Do not pass the execution
      controller, mutable run outcome, or a callable that can bypass a gate.
   - Require adapter-returned tool-use, permission, or lifecycle events to be
      normalized as observations. The execution controller decides whether the
      corresponding Hook/gate blocks, halts, or warns and records that decision
      in `EvidenceRecorder`.
   - Give denial and post-tool observations correlation IDs that match the
      original tool invocation so evidence links provider events with the direct
      execution boundary.

#### 3.4. **Add capability and ownership tests.**
   - Add `tests/test_adapter_capabilities.py` with fake adapters for: a full
      capability set, missing Skill loading, missing cancellation support, and
      a provider using local lifecycle wrappers.
   - Assert registry rejection or normalized failure for unsupported requested
      capabilities, while deterministic direct TOOL execution still succeeds
      with no adapter installed.
   - Assert a simulated provider-native allow/deny decision cannot mark a
      `CommandOutcome` accepted, bypass a failing `pre-tool`/`post-tool` Hook,
      or suppress terminal validation.
   - For each real adapter added in Step 2, add a table-driven capability test
      asserting its declared metadata matches the supported mapping in
      `ARCHITECTURE.md` §2.12.1. Update the architecture matrix and this test
      together if a provider SDK changes its support.

#### 3.5. **Verify completion.**
   - Run the new capability tests with the provider-neutral automation suite,
      then the full unittest suite and Ruff checks.
   - In each opted-in provider runtime suite, assert capability declarations
      against the actual exercised path rather than treating metadata alone as
      proof of support.
   - Mark this step complete only when every registered adapter advertises
      auditable capability metadata and direct `build_app` remains the sole
      component that records gate decisions and final acceptance.

### 4. **Implement provider-portable Hook execution**

**Status: Not started.** Begin after Steps 1–3. This step implements the
provider-neutral `pre-tool`, `post-tool`, and `session-stop` families defined
by the Hook Contracts Catalog. Provider events remain adapter inputs, not the
normative Hook implementation.

#### 4.1. **Create the Hook registry and contract bindings.**
   - Add `django_angular3/automation/hooks.py` with a `HookDefinition`,
      `HookContext`, and `HookRegistry` keyed by canonical Hook name and
      lifecycle family.
   - Express scope using canonical TOOL contract names and command predicates;
      do not match raw shell command strings or Claude event names in the
      shared registry.
   - Encode the four catalogued contracts incrementally: `pre-construction`,
      `migration-triggered`, `post-generation`, and `session-stop`. A hook implementation must call its documented TOOL
      boundary rather than duplicate a binary invocation.
   - Require every definition to declare its block/halt/warn consequence,
      evidence payload, and idempotency behavior before it can be registered.

#### 4.2. **Implement direct Hook dispatch and failure semantics.**
   - Replace the placeholder Hook boundaries from Step 1 with deterministic
      registry dispatch around direct command execution:
      - Run applicable `pre-tool` hooks before the wrapped TOOL and prevent the
        wrapper call when a blocking outcome fails.
      - Run applicable `post-tool` hooks after a successful wrapped TOOL and
        halt subsequent commands if their enforcement outcome fails.
      - Run `session-stop` exactly once from a `finally` path after the run
        outcome is decided; record failures as warnings without replacing an
        already determined success/failure result.
   - Use `EvidenceRecorder` for every Hook start, outcome, skip, and failure.
      The durable record must identify the canonical Hook, lifecycle family,
      wrapped TOOL/command ID, normalized error, and resulting decision.

#### 4.3. **Connect provider lifecycle observations through adapters.**
   - Add a narrow adapter method for delivering a normalized lifecycle
      observation to the direct execution controller. The controller decides
      whether an applicable Hook runs; adapters never run a shared Hook action
      independently.
   - Implement provider-specific event mapping only inside the relevant adapter
      module: Claude native hooks, OpenAI local guard/hook manager, Gemini
      decorators/wrappers, and Copilot permission/pre-post handlers all emit
      the same observation contract.
   - Handle duplicate events idempotently using run ID, command ID, Hook name,
      and lifecycle family. A repeated provider callback must not re-run a
      destructive Hook action or generate conflicting acceptance evidence.
   - Treat a provider hook-registration failure as a normalized adapter error;
      never weaken the direct Hook gate because a provider's native mechanism is
      unavailable.

#### 4.4. **Test Hook portability and authority.**
   - Add `tests/test_hooks.py` with in-process Tool/Hooks fixtures that cover
      registration scope, pre-tool blocking, post-tool halting, session-stop
      warning-only behavior, idempotency, error recording, and ordering.
   - Add adapter observation tests to the Step 2 stub suite. Feed equivalent
      Claude/OpenAI/Gemini/Copilot-shaped fake events into their mappers and
      assert the identical normalized Hook outcome and direct execution result.
   - Add a regression test proving that a provider reports success after a
      direct post-tool Hook failure but `build_app` still halts and records the
      Hook failure as the authoritative outcome.
   - Add real provider lifecycle tests only to the corresponding gated runtime
      suite; no default unit test may require a provider hook runtime.

#### 4.5. **Verify completion.**
   - Run the Hook, execution, adapter-contract, and focused `build_app` tests,
      then Ruff and the full unittest suite.
   - Use a generated-app-compatible dry run plus controlled failure fixtures to
      inspect evidence ordering: pre-tool → TOOL → post-tool → session-stop.
   - Mark this step complete only when no shared Hook contract refers to a
      provider event name, all provider events enter through adapters, and the
      direct execution controller enforces every block/halt/warn decision.

### 5. **Implement canonical Skill rendering and provider packaging**

**Status: Not started.** Begin after canonical Skill metadata can be resolved
in Step 2 and portable Hooks exist in Step 4. This step materializes the
documentation rule that Skills and plugins have one canonical contract while
provider packages are derived artifacts.

#### 5.1. **Create an executable canonical Skill and plugin catalog.**
   - Add `django_angular3/automation/skill_catalog.py` with immutable
      `CanonicalSkill` and `CanonicalPlugin` records. Include canonical name,
      purpose, inputs, outputs, dependencies, acceptance criteria, Tool/Hook
      bindings, and version.
   - Define a build-time source or checked-in machine-readable catalog derived
      from the authoritative Skills and Plugin Catalogs in
      `GENERATE_AI_AUTOMATIONS.md`. Do not parse Markdown at `build_app`
      runtime, and do not duplicate the catalog by hand in each adapter.
   - Add a catalog-validation command or build check that compares the
      machine-readable entries to the authoritative documentation source and
      fails on missing, renamed, or divergent canonical identifiers.
   - Make the Step 2 Skill resolver consume this catalog; remove any test-only
      temporary registry once the generated catalog is available.

#### 5.2. **Define renderer and package-builder interfaces.**
   - Add `django_angular3/automation/rendering.py` with a
      `ProviderSkillRenderer` protocol and a `ProviderPackageRenderer`
      protocol. Both accept only canonical catalog records and return derived
      artifact descriptions, never mutable source contracts.
   - Require a renderer to preserve canonical Skill name, purpose, inputs,
      outputs, dependencies, acceptance criteria, Tool identities, Hook names,
      and lifecycle families. Allow it to add provider-native metadata only in
      a namespaced/rendered field.
   - Define a generic package manifest record containing the canonical plugin
      identity/version and exact bundled Skills/Tools/Hooks. Provider renderers
      translate it to a native manifest/registry/package layout.
   - Keep all rendered output under an ignored build/distribution directory;
      never write provider-native frontmatter or manifests back into the
      canonical catalog.

#### 5.3. **Implement provider-specific renderers incrementally.**
   - Start with a Claude renderer that produces the Claude Agent Skills and
      `.claude-plugin` artifacts from canonical records. Treat `SKILL.md`
      frontmatter, plugin JSON, and slash invocation as output-only Claude
      concerns.
   - Add OpenAI, Gemini, and Copilot renderers only when their adapters exist.
      Their artifacts may be prompt/tool-registration/session bindings rather
      than filesystem skill files; do not invent a uniform native package format
      where a provider does not support one.
   - Render shared context by copying or inlining only as required by the target
      provider. Preserve source provenance and a content hash in the artifact
      manifest so stale generated artifacts can be detected.
   - Make package installation/configuration provider-specific and opt-in. It
      must not be triggered by `build_app --dry-run` or by default unit tests.

#### 5.4. **Add catalog and package conformance tests.**
   - Add `tests/test_skill_catalog.py` to verify every canonical Skill and
      Plugin has unique identifiers, valid dependency references, known
      Tool/Hook bindings, and complete acceptance criteria.
   - Add `tests/test_provider_rendering.py` using fake renderers plus the Claude
      renderer once available. Assert that derived artifacts preserve all
      required canonical fields, include no uncontracted capabilities, and do
      not mutate catalog input.
   - Add manifest conformance tests that compare each rendered package's bundled
      Skills/Tools/Hooks with the corresponding `CanonicalPlugin` exactly—no
      omissions, additions, renamed entries, or lifecycle-family drift.
   - Add packaging smoke tests in a temporary directory. Run real provider
      installation or discovery tests only in that provider's gated runtime
      suite, never in the default repository test run.

#### 5.5. **Verify completion.**
   - Run catalog, renderer, and manifest-conformance tests together with the
      full provider-neutral suite and Ruff checks.
   - For each implemented provider renderer, run its opted-in package/install
      smoke suite and retain redacted artifact manifests as evidence.
   - Mark this step complete only when canonical contracts have one executable
      source, every generated package is traceable to it, and no provider-native
      file or slash command is treated as a cross-provider source of truth.

### 6. **Implement adapter verification, runtime gating, and release controls**

**Status: Not started.** This final implementation stage operationalizes the
test matrix defined in the plans. It does not replace the ordinary unittest
suite with live SDK tests and must keep credentials outside the repository.

#### 6.1. **Organize test tiers and test selection.**
   - Keep credential-free contract, execution, Hook, catalog, and rendering
      tests under the existing `tests/` unittest discovery surface so
      `python -m unittest discover -s tests -p 'test*.py'` remains the default
      verification command.
   - Create an isolated `tests/integration/adapters/` package for real-provider
      tests. Add a project-supported test runner/configuration only if needed
      to select integration suites without altering the default unittest
      behavior.
   - Require an explicit opt-in environment selector per provider and verify
      optional SDK availability before constructing a live test. Missing opt-in,
      missing SDK, or missing provider credentials must produce a skip result,
      not a failure or interactive prompt.
   - Centralize the skip/availability logic in one test helper module. Test
      helpers may inspect whether a required environment variable is set but
      must never log its value or serialize it into test artifacts.

#### 6.2. **Implement the common adapter contract matrix once.**
   - Maintain the Step 2 `StubProviderAdapter` as the canonical, deterministic
      implementation used by all common cases: successful session, unmet
      acceptance, timeout, context exhaustion, tool denial, post-tool failure,
      and teardown.
   - Make each case assert a stable normalized error category, evidence order,
      direct `build_app` halt/advance result, and final run status. The case
      definitions must be shared by stub and runtime suites rather than copied
      into each provider test module.
   - Add regression fixtures for known dangerous sequences: provider success
      after terminal-validation failure, provider post-tool success after direct
      Hook failure, cancellation during teardown, and duplicate lifecycle
      callbacks.
   - Require all error/evidence assertions to use redacted summaries rather
      than raw SDK exceptions, provider responses, prompts, or credentials.

#### 6.3. **Add runtime suite adapters to the common matrix.**
   - For each implemented provider, write a small suite adapter that supplies
      the provider-specific session factory, credential prerequisite, expected
      rendering, and event-mapping assertions to the shared matrix.
   - Verify live behavior with a minimal, bounded test Skill and a controlled
      Tool allowlist. Do not run generated-app construction or arbitrary shell
      commands in a provider smoke test.
   - Add provider-specific checks only where required by the capability matrix:
      Claude native hook registration; OpenAI local guard/hook manager;
      Gemini decorator/wrapper; Copilot permission and pre/post handlers.
   - Record provider, SDK version, test selection, normalized result, and
      redacted diagnostics in the evidence output. Do not retain prompts,
      provider conversation contents, or credential-bearing headers by default.

#### 6.4. **Add CI and release policy without requiring universal credentials.**
   - Keep lint, format, default unittest, and documentation checks credential
      free and required on every change.
   - Run optional-SDK import/conformance tests whenever a provider adapter or
      its packaging code changes. Run live provider suites only in an approved,
      secret-managed environment and only for the affected provider(s).
   - Require a provider adapter release checklist: optional dependency locked
      or bounded; common contract matrix passing; provider runtime suite
      passing; capability metadata verified; package manifest/rendering
      conformance passing; no secrets in evidence or logs.
   - Do not claim that an adapter is implemented in a release note, package
      metadata, or capability registry until this checklist has passed.

#### 6.5. **Verify completion and maintain the backlog.**
   - Run the full credential-free verification sequence: Ruff format/check,
      complete unittest discovery, focused `build_app` dry-run coverage, and
      all catalog/package conformance tests.
   - Run each provider's explicit, credential-gated suite independently; record
      pass/skip/failure status without exposing credentials. A skipped runtime
      suite is not evidence of provider support.
   - Update `TODO.md`, the Phase 5/8 implementation status, and provider
      capability metadata only from actual test evidence. Keep unsupported or
      unverified adapters explicitly planned rather than inferred from shared
      stub-test success.
   - Mark this step complete only when test tiers are isolated, all implemented
      adapters pass their common and live suites, CI protects the credential-free
      baseline, and release documentation reflects verified—not anticipated—
      provider support.

---
