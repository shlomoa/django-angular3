# Make every milestone provable in a browser

A prioritized, no-optional-features plan for `openui-spec`, `angular-django2`,
and `django-angular3`: what closes the visibility gap, in what order, and
what CI hook makes it stick.

**Status:** Draft — for review
**Author:** Shlomo Anglister
**Date:** 2026-09-14

Copied from the Cowork session "Framework visibility plan"
(`session_01ExVg5N8tLgUS8NAqgk2Eam`), artifact "Visibility Plan".

## 01 · The pipeline as it stands

Three repos, one build order. Each is proven by what it hands the next
one — or isn't, today.

- **openui-spec** — UI taxonomy + JSON schema. Has a generated-examples app
  already.
- **angular-django2** — Schematics that consume the spec + OpenAPI. Has a
  live `/ui` reference app.
- **django-angular3** — Django orchestration layer. No frontend workspace
  yet — nothing to look at.

| Repo | Milestone | Progress | Flag |
| --- | --- | --- | --- |
| angular-django2 | "djangoangular e2e POC" — 3 issues from closed | 7 / 10 closed | |
| django-angular3 | "djangoangular e2e POC" — the MVP business module + Angular shell | 2 / 30 closed | due 2026-08-31 — overdue |
| django-angular3 | "djangoangular alpha" — Tool→Hook→Skill automation foundation | 0 / 11 closed | due 2026-09-14 — today, 0% done |
| openui-spec | No milestones — already has its demo app and treats visibility as a stated requirement | — | |

django-angular3's own e2e-POC issues (#65 scaffold backend, #73 Angular
shell/routing, #75 business module, #67 UI patterns, #78–#81
admin/notification/attachment screens, #83 `/ng/build` diagnostics) are the
actual work that gives it a frontend to demo — there's no shortcut around
them.

## 02 · What the answers settled

- **D1 — Granularity: per generated artifact type.** Every new
  Skill / schematic / scope / `ng_*` command gets a demo the first time it
  exists — not per-PR, not only at phase boundaries. This matches
  angular-django2's own Phase 4 plan, which already promised this and
  hasn't been held to it consistently.
- **D2 — Surface: keep the two existing per-repo demos, add
  django-angular3's — don't unify yet.** openui-spec's generated-examples
  app and angular-django2's `/ui` reference app stay as-is. django-angular3
  gets an equivalent, but only as the e2e-POC issues that build it land —
  see D3. A single cross-repo demo site is explicitly deferred (§05).
- **D3 — django-angular3's gap closes by executing the e2e-POC milestone,
  not a shortcut.** Both proposed shortcuts (hand-build `01_simple_crm` now;
  extend the `/ng/build` diagnostics page as a stand-in) were rejected. The
  real answer was already sitting in the milestone: 28 open issues —
  shell, routing, the business-module CRUD pattern, admin/notification/
  attachment screens — *are* the demo. This plan attaches a visibility
  requirement to those issues; it doesn't invent a parallel one.
- **D4 — The hook: capture a screenshot, and leave a live demo runnable —
  no diffing.** CI captures a screenshot as a build artifact and fails only
  if capture itself fails (no baseline to maintain). On top of that, the
  hook also has to leave behind a way to actually click around — a
  documented `ng serve` entrypoint with seeded fixture data, not just a
  picture.

## 03 · The hook, specified

`HOOK_CONTRACTS.md` already defines four lifecycle hooks
(`pre-construction`, `migration-triggered`, `post-generation`,
`session-stop`) — all deterministic, none visual, all still marked
"planned." This adds a fifth, in the same seven-field format, so it slots
into the Tool→Hook taxonomy rather than sitting outside it.

**`demo-capture`** — new, post-generation family

| Field | Value |
| --- | --- |
| Purpose | Prove a construction output renders, and leave it runnable for inspection — not just that it compiles. |
| Trigger event | Post-tool, immediately after `post-generation` succeeds for any artifact type carrying a UI surface (page, form, app-shell, admin screen). |
| Deterministic action | Boot the generated/reference app against seeded fixture data; capture one full-page screenshot per new artifact as a CI-uploaded build artifact; write a `DEMO.md` stub recording the exact `ng serve` / `manage.py runserver` command and URL that reproduces it locally. |
| Failure behavior | Fails the build only if the app fails to boot or the screenshot capture itself errors — never on visual difference. No baseline, no diffing, no flakiness budget to maintain. |
| Allowed wrapped tools | Headless browser capture tool; dev-server process manager. No AI judgment in the hook itself — matches the deterministic-only rule the other four hooks already follow. |
| Implementation reference | Planned — lands as an amendment to Phase 7 (`#162`, TOOL contracts) and Phase 8 (`#163`, HOOK contracts) of the automation build-out, not a standalone issue. |

Phases 7–8 are 0% done today (Alpha milestone, due today). Until they land,
§04's workstream 2 wires the same two checks in as a plain GitHub Actions
step — no Skill/Hook framework required — so enforcement starts now and
gets formalized later, not the reverse.

## 04 · Prioritized workstreams

Ordered by dependency and leverage, not by repo. No optional items —
everything below is required for D1–D4 to hold; anything speculative is in
§05 instead.

### 1. Close angular-django2's last mile — `angular-django2`

Already 70% done and closest to producing something real to look at — #27
is literally "assemble UI-description-derived content into the generated
app." Finishing it gives the whole pipeline its first genuine spec-to-screen
result.

- **Definition of done:** Generated app renders content sourced from an
  actual OpenUI document (not hand-coded), via the canonical TS parser.
- **Issues:** #27 assemble UI-derived content, #98 canonical parser
  integration, #103 schematics integration

### 2. Wire the interim CI gate — all 3 repos

The hook framework (§03) doesn't exist yet. This ships the same two
guarantees — screenshot artifact + reproducible `DEMO.md` entrypoint — as
a step in each repo's existing workflow file, so "hard-wired" is true
starting now.

- **Definition of done:** A CI job in each repo boots the relevant demo
  app, uploads a screenshot artifact, and fails the build if boot/capture
  fails.
- **Issues:** `django-angular3/.github/workflows/build.yml`,
  `angular-django2/.github/workflows/ci.yml`,
  `openui-spec/.github/workflows/build.yml`, +1 new issue per repo

### 3. Retrofit visual acceptance onto the e2e-POC build-out — `django-angular3`

This is the actual visibility gap. Each issue that produces a user-facing
screen gets an explicit, non-optional acceptance line: passes workstream 2's
CI gate before it can close.

- **Definition of done:** Every issue below is amended with "renders via
  demo-capture, screenshot attached to the PR" as a closing condition — not
  a suggestion.
- **Issues:** #65 scaffold backend, #73 Angular shell/routing, #67 UI
  patterns, #75 business module CRUD, #76 search/discovery, #78 user
  admin, #79 admin screens, #80 notifications, #81 attachments, #83
  `/ng/build` diagnostics

### 4. Bring openui-spec's demo up to the same bar — `openui-spec`

Lowest urgency — it's the one repo that already treats visibility as a
stated requirement. This just puts it on the same CI gate as the other two
so "visible" means the same thing everywhere.

- **Definition of done:** Generated-examples app runs through workstream
  2's CI job on every generator change.
- **Issues:** +1 new issue

### 5. Formalize demo-capture as a real Hook — `django-angular3`

Once the automation foundation actually ships, §03's hook replaces
workstream 2's plain CI step — same guarantee, now inside the governed
Tool/Hook/Skill model instead of bolted on.

- **Definition of done:** `demo-capture` appears in HOOK_CONTRACTS.md with
  an implemented reference, wired into the FR-10 global acceptance gate.
- **Issues:** #162 Phase 7 — TOOL contracts, #163 Phase 8 — HOOK contracts

## 05 · Explicitly deferred

Not in scope for this plan — named so nothing here quietly becomes an
unplanned extra:

- A single unified cross-repo demo site showing spec → generated Angular →
  running Django app end-to-end (D2) — revisit once django-angular3 has
  its own real demo from workstream 3.
- Visual regression / pixel diffing (D4 ruled this out explicitly —
  capture only).
- Hosting the demos anywhere persistent (GitHub Pages, a preview
  environment) — today's scope is CI artifact + local `DEMO.md` entrypoint
  only.
- Rescuing the "djangoangular alpha" milestone's own schedule (due today,
  0% done) — noted as a dependency for workstream 5, not something this
  plan fixes.

## 06 · On approval

1. **Edit** the 10 django-angular3 issues in workstream 3 to add the
   closing condition from their Definition of done.
2. **File** three new issues (one per repo) for the interim CI step in
   workstream 2, each linked to the workflow file it touches.
3. **File** one new issue in openui-spec for workstream 4.
4. **Comment** on #162/#163 in django-angular3 recording the demo-capture
   hook spec from §03 as an amendment, so it's not lost when Phase 7–8 work
   starts.
5. **Leave** #27 / #98 / #103 in angular-django2 as-is — they're already
   correctly scoped, just need finishing.

### The exact text added to each existing issue

Every edit below is additive — an appended acceptance section or comment,
nothing in an issue's existing body is removed or reworded. "Boot target"
is what demo-capture actually launches for that issue; screenshot count
follows D1 (one per distinct surface the issue produces).

**#65 — Scaffold the generated backend app structure** (1 screenshot)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots the scaffolded Django app against seeded fixture data
- [ ] Screenshot attached to PR: the app's browsable-API root
- [ ] DEMO.md records the `manage.py runserver` command + URL
- [ ] Issue does not close until this checklist passes
```

**#73 — Angular shell, routing, responsive navigation, global feedback**
(3 screenshots — shell counts as 3 distinct surfaces under D1)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots the generated Angular shell
- [ ] Screenshot 1: shell with navigation expanded, desktop width
- [ ] Screenshot 2: shell at mobile width, nav collapsed/responsive state
- [ ] Screenshot 3: a global feedback pattern (snackbar/toast) triggered and visible
- [ ] DEMO.md records the `ng serve` command + URL and how to trigger the feedback state
- [ ] Issue does not close until this checklist passes
```

**#67 — Reusable UI patterns: tables, detail views, forms, dialogs,
feedback** (5 screenshots — one per named pattern, per D1)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots the reference-app instance of each pattern below
- [ ] Screenshot: table pattern
- [ ] Screenshot: detail-view pattern
- [ ] Screenshot: form pattern
- [ ] Screenshot: dialog pattern (open state)
- [ ] Screenshot: feedback pattern (toast/inline message)
- [ ] DEMO.md lists the route/action to reach each pattern locally
- [ ] Issue does not close until every pattern above has its screenshot
```

**#75 — Business module pattern — list/detail/create/update/deactivate**
(5 screenshots — one per named flow)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots one seeded business-module instance
- [ ] Screenshot: list view with seeded records
- [ ] Screenshot: detail view
- [ ] Screenshot: create flow (populated form, pre-submit)
- [ ] Screenshot: update flow
- [ ] Screenshot: deactivate flow / confirmation state
- [ ] DEMO.md records the module's local URL and seed-data source
- [ ] Issue does not close until all five flow screenshots pass
```

**#76 — Search and data-discovery workflows** (1 screenshot)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots a business module with seeded, searchable records
- [ ] Screenshot: search results with an active query/filter applied
- [ ] DEMO.md records a sample query that reproduces the screenshot
- [ ] Issue does not close until this checklist passes
```

**#78 — User administration and self-service profile management**
(2 screenshots)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots the admin user list and the self-service profile page
- [ ] Screenshot 1: admin user list
- [ ] Screenshot 2: self-service profile form
- [ ] DEMO.md records both local URLs
- [ ] Issue does not close until both screenshots pass
```

**#79 — Administrative screens and centrally managed reference data**
(1 screenshot)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots the reference-data admin screen with seeded entries
- [ ] Screenshot: reference-data admin screen
- [ ] DEMO.md records the local URL
- [ ] Issue does not close until this checklist passes
```

**#80 — Notification support for account and workflow events**
(1 screenshot)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture triggers one seeded account/workflow event
- [ ] Screenshot: the resulting notification as delivered (toast or inbox item)
- [ ] DEMO.md records how to trigger that event locally
- [ ] Issue does not close until this checklist passes
```

**#81 — File attachment support — upload validation, permission-aware
download** (2 screenshots)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots the attachment upload flow and a permission-denied download attempt
- [ ] Screenshot 1: upload UI with a file attached
- [ ] Screenshot 2: permission-denied download state
- [ ] DEMO.md records both local reproduction steps
- [ ] Issue does not close until both screenshots pass
```

**#83 — Generated-app developer diagnostics and the gated /ng/build page**
(1 screenshot)

```
## Visual acceptance (visibility plan) — appended to issue body
- [ ] demo-capture boots the gated /ng/build page in DEBUG mode
- [ ] Screenshot: page showing build status, timestamps, and at least one compile warning
- [ ] DEMO.md records the gating flag and local URL
- [ ] Reinforces, not duplicates, this issue's existing "diagnostics visibility" test deliverable
```

**#162 — Phase 7 — deterministic TOOL contracts** (comment, not a body
edit)

> This phase should also define the `demo-capture` Tool — headless-browser
> capture + dev-server boot, no AI judgment — spec drafted in the
> visibility plan §03. Scope it in alongside the other deterministic tools
> this phase adds.

**#163 — Phase 8 — direct lifecycle HOOK contracts** (comment, not a body
edit)

> Add `demo-capture` as a fifth hook in HOOK_CONTRACTS.md, post-generation
> family — full 7-field spec in the visibility plan §03. It wraps the Tool
> from #162; until this phase lands, the same check runs as a plain CI
> step (visibility plan workstream 2).

---

plan v1 — corrections welcome before conversion to issues
