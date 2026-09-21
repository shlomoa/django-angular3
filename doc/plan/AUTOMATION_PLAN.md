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

### Ordered implementation plan

1. **Preflight: validate the canonical automation model.**
	- **1.1.** Validate that `doc/contracts/SKILL_CONTRACTS.md`, `doc/contracts/TOOL_CONTRACTS.md`, `doc/contracts/HOOK_CONTRACTS.md`, and `doc/contracts/PLUGIN_CONTRACTS.md` contain the required canonical Skill, Tool, Hook, and Plugin contracts without redefining them in this plan. <!-- STEP7-0963a0a2fac4 -->
	- **1.2.** Compare each `skill_creation/skills/` working copy with the canonical Skills catalog and update it through the [per-Skill cadence](#skill-authoring-and-derived-working-copies), without duplicating normative contracts. <!-- STEP7-1b6577edc2dc -->
	- **1.3.** Review planned capability bundles and add any missing canonical Plugin contracts to `doc/contracts/PLUGIN_CONTRACTS.md` before implementation or packaging work begins. <!-- STEP7-d8f1aeb440c6 -->
2. **Phase 1: resolve executable-contract design decisions.**
	- **2.1.** Finalize evidence redaction, dry-run evidence, and prior-input decisions in their owning contracts and specifications; apply the `ARCHITECTURE.md` §3.6.3 primitive-selection policy without redefining it here. <!-- STEP7-db81b18fba54 --> <!-- STEP7-cd7cb510c282 -->
	- **2.2.** Define every additional canonical Tool contract required by `APP_BUILDER_REQUIREMENTS.md` before claiming page, component, complex-component, reactive-form, or site support; reconcile the crosswalk, Tool catalog, and builder mapping first. <!-- STEP7-cef54b011de1 --> <!-- STEP7-5bcb5b8c2b4b -->
	- **2.3.** Record the local-to-global acceptance decision, including FR-8 failure handling and FR-9 terminal verification, in their owning requirements or contracts. <!-- STEP7-ba8cda71a1ec --> <!-- STEP7-187507ddf2f5 --> <!-- STEP7-501635306551 -->
3. **Phase 2: add the provider-neutral automation contracts package.**
	- **3.1.** Implement immutable, serializable provider-neutral result, error, and adapter-result contracts with deterministic validation and no provider imports. <!-- STEP7-608cc6741333 --> <!-- STEP7-b9e40abf7dd6 -->
	- **3.2.** Preserve canonical identity, input, output, and error boundaries; implement the executable catalog and resolver only as specified in `AI_AUTOMATION_SPECIFICATIONS.md`. <!-- STEP7-f3998a7d7736 --> <!-- STEP7-6a9d2c546778 --> <!-- STEP7-46ea2fee5395 --> <!-- STEP7-3213a38f3e91 -->
4. **Phase 3: implement durable provider-independent evidence recording.**
	- **4.1.** Implement injected, safe, ordered UTF-8 JSON Lines evidence recording with deterministic identifiers and timestamps, redaction, metadata finalization, malformed-prior-event handling, and structured recorder-write failures. <!-- STEP7-95afbbce44cc --> <!-- STEP7-f286a1e7d803 -->
	- **4.2.** Create the execution context after project-configuration validation and finalize evidence on every normal or error exit without claiming completion of existing OpenUI-diff or `NotImplementedError` work. <!-- STEP7-ea88b1840746 -->
5. **Phase 4: add provider-neutral direct-execution primitives.**
	- **5.1.** Implement synchronous execution context, Tool invocation, normalized outcomes, Hook consequences, and provider-free dry-run behavior without claiming `build_app` integration. <!-- STEP7-1d2daacdbca3 --> <!-- STEP7-e7b0be677eb6 --> <!-- STEP7-2bbd5c42c542 --> <!-- STEP7-1d4cbcc1fe90 -->
	- **5.2.** Preserve existing Django command errors and exit behavior while normalizing wrapper and recorder failures; no provider import or network use belongs in direct execution. <!-- STEP7-c00dd316684e --> <!-- STEP7-b694262f1573 -->
6. **Phase 5: add credential-free provider-neutral automation tests.**
	- **6.1.** Add deterministic contract, evidence, execution, and secret-prohibition tests using repository-local temporary artifacts and standard `unittest` discovery. Test serialization, dry runs, normalized errors, and recorder failures. <!-- STEP7-aa2f0088b4d0 --> <!-- STEP7-c54efc98e088 --> <!-- STEP7-f20bfd01d32d -->
	- **6.2.** Keep controller coverage in `tests/test_automation_execution.py` and focused command-boundary coverage in a dedicated `build_app` module; cover pre-Tool blocking, evidence finalization, command determinism, dependency skips, halt-on-failure, exit-code mapping, and canonical dry-run scenarios. <!-- STEP7-394434b9ab19 --> <!-- STEP7-0872fa19c0a5 --> <!-- STEP7-52bee6541dd3 --> <!-- STEP7-4c9400c3372c --> <!-- STEP7-d5a6ff3e560d --> <!-- STEP7-34bf010a962a --> <!-- STEP7-08764635f5d7 -->
7. **Phase 6: verify and document the foundation boundary.**
	- **7.1.** Run format, lint, focused automation tests, and full test discovery; document implemented foundation behavior and remaining `build_app` limitations without overstating support. <!-- STEP7-ca1e18e19e0e --> <!-- STEP7-0f7c49a7cbfc -->
	- **7.2.** Treat the existing CLI wrappers, `ensure_oasdiff()` acquisition, catalog contracts, build requirements, Skill working copies, and authenticated provider research as starting evidence—not proof that provider orchestration is implemented. <!-- STEP7-244b22b96a76 --> <!-- STEP7-cfdbfe1ff3c4 --> <!-- STEP7-3afcd0c47340 --> <!-- STEP7-616b278f5674 --> <!-- STEP7-3553167fc57e --> <!-- STEP7-ba292c49b963 --> <!-- STEP7-dfd02a744b05 --> <!-- STEP7-ab92c8417f09 --> <!-- STEP7-9646d470e48d -->
8. **Phase 7: implement deterministic Tool contracts.**
	- **8.1.** Implement each catalogued Tool through its canonical input, output, and error boundary, with conformance, error-category, and applicable FR-7/FR-8 tests; satisfy AIR-NFR-2 without redefining catalog entries. <!-- STEP7-ae3c4444fb15 --> <!-- STEP7-cd8248aa7ca1 --> <!-- STEP7-e93ecc429a67 --> <!-- STEP7-7e5c404e6205 -->
	- **8.2.** Do not claim an undefined OpenUI wrapper or operation as supported. `ngdj` schematic identity, options, behavior, and documentation remain upstream-owned under `ARCHITECTURE.md` §3.4. <!-- STEP7-f73ab95e9f66 -->
9. **Phase 8: implement direct lifecycle Hook contracts.**
	- **9.1.** Implement registry, dispatch, idempotency, persistence, and every catalogued Hook as specified, without redefining its trigger, scope, action, artifact, or failure consequence. <!-- STEP7-07e6ce269fc7 --> <!-- STEP7-9873033a418a --> <!-- STEP7-daabd8d9358b --> <!-- STEP7-66e10c67020a --> <!-- STEP7-9566fb176bd0 -->
	- **9.2.** Verify pre-Tool failures block, post-Tool failures halt and record, and session-stop failures warn without changing an already-decided exit result; test ordering, normalization, and equivalent provider-shaped lifecycle observations. <!-- STEP7-41ba89e57a6c --> <!-- STEP7-05ca26bd5270 --> <!-- STEP7-a56835ba9815 --> <!-- STEP7-a71c9ad11c4b --> <!-- STEP7-e14e54639011 -->
10. **Phase 9: implement direct `build_app` planning and execution.**
	- **10.1.** Repair the unfinished baseline; implement input discovery, change lanes, deterministic command translation, Tool and Hook boundaries, evidence, provider-free dry run, and terminal acceptance. Commands must use documented contract names and execute in dependency order. <!-- STEP7-b5fb48bfa4c9 --> <!-- STEP7-3e364793716f --> <!-- STEP7-e7210516ddf3 --> <!-- STEP7-c62fe1e70767 --> <!-- STEP7-8f20c02778fd --> <!-- STEP7-4105471c23c6 --> <!-- STEP7-011e91d36d43 -->
	- **10.2.** Complete canonical Skill authoring and working-copy alignment in dependency order before a selected Skill can be resolved, rendered, or executed. <!-- STEP7-f3d8206fd88c --> <!-- STEP7-59437800d439 --> <!-- STEP7-47924c62d577 --> <!-- STEP7-827e20f4b57a --> <!-- STEP7-e3b50d6cc681 --> <!-- STEP7-e1283cb70b74 -->
11. **Phase 10: implement guided-session adapter orchestration after direct execution.**
	- **11.1.** Implement the provider-neutral adapter interface, resolver, orchestration, stub adapter, and separately gated provider integrations. Provider outcomes must not bypass direct Tool, Hook, or terminal-validation authority; deterministic-only runs require no adapter. <!-- STEP7-78d7871e8584 --> <!-- STEP7-83340c91a5e3 --> <!-- STEP7-a0f7d2532949 --> <!-- STEP7-3eb71862cd8b --> <!-- STEP7-8454ec053897 -->
	- **11.2.** Package every provider SDK as an optional extra only with its adapter; retain shared credential-free coverage, and run provider integration suites only with bounded Skills/Tool allowlists and approved secret-managed environments. <!-- STEP7-21d8a3f2d6e7 --> <!-- STEP7-dc521f1b817d --> <!-- STEP7-cc9438e99f21 --> <!-- STEP7-a6bdfc38c410 --> <!-- STEP7-a310edb3c380 -->
	- **11.3.** Derive provider-specific Plugin packages from canonical contracts. Validate canonical preservation, exact manifests, provenance/hash staleness detection, installation/smoke behavior, and generated-workspace conformance. <!-- STEP7-296d439156d2 --> <!-- STEP7-35674349b69a --> <!-- STEP7-fd10b8999220 --> <!-- STEP7-e4966a166b23 --> <!-- STEP7-06732df6c184 --> <!-- STEP7-6852ed0af1ef --> <!-- STEP7-b0c60ee915c8 -->

<!-- Removed legacy migration trace marker IDs: STEP7-db81b18fba54 STEP7-cd7cb510c282 STEP7-244b22b96a76 STEP7-cfdbfe1ff3c4 STEP7-3afcd0c47340 STEP7-616b278f5674 STEP7-3553167fc57e STEP7-ba292c49b963 STEP7-dfd02a744b05 STEP7-ab92c8417f09 STEP7-9646d470e48d STEP7-969bf05201c3 STEP7-584bb46bffd2 STEP7-48f99ac4eb26 STEP7-9dfe8ebdfa5f STEP7-ba8cda71a1ec STEP7-cef54b011de1 STEP7-ff1e628b2cda STEP7-391cbeb13f15 STEP7-14d1e81dd2d5 STEP7-ae3c4444fb15 STEP7-f3998a7d7736 STEP7-6a9d2c546778 STEP7-46ea2fee5395 STEP7-cd8248aa7ca1 STEP7-e93ecc429a67 STEP7-7e5c404e6205 STEP7-95afbbce44cc STEP7-f286a1e7d803 STEP7-07e6ce269fc7 STEP7-9873033a418a STEP7-daabd8d9358b STEP7-66e10c67020a STEP7-96e9942e5e2b STEP7-fbaf2bb984e0 STEP7-41ba89e57a6c STEP7-05ca26bd5270 STEP7-a56835ba9815 STEP7-1d2daacdbca3 STEP7-e7b0be677eb6 STEP7-2bbd5c42c542 STEP7-b5fb48bfa4c9 STEP7-3e364793716f STEP7-1d4cbcc1fe90 STEP7-e7210516ddf3 STEP7-c62fe1e70767 STEP7-8f20c02778fd STEP7-c00dd316684e STEP7-b694262f1573 STEP7-f3d8206fd88c STEP7-59437800d439 STEP7-47924c62d577 STEP7-827e20f4b57a STEP7-8eebf79cfcc4 STEP7-4f62cd16d96a STEP7-13969132ef5f STEP7-e3b50d6cc681 STEP7-e1283cb70b74 STEP7-78d7871e8584 STEP7-cddb9e2717c4 STEP7-1496bb5d3423 STEP7-693cdc161855 STEP7-e8e916bac78a STEP7-c0682b03c673 STEP7-816f7b16b04c STEP7-83340c91a5e3 STEP7-a0f7d2532949 STEP7-3eb71862cd8b STEP7-8454ec053897 STEP7-c9b541737c42 STEP7-9dcd387045dd STEP7-80a57601adec STEP7-00670b6ff2ca STEP7-9e6564311efb STEP7-cc9438e99f21 STEP7-cac8d76798f4 STEP7-fcdb50e6d5c5 STEP7-296d439156d2 STEP7-35674349b69a STEP7-fd10b8999220 STEP7-e4966a166b23 STEP7-06732df6c184 STEP7-6852ed0af1ef STEP7-41d281188104 STEP7-6f569ec2a530 STEP7-3a981ddb0dd1 STEP7-1263bd5fba27 STEP7-2543f93b0d2f STEP7-b0c60ee915c8 STEP7-a6bdfc38c410 STEP7-a310edb3c380 STEP7-569596b8e500 STEP7-a6cce6b3c1dc STEP7-afddc77e74ab STEP7-2dcdd233a9ba STEP7-b02f182c103f STEP7-ea89af0bccab STEP7-fbbfa34764d2 STEP7-0323cc907509 STEP7-213207e9bd57 STEP7-3c02e09b8ff6 -->

### Skill authoring and derived working copies

#### Scope and ownership

This section defines the per-Skill authoring and verification cadence for the
eleven canonical guided Skills in `doc/contracts/SKILL_CONTRACTS.md`. Use a
Skill only for AI judgment, interpretation, iterative repair, or refinement;
deterministic generation belongs to a Tool contract.

It does not redefine Skill contracts, repository-wide sequencing, or
`build_app` behavior, which are owned by `doc/contracts/SKILL_CONTRACTS.md`,
the [dependency-ordered implementation phases](#dependency-ordered-implementation-phases),
and `doc/requirements/APP_BUILDER_REQUIREMENTS.md`, respectively.
`angular-django2` owns its public generation behavior; Skills use the upstream
sources referenced by `ARCHITECTURE.md` §3.4 rather than restating them.

Skills preserve intentional contract-derived representations across backend
models, OpenAPI, generated TypeScript models, and Angular validation; they
must not introduce competing hand-maintained sources.

#### Authoring and runtime input

Two distinct kinds of input are kept separate when a Skill is described.

**Authoring information** defines and verifies the Skill: purpose and selection
conditions, canonical runtime input/output contracts, dependencies, permitted
capabilities, acceptance criteria, test cases, expected evidence, and
provider-neutral context requirements. It is planning metadata, not an
invocation payload.

**Runtime input** is the single validated structured object that `build_app`
supplies for one selected guided command through the provider adapter.
Depending on the canonical Skill contract, it may contain:

- validated static settings required by the selected command;
- validated project identity and artifact locations;
- command-specific values derived during translation, such as affected
  resource/component identities and placement hints;
- the relevant atomic `ChangeSet` subset or affected identities; and
- bounded prior-command outcomes or acceptance evidence required by a declared
  dependency.

Skills consume these values without rereading configuration files, re-deriving
changes, or parsing raw `oasdiff` output. Guided sessions receive runtime input
from `build_app` through the provider adapter; interactive chat is not a
canonical runtime-input source.

Each Skill's `Inputs` section in `doc/contracts/SKILL_CONTRACTS.md` defines
only its runtime schema. Authoring information belongs to this plan and the
corresponding derived working copy, not to the runtime payload.

#### Canonical sources and derived output

The [Skills Catalog in `SKILL_CONTRACTS.md`](../contracts/SKILL_CONTRACTS.md#skills-catalog)
is the canonical `djng` Skill source for stable name, purpose, modes, inputs,
outputs, dependencies, and acceptance criteria. Numbered files in
`skill_creation/skills/` are derived authoring working copies; when they
differ, update the working copy rather than creating a competing source.

The executable canonical catalog and provider-neutral Skill resolver planned
in [Tools, Hooks, Skills, adapters, and Plugins](#tools-hooks-skills-adapters-and-plugins)
will provide runtime metadata without parsing this plan, working copies, or
provider-native files.

Provider adapters/renderers derive native prompts, tool registrations, Skill
files, or packages from the canonical contract. Every rendering must preserve
canonical identity, purpose, inputs, outputs, dependencies, acceptance
criteria, and Tool/Hook bindings and pass provider-package conformance tests.
Native metadata, filesystem layouts, invocation syntax, and permissions are
derived concerns, not the cross-provider format.

Shared context remains with canonical Skill material. A renderer may inline or
package it only when required; the copy is an artifact, not an independent
source. Rendered output belongs under the ignored build/distribution location
planned in [Tools, Hooks, Skills, adapters, and Plugins](#tools-hooks-skills-adapters-and-plugins)
and must not modify canonical sources. See `doc/contracts/SKILL_CONTRACTS.md`
§Canonical skill contract and provider renderings.

#### Tooling boundary

The deterministic integration toolchain and contracts are owned by
`doc/contracts/TOOL_CONTRACTS.md`,
`doc/requirements/APP_BUILDER_REQUIREMENTS.md`, and their implementations:
`drf-spectacular` for OpenAPI export, `oasdiff` for schema comparison,
`ng-openapi-gen` for Angular client generation, and governed wrappers around
public `angular-django2` schematics. This plan neither redefines them nor
introduces alternative generators or diff tools.

A Skill must not invoke raw Angular CLI, `ng-openapi-gen`, or `oasdiff`
binaries, bundle a wrapper, or recreate deterministic schematic logic in
scripts. `build_app` derives changes before guided execution; a Skill consumes
structured command input rather than rerunning the diff.

When guided work needs a deterministic operation, the provider adapter may
request only a canonical, allowed Tool. The direct execution controller
validates and runs it, applies allowlisting and Hooks, records evidence, and
determines failure consequences. A Skill/provider result cannot bypass those
gates or mark a command/run successful.

Executability follows the effective `tool.commandAllowlist` in static
`django-angular3.json`: the library fallback permits only `ng_openapi_gen`,
while repository/generated configurations may allow more wrappers. `--dry-run`
is diagnostic and non-mutating; its support proves neither a canonical Tool
contract nor a completed `build_app` mapping. Skills must not infer
executability from wrapper availability or dry-run output.

#### Per-Skill cadence

Every Skill follows four ordered stages with explicit user approval between
them:

1. **Plan** — capture intent, conduct the interview, and sketch `name`,
	`description`, runtime inputs and their sources, produced files,
	scripts/shared context, implementation questions, and test prompts.
2. **Implementation and test generation** — update the canonical contract and
	derived working copy; create required scripts, references, assets, prompts,
	and assertions; render/test native artifacts only through the applicable
	adapter.
3. **`build_app` command integration** — add the selected Skill command after
	the Skill exists.
4. **Verification** — run and grade with-Skill versus baseline tests, render
	results, incorporate feedback, and after approval run provider-package
	conformance tests before publishing a derived artifact.

Subagents may work within any stage—for example, parallel with-Skill and
baseline verification—but must not collapse or cross stage boundaries.

#### Input validation, authoring order, and working copies

Each Skill validates its canonical runtime-input shape and Skill-specific
semantic preconditions. Shared configuration, artifact, Tool, Hook, and
dependency validation stays at the owning direct `build_app` boundaries and is
not duplicated per Skill. Missing inputs have only the meanings in
`doc/requirements/APP_BUILDER_REQUIREMENTS.md`; Skills introduce no
promised-artifact state.

Author Skills in canonical dependency order so declared dependencies' outputs
are test ground truth. Select a Skill only for genuinely underspecified,
interpretive, or post-generation refinement; validated structured inputs use
deterministic Tools without a provider session.

This is only Skill authoring/verification order;
`doc/requirements/APP_BUILDER_REQUIREMENTS.md` defines the complete
mixed-automation execution order.

For focused authoring, use the matching
`skill_creation/skills/<number>-<skill-name>.md` plus only needed
`skill_creation/shared/` files. These are split working copies of
`doc/contracts/SKILL_CONTRACTS.md`; resolve incompleteness or inconsistency
against the canonical catalog and update the split file.

See `doc/requirements/APP_BUILDER_REQUIREMENTS.md` §Execution order for the
authoritative dependency chain.

## Provider-neutral foundation

Phases 1–6 establish the provider-neutral foundation. Their scope is limited to
the result/evidence contracts, direct execution, and credential-free
verification described in `AI_AUTOMATION_SPECIFICATIONS.md`; it does not claim
provider orchestration or complete `build_app` support.

## Dependency-ordered implementation phases

The [ordered implementation plan](#ordered-implementation-plan) is the sole
sequence in this document. Its phases are acceptance-gated and may start only
after their dependencies are satisfied. Normative behavior remains in
`doc/contracts/`, the automation and builder requirements, and
`AI_AUTOMATION_SPECIFICATIONS.md`; this plan only sequences those sources.

## Automation-specific acceptance

Completion of a phase requires its stated implementation and verification
substeps, including terminal validation where applicable. Provider research
informs adapter mappings only; it is neither a runtime dependency nor a
normative source. Provider adapters require credential-free contract and
capability tests, separately gated live suites, and release controls before
they may be advertised.

<!-- Removed legacy migration trace marker IDs: STEP7-067efeb856a7 STEP7-608cc6741333 STEP7-b9e40abf7dd6 STEP7-ca1e18e19e0e STEP7-ea88b1840746 STEP7-3213a38f3e91 STEP7-6c22067ba12e STEP7-5bcb5b8c2b4b STEP7-661b278dbe57 STEP7-97708fa5b165 STEP7-5a2cc0d20bf7 STEP7-c73f8e958d54 STEP7-446da3c1999f STEP7-5302299fa085 STEP7-f73ab95e9f66 STEP7-839d6f244fe8 STEP7-54eb264aaba7 STEP7-9f25bdae134b STEP7-9e1dcc220136 STEP7-4c5da1ae233e STEP7-bc3554bf70e7 STEP7-2742d208c411 STEP7-a31e0de7f65b STEP7-9566fb176bd0 STEP7-266554bf78bb STEP7-4105471c23c6 STEP7-011e91d36d43 STEP7-1ab6fa0eafaf STEP7-2fb5f5dd0d08 STEP7-da9c53771cb8 STEP7-21d8a3f2d6e7 STEP7-dc521f1b817d STEP7-d53d7e9cf222 STEP7-53521b5fa5d4 STEP7-0cc35573b09c STEP7-3128f63863e4 STEP7-db9221a0201d STEP7-74cb9f5dca64 STEP7-8b51f5552669 STEP7-187507ddf2f5 STEP7-501635306551 STEP7-0f7c49a7cbfc STEP7-aa2f0088b4d0 STEP7-c54efc98e088 STEP7-f20bfd01d32d STEP7-b1b3a20a324b STEP7-a71c9ad11c4b STEP7-e14e54639011 STEP7-394434b9ab19 STEP7-0872fa19c0a5 STEP7-52bee6541dd3 STEP7-4c9400c3372c STEP7-d5a6ff3e560d STEP7-34bf010a962a STEP7-08764635f5d7 STEP7-eae61ad3c95a STEP7-a12723934047 STEP7-ebf4c65d85a1 STEP7-1031bdc3e03b STEP7-1024c342bf9f STEP7-4015068cf5e1 STEP7-3d80674ced57 STEP7-8455ecf41867 STEP7-464ec679bada STEP7-f7ff46d94694 STEP7-509259f84310 STEP7-1fa2e777866c STEP7-2d1193d833a2 STEP7-6be0dc9bbe7f STEP7-f3490b673870 STEP7-30aeda2a3ea4 STEP7-3cb765faad1b STEP7-0be43e769a86 -->

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
