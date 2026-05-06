# Implementation Plan

This document captures the implementation sequencing derived from
`doc/ARCHITECTURE.md`, `doc/REQUIREMENTS.md`, and
`doc/APP_BUILDER_REQUIREMENTS.md`, `doc/GENERATE_SKILLS.md`, and
`doc/TEST_EXAMPLES.md`, and `doc/SKILL_AUTHORING_PLAN.md`.

## Roadmap

After the architecture, requirements, and app-builder requirements are
accepted, implementation should proceed in this order:

1. Finalize `REQUIREMENTS.md` and `APP_BUILDER_REQUIREMENTS.md`, including the
   construction, change-derivation, verification, and acceptance requirements.
2. Define the structured non-CRM input source schema, storage shape, and
   validation rules for reactive forms, pages, and other bespoke UI content.
3. Derive the complete set of `angular-django2` capabilities and `djng`
   command wrappers needed to materialize the required Angular-side outputs.
4. Revise and finalize `GENERATE_SKILLS.md` with the complete set of SKILLS
   needed for bounded construction and integration.
   - Revise the `skill_creation` folder content to reflect the complete set of
     SKILLS, with detailed descriptions and example prompts for each.
   - Keep SKILL dependencies, shared context expectations, templates, and
     invocation boundaries aligned with `doc/GENERATE_SKILLS.md`.
    - Keep SKILL format, author-time vs run-time input handling, and wrapper
       execution boundaries aligned with `doc/SKILL_AUTHORING_PLAN.md`.
5. Implement the OpenAPI schema extraction, contract normalization, and
   breaking-change gate on the Django/DRF side.
6. Implement the `djng` generator app entry points and the governed wrappers
   around `ngdj` actions used for workspace, app, contract-derived, and
   non-CRM construction.
7. Implement app-builder change detection, change classification, and
   deterministic build-plan emission from current and previous schema/config
   inputs.
   - Keep build-plan behavior aligned with the scenarios and expected change
     paths documented in `doc/TEST_EXAMPLES.md`.
8. Create SKILLS: define the Claude Code API SKILLS needed to perform bounded
   generation, modification, and integration work.
   - Author each SKILL using the per-skill cadence defined in
     `doc/SKILL_AUTHORING_PLAN.md`: plan, implementation including tests,
     app-builder procedure integration, and verification.
9. Implement the iterative orchestration flow using the `Claude Code Python
   SDK`, so construction can invoke, inspect, repair, and re-invoke SKILLS
   until acceptance conditions are satisfied.
10. Add automated verification across contract checks, construction-output
    checks, integration checks, and test-based verification.
   - Turn the scenarios in `doc/TEST_EXAMPLES.md` into executable acceptance
     cases for start-from-scratch, add, remove, replace, breaking-gate,
     config-only, and combined-change flows.
   - Verify each authored SKILL using the packaging and review expectations in
     `doc/SKILL_AUTHORING_PLAN.md` before treating it as ready for orchestration.
11. Build one business module end to end using the generator app, app builder,
    SKILLS, and wrappers together.
12. Add audit logging, health checks, generator verification, and staging
    smoke tests.
