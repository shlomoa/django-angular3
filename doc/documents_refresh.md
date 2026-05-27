# Documents Refresh — Validation Findings

Validation findings produced under the plan in
[document_validate_plan.md](document_validate_plan.md). Each finding is
actionable: file, lines, severity, what is wrong, why it matters, and the
concrete patch.

Severity scale: **Critical** (fix immediately, blocking correctness) →
**High** → **Medium** → **Low** (cosmetic / cleanup).

---

## Phase 1 — Master pair findings

Master pair: [ARCHITECTURE.md](ARCHITECTURE.md) +
[REQUIREMENTS.md](REQUIREMENTS.md).

### 1.1 External URL verification summary

All 22 external URLs cited in the master pair were fetched. Formal sources
were cross-checked against their GitHub repositories where applicable.

| # | URL | Status | Issue |
|---|---|---|---|
| 1 | https://www.djangoproject.com/ | 200 | None ✓ |
| 2 | https://github.com/django/django | 200, default `main`, pushed 2026-05-25 | Defined-not-cited |
| 3 | https://www.django-rest-framework.org/ | 200 | None ✓ |
| 4 | https://github.com/encode/django-rest-framework | 200, default `main`, pushed 2026-05-14 | Defined-not-cited |
| 5 | https://angular.dev/ | 200 | None ✓ |
| 6 | https://material.angular.dev/ | 200 | None ✓ |
| 7 | https://www.npmjs.com/package/angular-django2 | Package exists at v0.1.3 | ✓ |
| 8 | https://github.com/shlomoa/angular-django2 | 200, pushed 2026-05-04 | ✓ |
| 9 | https://pypi.org/project/django-angular3/ | Page renders; JSON API returns "Not Found" | **No published release** — `pip install django-angular3` would fail. Defined-not-cited. |
| 10 | https://github.com/shlomoa/django-angular3 | 200 | Defined-not-cited (self-reference) |
| 11 | https://www.npmjs.com/package/ng-openapi-gen | Package exists at v1.0.5 | ✓ |
| 12 | https://github.com/cyclosproject/ng-openapi-gen | 200, default `master`, pushed 2025-11-25 | ✓ |
| 13 | https://www.npmjs.com/ | 200 | ✓ |
| 14 | https://www.openapis.org/ | 200 | ✓ |
| 15 | https://spec.openapis.org/oas/v3.1.0.html | 200 | **3.1.0 superseded by 3.2.0.** Doc pins to a frozen older version. |
| 16 | https://drf-spectacular.readthedocs.io/en/latest/ | 200, active (v0.29.0, 2025-11-01) | Defined-not-cited |
| 17 | https://www.oasdiff.com/ | 200, supports OAS 3.0+3.1 (not yet 3.2) | ✓ |
| 18 | https://github.com/oasdiff/oasdiff | 200, pushed 2026-05-25 | Defined-not-cited |
| 19 | **https://platform.claude.com/docs/en/api/sdks/python** | 200 — **but this is the Anthropic Messages SDK, NOT the Claude Agent SDK** | **CRITICAL.** Cited URL is wrong SDK. Correct: `https://platform.claude.com/docs/en/agent-sdk/python` (307-redirects to `https://code.claude.com/docs/en/agent-sdk/python`). |
| 20 | https://github.com/anthropics/claude-agent-sdk-python | 200, pushed 2026-05-23. README confirms package is `claude-agent-sdk`, function is `query()` | Correct repo. **Label name "Claude Code Python SDK" is wrong** — formal product name is **"Claude Agent SDK"**. |
| 21 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration | 200, page title "Skill authoring best practices" | **WRONG SOURCE KIND for formal-definition role.** Best-practices pages should be used for examples, not formal definitions. |

### 1.2 Findings against `ARCHITECTURE.md`

#### A1 — §2.12 uses wrong product name and wrong SDK URL  ·  **Critical**

**Lines:** 62–64, 655

**What.** The section header is `### 2.12 [Claude Code API][Claude Code Python SDK]`. The body says "An API that allows developers to interact with the Claude AI assistant for coding tasks… Implementation and documentation of the Claude Code API Python SDK are available in [Claude Code Python SDK - GitHub]." The `[Claude Code Python SDK]` label (line 655) resolves to `https://platform.claude.com/docs/en/api/sdks/python` — the Anthropic Messages SDK page (`pip install anthropic`). The actual product used by `the agent` (§2.16) is the **Claude Agent SDK** (`pip install claude-agent-sdk`).

**Why.** Three product names for one product across the docs ("Claude Code API", "Claude Code Python SDK", "Claude Agent SDK"). The cited URL is the wrong SDK. Anyone following the link gets the wrong installation instructions. Violates SSOT and fresh-references rules.

**Patch.** Lines 62–64:
```diff
- ### 2.12 [Claude Code API][Claude Code Python SDK]
- An API that allows developers to interact with the Claude AI assistant for coding tasks. It can be used to automate code generation, refactoring, and other programming-related activities as part of the integration workflow between Django/DRF and Angular Material.
- Implementation and documentation of the Claude Code API Python SDK are available in [Claude Code Python SDK - GitHub].
+ ### 2.12 [Claude Agent SDK][Claude Agent SDK - Python]
+ Anthropic's official agent-construction SDK. The agent (§2.16) uses it to run each procedure as a guided agent session via `query()` calls. Installed as `pip install claude-agent-sdk`. Implementation repository: [Claude Agent SDK - Python - GitHub].
```

Lines 655–656:
```diff
- [Claude Code Python SDK]: https://platform.claude.com/docs/en/api/sdks/python
- [Claude Code Python SDK - GitHub]: https://github.com/anthropics/claude-agent-sdk-python
+ [Claude Agent SDK - Python]: https://platform.claude.com/docs/en/agent-sdk/python
+ [Claude Agent SDK - Python - GitHub]: https://github.com/anthropics/claude-agent-sdk-python
```

#### A2 — §2.14 uses best-practices page as formal SKILLS reference  ·  **High**

**Lines:** 73–76, 657

**What.** §2.14 cites `[SKILLS][Claude Skills]` where `[Claude Skills]` resolves to `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration` — the "Skill authoring best practices" page. The anchor `#evaluation-and-iteration` points to an iteration-process subsection.

**Why.** Per user clarification, formal definitions must cite formal sources; best-practices pages are for examples. The formal SKILLS sources are the overview page (concept) and the Claude Code / Agent SDK skills pages (format).

**Patch.** Line 657 — change one label, add three:
```diff
- [Claude Skills]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration
+ [Claude Skills]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
+ [Claude Code Skills]: https://code.claude.com/docs/en/skills
+ [Claude Agent SDK Skills]: https://code.claude.com/docs/en/agent-sdk/skills
+ [Claude Skills Best Practices]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
```

Lines 73–76 — expand to point to the right source for the right role:
```diff
- ### 2.14 [SKILLS][Claude Skills]
- Bounded AI skills that guide the agent within each guided agent session. Each SKILL encapsulates a constrained generation, modification, or integration capability used to create and glue application building blocks while remaining within architectural and contract-defined boundaries.
-
- SKILLS are a core architectural subsystem of `django-angular3`. Their subsystem architecture is defined in `doc/GENERATE_SKILLS.md`, and their implementation and authoring plan is defined in `doc/SKILL_AUTHORING_PLAN.md`. This document defines the role of SKILLS in the overall architecture and does not restate their internal design.
+ ### 2.14 [SKILLS][Claude Skills]
+ Bounded AI skills that guide the agent within each guided agent session. Each SKILL encapsulates a constrained generation, modification, or integration capability used to create and glue application building blocks while remaining within architectural and contract-defined boundaries.
+
+ The formal skill format is defined by Anthropic: see [Claude Skills] for the conceptual overview, [Claude Code Skills] for the CLI-facing reference (extended frontmatter, invocation control, dynamic context injection), and [Claude Agent SDK Skills] for SDK-side discovery and invocation. Authoring guidance is at [Claude Skills Best Practices].
+
+ SKILLS are a core architectural subsystem of `django-angular3`. Their subsystem architecture is defined in `doc/GENERATE_SKILLS.md`, and their implementation and authoring plan is defined in `doc/SKILL_AUTHORING_PLAN.md`. This document defines the role of SKILLS in the overall architecture and does not restate their internal design.
```

#### A3 — §20 has 7 defined-but-never-cited labels  ·  **Low**

**Lines:** 648, 651, 652, 654, 659, 661, 667

**What.** The following labels are defined but never referenced in the body of any reviewed doc: `[Django-github]`, `[django-angular3]`, `[django-angular3-github]`, `[ng-openapi-gen-github]`, `[oasdiff-github]`, `[DRF-github]`, `[drf-spectacular]`.

**Why.** Defining labels that nothing cites adds noise and creates SSOT confusion. Depends on **R4** because R4 merges `[ng-openapi-gen]` and `[ng-openapi-gen-github]` into a single label.

**Patch.** Cite `[drf-spectacular]` in §11.2 where OpenAPI export is discussed; delete the unused `-github` variants and the unreferenced `[django-angular3]` / `[django-angular3-github]` from §20.

Line ~511 (§11.2) add citation:
```diff
- - Any datamodel change creating a Django database migration file (after makemigrations) will force an OpenAPI schema extraction.
+ - Any datamodel change creating a Django database migration file (after makemigrations) will force an OpenAPI schema extraction via [drf-spectacular].
```

Lines 648–667 — delete unused (post-R4 state):
```diff
- [Django-github]: https://github.com/django/django
  [angular-django2]: https://www.npmjs.com/package/angular-django2
  [angular-django2-github]: https://github.com/shlomoa/angular-django2
- [django-angular3]: https://pypi.org/project/django-angular3/
- [django-angular3-github]: https://github.com/shlomoa/django-angular3
  [ng-openapi-gen]: https://github.com/cyclosproject/ng-openapi-gen
- [ng-openapi-gen-github]: https://github.com/cyclosproject/ng-openapi-gen
  ...
- [oasdiff-github]: https://github.com/oasdiff/oasdiff
  ...
- [DRF-github]: https://github.com/encode/django-rest-framework
  ...
```

#### A4 — `[OpenAPI 3.1 Specification]` pin is deliberate but toolchain compatibility is undocumented  ·  **Low–Med**

**Lines:** 56–57, 666

**What.** §2.10 defines the contract format as OpenAPI 3.1 with the URL `https://spec.openapis.org/oas/v3.1.0.html`. OAS 3.2 is now published. The doc does not state whether 3.1 is deliberate or stale, and does not document toolchain compatibility.

**Why.** Per user direction, 3.1 is the deliberate current choice and the compatibility (and incompatibility) of the toolchain with OAS versions must be explicitly documented. Verified component support:

| Component | Supported OAS versions | Source |
|---|---|---|
| `drf-spectacular` v0.29.0 (schema export) | "OpenAPI 3" — 3.0 family | PyPI summary, release 2025-11-01 |
| `oasdiff` (diff + breaking-change detection) | 3.0, 3.1 | oasdiff.com |
| `ng-openapi-gen` v1.0.5 (Angular client generation) | 3.0, 3.1 | repo README + package.json description |

No component currently advertises OAS 3.2 support.

**Patch.** Replace §2.10 with explicit compatibility documentation:
```diff
- ### 2.10 [OpenAPI contract - Schema][OpenAPI 3.1 Specification]
- The versioned OpenAPI schema exported from the DRF layer, serving as the source of truth for CRM-facing functionality and the basis for generating Angular integration artifacts.
+ ### 2.10 [OpenAPI contract - Schema][OpenAPI 3.1 Specification]
+ The versioned OpenAPI schema exported from the DRF layer, serving as the source of truth for CRM-facing functionality and the basis for generating Angular integration artifacts.
+
+ **Pinned to OpenAPI 3.1.** OAS 3.2 has been published by the OpenAPI Initiative but is not adopted here because the current toolchain does not support it:
+
+ | Component | Role | Supported OAS versions |
+ |---|---|---|
+ | [drf-spectacular] | DRF → OpenAPI schema export | "OpenAPI 3" (3.0 family) |
+ | [oasdiff] | schema diff and breaking-change detection | 3.0, 3.1 |
+ | [ng-openapi-gen] | OpenAPI → Angular client generation | 3.0, 3.1 |
+
+ The pin will be revisited if and when all three components advertise OAS 3.2 support.
```

#### A5 — §3.4 ngdj responsibility claims overstate current implementation status  ·  **Medium**

**Lines:** 163–169

**What.** ARCH §3.4 lists three responsibilities (`ngdj-o-1`, `ngdj-o-2`, `ngdj-o-3`) as already provided. Inspection of `shlomoa/angular-django2` at v0.1.3:

- **`ngdj-o-1` (workspace/app/project assembly schematics)** — confirmed. Schematics: `application`, `app-shell`, `component`, `project-structure`, `ng-app`, `material-setup`, `class`, `service`.
- **`ngdj-o-2` (OpenAPI-derived generation)** — partial. Schematics `ng-api` and `data-service` exist; OpenAPI consumption not documented as a current capability.
- **`ngdj-o-3` (non-CRM content generation)** — no evidence. No schematic addresses non-CRM content.

The repo README states: *"This repository is a work in progress although published to npm, it's not even alpha. The current state of the package is v0.1.3, pre-release."*

**Why.** ARCH §3.4 presents `ngdj-o-2` and `ngdj-o-3` as delivered. The repo's self-description and visible contents indicate these are target capabilities. Also aligns with CLAUDE.md: *"Do not assume that existing implementations in djng or ngdj are complete or correct… Requirements for ngdj are derived from djng development; the ngdj codebase is expected to evolve alongside skills work."*

**Patch.** Reframe §3.4 responsibilities as target capabilities with an explicit implementation-status line:
```diff
  ### 3.4 ngdj

  implemented in [angular-django2-github] and deployed to [angular-django2] npm package.

+ **Implementation status.** `ngdj` is at npm version 0.1.3 (pre-release; the project README describes it as "not even alpha"). The responsibilities below describe the target capability set this architecture requires; the gap between v0.1.3 and the target set evolves alongside `djng` skill authoring.
+
  - Purpose: A companion [Angular] ([npmjs] package) that provides the Angular-side construction substrate used to materialize required outputs.
- - Responsibilities:
+ - Responsibilities (target):
    - ngdj-o-1: Provide a set of commands for managing and assembling the Angular application, including workspace, project layout, application layout.
    - ngdj-o-2: Provide Angular schematics and code generation templates for generating Angular building blocks from OpenAPI contracts.
    - ngdj-o-3: Provide a set of Angular schematics and code generation templates for generating Angular building blocks from non-CRM content definitions.
```

### 1.3 Findings against `REQUIREMENTS.md`

#### R1 — Two competing reference structures (Appendix D + link-defs)  ·  **High**

**Lines:** 988–1007 (table) + 1009–1026 (link defs)

**What.** REQ ends with two parallel structures listing the same labels and targets — a markdown table (Appendix D) and a link-definitions block.

**Why.** Redundancy creates drift risk and violates SSOT.

**Patch.** Keep the link-defs block (required by markdown rendering). Reduce Appendix D to an annotated index that doesn't restate URLs.

```diff
- ### D. References
-
- | Label | Target | Kind |
- |---|---|---|
- | `[ARCHITECTURE.md]` | `ARCHITECTURE.md` | Internal document |
- ... (18 rows) ...
- | `[Claude Skills]` | `https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration` | External web reference |
+ ### D. References
+
+ External web references in this document mirror the canonical labels defined in `ARCHITECTURE.md` §20. Internal document links are listed below; URL definitions appear in the link-definitions block at the end of this file. When updating an external link, update both `ARCHITECTURE.md` §20 and this document's link-definitions block to keep them in sync.
+
+ | Internal label | Target |
+ |---|---|
+ | `[ARCHITECTURE.md]` | `ARCHITECTURE.md` |
+ | `[APP_BUILDER_REQUIREMENTS.md]` | `APP_BUILDER_REQUIREMENTS.md` |
+ | `[GENERATE_SKILLS.md]` | `GENERATE_SKILLS.md` |
+ | `[SKILL_AUTHORING_PLAN.md]` | `SKILL_AUTHORING_PLAN.md` |
+ | `[TEST_EXAMPLES.md]` | `TEST_EXAMPLES.md` |
+ | `[spec/examples/01_simple_crm/]` | `../spec/examples/01_simple_crm/` |
+ | `[spec/openapi/source/example.openapi.json]` | `../spec/openapi/source/example.openapi.json` |
+ | `[spec/ui/example.ui.json]` | `../spec/ui/example.ui.json` |
```

#### R2 — `[Claude Code Python SDK]` cascade from A1  ·  **Critical**

**Lines:** 933, 1005–1006, 1024–1025

**Patch.** Line 933:
```diff
- | **the agent** | The agentic orchestrator bundled in `djng`. At implementation level, driven by the [Claude Code Python SDK] (implementation repository: [Claude Code Python SDK - GitHub]). | `ARCHITECTURE.md` §2.16 |
+ | **the agent** | The agentic orchestrator bundled in `djng`. At implementation level, driven by the [Claude Agent SDK - Python] (implementation repository: [Claude Agent SDK - Python - GitHub]). | `ARCHITECTURE.md` §2.16 |
```

Lines 1024–1025:
```diff
- [Claude Code Python SDK]: https://platform.claude.com/docs/en/api/sdks/python
- [Claude Code Python SDK - GitHub]: https://github.com/anthropics/claude-agent-sdk-python
+ [Claude Agent SDK - Python]: https://platform.claude.com/docs/en/agent-sdk/python
+ [Claude Agent SDK - Python - GitHub]: https://github.com/anthropics/claude-agent-sdk-python
```

If R1 is applied, Appendix D rows at 1005–1006 are removed by R1's reshape.

#### R3 — `[Claude Skills]` cascade from A2  ·  **High**

**Lines:** 14, 1007, 1026

**Patch.** Line 1026:
```diff
- [Claude Skills]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration
+ [Claude Skills]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
```

#### R4 — `[ng-openapi-gen]` URL differs between ARCH and REQ  ·  **High**

**Lines:** REQ line 1023 vs ARCH line 653

**What.** Same label, different URLs:
- ARCH §20:653 → `https://www.npmjs.com/package/ng-openapi-gen`
- REQ line 1023 → `https://github.com/cyclosproject/ng-openapi-gen`

**Patch.** Update ARCH §20:653 to match (GitHub URL). REQ already has the correct URL.

#### R5 — §4.2.3 Swagger Studio parenthetical  ·  **Low**

**Lines:** 533

**Patch.**
```diff
- 1. A user designs or updates the OpenAPI specification in Swagger Studio
-    (SmartBear's API design tooling, historically associated with SwaggerHub)
+ 1. A user designs or updates the OpenAPI specification using SmartBear's
+    OpenAPI authoring tools (Swagger Studio or SwaggerHub)
```

#### R6 — Appendix C example artifacts verified  ·  **None**

**Lines:** 980–984. All cited paths exist. No patch.

### 1.4 Mutual alignment ARCH ↔ REQ

#### M1 — Three product names for one product  ·  **Critical**

**What.** Across the master pair: "Claude Code API", "Claude Code Python SDK", "Claude Agent SDK".

**Resolution.** Cascade of A1 + R2.

#### M2 — URL-def duplication between ARCH §20 and REQ link-defs  ·  **Medium**

**Patch.** Add sync-note at the top of REQ's link-defs block:
```diff
+ <!-- External URL labels below are mirrored from ARCHITECTURE.md §20 (the canonical reference table). When updating an external URL, update both files. Internal labels (other docs in this repo, spec/* paths) are owned by this file. -->
  [ARCHITECTURE.md]: ARCHITECTURE.md
  ...
```

#### M3 — ARCH §19 vs REQ Glossary product naming  ·  **Critical (sub-finding of M1)**

Resolved by A1 + R2 cascade.

#### M4 — REQ Glossary defers to ARCH §2.13 for "guided agent session"  ·  **None**

Correct deferral ✓.

#### M5 — All sampled REQ → ARCH cross-references resolve  ·  **None**

Verified §§1, 3, 7, 8.3, 11.1–11.4, 8.2–8.5, 10.2, 7.3, 9–10, 5, 14, 17, 17–18 ✓.

#### M6 — `oasdiff` and `ng-openapi-gen` aligned across the master pair  ·  **None**

ARCH §17 declares them; REQ §2.3 lists them. Consistent ✓.

### 1.5 Intra-doc SSOT findings

| # | Status |
|---|---|
| S1 | ARCH §19 condensed glossary intentionally duplicates §2 — ✓ no action |
| S2 | REQ Appendix A explicitly defers to ARCH §2 and §19 — ✓ no action |
| S3 | REQ internal URL-def duplication — see R1 |

### 1.6 Phase 1 summary

| ID | File | Severity | Title |
|---|---|---|---|
| **A1** | ARCH | Critical | §2.12 wrong SDK name + URL |
| **A2** | ARCH | High | §2.14 best-practices page used as formal SKILLS definition |
| **A3** | ARCH | Low | §20 dead labels (7 entries) |
| **A4** | ARCH | Low–Med | OpenAPI 3.1 pin — document toolchain compatibility |
| **A5** | ARCH | Medium | §3.4 ngdj responsibility claims overstate current implementation |
| **R1** | REQ | High | Two competing reference structures |
| **R2** | REQ | Critical | Cascade of A1 |
| **R3** | REQ | High | Cascade of A2 |
| **R4** | REQ vs ARCH | High | `[ng-openapi-gen]` URL mismatch |
| **R5** | REQ | Low | Swagger wording |
| **R6** | REQ | None | Examples verified ✓ |
| **M1** | both | Critical | Three product names — resolved by A1+R2 |
| **M2** | REQ | Medium | URL-def duplication of ARCH §20 |
| **M3** | both | Critical | Sub-finding of M1 |
| **M4–M6** | both | None | ✓ |
| **S1–S3** | each | None / see R1 | ✓ |

**Totals.** 11 actionable findings (5 ARCH + 5 REQ + 1 cross-cutting M2). M1 and M3 are descriptors of the same cross-doc consistency issue and are resolved by the A1+R2 cascade — they generate no separate patch. 5 Critical-or-High, 3 Medium / Low-Med, 3 Low. 0 deferred.

---

## Phase 2 — Downstream pair findings

Validated: [APP_BUILDER_REQUIREMENTS.md](APP_BUILDER_REQUIREMENTS.md) and
[GENERATE_SKILLS.md](GENERATE_SKILLS.md).

### 2.1 External URL verification — N/A

Neither downstream doc cites an external URL directly. Per the inheritance
model approved in Phase 1, external references inherit from the master pair
(`ARCHITECTURE.md` §20 + `REQUIREMENTS.md` link-defs). No URL-level finding
here; correctness of these inherited references is governed by Phase 1
patches A1/A2/R2/R3/R4.

### 2.2 Findings against `APP_BUILDER_REQUIREMENTS.md`

#### B1 — Line 122 vague REQ cross-reference  ·  **Low**

**Lines:** 122

**Patch.**
```diff
- This matches the contract normalization requirement in `REQUIREMENTS.md`.
+ This matches the contract normalization requirement in `REQUIREMENTS.md` §4.1.
```

### 2.3 Findings against `GENERATE_SKILLS.md`

#### G1 — `{{context:...}}` and `{{template:...}}` injection syntax does not exist  ·  **Critical**

**Lines:** 87–109 (definition of syntax), 209–214 (canonical template), and 11 skill sections that use the syntax (1296, 1712–1713, 1990, 2239, 2397, 3403, 4278, 4720, 5251, 5586, 5836).

**What.** §"Dynamic Context Injection" (lines 87–109) describes a substitution engine that replaces `{{context:filename.md}}` and `{{template:name.ts}}` with file contents at load time. No such mechanism exists.

**Why.** Per verified sources ([Claude Code Skills], [Claude Agent SDK Skills]): the real substitution mechanisms are `$ARGUMENTS`, `$N`, `$name`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`, and `` !`shell-command` ``. The `{{...}}` syntax has no parser. Progressive disclosure works through standard markdown links Claude reads via Read tool.

**Patch.** Rewrite §"Dynamic Context Injection" describing the real mechanisms. Replace every `{{context:...}}` and `{{template:...}}` across all 11 skills with standard markdown links.

```diff
- ## Dynamic Context Injection
-
- Skills can reference external context that gets injected at load time:
-
- ### Context File References
- ...
- {{context:filename.md}}
- ...
- ### Template References
- ...
- {{template:template-name.ts}}
- ...
+ ## Progressive disclosure of supporting files
+
+ Per the formal skill format ([Claude Code Skills]), SKILL.md preloads only its
+ YAML frontmatter into the session at startup. The body of SKILL.md loads when
+ the skill is invoked. Supporting files live on the filesystem and are read on
+ demand by Claude via the Read tool when SKILL.md links to them. Scripts in
+ `scripts/` are executed via Bash; their source is never loaded as context.
+
+ Reference supporting files using standard markdown links from SKILL.md. Keep
+ references one level deep to ensure Claude reads them in full:
+
+ ```markdown
+ ## Conventions
+ See [angular-conventions.md](../shared/angular-conventions.md) — read this before scaffolding.
+
+ ## Templates
+ - Component scaffold: [templates/component.ts.tpl](templates/component.ts.tpl) — read and adapt for the output file.
+ ```
+
+ For dynamic context injected at load time (CLI mode only), the formal mechanism
+ is shell-command interpolation via `` !`<command>` `` syntax. The SDK does not
+ perform this preprocessing — under SDK invocation Claude must use Bash explicitly.
```

Then in each of the 11 skill sections, replace `{{context:../../shared/<file>.md}}` with `[<file>](../shared/<file>.md)` and `{{template:<name>}}` with explicit instruction to read the template file from `templates/<name>`.

#### G2 — "Three Loading Levels" auto-injection model is inaccurate  ·  **High**

**Lines:** 65–85

**Patch.** Rewrite section to describe the real loading model:
```diff
- ## Three Loading Levels
- ...
- ### 1. Metadata Level (lowest cost)
- ...
- ### 2. Instructions Level (medium cost)
- ...
- ### 3. Resources Level (highest cost)
- ...
+ ## Skill loading model
+
+ At session start, the skill loader preloads only the YAML frontmatter (`name`,
+ `description`, `when_to_use`) of every discovered SKILL.md into the model's
+ context. When a skill is invoked — by the user typing `/<name>` in CLI mode, or
+ by `build_app` selecting it via `query(skills=[...])` in SDK mode — the SKILL.md
+ body loads. Supporting files (shared references, templates, scripts) live on the
+ filesystem and are read by Claude on demand via the Read tool when SKILL.md links
+ to them. Scripts are executed via Bash; their source is never loaded as context.
+
+ **Token strategy.** Keep SKILL.md body under ~500 lines (per [Claude Skills Best Practices]). Move detailed reference material into separate files in the same skill directory and link to them. Files that Claude does not need to read incur no token cost.
```

#### G3 — Canonical YAML frontmatter is incomplete and lacks dual-mode guidance  ·  **High**

**Lines:** 41–55, and the YAML blocks of all 11 skills.

**What.** Canonical frontmatter is incomplete and CLI-oriented. Missing: `when_to_use`, `disable-model-invocation`, `argument-hint`, `arguments`, `model`, `effort`, `paths`, `shell`, `agent`. Lacks dual-mode note about `allowed-tools` not being honored by SDK.

**Patch.**
```diff
  ## YAML Frontmatter

  Every `SKILL.md` file begins with YAML frontmatter that defines skill metadata:

  ```yaml
  ---
  name: <skill-name>
- description: <brief description of skill purpose>
+ description: <capability statement (third person, no I/you)>
+ when_to_use: <trigger conditions — "Use when build_app dispatches X, or when a user runs /<skill-name> to do Y">
  user-invocable: false
  context: fork
+ agent: <subagent-type if context: fork is set; usually general-purpose, Explore, or Plan>
  allowed-tools:
    - Read
    - Write
    - Edit
    - Bash
    - Grep
    - Glob
  ---
  ```
+
+ **Dual-mode requirement.** These skills are used both by direct CLI invocation
+ (a user types `/<skill-name>` in Claude Code) and by `build_app` via the
+ Claude Agent SDK (`query(skills=[...], allowedTools=[...])`). The `allowed-tools`
+ frontmatter field is honored by the CLI but **not** by the SDK — `build_app` must
+ mirror the same tool list in its `query()` `allowedTools` option. The canonical
+ tool list per skill in this document is the source of truth for both surfaces.
+ See [Claude Code Skills] and [Claude Agent SDK Skills] for the authoritative field
+ reference.
```

Then update each of the 11 skill YAML blocks (G6 covers this per-skill).

#### G4 — `openapi-integration.md` shared context violates the `oasdiff` ownership boundary  ·  **High**

**Lines:** 295 (description of shared context content); cross-references at 1020, 1941, 2056 are correctly aligned.

**Patch.** Rewrite line 295:
```diff
- - **oasdiff — schema diff and change detection**: Run `oasdiff` against the previous and current OpenAPI schema before any generation step. Breaking changes reported by `oasdiff` must be acknowledged or resolved before generation proceeds.
+ - **oasdiff — schema diff and change detection**: `oasdiff` is run by `build_app` during the Change Derivation phase, before any skill is invoked. Skills receive the resulting `ChangeSet` as procedure input (see `APP_BUILDER_REQUIREMENTS.md` §"Change Derivation"). Skills must **not** re-run `oasdiff`.
```

Apply the same change to the actual file at `skill_creation/shared/openapi-integration.md`.

#### G5 — "auto-invoked" language implies wrong invocation model  ·  **Medium**

**Lines:** 23, 1871.

**Patch.** Line 23:
```diff
- All skills in this document follow the **Agent Skills** format — reusable capabilities designed to be auto-invoked by an outer Claude API agent pipeline.
+ All skills in this document follow the **Agent Skills** format — reusable capabilities invoked explicitly by `build_app` via the Claude Agent SDK `query(skills=[...])` option, or by users via `/<skill-name>` in the Claude Code CLI.
```

Line 1871:
```diff
- description: Generate Angular API clients from OpenAPI specifications using ng-openapi-gen. Auto-invoked when the outer agent detects a need to generate or regenerate API service layer code from an OpenAPI schema.
+ description: Generate TypeScript API client code from an OpenAPI specification using ng-openapi-gen.
+ when_to_use: When build_app dispatches an api-generation procedure node (initial generation or schema-change regeneration), or when a user runs /ng-api to regenerate API clients after schema changes.
```

#### G6 — 11 skill descriptions lack `when_to_use` trigger language  ·  **High**

**Lines:** YAML `description:` lines at 1031, 1449, 1871, 2122, 2333, 2955, 3797, 4520, 4829, 5421, 5686.

**Patch.** Add a `when_to_use` field to every skill YAML. Per-skill text deferred to Phase 4. Example for `ng-workspace`:
```diff
  ---
  name: ng-workspace
  description: Create, modify, or delete an Angular Material workspace with modern conventions (standalone components, signals, SCSS theming)
+ when_to_use: When build_app dispatches a workspace-creation or workspace-modification procedure node, or when a user runs /ng-workspace to scaffold or update an Angular workspace from django-angular3.json.
  user-invocable: false
  context: fork
  ...
  ---
```

#### G7 — `ng-workspace` Delete mode backup inconsistency  ·  **Low**

**Lines:** 1270–1283 (Delete-mode Process), 1430–1442 (Example 3).

**What.** Process steps describe running the `ng_workspace_delete` wrapper only. Example 3 shows a tarball backup output. The Process does not create a backup.

**Patch.** Two options (pick one):

(a) Add a backup step to the Process:
```diff
  #### Process (Delete Mode)

+ 0. **Create backup tarball**:
+    ```bash
+    tar -czf <angular.output>-backup-$(date +%Y%m%d-%H%M%S).tar.gz <angular.output>
+    ```
  1. **Remove workspace via djng wrapper**:
     ...
```

(b) Remove the backup tarball from Example 3's output.

#### G8 — Skill Architecture section makes external-content claims without referencing master-pair formal sources  ·  **Medium**

**Lines:** 21–234 (Skill Architecture section).

**Patch.** Add a leading paragraph referencing the master-pair entries (after A2 lands):
```diff
  # Skill Architecture

+ The formal skill format used here is defined by Anthropic — see
+ `ARCHITECTURE.md` §20: [Claude Skills] (conceptual overview),
+ [Claude Code Skills] (CLI-side reference), and [Claude Agent SDK Skills]
+ (SDK-side discovery and invocation). This section describes the
+ project-specific application of that format; for the authoritative
+ skill-format reference, consult the upstream documents.

  All skills in this document follow the **Agent Skills** format ...
```

### 2.4 Cross-pair findings

#### X1 — Skill #5 name mismatch between APP_BUILDER and GENERATE_SKILLS  ·  **Critical**

**Files / lines:** `APP_BUILDER_REQUIREMENTS.md` line 213 vs `GENERATE_SKILLS.md` line 2332.

**What.** APP_BUILDER refers to skill #5 as `ng-small-field`; GENERATE_SKILLS YAML names it `ng-field-component`. Verified all 11 YAML names — only this one mismatches.

**Why.** SDK `query(skills=["ng-small-field"])` will fail to find the skill (filesystem skills keyed by YAML name = directory name).

**Patch.** Pick one canonical name (recommendation: `ng-field-component`, descriptive and distinct from `ng-form-field`):
```diff
  1  ng-workspace   (foundation)
  2  ng-app         (depends on 1)
  3  ng-api         (depends on 2)
  4  ng-data-service (depends on 3)
- 5  ng-small-field  (depends on 2)
+ 5  ng-field-component (depends on 2)
  6  ng-form-field   (depends on 2)
```

Apply replace_all `ng-small-field` → `ng-field-component` in `APP_BUILDER_REQUIREMENTS.md`.

#### X2 — `oasdiff` ownership boundary — see G4

Subsumed by G4.

### 2.5 Phase 2 summary

| ID | File | Severity | Title |
|---|---|---|---|
| **B1** | APP_BUILDER | Low | Line 122 vague REQ cross-reference (missing §4.1 pointer) |
| **G1** | GENERATE_SKILLS | Critical | `{{context:...}}` / `{{template:...}}` syntax does not exist |
| **G2** | GENERATE_SKILLS | High | "Three Loading Levels" auto-injection model is inaccurate |
| **G3** | GENERATE_SKILLS | High | Canonical YAML frontmatter incomplete; missing dual-mode guidance |
| **G4** | GENERATE_SKILLS | High | `openapi-integration.md` shared context violates `oasdiff` boundary |
| **G5** | GENERATE_SKILLS | Medium | "auto-invoked" language implies wrong invocation model |
| **G6** | GENERATE_SKILLS | High | 11 skill descriptions lack `when_to_use` trigger language |
| **G7** | GENERATE_SKILLS | Low | `ng-workspace` Delete-mode backup inconsistency |
| **G8** | GENERATE_SKILLS | Medium | Skill Architecture section makes claims without referencing master-pair formal sources |
| **X1** | both | Critical | Skill #5 name mismatch (`ng-small-field` vs `ng-field-component`) |
| **X2** | (G4) | — | Resolved by G4 |

**Totals.** 10 actionable findings in Phase 2 (1 APP_BUILDER B1 + 8 GENERATE_SKILLS G1–G8 + 1 cross-pair X1). X2 is fully subsumed by G4. 2 Critical, 4 High, 2 Medium, 2 Low.

---

## Phase 3 — Consolidated register

### 3.1 Flat enumeration of all findings  ·  `completed`

Every finding from Phases 1 and 2 in one flat list. Includes actionable
patches, verification entries (no patch but a cross-check required after
related patches apply), and verified entries (no action).

#### Phase 1 — Master pair

| ID | File | Severity | Title | Kind |
|---|---|---|---|---|
| A1 | ARCH | Critical | §2.12 wrong SDK name + URL | Patch |
| A2 | ARCH | High | §2.14 wrong SKILLS source; add [Claude Code Skills] + [Claude Agent SDK Skills] | Patch |
| A3 | ARCH | Low | §20 dead labels (7 entries) | Patch |
| A4 | ARCH | Low–Med | OpenAPI 3.1 pin — document toolchain compatibility | Patch |
| A5 | ARCH | Medium | §3.4 ngdj responsibility claims overstate current implementation | Patch |
| R1 | REQ | High | Two competing reference structures | Patch |
| R2 | REQ | Critical | Cascade of A1 | Patch |
| R3 | REQ | High | Cascade of A2 | Patch |
| R4 | REQ vs ARCH | High | `[ng-openapi-gen]` URL mismatch | Patch |
| R5 | REQ | Low | §4.2.3 Swagger Studio wording | Patch |
| R6 | REQ | None | Appendix C examples verified ✓ | Verified — no action |
| M1 | both | Critical | Three product names across master pair | Verification — resolved by A1+R2 |
| M2 | REQ | Medium | URL-def duplication between ARCH §20 and REQ link-defs | Patch |
| M3 | both | Critical | ARCH §19 vs REQ Glossary product naming | Verification — sub-finding of M1 |
| M4 | REQ | None | REQ Glossary correctly defers ✓ | Verified — no action |
| M5 | both | None | All sampled cross-refs resolve ✓ | Verified — no action |
| M6 | both | None | `oasdiff`/`ng-openapi-gen` aligned ✓ | Verified — no action |
| S1 | ARCH | None | §19 condensed glossary intentional ✓ | Verified — intentional |
| S2 | REQ | None | Appendix A intentional deferral ✓ | Verified — intentional |
| S3 | REQ | — | REQ URL-def duplication | Subsumed by R1 |

#### Phase 2 — Downstream pair

| ID | File | Severity | Title | Kind |
|---|---|---|---|---|
| B1 | APP_BUILDER | Low | Line 122 vague REQ cross-ref | Patch |
| G1 | GENERATE_SKILLS | Critical | `{{context:...}}` / `{{template:...}}` syntax does not exist | Patch |
| G2 | GENERATE_SKILLS | High | "Three Loading Levels" auto-injection model is inaccurate | Patch |
| G3 | GENERATE_SKILLS | High | Canonical YAML frontmatter incomplete; lacks dual-mode guidance | Patch |
| G4 | GENERATE_SKILLS | High | `openapi-integration.md` violates `oasdiff` boundary | Patch |
| G5 | GENERATE_SKILLS | Medium | "Auto-invoked" language is wrong invocation model | Patch |
| G6 | GENERATE_SKILLS | High | 11 skill descriptions lack `when_to_use` | Patch |
| G7 | GENERATE_SKILLS | Low | `ng-workspace` Delete-mode backup inconsistency | Patch |
| G8 | GENERATE_SKILLS | Medium | Skill Architecture section needs to reference master-pair sources | Patch |
| X1 | both | Critical | Skill #5 name mismatch (`ng-small-field` vs `ng-field-component`) | Patch |
| X2 | (G4) | — | `oasdiff` boundary cross-pair contradiction | Subsumed by G4 |

#### Roll-up

| Phase | Patch | Verification | Verified-no-action | Subsumed | Total entries |
|---|---|---|---|---|---|
| 1 | 11 (A1–A5, R1–R5, M2) | 2 (M1, M3) | 6 (R6, M4, M5, M6, S1, S2) | 1 (S3 → R1) | 20 |
| 2 | 10 (B1, G1–G8, X1) | 0 | 0 | 1 (X2 → G4) | 11 |
| **Combined** | **21 patches** | **2 verifications** | **6 verified** | **2 subsumed** | **31 entries** |

### 3.2 Severity tagging  ·  `completed`

Distribution of the 21 patch entries:

| Severity | Count | Patches |
|---|---|---|
| Critical | 4 | A1, R2, X1, G1 |
| High | 8 | A2, R3, R4, R1, G4, G2, G3, G6 |
| Medium | 4 | A5, M2, G5, G8 |
| Low–Med | 1 | A4 |
| Low | 4 | A3, R5, B1, G7 |
| **Total** | **21** | |

Plus 2 verification entries (M1, M3) recorded as one combined row "M1+M3"
in §5 of `document_validate_plan.md`.

### 3.3 Group findings by target file  ·  `completed`

| Target file | Patches | Other touch points |
|---|---|---|
| `doc/ARCHITECTURE.md` | A1, A2, A3, A4, A5, R4* | R4* also requires REQ-side verification (same `[ng-openapi-gen]` label) |
| `doc/REQUIREMENTS.md` | R1, R2, R3, R5, M2 | — |
| `doc/APP_BUILDER_REQUIREMENTS.md` | B1, X1 | X1 reconciles a name used in `GENERATE_SKILLS.md`; only `APP_BUILDER` is edited |
| `doc/GENERATE_SKILLS.md` | G1, G2, G3, G4*, G5, G6, G7, G8 | G4* also edits `skill_creation/shared/openapi-integration.md` |

**Edit cluster sizes:**

- `ARCHITECTURE.md` — 6 edits (A1, A2, A3, A4, A5, R4). Largest by cluster.
- `GENERATE_SKILLS.md` — 8 edits (G1–G8). Largest by count; G1 alone touches the canonical template + 11 skill sections.
- `REQUIREMENTS.md` — 5 edits (R1, R2, R3, R5, M2). R1 is the largest single edit (Appendix D restructure).
- `APP_BUILDER_REQUIREMENTS.md` — 2 edits (B1, X1).

### 3.4 Cascade dependencies  ·  `completed`

**Group 1: master-pair SDK rename**
```
A1 ─→ R2
   └→ (verify M1, M3 after both apply)
```

**Group 2: master-pair SKILLS source labels**
```
A2 ─→ R3
   ├→ G2
   ├→ G3 ─→ G6
   └→ G8
```

**Group 3: master-pair ng-openapi-gen URL**
```
R4 ─→ A3
```

**Independent patches (no incoming dependencies):**

A1, A2, R1, R4, A4, A5, M2, X1, G1, G4, G5, G7, B1, R5

#### Verification entries

- **M1** + **M3** — Cross-check after Group 1: grep the master pair for stale occurrences of "Claude Code API" or "Claude Code Python SDK". Both findings are resolved when grep returns nothing.
- **X2** — Subsumed by G4.

### 3.5 Global apply-order — ratified  ·  `completed`

The merged ordering in [`document_validate_plan.md` §5](document_validate_plan.md)
was cross-checked against:

| Check | Result |
|---|---|
| All 21 patches present + 1 verification row | ✓ 22 rows total in §5 |
| Critical entries (4) before High | ✓ rows 1, 2, 4, 5 |
| High (8) before Medium | ✓ rows 6–13 |
| Medium (4) before Low–Med | ✓ rows 14–17 |
| Low–Med (1) before Low | ✓ row 18 |
| Low (4) at the end | ✓ rows 19–22 |
| Dependency edges satisfied | ✓ A1<R2; A2<{R3,G2,G3,G6,G8}; G3<G6; R4<A3 |
| Verification row positioned after both inputs | ✓ M1+M3 row at #3 after A1#1 and R2#2 |
| No finding double-counted | ✓ M1+M3 single row, X2 absent (subsumed by G4) |

The ordering in §5 is **ratified** as the apply-order for Phase 4.

#### File-level edit-session sequence

If Phase 4 prefers grouping by file:

1. **`ARCHITECTURE.md`** first (A1 unblocks R2; A2 unblocks R3, G2, G3, G6, G8; R4 unblocks A3).
2. **`REQUIREMENTS.md`** next (R1, R2, R3, R5, M2).
3. **`APP_BUILDER_REQUIREMENTS.md`** (B1, X1).
4. **`GENERATE_SKILLS.md`** last (G1–G8; G2/G3/G6/G8 depend on A2 already landed).
5. **`skill_creation/shared/openapi-integration.md`** in tandem with G4.

Within each file, apply in §5 order. Run the M1+M3 verification grep after step 2.

### 3.6 Phase 3 deliverable — ratified register  ·  `completed`

The ratified apply-order lives in
[`document_validate_plan.md` §5](document_validate_plan.md). User signed off
on the Phase 3 register. Phase 4 (patch application) is now `pending` — awaiting
explicit direction to begin and per-patch approval per the operating rules.

---

## Phase 4 — Applied patches log

**Status:** `pending` — Phase 3 sign-off received. Awaiting direction to start patch application; per-patch approval still required.

Phase 4 will record each applied patch (file, finding ID, commit reference)
and any follow-up issues discovered during application.
