# Document Validation Plan

## 1. Purpose

Procedure for validating the `doc/` documentation set against the operating
rules in `.github/copilot-instructions.md`, and for refreshing those documents
where they have drifted from their canonical sources.

The end goal is correct, up-to-date, coherent documentation:

- Fresh and updated references (each cited URL resolves and points at a source
  of the correct kind — formal source for formal definitions, best-practices
  pages only for examples).
- Single source of truth (definitions live in exactly one place; downstream
  docs reference, not redefine).
- Alignment with the master pair (`ARCHITECTURE.md` + `REQUIREMENTS.md`).
- Alignment with external documentation (cross-checked with GitHub latest for
  formal sources).

## 2. Scope

Four documents in `doc/`, validated in this order:

1. **Master pair** — `ARCHITECTURE.md` and `REQUIREMENTS.md`, validated
   together. Authoritative for definitions and external references.
2. **Downstream pair** — `APP_BUILDER_REQUIREMENTS.md` and
   `GENERATE_SKILLS.md`. Inherit from the master pair; must reference (not
   redefine) shared content.

Out of scope unless explicitly requested:

- `SKILL_AUTHORING_PLAN.md`, `TEST_EXAMPLES.md`
- `CLAUDE.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`
- `skill_creation/` working files
- Implementation code under `django_angular3/`

## 3. Validation criteria per document

Every document is validated against three criteria:

- **A. Repo rules:** fresh references, single source of truth.
- **B. Alignment with the master pair** (skipped for the master pair itself;
  for the master pair this becomes mutual alignment between ARCH and REQ).
- **C. Alignment with external documentation** as cited in the document's
  reference table. Formal sources verified against GitHub latest;
  best-practices pages flagged when used in a formal-definition role.

## 4. Phases

### Phase 0 — Discovery `[completed]`

Read all four documents and build a working index before any validation.

| # | Sub-step |
|---|---|
| 0.1 | Read each document fully (or via grep for the very large ones). |
| 0.2 | Extract each document's section structure. |
| 0.3 | Extract each document's reference table and external URL set. |
| 0.4 | Build the union of external URLs across the four documents. |
| 0.5 | Map cross-references between documents. |
| 0.6 | Identify documents with no reference table — confirm those expect to inherit from the master pair rather than own their own. |
| 0.7 | Report findings and stop for approval. |

**Deliverable:** Phase 0 report (see §6 of this file for status).

### Phase 1 — Validate master pair `[completed]`

Validate `ARCHITECTURE.md` and `REQUIREMENTS.md` against criteria A, B, C.

| # | Sub-step | Urgency |
|---|---|---|
| 1.1 | Verify every external URL (criterion C): live, correct kind for its role, content still supports the doc's claim. Cross-check formal definitions with GitHub latest. | High |
| 1.2 | Verify every internal cross-reference (§ numbers, file paths). | High |
| 1.3 | Identify duplicate/redundant reference structures within each doc. | High |
| 1.4 | Identify defined-but-never-cited reference labels. | Low |
| 1.5 | Identify inconsistent product names, terminology, or URL targets across the two docs. | Critical |
| 1.6 | Verify ARCH and REQ glossaries defer to each other consistently. | Medium |
| 1.7 | Produce findings report with patches (file, lines, what, why, old text, new text). | High |
| 1.8 | Stop for approval before Phase 2. | — |

**Deliverable:** Phase 1 findings in `documents_refresh.md` §Phase 1.

### Phase 2 — Validate downstream pair `[completed]`

Validate `APP_BUILDER_REQUIREMENTS.md` and `GENERATE_SKILLS.md` against
criteria A, B, C, and against each other.

| # | Sub-step | Urgency | Status |
|---|---|---|---|
| 2.1 | Confirm absence of reference tables (per the inheritance model). | High | `completed` — neither has a reference table; both rely on inline plain-text references to master pair files. |
| 2.2 | Verify every internal cross-reference, especially ARCH/REQ refs. | High | `completed` — all sampled refs resolve. |
| 2.3 | Identify content in downstream docs that **redefines** master-pair content rather than referencing it. | Critical | `completed` — both glossaries follow the intentional inheritance pattern (defer to ARCH §2/§19, add only scope-specific terms `ChangeSet`, `<project>.project.json`). |
| 2.4 | Identify product-name or terminology drift from the master pair (e.g., "Claude Code API" vs "Claude Agent SDK"). | Critical | `completed` — both downstream docs already use the correct "Claude Agent SDK" name; mismatch is in the master pair (covered by A1+R2). One cross-pair name mismatch found: see X1. |
| 2.5 | Cross-check `GENERATE_SKILLS.md` skill-format claims against the formal Claude Skills sources identified in Phase 1 finding A2. | Critical | `completed` — findings G1, G2, G3, G6, G8 captured. |
| 2.6 | Identify contradictions between `APP_BUILDER_REQUIREMENTS.md` and `GENERATE_SKILLS.md` (e.g., `oasdiff` ownership boundary). | High | `completed` — X1 (skill name mismatch), G4 (oasdiff boundary). |
| 2.7 | Identify any external URLs cited in downstream docs that should be promoted to the master pair's reference table. | Medium | `completed` — downstream docs cite no external URLs directly; everything inherits from master pair via plain-text references. |
| 2.8 | Produce findings report with patches. | High | `completed` — see `documents_refresh.md` Phase 2. |
| 2.9 | Stop for approval before Phase 3. | — | `completed` — user approved Phase 3 start. |

**Deliverable:** Phase 2 findings in `documents_refresh.md` §Phase 2.

### Phase 3 — Consolidated register `[completed]`

Merge Phase 1 and Phase 2 findings into one actionable register.

| # | Sub-step | Urgency | Status |
|---|---|---|---|
| 3.1 | Collect every finding from Phases 1 and 2 in one list. | Medium | `completed` — 31 entries enumerated (21 patches + 2 verifications + 6 verified-no-action + 2 subsumed). See `documents_refresh.md` §3.1. |
| 3.2 | Tag each finding with severity (Critical / High / Medium / Low). | Medium | `completed` — distribution: 4 Critical / 8 High / 4 Medium / 1 Low-Med / 4 Low. See `documents_refresh.md` §3.2. |
| 3.3 | Group findings by target file. | Low | `completed` — 4 file clusters (ARCH 6, REQ 5, APP_BUILDER 2, GENERATE_SKILLS 8). 2 cross-file patches (R4, G4). See `documents_refresh.md` §3.3. |
| 3.4 | Identify cascade dependencies (e.g., R2 cascades from A1). | High | `completed` — 3 cascade groups identified: {A1→R2}, {A2→R3,G2,G3,G6,G8} with G3→G6 inner edge, {R4→A3}. 14 independent patches. See `documents_refresh.md` §3.4. |
| 3.5 | Sort the global apply-order by urgency + dependencies. | High | `completed` — §5 ordering ratified: all severity bands ordered correctly, all dependency edges satisfied, no double-counting. See `documents_refresh.md` §3.5. |
| 3.6 | Stop for approval before Phase 4. | — | `completed` — user signed off on Phase 3 register. |

**Deliverable:** Ratified §5 ordering below.

### Phase 4 — Apply approved patches `[pending — awaiting Phase 3 sign-off]`

Apply the patches to the four documents in dependency-and-severity order.

| # | Sub-step | Urgency |
|---|---|---|
| 4.1 | Apply each patch with `Edit` against the target file. | (per item) |
| 4.2 | After each patch, verify the change rendered correctly (no broken markdown, no orphaned link refs). | High |
| 4.3 | After each patch, search the rest of the doc set for instances of the same issue that were missed in the report. | High |
| 4.4 | Re-run external URL verification on touched URLs. | Medium |
| 4.5 | Mark each applied finding as resolved in the register. | Low |
| 4.6 | Final pass: re-grep the doc set for known-wrong patterns (`Claude Code API`, `Claude Code Python SDK`, `best-practices#`). | Medium |

## 5. Patch application order (urgency-sorted, merged) — ratified

Phase 1 + Phase 2 findings, merged. Sorted by severity, then by dependency
chain (A2 must precede G2/G3/G6/G8 because those reference labels added
by A2). Phase 3 ratified this ordering in sub-step 3.5.

| Order | Tier | Finding | Severity | Status | Title | File(s) | Depends on |
|---|---|---|---|---|---|---|---|
| 1 | 1 | **A1** | Critical | ✅ applied | ARCH §2.12 wrong SDK name + URL (`Claude Code API`/`Claude Code Python SDK` → `Claude Agent SDK`) | `ARCHITECTURE.md` lines 62–64, 655 | — |
| 2 | 1 | **R2** | Critical | ✅ applied | REQ Glossary + Appendix D + link-defs SDK references (cascade from A1) | `REQUIREMENTS.md` lines 933, 1005–1006, 1024–1025 | A1 |
| 3 | 1 | **M1+M3** | Critical | ✅ verified | Single product-name cleanup across master pair (resolved by 1+2 cascade); grep confirms no remaining `Claude Code API` / `Claude Code Python SDK` in primary docs | both | A1, R2 |
| 4 | 1 | **X1** | Critical | ✅ applied | Skill #5 name mismatch (`ng-small-field` → `ng-field-component`) | `APP_BUILDER_REQUIREMENTS.md` line 213 | — |
| 5 | 1 | **G1** | Critical | ✅ applied | `{{context:...}}` / `{{template:...}}` syntax removed (3 meta-doc rewrites + 3 surgical inline fixes + 3 context replace_all + 19 template replace_all + 1 leftover template-section preamble) | `GENERATE_SKILLS.md` §"Dynamic Context Injection" + canonical template + shared-context preamble + all 11 skill sections | — |
| 6 | 2 | **A2** | High | ✅ applied | ARCH §2.14 body cites [Claude Code Skills] + [Claude Agent SDK Skills] + [Claude Skills Best Practices]; §20 [Claude Skills] URL rebound to `.../overview` + 3 new labels added | `ARCHITECTURE.md` lines 73–76, 656 | — |
| 7 | 2 | **R3** | High | ✅ applied | REQ Appendix D + link-defs `[Claude Skills]` URL → `.../overview` | `REQUIREMENTS.md` lines 1007, 1026 | A2 |
| 8 | 3 | **R4** | High | ✅ applied | ARCH `[ng-openapi-gen]` URL aligned to GitHub (matches REQ). `[ng-openapi-gen-github]` is now a duplicate URL — will be cleaned up by A3 in Tier 6. | `ARCHITECTURE.md` line 653 | — |
| 9 | 3 | **R1** | High | ✅ applied | REQ Appendix D collapsed to a 2-sentence note: internal labels owned here, external labels mirror ARCH §20. The link-defs block at end of file is the actual index. | `REQUIREMENTS.md` lines 986–988 | — |
| 10 | 2 | **G4** | High | ✅ applied | `openapi-integration.md` oasdiff bullet rewritten in `GENERATE_SKILLS.md` line 291 and in `skill_creation/shared/openapi-integration.md` — now states `build_app` runs oasdiff before invocation; skills consume ChangeSet | `GENERATE_SKILLS.md` line 291 + `skill_creation/shared/openapi-integration.md` | — |
| 11 | 3 | **G2** | High | ✅ applied | `§"Three Loading Levels"` replaced with `§"Skill loading model"` describing the real preload-frontmatter-on-startup + body-on-invocation + supporting-files-on-demand model. Token-strategy note cites [Claude Skills Best Practices]. | `GENERATE_SKILLS.md` lines 69–89 | A2 |
| 12 | 2 | **G3** | High | ✅ applied | Canonical YAML frontmatter at line 41 + at line 137 both expanded with `when_to_use`, `agent`, and updated description guidance; dual-mode requirement note added after the first canonical block | `GENERATE_SKILLS.md` lines 41–55 + 137–149 | A2 |
| 13 | 2 | **G6** | High | ✅ applied | All 11 skill YAML blocks gained a `when_to_use:` line with explicit `build_app` dispatch + CLI invocation triggers (verified grep `^when_to_use:` = 13 total = 11 skills + 2 canonical templates) | `GENERATE_SKILLS.md` 11 skill YAML blocks | G3 (template) |
| 14 | 4 | **G5** | Medium | ✅ applied (early) | Both occurrences resolved. Line 1871 was rewritten in Tier 2 via G6's description rewrite (replaced "Auto-invoked when the outer agent detects" wording). Line 23 was rewritten in Tier 3 alongside G8 (replaced "designed to be auto-invoked by an outer Claude API agent pipeline" with the correct explicit-invocation model). | `GENERATE_SKILLS.md` lines 23, 1871 | — |
| 15 | 3 | **G8** | Medium | ✅ applied | `§"Skill Architecture"` intro gained a leading paragraph citing `ARCHITECTURE.md` §20: [Claude Skills], [Claude Code Skills], [Claude Agent SDK Skills]. The following sentence about the Agent Skills format was also rewritten to describe the explicit `query(skills=[...])` and `/<skill-name>` invocation paths (which subsumes G5's line 23 fix). | `GENERATE_SKILLS.md` lines 21–23 | A2 |
| 16 | 4 | **M2** | Medium | ✅ applied | One-line HTML comment added above REQ link-defs block: external URLs mirror ARCH §20; update both. | `REQUIREMENTS.md` line ~1010 | — |
| 17 | 4 | **A5** | Medium | closed (no-op) | Architecture documents describe target capabilities by convention; an implementation-status line does not belong in this kind of document. Reverted §3.4 to original wording. | `ARCHITECTURE.md` line 165 | — |
| 18 | 5 | **A4** | Low–Med | ✅ applied | One-line note added to REQ §2.3 OpenAPI bullet: "OAS 3.1 is the pinned version; the toolchain does not yet support OAS 3.2." ARCH §2.10 not modified (architecture docs do not carry version-status detail per the A5 directive). | `REQUIREMENTS.md` line 128 | — |
| 19 | 6 | **G7** | Low | ✅ applied | `ng-workspace` Example 3 execution + output aligned with Process steps (backup tarball mention removed). | `GENERATE_SKILLS.md` lines 1425–1431 | — |
| 20 | 6 | **A3** | Low | ✅ applied | All 7 formerly-dead labels are now cited in ARCH body (citation not deletion). `[django-angular3]` + `[django-angular3-github]` → §1; `[Django-github]` → §2.1; `[DRF-github]` → §2.2; `[drf-spectacular]` → §11.2; `[oasdiff-github]` + `[ng-openapi-gen-github]` → §17. | `ARCHITECTURE.md` lines 5, 27, 31, 512, 620, 621 | R4 |
| 21 | 6 | **B1** | Low | ✅ applied | APP_BUILDER line 122 `§4.1` section pointer added. | `APP_BUILDER_REQUIREMENTS.md` line 122 | — |
| 22 | 6 | **R5** | Low | ✅ applied | REQ §4.2.3 line 533 rewrites Swagger Studio parenthetical. | `REQUIREMENTS.md` lines 533–534 | — |

**Totals.** 21 patches + 1 verification row (M1+M3). 4 Critical patches, 8
High, 4 Medium, 1 Low-Med, 4 Low. 3 cascade groups: {A1, R2}, {A2, R3, G2,
G3, G6, G8} (with G3→G6 inner edge), {R4, A3}. 14 independent patches.

## 6. Current status

| Phase | Status | Notes |
|---|---|---|
| 0 — Discovery | `completed` | Phase 0 report delivered; cleared by user. |
| 1 — Master pair | `completed` | 11 actionable findings, 0 deferred. |
| 2 — Downstream pair | `completed` | 10 actionable findings (1 APP_BUILDER + 8 GENERATE_SKILLS + 1 cross-pair X1). 2 Critical, 4 High, 2 Medium, 2 Low. |
| 3 — Consolidated register | `completed` | All sub-steps 3.1–3.6 completed. §5 ordering ratified and signed off. 21 patches across 4 docs (+ 1 shared-context file via G4). 3 cascade groups, 14 independent patches. |
| 4 — Apply patches | `completed` | All tiers applied. A5 closed as no-op. R4 reverted by user (kept both `[ng-openapi-gen]` npm and `[ng-openapi-gen-github]` labels). A3 resolved by citing each formerly-dead label in its natural location in ARCH body (no deletions). |

## 7. Open questions

All three open questions from Phase 1 were resolved on 2026-05-26:

1. **Patch-application timing — resolved.** Patches stay documented in
   `documents_refresh.md` and are applied in Phase 4 after the consolidated
   register lands. No interactive in-phase application.
2. **Finding A5 (ngdj inspection) — resolved.** Inspection of
   `shlomoa/angular-django2` v0.1.3 completed; A5 promoted from `deferred`
   to **Medium** with a concrete patch (reframe §3.4 responsibilities as
   target capabilities).
3. **OpenAPI 3.1 vs 3.2 (A4) — resolved.** 3.1 is the deliberate current
   choice; toolchain compatibility (and incompatibility) is now documented
   in the A4 patch as a per-component support table.

## 8. Operating-rule alignment

This plan was produced under the `.github/copilot-instructions.md` rules:

- **Plan first.** Phases proposed and approved before execution.
- **Sanitize user instructions.** Ambiguity surfaced as clarifying questions
  at phase boundaries before action.
- **Stop when ambiguity is medium-to-high.** Each phase ends with a stop
  point and explicit approval gate.
- **Single source of truth.** Findings report (`documents_refresh.md`) is
  the canonical place for findings; this plan does not restate them.
- **Avoid speculative implementation.** External URLs are fetched and
  cross-checked rather than asserted from memory.
