# Phased Implementation Plan — Tools, Hooks, Skills, Plugins

## Purpose

This document derives a phased implementation plan that turns the architectural
recommendations in `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` and the normative
contracts in `doc/GENERATE_AI_AUTOMATIONS.md` into an ordered, acceptance-gated
sequence of implementation work.

It fulfils the "phased implementation plan" deliverable of the
*Architecture alignment — Phased implementation plan* issue and feeds the
finalisation of `doc/GENERATE_AI_AUTOMATIONS.md` as the umbrella design spec for
the full automation model (Skills + Tools + Hooks + Plugins), not Skills alone.

### How to read this plan

- Each phase lists its **goal**, its **dependencies** (what must land first),
  the **work items**, **acceptance criteria** (the conditions that must hold
  before the phase is considered done), and **test / verification coverage**.
- Phases are ordered by dependency. A phase must not start while an upstream
  phase it is blocked on is unsatisfied — the same dependency-gating principle
  the procedure graph enforces at runtime (`APP_BUILDER_REQUIREMENTS.md` FR-2,
  FR-8).
- Authoritative sources are the contracts in `doc/GENERATE_AI_AUTOMATIONS.md`
  and the functional requirements in `doc/APP_BUILDER_REQUIREMENTS.md`. Where
  this plan and those documents disagree, the contracts and FRs win; update this
  plan to match.

### Primitive-selection policy

This plan applies the primitive-selection policy from
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` §5:

| If the work… | Use |
|---|---|
| Requires AI judgment, iteration, or multi-step code authoring | **Skill** |
| Is a single deterministic command, API call, or file operation | **Tool** |
| Must run automatically at a lifecycle event, regardless of agent choices | **Hook** |
| Is a coherent set of capabilities intended for distribution or reuse | **Plugin** |

---

## Current state (baseline)

The following already exist on `main` and are the starting point for this plan:

- **CLI wrappers** (Django management commands): `export_schema`, `build_app`,
  `ng_new`, `ng_add`, `ng_config`, `ng_gen_app`, `ng_openapi_gen`, `ng_build`,
  `ng_workspace`, `ng_workspace_delete`, `ng_workspace_modify`
  (`django_angular3/management/commands/`).
- **oasdiff acquisition**: `django_angular3/tools.py:ensure_oasdiff()`.
- **Normative contracts** for every Tool, Hook, and Plugin
  (`doc/GENERATE_AI_AUTOMATIONS.md` §Tool / §Hook / §Plugin Contracts Catalog).
  Most of these contracts carry an *Implementation reference* of "planned" — the
  contract is defined but the backing artifact does not yet exist.
- **App-builder functional requirements** for traversal, failure handling, and
  terminal verification (`doc/APP_BUILDER_REQUIREMENTS.md` FR-1…FR-10), including
  FR-9 (tool failure handling), FR-9a (hook failure handling), and FR-10
  (terminal verification contract).
- **Skill working copies** under `skill_creation/skills/` (split copies of the
  `GENERATE_AI_AUTOMATIONS.md` Skills Catalog); the eleven Skills are not yet
  authored as runnable `SKILL.md` units (`TODO.md` item 7).

What is *not* yet implemented and is therefore scheduled below: the deterministic
tool wrappers, the lifecycle hook scripts, the procedure-graph traversal that
calls them, the SDK-driven Skill orchestration, the terminal verification
procedures, and the plugin packaging.

---

## Phase 0 — Design alignment (this issue)

**Goal**: Land the design alignment that lets implementation proceed against
stable contracts.

**Dependencies**: none.

**Work items**:
- Promote Tools / Hooks / Plugins recommendations into normative contracts in
  `doc/GENERATE_AI_AUTOMATIONS.md` (done — see its Contracts Catalogs).
- Add app-builder FRs for failure handling and terminal verification
  (`doc/APP_BUILDER_REQUIREMENTS.md` FR-9, FR-9a, FR-10) (done).
- Record this phased implementation plan (this document).
- Record the local-to-global acceptance decision (Phase 7).

**Acceptance criteria**:
- Every Tool, Hook, and Plugin recommendation in
  `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` maps to exactly one normative contract.
- This plan exists and references the contracts and FRs by name.

**Test / verification coverage**: documentation review only — no code behaviour
changes in this phase.

---

## Phase 1 — Deterministic tool contracts

**Goal**: Implement the deterministic tool wrappers so the agent calls bounded
operations and receives structured results, replacing raw CLI parsing.

**Dependencies**: Phase 0.

**Work items** (one per Tool contract in
`doc/GENERATE_AI_AUTOMATIONS.md` §Tool Contracts Catalog):
- `openapi_schema_export` — wrap `export_schema` to return schema path and a
  `schema_changed` flag.
- `oasdiff_diff` — wrap the `ensure_oasdiff()` binary to return
  `{ breaking: [], non_breaking: [], schema_changed: bool }`.
- `validate_openapi_schema` — wrap an OAS 3.1 validator to return
  `{ valid: bool, errors: [] }`.
- `angular_api_client_generate` — wrap `ng_openapi_gen` to return
  `generated_files: []`.
- `angular_workspace_scaffold`, `angular_app_scaffold` — wrap `ng_new` / the
  app-scaffold wrapper to return structured result objects.

Each tool MUST honour the **Tool contract shape**
(`doc/GENERATE_AI_AUTOMATIONS.md` §Tool contract shape): structured inputs,
structured outputs, and a structured error object whose `category` is one of
`{ invalid_input, missing_dependency, external_tool_failed, output_invalid }`.

**Acceptance criteria**:
- Each tool's return value validates against its contract's declared output
  shape.
- Each tool surfaces failures through the structured error object — never as an
  unstructured exception or stdout-only message — so FR-9 handling can act on
  `category`.
- Tool names exactly match the contract names emitted in the procedure graph
  `tool` field (FR-8).

**Test / verification coverage**:
- Unit tests per tool: success path, each error `category`, and dry-run/plan
  output where applicable.
- A contract-conformance test asserting each tool's output keys match its
  contract.

---

## Phase 2 — Lifecycle hook contracts

**Goal**: Implement the deterministic enforcement and side-effect hooks so gates
and mandatory side effects always run, independent of agent choices.

**Dependencies**: Phase 1 (hooks wrap tool outputs).

**Work items** (one per Hook contract in
`doc/GENERATE_AI_AUTOMATIONS.md` §Hook Contracts Catalog):
- `pre-construction` — `Pre*` gate: schema exists, is valid OAS 3.1, and is at
  least as fresh as the latest migration before any Angular generation tool.
- `migration-triggered` — `Post*`: re-export the schema when a new migration
  appears; append a status record to `build/hook-log.jsonl`.
- `breaking-change` — gate consuming `oasdiff_diff` output; block downstream
  construction until breaking changes are acknowledged. This is the **single**
  point of enforcement (FR-4); `build_app` MUST NOT re-implement the gate.
- `post-generation` — `Post*`: run a structural check after each generation tool
  and append a pass/fail entry to `build/verification.log`.
- `session-stop` — `Stop`: archive durable artifacts and write a session
  summary; MUST NOT change the session exit code (FR-9a).

**Acceptance criteria**:
- `Pre*` hook non-zero exit blocks the wrapped tool and every dependent
  procedure (FR-9a).
- `breaking-change` returns the dedicated breaking-change exit code (FR-4); other
  hook failures return a distinct hook-failure exit code (FR-9a).
- `session-stop` only appends warnings and never alters the exit code.
- Each hook writes its structured error fields to stderr / `build/hook-log.jsonl`.

**Test / verification coverage**:
- Per-hook tests: trigger event fires the hook, blocking hook halts traversal,
  non-blocking `Post*` failure halts and records, `Stop` hook cannot change exit
  code.
- Exit-code distinctness tests (breaking-change vs other hook failure vs tool
  failure).

---

## Phase 3 — Procedure graph and `build_app` traversal

**Goal**: Make `build_app` traverse the procedure graph in dependency order and
dispatch each node to the right primitive.

**Dependencies**: Phases 1–2.

**Work items**:
- Emit `tool`, `gate`, and `skill-session` nodes whose `tool` / `hook` fields
  equal the contract names (FR-8).
- Traverse in dependency order; for `tool` nodes call the Phase 1 tools, for
  `gate` nodes apply the Phase 2 hooks.
- Implement FR-9 / FR-9a failure handling: halt at the failed node, refuse to
  start dependents, emit structured error, exit with the contract-specific code.
- Keep `--dry-run` emitting the graph without invoking any automation (FR-3).

**Acceptance criteria**:
- A node never starts while a dependency it is blocked on is unsatisfied
  (FR-2, FR-8).
- A failed tool or `Pre*`/`Post*` hook stops traversal and produces the correct,
  distinct exit code.
- `--dry-run` output is deterministic and human-readable for the same inputs.

**Test / verification coverage**:
- Graph-determinism tests (same inputs → same graph).
- Traversal tests: dependency ordering, halt-on-failure, dependent-skip,
  exit-code mapping.
- Dry-run snapshot tests for the documented `TEST_EXAMPLES.md` scenarios.

---

## Phase 4 — Skills authoring

**Goal**: Author the eleven Angular construction Skills as runnable `SKILL.md`
units with per-skill acceptance criteria.

**Dependencies**: Phase 3 (Skills run as `skill-session` nodes the graph emits).

**Work items**:
- Author each Skill per `doc/SKILL_AUTHORING_PLAN.md` (plan, implementation +
  tests, app-builder procedure integration, verification).
- Keep `skill_creation/skills/` working copies aligned with the authoritative
  `GENERATE_AI_AUTOMATIONS.md` Skills Catalog.
- Define each Skill's local acceptance criteria during its Plan phase: the exact
  pass/fail conditions, the tools used to verify them, and what "done" means
  locally.

**Acceptance criteria**:
- Each Skill declares explicit, checkable acceptance criteria (no arbitrary
  termination).
- The Skill dependency chain matches the dependency edges the procedure graph
  emits within the Skill-session subset (FR-2).

**Test / verification coverage**:
- Per-skill component tests for the generated Angular artifacts.
- Skill-catalog-alignment check between `skill_creation/skills/` and
  `GENERATE_AI_AUTOMATIONS.md`.

---

## Phase 5 — Orchestration flow (Claude Agent SDK)

**Goal**: Drive each `skill-session` node through the Claude Agent SDK until its
acceptance criteria are satisfied.

**Dependencies**: Phases 3–4.

**Work items**:
- For each `skill-session` node, make a Claude Agent SDK call with the Skill(s)
  enabled, procedure inputs as the prompt, and the working directory set to
  `angular.output` (FR-8).
- Specify and implement what `build_app` does when an agent session ends without
  evidence of success — halt, surface a structured error, and refuse to advance
  (no silent advance past unmet acceptance criteria).

**Acceptance criteria**:
- `build_app` detects a session that ended without satisfying its acceptance
  criteria and halts instead of advancing.
- Session failures are surfaced as structured errors consistent with FR-9.

**Test / verification coverage**:
- Orchestration tests with a stubbed SDK: success advances, unmet-acceptance
  halts, context-exhaustion / timeout produce a structured error.

---

## Phase 6 — Terminal verification

**Goal**: Make every run terminate in verification procedures that decide success
on recorded construction results, not a separate filesystem rescan.

**Dependencies**: Phases 3–5.

**Work items**:
- Implement the terminal verification procedures the procedure graph always ends
  in (FR-10), consuming structured tool outputs (for example the
  `generated_files` array from `angular_api_client_generate`).
- Cover the four verification categories in `doc/ARCHITECTURE.md` §7.3: contract,
  construction-output, integration, and test-based verification.

**Acceptance criteria**:
- A run is reported successful only when every terminal verification procedure
  reports success (FR-10).
- A failed terminal verification follows FR-9 failure handling.

**Test / verification coverage**:
- Terminal-verification tests: success only on all-pass; failure path mirrors
  FR-9; verification consumes recorded tool outputs rather than rescanning.

---

## Phase 7 — Local-to-global acceptance gate

**Goal**: Close the gap where each Skill declares "done" locally but the composed
application is still incorrect (the `getOrder(id: number)` →
`load(id: string)` interface-drift chain in `TODO.md` §9.3).

**Dependencies**: Phases 4–6.

**Local-to-global architectural decision** (records the decision required by the
issue for `doc/ARCHITECTURE.md` §7.2/§7.3):

> Local acceptance by an individual Skill session is necessary but **not
> sufficient** for global correctness. The architecture therefore requires a
> distinct **global acceptance gate**, applied after all Skill sessions and
> deterministic procedures complete, that verifies properties no single Skill
> can see:
>
> 1. **Cross-Skill interface consistency** — types and signatures produced by one
>    Skill match what downstream Skills consume (no silent `number`/`string`
>    drift across the api → data-service → page chain).
> 2. **Backend-contract / Angular-client alignment** — the generated client
>    matches the exported OpenAPI contract.
> 3. **Runtime smoke tests** — the composed application starts and the main
>    flows run.
>
> This gate is owned by the terminal verification procedures (Phase 6 / FR-10),
> not by any Skill. A run is "a correct working application"
> (`doc/ARCHITECTURE.md` §2.17) only when this global gate passes. This decision
> belongs in `doc/ARCHITECTURE.md` §7.2/§7.3 and the global acceptance criteria
> in `doc/REQUIREMENTS.md` §6.4.

**Acceptance criteria**:
- The global acceptance gate is documented in `doc/ARCHITECTURE.md` §7.2/§7.3 and
  `doc/REQUIREMENTS.md` §6.4 (recorded for the design-alignment phase; future
  implementation phases must keep those sections aligned with the executable
  gate).
- The gate fails the run on cross-Skill interface drift even when every Skill
  passed its local acceptance.

**Test / verification coverage**:
- A regression test reproducing the interface-drift failure chain and asserting
  the global gate catches it.

---

## Phase 8 — Plugin packaging and distribution

**Goal**: Package the coherent capability sets as installable Claude plugins.

**Dependencies**: Phases 1–7 (a plugin bundles already-implemented primitives).

**Work items** (one per Plugin contract in
`doc/GENERATE_AI_AUTOMATIONS.md` §Plugin Contracts Catalog):
- `djng-angular-construction` — all eleven Skills + schema/generation tools +
  validation/enforcement hooks.
- `ngdj-scaffold` — workspace/app/feature scaffold tools.
- `contract-lifecycle` — export → validate → diff → version → gate tools and
  hooks.

**Acceptance criteria**:
- Each plugin bundles exactly the Skills / Tools / Hooks named in its contract.
- Each plugin installs and versions independently of the Python package.

**Test / verification coverage**:
- Plugin-manifest conformance tests (declared contents match the contract).
- Install / smoke test per plugin against a generated-app workspace.

---

## Dependency summary

```
Phase 0 (design)
  └─ Phase 1 (tools)
       └─ Phase 2 (hooks)
            └─ Phase 3 (procedure graph + traversal)
                 ├─ Phase 4 (skills)
                 │    └─ Phase 5 (orchestration / SDK)
                 │         └─ Phase 6 (terminal verification)
                 │              └─ Phase 7 (local-to-global gate)
                 └─ Phase 8 (plugin packaging — after 1–7)
```

## Test and verification coverage migration

As behaviour moves from AI-guided Skill flow to deterministic tool/hook
enforcement, test ownership moves with it:

- Operations promoted to **Tools** (Phase 1) gain deterministic unit tests with
  fixed inputs/outputs, replacing reliance on Skill self-checks.
- Gates and side effects promoted to **Hooks** (Phase 2) gain lifecycle-event
  and exit-code tests, replacing "the agent remembered to do it" assumptions.
- **Skills** (Phase 4) retain component/behaviour tests for generative output.
- **Terminal verification** (Phase 6) and the **global acceptance gate**
  (Phase 7) own cross-Skill and integration correctness — the properties no
  single primitive's tests can establish.

## Related documents

- `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` — source recommendations and primitive
  comparison.
- `doc/GENERATE_AI_AUTOMATIONS.md` — authoritative Tool / Hook / Plugin / Skill
  contracts.
- `doc/APP_BUILDER_REQUIREMENTS.md` — FR-1…FR-10 (traversal, failure handling,
  terminal verification).
- `doc/ARCHITECTURE.md` — §2 automation primitive definitions, §7 construction
  and verification flow.
- `TODO.md` — open backlog items this plan sequences (notably items 6–9, 12).
