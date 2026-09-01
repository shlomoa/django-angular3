# AI Automation Specifications

## 1. Purpose and scope

This document defines the exact internal organization and realization of the
`djng` AI automation subsystem. It specifies module placement, evidence
persistence, Hook registration, direct execution, runtime Skill resolution,
provider-adapter isolation, and derived package rendering.

This document does not define requirements, architecture, interface contracts,
implementation sequencing, or test coverage. Those concerns are owned by
[AI_AUTOMATION_REQUIREMENTS.md], [ARCHITECTURE.md],
[AI_AUTOMATION_CONTRACTS.md], [APP_BUILDER_REQUIREMENTS.md], and
[phased_implementation_plan.md], respectively.

Tool, Hook, Plugin, Skill, and provider-adapter names, inputs, outputs,
lifecycle families, failure categories, and caller/implementation boundaries
are contracts. This specification consumes those definitions and does not
redefine them.

## 2. Package and module organization

The provider-neutral automation implementation lives under
`django_angular3/automation/`. Its package initializer must not import a
provider SDK.

| Concern | Module |
|---|---|
| Shared immutable automation models and serialization | `django_angular3/automation/contracts.py` |
| Durable evidence recording | `django_angular3/automation/evidence.py` |
| Hook registry and direct Hook dispatch | `django_angular3/automation/hooks.py` |
| Synchronous direct execution | `django_angular3/automation/execution.py` |
| Runtime Skill resolution | `django_angular3/automation/skills.py` |
| Executable canonical Skill catalog | `django_angular3/automation/skill_catalog.py` |
| Guided-session orchestration | `django_angular3/automation/orchestrator.py` |
| Provider-neutral package rendering | `django_angular3/automation/rendering.py` |
| Provider-free adapter interface | `django_angular3/automation/adapters/base.py` |
| Adapter capability metadata | `django_angular3/automation/adapters/capabilities.py` |
| Claude adapter | `django_angular3/automation/adapters/claude.py` |
| OpenAI adapter | `django_angular3/automation/adapters/openai.py` |
| Gemini adapter | `django_angular3/automation/adapters/gemini.py` |
| Copilot adapter | `django_angular3/automation/adapters/copilot.py` |

Provider registration belongs at the adapter package boundary. `build_app`
must not branch directly on provider identity.

## 3. Evidence persistence

### 3.1. Recorder behavior

`EvidenceRecorder` is append-only and dependency-injected. It writes stable
UTF-8 JSON Lines below the selected build output. The stream contains run
metadata and ordered Tool, Hook, and acceptance events.

Identifiers and timestamps enter serialized records through the execution
boundary rather than through hidden global state. Completed events are flushed
so a halted run remains inspectable. A recorder write failure is normalized as
a structured direct-execution failure.

The recorder excludes secrets, credentials, request headers, and
provider-native payloads. A provider adapter returns its normalized result to
`build_app`; it does not write directly to the authoritative evidence stream.

### 3.2. Hook artifacts

Hook implementations use these durable artifact locations:

| Hook concern | Artifact |
|---|---|
| Hook status and failure records | `build/hook-log.jsonl` |
| Post-generation structural verification | `build/verification.log` |

The canonical Hook contracts define which Hook writes each artifact and the
record fields and failure consequences.

## 4. Hook registry and dispatch

The provider-neutral Hook registry is keyed by canonical Hook name and the
provider-neutral lifecycle family defined by [AI_AUTOMATION_CONTRACTS.md]. Each
registration associates the canonical contract with its Tool or command scope,
consequence, evidence payload, and idempotency behavior.

Registry matching uses canonical identities. It must not inspect raw shell
command strings or provider-native event names. Direct dispatch and provider
event adapters normalize observations to the same registry identity before a
Hook runs.

Duplicate lifecycle observations use the registration's idempotency behavior
so destructive work is not repeated and conflicting acceptance evidence is not
emitted.

## 5. Direct execution

### 5.1. Controller model

Direct automation execution is synchronous and implemented by
`django_angular3/automation/execution.py`; it does not introduce a separate
asynchronous framework around the existing Django command and subprocess
model.

The injected execution context contains:

- the validated project configuration;
- the selected build output path;
- the run identifier;
- dry-run and acknowledgement flags; and
- the evidence recorder.

The controller implements Tool execution and pre-execution, post-execution,
and session-stop Hook boundaries. Those boundaries normalize expected failures
and unexpected exceptions, record outcomes, and apply the consequences defined
by the canonical contracts.

The enforcement ownership and acceptance rules are defined by
[AI_AUTOMATION_REQUIREMENTS.md] AIR-5 and
[APP_BUILDER_REQUIREMENTS.md] FR-2, FR-7, FR-8, and FR-9.

### 5.2. Existing validation boundaries

Existing validation functions remain authoritative for their public
return types, diagnostics, and messages. When a recorder is injected, a
validation function first produces its normal result and then records that
result. Validation functions do not open independent automation logs.

### 5.3. Dry run

Dry-run behavior is defined by [APP_BUILDER_REQUIREMENTS.md] FR-3 and
[AI_AUTOMATION_REQUIREMENTS.md] AIR-8. Runtime planning resolves the canonical
selection without constructing an adapter, importing a provider SDK,
discovering credentials, opening a session, or writing provider artifacts.

## 6. Runtime Skill catalog and resolution

The executable canonical Skill catalog is implemented in
`django_angular3/automation/skill_catalog.py`. Its records are generated from,
or validated against, the canonical Skill contracts in
[AI_AUTOMATION_CONTRACTS.md]. Runtime execution does not parse planning
Markdown, authoring working copies, or provider-native Skill files.

The provider-neutral resolver is implemented in
`django_angular3/automation/skills.py`. It validates the selected canonical
Skill identity, dependencies, and Tool and Hook bindings before an adapter
request is created. A temporary fixture registry may support implementation
only until the executable catalog is available; it is not an alternative
runtime source of truth.

The catalog fields and Skill boundary semantics remain owned by the canonical
Skill contracts rather than this internal specification.

## 7. Provider adapters and guided sessions

### 7.1. Provider-free boundary

The provider-neutral adapter base uses synchronous operations for session
creation, canonical Skill loading, command execution, cancellation, and close.
Session request, handle, and result values are immutable. A handle does not
expose a provider client to `build_app`.

Adapter capability metadata declares Skill loading, Tool calling, lifecycle
observation, structured-result, cancellation/timeout, and teardown support. It
distinguishes provider-native support from a local mapping. Registration and
command creation reject adapters that lack a required normalization
capability.

The exact adapter inputs, outputs, capabilities, and normalized failure
categories are interface contracts owned by [AI_AUTOMATION_CONTRACTS.md].

### 7.2. Guided-session algorithm

The orchestrator in `django_angular3/automation/orchestrator.py` is injected
with the selected adapter, Skill resolver, direct execution context, and
evidence recorder. For one guided command it:

1. validates dependencies;
2. resolves the canonical Skill;
3. creates a sanitized session request;
4. opens and runs the guided session;
5. normalizes the adapter result;
6. checks for contract-matching acceptance evidence;
7. returns the result to direct execution for authoritative recording and
   acceptance; and
8. closes the session from a `finally` path.

The first implementation performs no implicit retries.

Adapters receive sanitized canonical command context and allowed Tool names.
They do not receive the mutable direct-execution controller or authoritative
run outcome.

### 7.3. Provider isolation

Each provider implementation is isolated in the module listed in §2 and may
import only its own optional SDK. Importing one adapter must not import another
provider SDK. An unavailable selected SDK is normalized to the canonical
`missing_dependency` failure with installation guidance naming the applicable
optional dependency extra.

Credential discovery occurs only inside the selected adapter and uses the
provider-approved runtime mechanism. Provider SDK dependencies remain optional
to provider-neutral and deterministic-only execution.

## 8. Derived package rendering

Provider-neutral Skill and package rendering is implemented in
`django_angular3/automation/rendering.py`. Renderers consume canonical catalog
records and produce provider-specific representations without modifying the
canonical sources.

Rendered artifacts are written under ignored build or distribution
directories. Each artifact records source provenance and content hashes so
stale output can be detected. Provider-native frontmatter and manifests are
never written back into canonical contract or Skill sources.

The generic package manifest carries canonical Plugin identity and version and
the exact bundled Skill, Tool, and Hook identities. Its interface fields and
content constraints are owned by the Plugin contracts in
[AI_AUTOMATION_CONTRACTS.md]. Provider-native metadata remains namespaced in
derived output.

A Claude rendering may emit `SKILL.md` and `.claude-plugin` artifacts. Other
providers may realize the same canonical definitions through session and Tool
registration instead of a common filesystem representation.

Provider installation and discovery are opt-in and do not run during dry runs
or default tests.

[AI_AUTOMATION_CONTRACTS.md]: ../contracts/AI_AUTOMATION_CONTRACTS.md
[AI_AUTOMATION_REQUIREMENTS.md]: ../requirements/AI_AUTOMATION_REQUIREMENTS.md
[APP_BUILDER_REQUIREMENTS.md]: ../requirements/APP_BUILDER_REQUIREMENTS.md
[ARCHITECTURE.md]: ../ARCHITECTURE.md
[phased_implementation_plan.md]: ../phased_implementation_plan.md
