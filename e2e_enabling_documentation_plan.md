
# End-to-End Enabling Plan: simple_crm fully functional app

Structured by phase. Steps marked ✓ are functional today. Each step lists
GitHub issues that must be resolved before that step can execute; titles are
given exactly as they should be filed.

- **djng** issues → `shlomoa/django-angular3`
- **ngdj** issues → `shlomoa/angular-django2`

---

## Phase A — Deterministic bootstrap (no AI orchestration)

**Goal**: Angular app shell running in a browser, making authenticated API calls to Django.

---

**1. Install the tutorial and run the Django backend** ✓

```bash
django-angular3 install-tutorial simple_crm
cd simple_crm
python manage.py migrate && python manage.py createsuperuser && python manage.py runserver
```

*No issues required.*

---

**2. Validate project configuration** ✓

```bash
django-angular3 validate-project django-angular3.json
```

*No issues required.*

---

**3. Scaffold the Angular workspace**

```bash
django-angular3 ng_workspace django-angular3.json
```

| Repo | Issue | Context |
|---|---|---|
| **ngdj** | `Implement angular-django2:ng-workspace schematic` ([angular-django2#24](https://github.com/shlomoa/angular-django2/issues/24)) | `ng_workspace` calls `ng generate angular-django2:ng-workspace`; absent or broken schematic fails the entire bootstrap |
| **djng** | `Add ng_workspace, ng_new, ng_add, ng_config, ng_gen_app to default command_allowlist in settings.py` ([django-angular3#57](https://github.com/shlomoa/django-angular3/issues/57)) | Default allowlist is `("ng_openapi_gen",)` only; none of the workspace bootstrap sub-commands can execute without this |

---

**4. Generate the OpenAPI client**

```bash
django-angular3 ng_openapi_gen django-angular3.json
```

| Repo | Issue | Context |
|---|---|---|
| **ngdj** | `Include ng-openapi-gen as a devDependency in ng-workspace schematic output` ([angular-django2#26](https://github.com/shlomoa/angular-django2/issues/26)) | `ng_openapi_gen` runs `pnpm exec ng-openapi-gen`; if the package is absent the command fails |

---

**5. Build the Angular app**

```bash
django-angular3 ng_build django-angular3.json
```

| Repo | Issue | Context |
|---|---|---|
| **ngdj** | `ng-workspace schematic output passes tsc --noEmit with zero errors` ([angular-django2#25](https://github.com/shlomoa/angular-django2/issues/25)) | A schematic that emits invalid TypeScript blocks every downstream step |

---

**6. Serve the integrated app** *(step currently absent from docs and tooling)*

| Repo | Issue | Context |
|---|---|---|
| **djng** | `Serve Angular build output via Django static-files URL in development (whitenoise or TemplateView)` (not filed) | `ng_build` writes to `angular.output`; no Django URL or static-files config currently routes to it |
| **ngdj** | `Ship proxy.conf.json in ng-workspace output forwarding /api/ to http://127.0.0.1:8000` ([angular-django2#25](https://github.com/shlomoa/angular-django2/issues/25)) | Without a proxy config, `ng serve` API calls hit CORS and Django session-cookie failures |
| **djng** | `Document CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS settings for Angular dev server in getting-started.md` (not filed) | No current guidance; without these, authenticated DRF calls from `ng serve` are rejected |

After step 6: the app shell loads in a browser. There are no Customer/Product pages yet — the workspace is a structural scaffold only.

---

## Phase B — CRM module construction (AI-orchestrated via `build_app`)

**Goal**: Navigable Customer and Product list/detail/form pages generated from the simple_crm OpenAPI schema.

---

**7. Define the non-CRM project config schema** *(TODO item 1 — currently blocked)*

| Repo | Issue | Context |
|---|---|---|
| **djng** | `Define JSON schema and filename for <project>.project.json (non-CRM UI config)` ([django-angular3#74](https://github.com/shlomoa/django-angular3/issues/74)) | `build_app` non-CRM change derivation is entirely blocked until this schema exists; also gates step 10 non-CRM pages |

---

**8. Implement the 11 SKILLS** *(TODO item 7)*

One djng issue and one ngdj issue per SKILL:

| # | SKILL | djng issue (`shlomoa/django-angular3`) | ngdj issue (`shlomoa/angular-django2`) |
|---|---|---|---|
| 1 | `angular-workspace-foundation` | `Complete skill_creation/skills/01-angular-workspace-foundation.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | see step 3 — ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 2 | `angular-app-composition` | `Complete skill_creation/skills/02-angular-app-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-app schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 3 | `angular-api-integration` | `Complete skill_creation/skills/03-angular-api-integration.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-api schematic` ([#26](https://github.com/shlomoa/angular-django2/issues/26)) |
| 4 | `angular-data-service-composition` | `Complete skill_creation/skills/04-angular-data-service-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-data-service schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 5 | `angular-field-component-composition` | `Complete skill_creation/skills/05-angular-field-component-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-field-component schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 6 | `angular-form-field-composition` | `Complete skill_creation/skills/06-angular-form-field-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-form-field schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 7 | `angular-component-composition` | `Complete skill_creation/skills/07-angular-component-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-component schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 8 | `angular-complex-component-composition` | `Complete skill_creation/skills/08-angular-complex-component-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-complex-component schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 9 | `angular-reactive-form-composition` | `Complete skill_creation/skills/09-angular-reactive-form-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-reactive-form schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 10 | `angular-page-composition` | `Complete skill_creation/skills/10-angular-page-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-page schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |
| 11 | `angular-site-composition` | `Complete skill_creation/skills/11-angular-site-composition.md: add local acceptance criteria` ([#89](https://github.com/shlomoa/django-angular3/issues/89)) | `Implement angular-django2:ng-site schematic` ([#24](https://github.com/shlomoa/angular-django2/issues/24)) |

Each djng SKILL issue must include local acceptance criteria per `SKILL_AUTHORING_PLAN.md` (without these, `build_app` cannot judge completion — see TODO §7).

---

**9. Implement `build_app` orchestration flow** *(TODO items 6, 8)*

| Repo | Issue | Context |
|---|---|---|
| **djng** | `Replace build_app ChangeSet plan emission with structured ProcedureGraph nodes` ([django-angular3#59](https://github.com/shlomoa/django-angular3/issues/59)) | Current `build_app.py` emits CLI command strings; structured nodes are required before SDK integration |
| **djng** | `Wire Claude Agent SDK into build_app: call sdk.query() per SKILL procedure node` ([django-angular3#59](https://github.com/shlomoa/django-angular3/issues/59)) | Core of TODO item 8; without it `build_app` cannot drive any SKILL session |
| **djng** | `Implement build_app failure policy for SKILL sessions that end without satisfying local acceptance criteria` ([django-angular3#60](https://github.com/shlomoa/django-angular3/issues/60)) | Currently unspecified; `build_app` advances to the next procedure node regardless of outcome |

---

**10. Run `build_app` cold-start for simple_crm** *(TODO item 10)*

```bash
python manage.py build_app django-angular3.json
```

Triggers all 11 SKILL sessions in dependency order against the simple_crm schema.

| Repo | Issue | Context |
|---|---|---|
| **djng** | `Verify simple_crm cold-start procedure graph: all 11 SKILL sessions emitted in dependency order (TEST_EXAMPLES.md example 1)` ([django-angular3#84](https://github.com/shlomoa/django-angular3/issues/84)) | Input files exist at `django_angular3/examples/01_simple_crm/`; full chain not yet run end-to-end |
| **ngdj** | `Integration test: all 11 schematics accept build_app procedure inputs for simple_crm schema` ([angular-django2#24](https://github.com/shlomoa/angular-django2/issues/24)) | Each schematic is the execution counterpart of a SKILL; correctness is currently unverified |

---

**11. E2E verification** *(TODO item 9.2 — currently unspecified)*

| Repo | Issue | Context |
|---|---|---|
| **djng** | `Populate REQUIREMENTS.md §6.4: global acceptance criteria covering cross-SKILL type consistency, backend/Angular contract alignment, and runtime smoke tests` ([django-angular3#84](https://github.com/shlomoa/django-angular3/issues/84)) | Section exists but is empty; `ng_build` compiling is not sufficient to declare the app correct (see TODO §9.3) |
| **djng** | `Add terminal verification procedure node to build_app procedure graph: run §6.4 acceptance tests after all SKILL sessions` ([django-angular3#84](https://github.com/shlomoa/django-angular3/issues/84)) | Without this, the pipeline has no deterministic pass/fail signal |
| **ngdj** | `Define and implement ngdj schematic test harness against a real Angular workspace` ([angular-django2#24](https://github.com/shlomoa/angular-django2/issues/24)) | Schematic correctness is entirely unverified; TODO §9.2 identifies this as a blocking gap |

---

## Summary

| Phase | Steps | Status |
|---|---|---|
| A — Bootstrap | 1–5 | Steps 1–2 work today; 3–5 blocked on ngdj schematics being functional |
| A — Serve | 6 | No tooling or docs exist; requires 3 new issues |
| B — CRM construction | 7–10 | Requires 2 + 22 + 3 + 2 = 29 issues across djng and ngdj |
| B — Verification | 11 | Requires 3 issues; spec is currently empty |
