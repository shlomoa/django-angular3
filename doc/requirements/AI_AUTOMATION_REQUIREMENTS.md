# AI Automation Requirements

## 1. Purpose and scope

This document defines the product and quality requirements for the `djng` AI
automation subsystem. It covers provider-neutral execution, evidence,
lifecycle enforcement, Skill resolution, provider adapters, and distribution.
It does not define implementation sequencing, exact representations, or
interface contracts.

Implementation sequencing is owned by
[phased_implementation_plan.md]. Automation architecture is owned by
[ARCHITECTURE.md]. Normative Tool, Hook, Plugin, Skill, and provider-adapter
boundaries are owned by [AI_AUTOMATION_CONTRACTS.md]. Detailed `build_app`
requirements are owned by [APP_BUILDER_REQUIREMENTS.md]. Exact automation
realization is owned by [AI_AUTOMATION_SPECIFICATIONS.md].

## 2. Functional requirements

### AIR-1: Canonical automation definitions

- Every Tool, Hook, Plugin, and Skill must have one canonical normative
  definition.
- Commands, provider bindings, and distribution artifacts may reference or
  compose a canonical definition but must not redefine it.
- Runtime automation resolution must not treat planning documents or
  provider-native renderings as canonical definitions.

### AIR-2: Provider-neutral automation foundation

- Shared automation execution, evidence, contract models, and resolution must
  operate without importing or invoking a provider SDK.
- Deterministic Tool and Hook execution must not require a provider session or
  network access.
- Provider integration must remain behind a provider-neutral adapter boundary.

### AIR-3: Durable and safe evidence

- Automation activity must produce ordered, machine-readable evidence that
  remains inspectable after success, failure, or a halted run.
- Evidence must correlate Tool, Hook, Skill-session, command, acceptance, and
  run outcomes sufficiently for diagnosis and acceptance decisions.
- Evidence must not contain secrets, credentials, request headers, or
  provider-native payloads that may carry sensitive data.
- Evidence-recording failures must be surfaced as structured execution
  failures rather than silently ignored.
- A provider adapter must not mutate the authoritative run outcome or write
  directly to the authoritative evidence stream.

### AIR-4: Contract-conforming Tool and Hook execution

- Each Tool must accept and return data conforming to its canonical contract.
- Tool failures must be normalized into structured errors that direct
  execution can evaluate.
- Hook dispatch must use canonical lifecycle and scope information rather than
  raw shell strings or provider event names.
- Hook execution must be idempotent when duplicate lifecycle observations are
  possible.
- Hook outcomes and failures must be correlated with the affected run, command,
  and Tool invocation.

### AIR-5: Enforcement ownership

- Direct `djng` execution must remain the sole authority for dependency gates,
  blocking Hook consequences, terminal validation, and final run acceptance.
- Provider results, provider-native Hooks, permission events, and local adapter
  wrappers must not bypass or substitute for direct `djng` enforcement.
- A provider result must not invoke direct gates, mark a command or run
  successful, or mutate the authoritative run outcome.

### AIR-6: Canonical Skill resolution

- Every Skill must declare explicit and checkable local acceptance criteria.
- Runtime Skill resolution must use a canonical executable catalog and reject
  unknown Skills, unsatisfied dependencies, and unknown Tool or Hook bindings.
- Provider-native Skill files must be derived from canonical Skill content and
  must not become independent sources of truth.
- A Skill session's local acceptance must not determine global generated-app
  acceptance.

### AIR-7: Provider-adapter behavior

- Provider adapters must expose a common provider-neutral capability and
  result boundary.
- An AI-guided command must halt when its session ends without sufficient
  acceptance evidence; execution must not silently advance or retry.
- Adapter failures must be normalized into structured, diagnosable outcomes.
- Adapter sessions must close on success, failure, cancellation, and timeout.
- Teardown warnings must not mask or replace an earlier command result.
- Provider adapters must be testable through credential-free stubs without
  changing direct Tool, Hook, or terminal-validation semantics.

### AIR-8: Provider isolation and credentials

- Each provider adapter must isolate its optional SDK dependency from shared
  automation code and from other adapters.
- Deterministic-only and dry-run execution must not initialize a provider
  adapter, discover credentials, open a provider session, or write provider
  artifacts.
- Credential discovery must remain inside the selected adapter and use the
  provider-approved runtime mechanism.
- Credentials must never be stored in source, fixtures, evidence, or command
  output.

### AIR-9: Verified provider support

- A provider adapter must not be reported as implemented or supported until
  both its provider-neutral contract tests and its explicitly enabled runtime
  integration suite pass.
- Capability metadata alone and skipped runtime tests must not be treated as
  evidence of working provider support.
- Provider runtime suites must be optional and must not prompt for or expose
  credentials when their prerequisites are absent.

### AIR-10: Derived automation distribution

- Provider-specific Skill and Plugin packages must be derived from canonical
  automation definitions.
- A derived package must preserve canonical identity, declared contents,
  dependencies, bindings, and acceptance criteria.
- A package must not add a capability absent from its canonical definition.
- Generated distribution artifacts must be traceable to their canonical
  sources and must not overwrite those sources.
- Provider installation and discovery must be opt-in and absent from dry runs
  and default tests.

## 3. Non-functional requirements

### AIR-NFR-1: Determinism

For the same validated inputs and injected execution metadata, provider-neutral
serialization, evidence ordering, catalog resolution, and direct automation
selection must be deterministic.

### AIR-NFR-2: Inspectability

Automation failures and incomplete runs must retain enough structured evidence
to identify the failed boundary without relying exclusively on console output
or provider-native session history.

### AIR-NFR-3: Portability

Canonical automation definitions and direct correctness gates must remain
provider-independent. Provider-specific capabilities may be mapped through
adapters or derived packages without changing canonical semantics.

[AI_AUTOMATION_CONTRACTS.md]: ../contracts/AI_AUTOMATION_CONTRACTS.md
[AI_AUTOMATION_SPECIFICATIONS.md]: ../specifications/AI_AUTOMATION_SPECIFICATIONS.md
[APP_BUILDER_REQUIREMENTS.md]: APP_BUILDER_REQUIREMENTS.md
[ARCHITECTURE.md]: ../ARCHITECTURE.md
[phased_implementation_plan.md]: ../phased_implementation_plan.md
