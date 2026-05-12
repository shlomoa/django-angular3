# Open Items — djng/ngdj Documentation

Generated: 2026-05-11. All items below are open unless marked **Resolved**.

---

## 1. Missing Requirement Definitions

| # | Item | Detail | Options / proposals | Origin | Input sources |
|---|---|---|---|---|---|
| MR1 | **⚠️ TOP PRIORITY — Generated app config file: schema and name not defined** | The generated app's configuration file (placeholder: `<project>.project.json`) defines the UI artifacts — pages, components, forms — used for non-CRM change detection. Its schema and final file name are not yet defined. Non-CRM change detection cannot be implemented until this is resolved. When resolved, also add a sentence to `REQUIREMENTS.md` §4.2.2 naming the non-CRM content stage as a discrete governed construction stage (currently absent from §4.2.2; covered by `ARCHITECTURE.md` §7.1 stage 4). | Define the JSON schema and the final file name for the generated app config file. | `APP_BUILDER_REQUIREMENTS.md` §Inputs, §Change Derivation; `ARCHITECTURE.md` §7.1 stage 4; `REQUIREMENTS.md` §4.2.2 | `spec/ui/`, `django_angular3/validation.py` |

---

## 2. `spec/examples/` Input Files Missing

The six scenarios in `doc/TEST_EXAMPLES.md` reference input files under
`spec/examples/<example-name>/` — `schema.yaml`, `django-angular3.json`, and
where applicable `previous-schema.yaml`, `previous-config.json`, and `ui.json`.
None of these files exist. The examples cannot be run even with `--dry-run`
until the input files are created.

| Example | Files needed | Blocked by |
|---|---|---|
| 1 Simple CRM | `schema.yaml`, `django-angular3.json`, `ui.json` | — |
| 2 Add Resource | `schema.yaml`, `django-angular3.json` | Example 1 files |
| 3 Breaking Change | `schema.yaml`, `django-angular3.json` | Example 1 files |
| 4 Config Change | `django-angular3.json` with inline `ui.pages`/`ui.components` | MR1 |
| 5 Combined | `schema.yaml`, `django-angular3.json` | Example 2 files |
| 6 Replace Resource | `schema.yaml`, `django-angular3.json` | Example 2 files |

Examples 1, 2, 3, 5, and 6 are unblocked. Example 4 depends on MR1.

Prerequisite for `IMPLEMENTATION_PLAN.md` item 10.

---

## 3. Missing E2E Verification Specification

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

## 4. Success Criteria — Not Yet Specified

The most consequential gap. Without this, Option B is a statement of intent, not a guarantee. A SKILL agent session can end without meeting requirements. Local acceptance by each SKILL does not imply global correctness of the assembled application.

### 4.1 Failure modes for a SKILL agent session

| Failure mode | Mechanism | Consequence for build_app |
|---|---|---|
| Agent context exhaustion | Long repair loops fill the session context window | Session ends mid-work; partial output written to disk |
| Premature convergence | Agent judges acceptance criteria satisfied when they are not | SKILL returns "done"; defect silently passes through |
| Underspecified acceptance criteria | SKILL instructions do not define pass/fail precisely enough | Agent cannot evaluate completion; arbitrary termination |
| Tool / wrapper failure | ngdj schematic or djng wrapper errors consistently | Agent exhausts retries, surfaces error or partial output |
| SDK timeout | Session runs too long | Hard stop; no guarantee of rollback |
| Hallucination | Agent generates code that looks correct but has subtle bugs | Passes agent's own self-check; defect persists |

**Current gap**: `build_app` has no mechanism to detect that a SKILL agent ended without satisfying its acceptance criteria. It makes one SDK call per procedure and advances to the next node regardless.

### 4.2 Local vs. global correctness

Each SKILL agent verifies its own output against its own local acceptance criteria. Local satisfaction is necessary but not sufficient for global correctness. A representative failure chain:

```
ng-api   generates  OrderApiService.getOrder(id: number)
ng-data-service wraps it as  load(id: string)   ← locally valid TypeScript
ng-page  calls      dataService.load(route.params.id)  ← locally valid
```

Each agent declared "done." `ng_build` passes (TypeScript compiler accepts it). At runtime, a string is silently passed where a number is expected. No existing check catches this.

### 4.3 What must be specified

| Level | What it covers | Status | Blocking |
|---|---|---|---|
| **Per-SKILL acceptance criteria** (local) | For each of the eleven SKILLS: the exact conditions the SKILL agent must verify before declaring completion, the tools used to verify them, and what "done" means locally. Must be deterministic and evaluable with available tools (compile, lint, type-check, targeted test). | Not specified for any SKILL | Blocks SKILL authoring |
| **Global acceptance criteria** | The concrete tests the terminal procedure(s) in the procedure graph must pass to declare the generated app correct. Must cover: cross-SKILL interface consistency, backend contract / Angular client alignment, runtime smoke tests. ARCHITECTURE.md §2.17 defines "correct working application" but provides no concrete test that decides it. | Not specified | Blocks E2E verification |
| **Failure handling** | What `build_app` does when a SKILL agent ends without evidence of success: halt, retry the SDK call, surface a structured error, or roll back partial changes. | Not specified | Blocks build_app implementation |
| **Local-to-global gap coverage** | How the architecture ensures a set of locally-correct SKILL outputs also satisfies global correctness. Options: integration tests in the terminal procedure, a dedicated cross-SKILL consistency check, or a post-graph verification SKILL. | Not specified; architecture currently silent | Blocks E2E goal |

### 4.4 Where this must land

- **Per-SKILL acceptance criteria**: in each SKILL's `SKILL.md` instructions (during SKILL authoring, Plan phase).
- **Global acceptance criteria**: in `doc/REQUIREMENTS.md` §6.4 Mandatory Acceptance Scenarios (currently an empty header) and `doc/APP_BUILDER_REQUIREMENTS.md` §Functional Requirements (new FR for terminal verification).
- **Failure handling**: in `doc/APP_BUILDER_REQUIREMENTS.md` as a new functional requirement (FR-9 or similar).
- **Local-to-global gap**: architectural decision required; must be recorded in `doc/ARCHITECTURE.md` §7.2 or §7.3 and cross-referenced in `doc/APP_BUILDER_REQUIREMENTS.md`.

---
