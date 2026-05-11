# Open Items — djng/ngdj Documentation

Generated: 2026-05-11. All items below are open unless marked **Resolved**.

---

## 1. APP_BUILDER_REQUIREMENTS.md — Open Questions (OQ1–OQ3)

These were in the `doc/APP_BUILDER_REQUIREMENTS.md` Open Questions section from the outset.
OQ4 and OQ5 are resolved and crossed out in the document; OQ1–OQ3 remain open.

| # | Question | Detail | Options / proposals | Origin | Input sources |
|---|---|---|---|---|---|
| OQ1 | **Schema format** | `openapi.source` in `django-angular3.json` currently points to a JSON file. The app builder should accept both YAML and JSON OAS 3.x files. | (a) Accept both; auto-detect by file extension or content. (b) Require YAML only. (c) Require JSON only. | APP_BUILDER_REQUIREMENTS.md §Inputs table; `spec/openapi/` examples use JSON | `django_angular3/config.py`, `spec/openapi/source/`, `django-angular3.json` `openapi.source` key |
| OQ2 | **UI definition format** | `ui.source` points to a JSON file (`spec/ui/example.ui.json`). The schema for inline `ui.pages`, `ui.components`, and `ui.forms` in `django-angular3.json` is not yet defined. Config change detection cannot be implemented until the schema is fixed. | Define a JSON Schema for each inline section, OR require `ui.source` only (no inline definitions). | APP_BUILDER_REQUIREMENTS.md §Inputs — Config keys table; `spec/ui/example.ui.json` | `spec/ui/`, `django_angular3/validation.py`, `django-angular3.json` `ui.*` keys |
| OQ3 | **Previous-state storage** | `build_app` compares current schema/config against a previous version. Where the previous version lives is unspecified. | (a) Git: diff HEAD vs working tree or two named commits. (b) Committed baseline file (e.g. `spec/openapi/previous.json`). (c) Explicit `--previous-schema` / `--previous-config` CLI paths (already defined as optional flags — this option treats them as the sole mechanism). | APP_BUILDER_REQUIREMENTS.md §Optional inputs table and §Change Derivation | `django_angular3/management/commands/`, `spec/openapi/`, APP_BUILDER_REQUIREMENTS.md |

---

## 2. APP_BUILDER_REQUIREMENTS.md — Architectural Item (A3)

| # | Item | Detail | What is missing | Origin | Input sources |
|---|---|---|---|---|---|
| A3 | **Per-stage durable artifacts table** | ARCHITECTURE.md §7.1 states each stage should produce durable artifacts that can be inspected, tested, and reused across iterations. APP_BUILDER_REQUIREMENTS.md defines the three phases (change derivation, procedure graph construction, SKILLS execution) and their outputs textually, but no table maps phase → artifact → format → storage location. | Add a table with columns: Phase, Artifact produced, Format, Storage path, Inspectable? | ARCHITECTURE.md §7.1 specifies durable artifacts per stage; APP_BUILDER_REQUIREMENTS.md §JSON representation describes the procedure graph structure but only as a `[DEBUG]` side-effect, not a first-class artifact record. | ARCHITECTURE.md §7.1, APP_BUILDER_REQUIREMENTS.md §Procedure Graph, §JSON representation |

---

## 3. Cross-Document Misalignment — SKILL_AUTHORING_PLAN.md vs APP_BUILDER_REQUIREMENTS.md

| Aspect | SKILL_AUTHORING_PLAN.md says | APP_BUILDER_REQUIREMENTS.md says | Gap |
|---|---|---|---|
| How SKILLS are invoked | SKILLS invoke djng Python wrappers (`ng_new`, `ng_config`, `ng_openapi_gen`, `ng_build`, etc.) bundled in `scripts/`. | SKILLS are invoked via Claude Code Python SDK API calls. `build_app` makes one SDK call per procedure. | Neither document acknowledges the other level. The full chain is: `build_app` → SDK call → agent session → Bash → djng wrapper → ngdj schematic. |
| Who is the loop controller | Per-skill cadence includes a Verification phase; SKILL instructions define acceptance criteria. | Option B (resolved): the agent executing the SKILL iterates natively until SKILL acceptance criteria are satisfied. | Consistent in intent, but the chain description in SKILL_AUTHORING_PLAN.md stops at the djng-wrapper level without acknowledging the agent/SDK wrapper above it. |
| Resolution needed | Neither document needs to be the single source of truth, but each should acknowledge the other level with a one-sentence cross-reference. | Same. | Draft: SKILL_AUTHORING_PLAN.md should note SKILLS are invoked via SDK calls; APP_BUILDER_REQUIREMENTS.md FR-8 already states SDK invocation but should note SKILLS internally call djng wrappers. |

**Origin**: identified during OQ5 analysis. Reading GENERATE_SKILLS.md (SKILLS are agent instructions in forked contexts) and SKILL_AUTHORING_PLAN.md (SKILLS call djng wrappers) together reveals the gap.
**Input sources**: `doc/SKILL_AUTHORING_PLAN.md` §Tooling boundary, `doc/APP_BUILDER_REQUIREMENTS.md` §FR-8, `doc/GENERATE_SKILLS.md` §Auto-invocation model.

---

## 4. Missing E2E Verification Specification

Prerequisite for the original session goal: E2E test from example Django app to a running integrated application.

| Aspect | Current state | What is missing | Why it matters |
|---|---|---|---|
| Terminal procedure | `ng_build` is the final verification procedure in the procedure graph. | `ng_build` only confirms the Angular app compiles. It does not verify backend API / Angular client alignment, runtime integration, or business-logic correctness. | A build that compiles is not the same as a working integrated application. |
| Backend/frontend alignment | REQUIREMENTS.md §4.2.2 requires "alignment between backend behavior, generated Angular integration artifacts, and frontend composition." | No specification of how this alignment is verified programmatically. No test queries a DRF endpoint and compares the response shape against what the generated Angular client expects. | Alignment can silently break when the OpenAPI schema diverges from the running backend. |
| Full-stack E2E test spec | REQUIREMENTS.md §4.16 defines four verification categories: contract, construction-output, integration, test-based. | None of the four categories has a concrete acceptance test specification. §6.4 Mandatory Acceptance Scenarios header exists but content is not populated. | Without concrete acceptance scenarios the verification stage has no pass/fail criterion beyond "Angular compiled." |
| ngdj test surface | ngdj schematics are not tested by the djng test suite. | No specification for how SKILL-generated ngdj outputs are tested against a real Angular workspace. | Correctness of the generated Angular application depends on ngdj schematic outputs, which are currently unverified. |

**Origin**: identified when confirming Option B. `ng_build` as the only terminal procedure closes the procedure graph but not the E2E correctness question. REQUIREMENTS.md §6.4 header exists with no populated content.
**Input sources**: `doc/REQUIREMENTS.md` §4.16, §6.1, §6.4; `doc/ARCHITECTURE.md` §7.3; `doc/APP_BUILDER_REQUIREMENTS.md` §Procedure Graph (terminal nodes), §FR-8; `doc/SKILL_AUTHORING_PLAN.md` §Per-skill cadence (Verification phase).

---

## 5. REQUIREMENTS.md — Consistency Items (C3–C10)

C1 (cross-reference strategy) and C2 (deployment topology) were resolved and committed. The following remain open.

| # | Item | Location in REQUIREMENTS.md | Alignment issue | Authoritative source | Resolution needed | Priority |
|---|---|---|---|---|---|---|
| C3 | **Non-CRM content stage not enumerated as a discrete stage in §4.2** | §4.2.3 step 3 mentions non-CRM changes; §4.2.2 does not list the non-CRM content stage as a discrete governed stage. | ARCHITECTURE.md §7.1 lists stage 4 "Non-CRM content stage" as a distinct control-loop stage with its own durable artifacts. REQUIREMENTS.md treats it as implicit within the build flow. | ARCHITECTURE.md §7.1 | Add a sentence to §4.2.2 explicitly naming the non-CRM content stage as a governed construction stage, parallel to contract normalization and CRM artifact generation. | Medium |
| C4 | **Two-stream separation strength mismatch** | §4.13: "these two streams must remain separate and must not be merged into a single source of truth." | REQUIREMENTS.md uses "must"; ARCHITECTURE.md §8.2 uses "should." Mismatched normative strength for the same constraint. | REQUIREMENTS.md §4.13 | Align ARCHITECTURE.md §8.2 to use "must" for the separation constraint. | Low |
| C5 | **`angular-code-agent` term unused in REQUIREMENTS.md** | Not present in REQUIREMENTS.md. | ARCHITECTURE.md §2.16 defines `angular-code-agent` as the orchestrator. REQUIREMENTS.md references `djng` and `build_app` but never uses this term. REQUIREMENTS.md §1.1 cross-references §§2.5–2.6 and §§2.14–2.15 but not §2.16. | ARCHITECTURE.md §2.16 | Add `angular-code-agent` to the defined-terms cross-reference in REQUIREMENTS.md §1.1, or clarify that `build_app` is the djng-level entry point for the orchestrator role in §2.16. | Medium |
| C6 | **PostgreSQL assumption not scoped to production** | REQUIREMENTS.md §1.4: "PostgreSQL is the primary relational database." | Stated without qualification; could be read as a constraint on the test environment. Django and the djng test suite default to SQLite. | REQUIREMENTS.md §1.4 | Qualify: "PostgreSQL is the primary relational database for the generated application in production. SQLite is acceptable for local development and automated tests." | Low |
| C7 | **No API-level versioning constraint — verify closed** | REQUIREMENTS.md §4.1: "The platform must not require API-level namespace versioning as the contract versioning mechanism." | Constraint is present. Verify alignment with ARCHITECTURE.md §8.3: "API contracts must be versioned, with versioning in the backend's responsibility." | — | Confirm alignment and close. | None — verify and close |
| C8 | **Repair loop cross-reference absent** | REQUIREMENTS.md §4.2.2: "Governed construction must support iterative inspection, repair, retry, and refinement…" | Correct in intent but no pointer to where the loop lives. With Option B resolved, the loop lives inside the SKILL agent session. | ARCHITECTURE.md §7.2; APP_BUILDER_REQUIREMENTS.md OQ5 (resolved) | Add a cross-reference from §4.2.2 to ARCHITECTURE.md §7.2 and APP_BUILDER_REQUIREMENTS.md OQ5. | Low |
| C9 | **Editorial note duplicates §1.1 purpose statement** | REQUIREMENTS.md §1 begins with an unlabelled "Separation of Concerns" editorial note. §1.1 then restates the SoC boundary. | Two statements of the same boundary in the same section; the editorial note reads as a draft artifact. | REQUIREMENTS.md §1, §1.1 | Remove the editorial note from §1 and consolidate into §1.1, or promote it to a named §1.1 sub-section. | Low |
| C10 | **ngdj testing requirements absent** | Not present in REQUIREMENTS.md. | ARCHITECTURE.md §3.5 states "Requirements for SKILLS and ngdj are derived from djng." §4.16 Verification Requirements does not name ngdj schematic outputs as a test surface. | REQUIREMENTS.md §4.16; ARCHITECTURE.md §3.5 | Add to §4.16 test-based verification: ngdj schematic outputs must be covered by end-to-end tests exercising a real Angular workspace fixture, not only the djng Python-side test suite. Feeds directly into §4 (Missing E2E Verification). | High — blocks E2E goal |

---

## 6. ARCHITECTURE.md — Option B Misalignment

Option B (resolved in APP_BUILDER_REQUIREMENTS.md OQ5): the Claude Code SDK call IS the repair/refinement loop. The agent running the SKILL is the loop controller. `build_app` makes one SDK call per procedure; the agent iterates natively until SKILL acceptance criteria are satisfied.

The following ARCHITECTURE.md passages were written before this model was settled and contradict it.

| Location | Current text | Problem | Resolution needed |
|---|---|---|---|
| §2.13 `agentic orchestration` | "The orchestrator… applies SKILLS as needed, **and iterates** toward a correct working application." | Iteration attributed to the outer orchestrator. Under Option B `build_app` traverses the procedure graph once; iteration lives inside the SKILL agent session. | Rewrite: the outer orchestrator applies SKILLS via SDK calls; convergence toward a correct application is achieved through the aggregate of SKILL agent sessions, each of which iterates internally. |
| §2.14 `SKILLS` | "Bounded construction units **used by** the agentic orchestrator." | Correct that SKILLS are invoked by the orchestrator; silent on the fact that each SKILL invocation is itself an agent session that runs the repair loop. | Add: each SKILL invocation is an agent session that iterates internally until SKILL-level acceptance criteria are satisfied. |
| §2.16 `angular-code-agent` | "It… **applies** SKILLS-based construction… and **drives** the system toward a correct working application." | "Drives toward" implies the outer orchestrator is the convergence engine. Under Option B the SKILL agent drives each procedure to convergence; `build_app` assembles the graph and fires SDK calls. | Rewrite: `build_app` / `angular-code-agent` constructs the procedure graph and invokes one SDK call per procedure; each SKILL agent drives its procedure to local acceptance; global correctness is verified by terminal procedures. |
| §3.3 djng-o-3 | "Converting change requirements into `prompts`" | "Prompts" predates the procedure-graph model. djng converts change requirements into a typed ChangeSet → procedure graph → SDK call inputs. | Replace "prompts" with "procedure graph inputs" or "SDK call inputs for each SKILL procedure." |
| §7.2 Repair and refinement loop steps 3–5 | "inspect emitted artifacts… repair, refine, or retry… continue iterating…" — all attributed to "the orchestrator." | Steps 3–5 describe the loop. Under Option B these steps happen inside the SKILL agent session. The outer orchestrator (`build_app`) does not inspect SKILL outputs and does not re-invoke SKILLS. | Reframe §7.2 to distinguish two scopes: (a) the outer orchestrator's responsibility — procedure graph traversal, one SDK call per node; (b) the SKILL agent's responsibility — inspect, repair, retry, iterate until local acceptance criteria are met. |
| §4.2.2 REQUIREMENTS.md | "The delivery process must support an agentically orchestrated control loop **with defined handoff artifacts** between schema generation, oasdiff change detection, client generation, UI assembly, and app integration." | "Defined handoff artifacts between stages" implies a structured pass-through. Under Option B the SKILL agent reads and writes the generated app directly via filesystem tools; there are no explicit artifacts passed between SDK calls. The procedure graph encodes dependencies, not artifacts. | Replace "defined handoff artifacts between stages" with language consistent with the procedure-graph dependency model and direct filesystem access by the SKILL agent. |

---

## 7. Success Criteria — Not Yet Specified

The most consequential gap. Without this, Option B is a statement of intent, not a guarantee. A SKILL agent session can end without meeting requirements. Local acceptance by each SKILL does not imply global correctness of the assembled application.

### 7.1 Failure modes for a SKILL agent session

| Failure mode | Mechanism | Consequence for build_app |
|---|---|---|
| Agent context exhaustion | Long repair loops fill the session context window | Session ends mid-work; partial output written to disk |
| Premature convergence | Agent judges acceptance criteria satisfied when they are not | SKILL returns "done"; defect silently passes through |
| Underspecified acceptance criteria | SKILL instructions do not define pass/fail precisely enough | Agent cannot evaluate completion; arbitrary termination |
| Tool / wrapper failure | ngdj schematic or djng wrapper errors consistently | Agent exhausts retries, surfaces error or partial output |
| SDK timeout | Session runs too long | Hard stop; no guarantee of rollback |
| Hallucination | Agent generates code that looks correct but has subtle bugs | Passes agent's own self-check; defect persists |

**Current gap**: `build_app` has no mechanism to detect that a SKILL agent ended without satisfying its acceptance criteria. It makes one SDK call per procedure and advances to the next node regardless.

### 7.2 Local vs. global correctness

Each SKILL agent verifies its own output against its own local acceptance criteria. Local satisfaction is necessary but not sufficient for global correctness. A representative failure chain:

```
ng-api   generates  OrderApiService.getOrder(id: number)
ng-data-service wraps it as  load(id: string)   ← locally valid TypeScript
ng-page  calls      dataService.load(route.params.id)  ← locally valid
```

Each agent declared "done." `ng_build` passes (TypeScript compiler accepts it). At runtime, a string is silently passed where a number is expected. No existing check catches this.

### 7.3 What must be specified

| Level | What it covers | Status | Blocking |
|---|---|---|---|
| **Per-SKILL acceptance criteria** (local) | For each of the eleven SKILLS: the exact conditions the SKILL agent must verify before declaring completion, the tools used to verify them, and what "done" means locally. Must be deterministic and evaluable with available tools (compile, lint, type-check, targeted test). | Not specified for any SKILL | Blocks SKILL authoring |
| **Global acceptance criteria** | The concrete tests the terminal procedure(s) in the procedure graph must pass to declare the generated app correct. Must cover: cross-SKILL interface consistency, backend contract / Angular client alignment, runtime smoke tests. ARCHITECTURE.md §2.17 defines "correct working application" but provides no concrete test that decides it. | Not specified | Blocks E2E verification |
| **Failure handling** | What `build_app` does when a SKILL agent ends without evidence of success: halt, retry the SDK call, surface a structured error, or roll back partial changes. | Not specified | Blocks build_app implementation |
| **Local-to-global gap coverage** | How the architecture ensures a set of locally-correct SKILL outputs also satisfies global correctness. Options: integration tests in the terminal procedure, a dedicated cross-SKILL consistency check, or a post-graph verification SKILL. | Not specified; architecture currently silent | Blocks E2E goal |

### 7.4 Where this must land

- **Per-SKILL acceptance criteria**: in each SKILL's `SKILL.md` instructions (during SKILL authoring, Plan phase).
- **Global acceptance criteria**: in `doc/REQUIREMENTS.md` §6.4 Mandatory Acceptance Scenarios (currently an empty header) and `doc/APP_BUILDER_REQUIREMENTS.md` §Functional Requirements (new FR for terminal verification).
- **Failure handling**: in `doc/APP_BUILDER_REQUIREMENTS.md` as a new functional requirement (FR-9 or similar).
- **Local-to-global gap**: architectural decision required; must be recorded in `doc/ARCHITECTURE.md` §7.2 or §7.3 and cross-referenced in `doc/APP_BUILDER_REQUIREMENTS.md`.
