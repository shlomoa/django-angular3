# Application Delivery Plan

## Purpose and boundary

Generated-application readiness, backend and frontend delivery, security and business capabilities, and operational delivery.

Normative behavior remains owned by the referenced requirements,
specifications, contracts, architecture, and executable/configuration sources.
GitHub owns issue scope and tracking.

## Related domain plans

- [Construction Plan](CONSTRUCTION_PLAN.md)
- [Verification Plan](VERIFICATION_PLAN.md)

## Implementation readiness and MVP

### Planning details

- The platform is ready for implementation handoff when: <!-- STEP7-f8985c3fdfaf -->
- The MVP scope includes one full business module and the shared platform services it needs. <!-- STEP7-8eae09f26a41 -->

## Backend and frontend delivery

### Planning details

- See `ARCHITECTURE.md` §§ 17-18 for the related architectural decision and implementation-sequencing context. <!-- STEP7-244e19925a12 -->
- The backend/frontend integration model is agreed upon <!-- STEP7-89081736301c -->
- OpenAPI and OpenUI inputs have clear ownership and boundaries <!-- STEP7-190f9f9d2904 -->
- Non-functional requirements are concrete enough to guide engineering choices <!-- STEP7-444350eb5815 -->
- The architecture supports adding future modules without reworking the core stack. <!-- STEP7-891e66c50e86 -->
- The first implementation should include: <!-- STEP7-d8da91dbf232 -->
- Backend project setup with Django and DRF <!-- STEP7-6f1894e4a777 -->
- Angular frontend setup with Angular Material <!-- STEP7-35e2f258ad20 -->
- Generated Angular integration artifacts for shared Angular/Django integration logic. <!-- STEP7-d1f1b25c453f -->
- User profile and user administration <!-- STEP7-e1f243f52e82 -->
- OpenAPI export and consumption flow for API-contract-derived features <!-- STEP7-028e321f0f5c -->
- An OpenUI concrete UI document for pages, forms, navigation, and workflows <!-- STEP7-8fa17dcad321 -->
- One complete business module implemented end to end <!-- STEP7-f7fe35bc58c9 -->
- Shared list, detail, and form patterns <!-- STEP7-572298adc59b -->

### Open backlog

- [ ] Build one module through the governed wrappers, Tools, Hooks, Skills, direct execution, and global acceptance gate. <!-- STEP7-e3cc0454e980 -->

### Authoritative references

- Tool authority: TOOL_CONTRACTS.md; sequencing only belongs in a domain plan. <!-- STEP7-9b3c9c0cfd46 -->

## Security and business capabilities

### Planning details

- Authentication, authorization, and audit expectations are explicit <!-- STEP7-2a4b7ea0f0cd -->
- Authentication and role-based authorization <!-- STEP7-baf481858351 -->

## Operational delivery

### Planning details

- Audit logging for key actions <!-- STEP7-23d210f47934 -->
- Error handling, health checks, and baseline automated tests <!-- STEP7-33a0726b10cb -->
- Local development workflow plus staging-ready deployment setup <!-- STEP7-fbdfc4c1b78f -->

### Open backlog

- [ ] Add durable audit records and generated-app health checks. <!-- STEP7-3fb4670e7acd -->
- [ ] Verify representative generated-app workflows in staging. <!-- STEP7-06fd54fd9bb4 -->

## Tracked GitHub issues

- [#64 — Expose non-production schema generation and browsable API docs](https://github.com/shlomoa/django-angular3/issues/64) <!-- STEP7-381fa24c03d0 -->
- [#65 — Scaffold the generated backend app structure (`common`, `accounts`, `access`, domain apps)`](https://github.com/shlomoa/django-angular3/issues/65) <!-- STEP7-29bd1e02b6ff -->
- [#67 — Standardize reusable UI patterns for tables, detail views, forms, dialogs, and feedback](https://github.com/shlomoa/django-angular3/issues/67) <!-- STEP7-15d32391faaf -->
- [#68 — Implement authentication, password reset, recovery, and session timeout flows](https://github.com/shlomoa/django-angular3/issues/68) <!-- STEP7-336cf3cd992c -->
- [#69 — Implement role-based authorization across API endpoints and UI navigation](https://github.com/shlomoa/django-angular3/issues/69) <!-- STEP7-fbced36fce7f -->
- [#70 — Implement authenticated DRF endpoints with validation and standard HTTP semantics](https://github.com/shlomoa/django-angular3/issues/70) <!-- STEP7-0b36043cbc4e -->
- [#71 — Add filtering, sorting, pagination, and deterministic ordering for list endpoints](https://github.com/shlomoa/django-angular3/issues/71) <!-- STEP7-04d8cdf2b28e -->
- [#72 — Normalize API error responses for Angular form and notification handling](https://github.com/shlomoa/django-angular3/issues/72) <!-- STEP7-e123fde75392 -->
- [#73 — Build the Angular shell, routing, responsive navigation, and global feedback patterns](https://github.com/shlomoa/django-angular3/issues/73) <!-- STEP7-6e5718ed853d -->
- [#75 — Deliver the reusable business module pattern with list/detail/create/update/deactivate flows](https://github.com/shlomoa/django-angular3/issues/75) <!-- STEP7-d25f25791bc7 -->
- [#76 — Implement search and data-discovery workflows for business records](https://github.com/shlomoa/django-angular3/issues/76) <!-- STEP7-15f4be217610 -->
- [#77 — Add audit logging for security and business events with authorized history views](https://github.com/shlomoa/django-angular3/issues/77) <!-- STEP7-0608dfbee129 -->
- [#78 — Implement user administration and self-service profile management](https://github.com/shlomoa/django-angular3/issues/78) <!-- STEP7-7a26cd1d075b -->
- [#79 — Add administrative screens and centrally managed reference data](https://github.com/shlomoa/django-angular3/issues/79) <!-- STEP7-502b0b8768ff -->
- [#80 — Add notification support for account and workflow events](https://github.com/shlomoa/django-angular3/issues/80) <!-- STEP7-3416266e4b61 -->
- [#81 — Add file attachment support with upload validation and permission-aware downloads](https://github.com/shlomoa/django-angular3/issues/81) <!-- STEP7-e7d0d90e7411 -->
- [#82 — Implement user-safe error handling and recoverable unsaved-form behavior](https://github.com/shlomoa/django-angular3/issues/82) <!-- STEP7-077efc220329 -->
- [#83 — Add generated-app developer diagnostics and the gated `/ng/build` page](https://github.com/shlomoa/django-angular3/issues/83) <!-- STEP7-5ab85d109c02 -->

Issue bodies, status, timestamps, relationships, dependency lists, and
acceptance criteria are intentionally not copied into this plan.
