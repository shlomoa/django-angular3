# Construction Plan

## Purpose and boundary

Governed construction, wrappers and generation entry points, change derivation, OpenAPI/OpenUI construction, and direct `build_app` execution.

Normative behavior remains owned by the referenced requirements,
specifications, contracts, architecture, and executable/configuration sources.
GitHub owns issue scope and tracking.

## Related domain plans

- [Configuration Plan](CONFIGURATION_PLAN.md)
- [Automation Plan](AUTOMATION_PLAN.md)
- [Verification Plan](VERIFICATION_PLAN.md)

## Governed construction

### Planning details

- See `ARCHITECTURE.md` §§ 4.1-4.3 and 7.1-7.4 for the governing ownership boundaries, architectural control-loop, verification, and build-flow model. <!-- STEP7-b782f15b1d09 -->
- logic, authenticated APIs, authentication services, authorization enforcement, and backend integrations <!-- STEP7-142a08e2ba7e -->
- reference data, and operational tooling, including backend-oriented administration interfaces <!-- STEP7-7df45d631067 -->
- navigation, forms, tables, dialogs, interaction design, and end-user application routing, with Angular Material as the primary UI system <!-- STEP7-11d02bd4b49e -->
- as defined by `ARCHITECTURE.md` §7.1 stage 4 <!-- STEP7-40d2ba4f60c5 -->
- Related automations may be packaged as PLUGINS, but those packaging <!-- STEP7-87660656d306 -->
- The user exports or dumps the OAS artifact to the path selected by <!-- STEP7-1318c05a12ca -->
- The user fires a build from the repository <!-- STEP7-7ac19d95c084 -->
- API-contract-derived artifacts, assembles the Angular app, and reports any stage- specific contract or input errors clearly <!-- STEP7-500c3cc89d08 -->
- For this flow: <!-- STEP7-e92386bf264c -->
- validation and acceptance behavior even if internal construction steps vary <!-- STEP7-245ba96014d7 -->
- Snapshot dated 2026-08-31: all **39 open issues** are ordered topologically so every open same-repository dependency appears before the issue it blocks, with issue number as the stable tie breaker. <!-- STEP7-661c7948b687 -->

### Corrected current identities

- The completed terminology alignment maps to GitHub issue #74 and the Construction plan's OpenAPI/OpenUI flow. <!-- STEP7-6ad8ca1764a5 -->

### Authoritative references

- Construction authority: APP_BUILDER_REQUIREMENTS, Change Model/Tool contracts, and executable wrapper/config sources. <!-- STEP7-122e041270f4 -->
- Verification authority: APP_BUILDER_REQUIREMENTS FR-8–FR-10, TEST_EXAMPLES, and test scenario contracts/specifications. <!-- STEP7-986767d3887e -->
- Configuration authority: SPECIFICATIONS §2, django_angular3/settings.py, and django_angular3/config.py. <!-- STEP7-3e19b7cad1df -->

## Wrappers and generation entry points

### Planning details

- schematics, templates, and assembly behavior defined by the authoritative `ngdj` sources in `ARCHITECTURE.md` §2.6. A missing capability is an upstream dependency, not a locally defined `ngdj` requirement. <!-- STEP7-dbf7c05c029c -->
- including `ngdj` schematics, through TOOL/wrapper contracts without requiring an agent or provider session. Optional AI-guided work may run through the agent using SKILLS only when the selected task is genuinely underspecified or non-deterministic. HOOKS provide lifecycle gates or mandatory side effects independently of either execution path. <!-- STEP7-c8c133d8e199 -->

### Open backlog

- [ ] Resolve ngdj facts through `doc/ARCHITECTURE.md` §2.6. The executable djng wrapper registry is `django_angular3/angular.py::_COMMAND_BUILDERS`, and `docs/commands.md` owns its public interface documentation. <!-- STEP7-3b6c35a1bc86 -->
- [ ] Decide whether service, class, field-component, form-field, application, project-structure, embed-component, and app-shell require dedicated wrappers, bounded composition, or explicit unsupported status. <!-- STEP7-b145635d5021 -->
- [ ] Add only wrappers justified by approved djng requirements; do not mirror the complete upstream schematic surface. <!-- STEP7-a3209638072a -->
- [ ] Label direct upstream usage as ngdj invocation and align workspace creation references with the composite `ng_workspace` flow. <!-- STEP7-ff3f7c36e73c -->
- [ ] Implement the decisions from §1 with dry-run, command-contract, and public interface coverage. <!-- STEP7-043f48e9ec7d -->
- [ ] `doc/requirements/APP_BUILDER_REQUIREMENTS.md` owns the complete orchestration requirements. Implement direct execution in the Construction plan, AI-guided sequencing in the Automation plan, and terminal acceptance in the Verification plan. <!-- STEP7-a6aa4bcf9d32 -->
- [ ] Execute wrappers, Tools, and Hooks in dependency order, halt on the first failure, and surface it through Django error handling. Keep `--dry-run` diagnostic-only and non-mutating. <!-- STEP7-583c06f32c9b -->
- [ ] Follow `doc/SKILL_AUTHORING_PLAN.md` for each Skill: plan, implement, test, integrate with `build_app`, and verify explicit acceptance criteria. <!-- STEP7-410358c1d7e3 -->
- [ ] Implement session lifecycle, Skill loading, Tool dispatch, Hook normalization, structured results, cancellation, timeouts, and credential handling without changing direct-execution semantics. <!-- STEP7-d26a5bebdbc7 -->
- [ ] Cover success, unmet acceptance, timeout or context exhaustion, Tool denial, Hook failure, evidence handling, and teardown with provider-independent stubs. <!-- STEP7-9e8985db4390 -->
- [ ] Implement and runtime-gate the Claude, OpenAI, Gemini, and Copilot adapters against the provider-neutral contract. <!-- STEP7-7494bc12219c -->
- [ ] Use `ng_build` as the compile gate and add the integration and global acceptance checks required by `doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-9. <!-- STEP7-a86e1cc62f25 -->
- [ ] Cover Windows and non-Windows defaults and explicit `tool.executables` values. <!-- STEP7-c75d7204b7eb -->
- [ ] Validate Python subprocess path resolution, environment handling, and shell invocation on Windows, Linux, and macOS. <!-- STEP7-fc0ed266e3a7 -->

## Change derivation

### Planning details

- Angular construction, including backend contract lifecycle governance, change-requirement derivation, orchestration-facing work definitions, generator-app execution, and governed command wrappers around `ngdj` actions <!-- STEP7-c9d76c4cc5d2 -->

### Open backlog

- [ ] Replace the coarse change categories in `build_app.py` with the canonical Change Model from `doc/contracts/CHANGE_MODEL_CONTRACTS.md` §2. <!-- STEP7-e85b0863cf08 -->
- [ ] Map each supported atomic change to its executable boundary, mode, inputs, ordering prerequisites, and terminal validation. Fail explicitly for every unsupported required change. <!-- STEP7-0a9f2900f04e -->

## OpenAPI/OpenUI construction flow

### Planning details

- OpenAPI schema re-extraction before the contract normalization stage proceeds <!-- STEP7-f17a5eee63ab -->
- A user designs or updates the OpenAPI specification using SmartBear's <!-- STEP7-7791373b593e -->
- OpenAPI authoring tools (Swagger Studio or SwaggerHub) <!-- STEP7-b58ecfa88943 -->
- `artifacts.openapiSchema` in the project configuration <!-- STEP7-3c33c2a98f0b -->
- The user adds the OpenUI concrete UI document describing pages, forms, <!-- STEP7-1c91ebae1acf -->
- navigation, workflows, and related UI concerns at the path selected by `artifacts.openuiSpecification` <!-- STEP7-28b57d6f506d -->
- The build validates the OAS and OpenUI artifacts, generates <!-- STEP7-bf9889f29c89 -->
- `artifacts.openapiSchema` <!-- STEP7-6619462cd5a8 -->
- document through `artifacts.openuiSpecification` <!-- STEP7-80f83b9549ef -->
- contract validation, code generation, OpenUI input validation, or final app assembly <!-- STEP7-052717bbb9a0 -->

### Open backlog

- [ ] Resolve baseline OpenAPI and OpenUI artifacts through the previous project configuration. Do not add a separate `--previous-openui` input or `.previous` OpenUI filename convention. <!-- STEP7-008ff620dcc7 -->
- [ ] Derive supported static-configuration, project-configuration, OpenAPI, and OpenUI `create`, `delete`, `update`, and `move` changes, including first-run creation when no baseline exists. <!-- STEP7-54300f866d17 -->
- [ ] Add `django-admin validate_openui <path>` as a thin wrapper around `validate_openui_file(path)`. Propagate upstream diagnostics without copying OpenUI grammar, catalog, or duplicate-ID validation logic. <!-- STEP7-46540e6cb004 -->
- [ ] Cover a valid document and propagation of an upstream `openui-spec` diagnostic. <!-- STEP7-32db7a941e4f -->
- [ ] OpenUI artifact roles remain defined by the external artifact-role SSOT linked from `doc/ARCHITECTURE.md` §2.8.1. <!-- STEP7-00ed43aacb33 -->
- [ ] Verify that `build_app` rejects an invalid OpenUI document before change derivation. <!-- STEP7-1d1137e2fc1f -->
- [ ] Transform validated canonical OpenUI atomic changes into explicit ngdj construction inputs without treating ngdj's package-local site assembly definition as a canonical OpenUI document. <!-- STEP7-42249912b4b3 -->
- [ ] Cover the transformation contract, unsupported changes, command ordering, dry-run non-modification, and composed generated-app output. <!-- STEP7-7a7c9fc8bc13 -->

### Corrected current identities

- OpenUI integration and source-derived terminology work map to GitHub issue #74 and the Construction plan's OpenAPI/OpenUI flow. <!-- STEP7-45590dc41ae7 -->

### Authoritative references

- OpenUI authority: external artifact-role SSOT via ARCHITECTURE §2.8.1; djng integration: APP_BUILDER_REQUIREMENTS and the Construction plan's OpenAPI/OpenUI construction flow. <!-- STEP7-b25a7343d316 -->

## Direct `build_app` execution

### Planning details

- Governed construction may consume only the Angular-side commands, <!-- STEP7-7cb5bf8dc07b -->

### Authoritative references

- Skill authority: SKILL_CONTRACTS.md and SKILL_AUTHORING_PLAN.md. <!-- STEP7-b2088701b5a7 -->

## Tracked GitHub issues

- [#56 — [shadow] Track ngdj construction capabilities required by djng](https://github.com/shlomoa/django-angular3/issues/56) <!-- STEP7-0d70132a303b -->
- [#57 — Complete djng generation entry points and governed ngdj wrappers](https://github.com/shlomoa/django-angular3/issues/57) <!-- STEP7-a8153bcd2c68 -->
- [#61 — Derive required work from the previously accepted state](https://github.com/shlomoa/django-angular3/issues/61) <!-- STEP7-99c0e6ca1925 -->
- [#62 — Trigger OpenAPI re-extraction after migration-producing backend changes](https://github.com/shlomoa/django-angular3/issues/62) <!-- STEP7-3ced2bd26cb4 -->
- [#63 — Add generation-compatibility gating and stage-specific first-build failures](https://github.com/shlomoa/django-angular3/issues/63) <!-- STEP7-3ef4d7a69ada -->
- [#66 — [shadow] Consume ngdj Angular frontend structure capability](https://github.com/shlomoa/django-angular3/issues/66) <!-- STEP7-1673df65ff9f -->
- [#74 — [integration] Assemble OpenAPI and OpenUI input streams across djng/ngdj](https://github.com/shlomoa/django-angular3/issues/74) <!-- STEP7-1c14a4dddea1 -->
- [#164 — Phase 9: implement direct build_app planning and execution](https://github.com/shlomoa/django-angular3/issues/164) <!-- STEP7-28c25df4c0af -->

Issue bodies, status, timestamps, relationships, dependency lists, and
acceptance criteria are intentionally not copied into this plan.
