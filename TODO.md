# Open Items — djng/ngdj

Generated: 2026-06-14. Items are ordered by implementation sequence. Status is
shown for each item.

---

## 1. Non-CRM UI Input Format: Requirement Not Defined

**Status: Blocked — Top Priority**

The generated app's configuration file (placeholder: `<project>.project.json`)
defines the UI artifacts — pages, components, forms — used for non-CRM change
detection. Its schema and final file name are not yet defined. Non-CRM change
detection cannot be implemented until this is resolved. When resolved, also add
a sentence to `REQUIREMENTS.md` §4.2.2 naming the non-CRM content stage as a
discrete governed construction stage (currently absent from §4.2.2; covered by
`ARCHITECTURE.md` §7.1 stage 4).

| | |
|---|---|
| **Options** | Define the JSON schema and the final file name for the generated app config file. |
| **Origin** | `APP_BUILDER_REQUIREMENTS.md` §Inputs, §Change Derivation; `ARCHITECTURE.md` §7.1 stage 4; `REQUIREMENTS.md` §4.2.2 |
| **Input sources** | `spec/ui/`, `django_angular3/validation.py` |

---

## 2. Derive Angular-Django2 Capabilities and Wrappers

**Status: In progress**

Derive the complete set of `angular-django2` capabilities and `djng` command
wrappers needed to materialize the required Angular-side outputs.

- Wrappers implemented: `ng_new`, `ng_workspace`, `ng_add`, `ng_config`,
  `ng_gen_app`, `ng_openapi_gen`, `ng_build`, `ng_workspace_delete`,
  `ng_workspace_modify`.
- `ng_workspace` now represents the upstream-aligned empty-workspace bootstrap
  flow: `ng new` + workspace defaults + `ng add angular-django2` +
  `ng generate angular-django2:ng-workspace`.
- Broader repository docs under `doc/` still need wording alignment where they
  describe workspace creation as `ng_new`-first rather than the composite
  `ng_workspace` flow.
- Complete derivation aligned with all 11 SKILLS not yet done.

---

## 3. Revise and Finalize GENERATE_AI_AUTOMATIONS.md

**Status: Substantially complete**

Revise and finalize `GENERATE_AI_AUTOMATIONS.md` as the design specification
for the complete AI automation model needed for bounded construction and
integration, covering SKILLS, TOOLS, HOOKS, and PLUGINS.

- Revise `doc/GENERATE_AI_AUTOMATIONS.md` to define primitive boundaries and
  selection policy across SKILLS, TOOLS, HOOKS, and PLUGINS.
- Keep the `skill_creation` folder aligned with the skills subset of
  `doc/GENERATE_AI_AUTOMATIONS.md`, with detailed descriptions and example
  prompts for each SKILL.
- Keep SKILL dependencies, shared context expectations, templates, invocation
  boundaries, and mixed automation execution-model references aligned with
  `doc/GENERATE_AI_AUTOMATIONS.md`, `doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md`, and
  `doc/SKILL_AUTHORING_PLAN.md`.
- `GENERATE_AI_AUTOMATIONS.md` now carries normative per-capability catalogs for
  all four primitives (Tool Contracts, Hook Contracts, Plugin Contracts, Skills)
  alongside the primitive-selection policy; the umbrella framing no longer
  treats SKILLS as the only detailed family. `skill_creation` skill frontmatter
  (`description`, `when_to_use`) is aligned with the authoritative SKILLS subset.

---

## 4. OpenAPI Schema Extraction and Breaking-Change Gate

**Status: Substantially implemented**

Implement the OpenAPI schema extraction, contract normalization, and
breaking-change gate on the Django/DRF side.

- oasdiff integration, breaking-change detection, and breaking-change gate
  implemented in `build_app.py`.
- Schema extraction via `drf-spectacular` is the consuming Django project's
  responsibility.

---

## 5. djng Generator Entry Points and Wrappers

**Status: Substantially implemented**

Implement the `djng` generator app entry points and the governed wrappers around
`ngdj` actions used for workspace, app, contract-derived, and non-CRM
construction.

- All current workspace/app/contract wrappers implemented, including the
  explicit `ng_workspace` bootstrap wrapper aligned with the upstream
  `angular-django2:ng-workspace` schematic. Non-CRM construction wrappers
  depend on item 1 (MR1).

---

## 6. app-builder Change Detection and Plan Emission

**Status: Partially implemented**

Implement app-builder change detection, change classification, and deterministic
build-plan emission from current and previous schema/config inputs.

- Schema change detection, classification (start-from-scratch, add-things,
  remove-things, replace-things, breaking), and plan emission implemented in
  `build_app.py`.
- Start-from-scratch workspace steps now emit `ng_workspace` so build plans use
  the same upstream-aligned workspace bootstrap contract as the CLI wrappers.
- Config change detection covers only project rename; pages, components, and
  forms change detection not implemented (blocked by item 1).
- Plan currently emits CLI command strings. Must be replaced with SDK call
  specs (procedure graph) once item 8 is underway.
- Example 1 input files now exist at `django_angular3/examples/01_simple_crm/` (see item 9);
  examples 2–6 still need their own input files before scenarios 2–6 can be verified.

---

## 7. Create SKILLS

**Status: Not started**

Author each of the eleven SKILLS using the per-skill cadence defined in
`doc/SKILL_AUTHORING_PLAN.md`: plan, implementation including tests, app-builder
procedure integration, and verification.

Per-SKILL acceptance criteria must be defined during the Plan phase of each
SKILL — the exact conditions the agent must verify before declaring a procedure
complete, the tools used to verify them, and what "done" means locally. Without
this, the agent cannot evaluate completion and may terminate arbitrarily.

| Failure mode | Mechanism | Consequence |
|---|---|---|
| Premature convergence | Agent judges acceptance criteria satisfied when they are not | Defect silently passes through |
| Underspecified acceptance criteria | SKILL instructions do not define pass/fail precisely enough | Arbitrary termination |
| Tool / wrapper failure | ngdj schematic or djng wrapper errors consistently | Agent exhausts retries, surfaces partial output |
| Hallucination | Agent generates code that looks correct but has subtle bugs | Passes agent's own self-check; defect persists |

---

## 8. Implement Orchestration Flow

**Status: Not started**

Implement the iterative orchestration flow using the Claude Code Python SDK, so
construction can invoke the agent with SKILLS enabled until acceptance conditions
are satisfied.

Failure handling must be specified: what `build_app` does when the agent ends
without evidence of success — halt, retry the SDK call, surface a structured
error, or roll back partial changes. Currently unspecified; blocks
`build_app` implementation.

| Failure mode | Mechanism | Consequence |
|---|---|---|
| Agent context exhaustion | Long repair loops fill the session context window | Session ends mid-work; partial output written to disk |
| SDK timeout | Session runs too long | Hard stop; no guarantee of rollback |

`build_app` currently has no mechanism to detect that the agent ended without
satisfying its acceptance criteria. It makes one SDK call per procedure and
advances to the next node regardless.

---

## 9. Automated Verification

**Status: Not started**

Add automated verification across contract checks, construction-output checks,
integration checks, and test-based verification.

### 9.1 Example Input Files

The six scenarios in `doc/TEST_EXAMPLES.md` require input files for each example.
Example 1 is now bundled in the package at `django_angular3/examples/01_simple_crm/`.
Examples 2–6 still need their input files under `spec/examples/<example-name>/`.

| Example | Location | Status |
|---|---|---|
| 1 Simple CRM | `django_angular3/examples/01_simple_crm/` | ✓ exists |
| 2 Add Resource | `spec/examples/02-add-order/` | missing |
| 3 Breaking Change | `spec/examples/03-breaking-change/` | missing |
| 4 Config Change | `spec/examples/04-add-dashboard/` | missing; blocked by item 1 (MR1) |
| 5 Combined | `spec/examples/05-combined-change/` | missing |
| 6 Replace Resource | `spec/examples/06-replace-resource/` | missing |

Example 1 is runnable. Examples 2, 3, 5, and 6 are unblocked pending their files. Example 4 depends on item 1.

### 9.2 E2E Verification Specification Missing

| Aspect | Current state | What is missing | Why it matters |
|---|---|---|---|
| Terminal procedure | `ng_build` is the final verification procedure in the procedure graph. | `ng_build` only confirms the Angular app compiles. It does not verify backend API / Angular client alignment, runtime integration, or business-logic correctness. | A build that compiles is not the same as a working integrated application. |
| Backend/frontend alignment | REQUIREMENTS.md §4.2.2 requires "alignment between backend behavior, generated Angular integration artifacts, and frontend composition." | No specification of how this alignment is verified programmatically. | Alignment can silently break when the OpenAPI schema diverges from the running backend. |
| Full-stack E2E test spec | REQUIREMENTS.md §4.16 defines four verification categories. | None has a concrete acceptance test specification. §6.4 Mandatory Acceptance Scenarios header exists but content is not populated. | No pass/fail criterion beyond "Angular compiled." |
| ngdj test surface | ngdj schematics are not tested by the djng test suite. | No specification for how SKILL-generated ngdj outputs are tested against a real Angular workspace. | Correctness of the generated Angular application depends on ngdj schematic outputs, which are currently unverified. |

### 9.3 Global Acceptance Criteria Not Specified

Local acceptance by each SKILL does not imply global correctness. A
representative failure chain:

```
ng-api          generates  OrderApiService.getOrder(id: number)
ng-data-service wraps it as load(id: string)   ← locally valid TypeScript
ng-page         calls      dataService.load(route.params.id)  ← locally valid
```

Each agent declared "done." `ng_build` passes. At runtime, a string is silently
passed where a number is expected. No existing check catches this.

Global acceptance criteria must cover: cross-SKILL interface consistency,
backend contract / Angular client alignment, and runtime smoke tests.
`ARCHITECTURE.md` §2.17 defines "correct working application" but provides no
concrete test that decides it.

Where this must land:
- **Global acceptance criteria**: `doc/REQUIREMENTS.md` §6.4 (currently empty)
  and `doc/APP_BUILDER_REQUIREMENTS.md` §Functional Requirements (new FR for
  terminal verification).
- **Failure handling**: `doc/APP_BUILDER_REQUIREMENTS.md` as a new functional
  requirement.
- **Local-to-global gap**: architectural decision required; must be recorded in
  `doc/ARCHITECTURE.md` §7.2 or §7.3.

---

## 10. Build One Business Module End to End

**Status: Not started**

Build one business module end to end using the generator app, app builder,
SKILLS, and wrappers together.

---

## 11. Audit Logging, Health Checks, and Staging Smoke Tests

**Status: Not started**

Add audit logging, health checks, generator verification, and staging smoke
tests.

---

## 12. Architecture Alignment: Tools, Hooks, Skills, Plugins

**Status: Not started**

Incorporate the architectural recommendations captured in
`doc/TOOLS_HOOKS_SKILLS_ANALYSIS.md` into implementation planning and design
docs. This item feeds item 3 so `doc/GENERATE_AI_AUTOMATIONS.md` becomes the
umbrella design spec for the full automation model rather than SKILLS alone.

- Convert deterministic construction and contract operations currently treated
  as SKILL/script responsibilities into explicit tool contracts (for example:
  schema export, schema diff, contract validation, and Angular/client generation
  wrappers).
- Add lifecycle enforcement points as hooks for gates and mandatory side
  effects (for example: breaking-change gate, migration-triggered schema export,
  pre-construction contract validation, post-run verification logging,
  session-stop archiving/audit).
- Define packaging boundaries for reusable capability bundles (plugin-oriented
  grouping), including:
  - djng Angular construction capability bundle
  - ngdj scaffold capability bundle
  - contract lifecycle capability bundle
- Document primitive-selection policy (Skill vs Tool vs Hook vs Plugin) in
  architecture/requirements docs so new capabilities are categorized
  consistently.
- Derive a phased implementation plan with acceptance criteria for the above,
  including test and verification coverage updates where behavior moves from
  AI-guided flow to deterministic tool/hook enforcement.
