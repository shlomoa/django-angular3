# Verification Plan

## Purpose and boundary

Scenario, construction, integration, terminal, global, cross-platform, and staging verification.

Normative behavior remains owned by the referenced requirements,
specifications, contracts, architecture, and executable/configuration sources.
GitHub owns issue scope and tracking.

## Related domain plans

- [Configuration Plan](CONFIGURATION_PLAN.md)
- [Construction Plan](CONSTRUCTION_PLAN.md)
- [Automation Plan](AUTOMATION_PLAN.md)
- [Application Delivery Plan](APPLICATION_DELIVERY_PLAN.md)

## Scenario coverage

### Planning details

- See `TEST_EXAMPLES.md` for the scenario definitions and expected outputs. <!-- STEP7-73e2b2d89da4 -->
- **Start from scratch**: a cold-start build with no previous state, invoking <!-- STEP7-aa63b920ffdb -->
- the full automation chain from workspace creation through app assembly and verification <!-- STEP7-25bece09a65e -->
- **Schema evolution — add**: an incremental schema change that adds a <!-- STEP7-0ac616eb7046 -->
- resource; only the required automation commands run, and existing workspace, app, and components are preserved <!-- STEP7-95229e9b51fe -->
- **Schema evolution — removal**: an incremental schema change removes a <!-- STEP7-ecd76149fb41 -->
- **OpenUI-only change**: an `app.openui.json` change with no schema change; only <!-- STEP7-8bdc9eef607b -->
- OpenUI-derived automation commands run <!-- STEP7-540aefacdf3d -->
- **Combined schema and OpenUI change**: both the contract and the OpenUI <!-- STEP7-d0dc2b209acb -->
- input source change in the same build; both change paths activate and interleave correctly <!-- STEP7-93a29d49b360 -->
- **Full replacement**: a resource is removed and a different resource is <!-- STEP7-8d2b4356ad3b -->
- added; remove steps precede add steps at the same dependency level <!-- STEP7-fdc9c054504f -->
- Skill acceptance does not compose into cross-Skill interface consistency, backend-contract / Angular-client alignment, and runnable application flows <!-- STEP7-a7273355a0df -->

### Open backlog

- [ ] Use `doc/TEST_EXAMPLES.md` fixtures to cover all configuration, OpenAPI, and OpenUI scenario-axis combinations, plus first-run, source-selection, mixed create/delete, deletion, and command-failure cases. <!-- STEP7-b03bd33e95b1 -->

### Authoritative references

- Automation authority: automation requirements/specification and split primitive contracts. <!-- STEP7-7385437b03bd -->

## Construction and integration verification

### Open backlog

- [ ] Verify that djng selects, orders, and composes upstream ngdj operations in a real generated Angular workspace without duplicating ngdj's schematic tests. <!-- STEP7-3c60ec5f30ec -->

### Implementation sequence

- As behaviour moves from AI-guided Skill flow to deterministic tool/hook enforcement, test ownership moves with it: <!-- STEP7-9618b79718b9 -->
- Operations promoted to **Tools** (Phase 1) gain deterministic unit tests with <!-- STEP7-3048ead969d6 -->
- fixed inputs/outputs, replacing reliance on Skill self-checks. <!-- STEP7-7b2c9d4b7091 -->
- Gates and side effects promoted to **Hooks** (Phase 2) gain lifecycle-event <!-- STEP7-804fd6f71190 -->
- and exit-code tests, replacing "the agent remembered to do it" assumptions. <!-- STEP7-5f1757d8aba9 -->
- **Skills** (Phase 4) retain component/behaviour tests for generative output. <!-- STEP7-01a8c3183084 -->
- (Phase 7) own cross-Skill and integration correctness — the properties no single primitive's tests can establish. <!-- STEP7-ad63a88e25bf -->
- **Provider adapters** (Phase 5) first share a credential-free stub matrix; <!-- STEP7-37293ce82449 -->
- each real adapter then runs that matrix plus provider-specific rendering and lifecycle checks in an isolated, explicitly opted-in runtime suite. Missing credentials or SDKs skip live tests without prompting or exposing values. <!-- STEP7-e005967aff29 -->
- The default verification path remains credential-free: <!-- STEP7-bdd9f4471cda -->
- `ruff format django_angular3 tests` <!-- STEP7-055b07f996cc -->
- `ruff check django_angular3 tests` <!-- STEP7-2476e5b3fffe -->
- focused tests for the affected automation/build boundaries <!-- STEP7-924f34f342bd -->
- `python -m unittest discover -s tests -p 'test*.py'` <!-- STEP7-526734476145 -->
- generated-app-compatible `django-admin build_app --dry-run` coverage <!-- STEP7-b9002c79c218 -->
- Update implementation status, capability metadata, and the backlog only from actual test evidence. Provider-neutral stub success alone does not establish provider support. <!-- STEP7-be20b23163a3 -->

## Terminal and global acceptance

### Planning details

- **Global acceptance gate**: terminal verification fails the run when local <!-- STEP7-e8898cb29cfe -->

### Open backlog

- [ ] Verify cross-Skill interface consistency, backend-contract/Angular-client alignment, and runnable application flows according to `doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-10 and `doc/ARCHITECTURE.md` §§7.2–7.3. <!-- STEP7-a674b317b27a -->

### Implementation sequence

- **Goal**: Implement the terminal validation required by FR-9 and FR-10. <!-- STEP7-bc7fc7051940 -->
- **Dependencies**: Phases 3–5. <!-- STEP7-b64d9320145e -->
- Implement the terminal validation commands required by FR-9 and FR-10. <!-- STEP7-0bd00cbb73b6 -->
- Cover the four verification categories in `doc/ARCHITECTURE.md` §7.3: <!-- STEP7-30200c217ebf -->
- contract, construction-output, integration, and test-based verification. <!-- STEP7-a6b00647f6ef -->
- Apply AIR-3 and AIR-5 to terminal acceptance evidence. <!-- STEP7-82084302ca09 -->
- Terminal verification satisfies FR-8 and FR-9 in <!-- STEP7-f48531f20d7a -->
- `doc/requirements/APP_BUILDER_REQUIREMENTS.md`. <!-- STEP7-ffa4f4c12abb -->
- Terminal-verification tests: success only on all-pass; failure path mirrors <!-- STEP7-9aef0114edc4 -->
- FR-8; verification consumes recorded tool outputs rather than rescanning. <!-- STEP7-d3ddd0bca0b4 -->
- **Dependencies**: Phases 4–6. <!-- STEP7-7c7b1d450fe1 -->
- The global acceptance requirement is defined by `doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-10. Its architectural ownership and rationale are defined in `doc/ARCHITECTURE.md` §§7.2–7.3. <!-- STEP7-c7ca12d651cc -->
- Implement the FR-10 global acceptance gate after the Phase 6 terminal validation foundation exists. <!-- STEP7-09837627733f -->
- Keep the global gate independent of any individual Skill's local acceptance decision. <!-- STEP7-4efbf1bceafe -->
- The implemented gate satisfies FR-10 in <!-- STEP7-92dddc92427b -->
- A regression test reproducing the interface-drift failure chain and asserting the global gate catches it. <!-- STEP7-661b93179860 -->
- **Terminal verification** (Phase 6) and the **global acceptance gate** <!-- STEP7-a4d9adc06886 -->

### Corrected current identities

- Cross-Skill interface-drift regression coverage maps to the Verification plan's global acceptance gate. <!-- STEP7-83db36d80726 -->

### Sequence structure

The source phase structure includes work-item, acceptance, and test
coverage blocks. Their substantive claims are rendered in this plan.

## Cross-platform and staging verification

No current verification work is assigned exclusively to this domain section.

## Tracked GitHub issues

- [#84 — Implement staged verification across contract, construction, integration, and tests](https://github.com/shlomoa/django-angular3/issues/84) <!-- STEP7-dda276a46eaf -->
- [#160 — Phase 5: add credential-free provider-neutral automation tests](https://github.com/shlomoa/django-angular3/issues/160) <!-- STEP7-33102fa31a8b -->
- [#161 — Phase 6: verify and document the foundation boundary](https://github.com/shlomoa/django-angular3/issues/161) <!-- STEP7-295acb362ccd -->

Issue bodies, status, timestamps, relationships, dependency lists, and
acceptance criteria are intentionally not copied into this plan.
