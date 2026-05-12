# Implementation Plan

This document captures the implementation sequencing derived from
`doc/ARCHITECTURE.md`, `doc/REQUIREMENTS.md`, and
`doc/APP_BUILDER_REQUIREMENTS.md`, `doc/GENERATE_SKILLS.md`, and
`doc/TEST_EXAMPLES.md`, and `doc/SKILL_AUTHORING_PLAN.md`.

## Roadmap

After the architecture, requirements, and app-builder requirements are
accepted, implementation should proceed in this order:

1. **[Blocked — MR1]** Define the structured non-CRM input source schema, storage
   shape, and validation rules for reactive forms, pages, and other bespoke UI
   content.
   - Blocked by `TODO.md` MR1. The schema for `ui.pages`, `ui.components`, and
     `ui.forms` in `django-angular3.json` is not yet defined.

2. **[In progress]** Derive the complete set of `angular-django2` capabilities and
   `djng` command wrappers needed to materialize the required Angular-side outputs.
   - Wrappers implemented: `ng_new`, `ng_add`, `ng_config`, `ng_gen_app`,
     `ng_openapi_gen`, `ng_build`, `ng_workspace_delete`, `ng_workspace_modify`.
     Complete derivation aligned with all 11 SKILLS not yet done.

3. **[In progress]** Revise and finalize `GENERATE_SKILLS.md` with the complete set
   of SKILLS needed for bounded construction and integration.
   - Revise the `skill_creation` folder content to reflect the complete set of
     SKILLS, with detailed descriptions and example prompts for each.
   - Keep SKILL dependencies, shared context expectations, templates, and
     invocation boundaries aligned with `doc/GENERATE_SKILLS.md`.
   - Keep SKILL format, author-time vs run-time input handling, and wrapper
     execution boundaries aligned with `doc/SKILL_AUTHORING_PLAN.md`.
   - `GENERATE_SKILLS.md` revised (Invocation Model, Glossary). `skill_creation`
     content and complete SKILLS set not yet finalized.

4. **[Substantially implemented]** Implement the OpenAPI schema extraction, contract
   normalization, and breaking-change gate on the Django/DRF side.
   - oasdiff integration, breaking-change detection, and breaking-change gate
     implemented in `build_app.py`. Schema extraction via `drf-spectacular` is
     the consuming Django project's responsibility.

5. **[Substantially implemented]** Implement the `djng` generator app entry points
   and the governed wrappers around `ngdj` actions used for workspace, app,
   contract-derived, and non-CRM construction.
   - All wrappers implemented. Non-CRM construction wrappers depend on MR1.

6. **[Partially implemented]** Implement app-builder change detection, change
   classification, and deterministic build-plan emission from current and previous
   schema/config inputs.
   - Schema change detection, classification (start-from-scratch, add-things,
     remove-things, replace-things, breaking), and plan emission implemented in
     `build_app.py`.
   - Config change detection covers only project rename; pages, components, and
     forms change detection not implemented (blocked by MR1).
   - Plan currently emits CLI command strings. Must be replaced with SDK call
     specs (procedure graph) once item 8 is underway.
   - Keep build-plan behavior aligned with the scenarios and expected change
     paths documented in `doc/TEST_EXAMPLES.md`. The `spec/examples/` input
     files referenced by those scenarios do not yet exist (see `TODO.md`
     item 2); behavior cannot be verified against them until they are created.

7. **[Not started]** Create SKILLS: define the Claude Code API SKILLS needed to
   perform bounded generation, modification, and integration work.
   - Author each SKILL using the per-skill cadence defined in
     `doc/SKILL_AUTHORING_PLAN.md`: plan, implementation including tests,
     app-builder procedure integration, and verification.

8. **[Not started]** Implement the iterative orchestration flow using the Claude
   Code Python SDK, so construction can invoke the agent with SKILLS enabled
   until acceptance conditions are satisfied.

9. **[Not started]** Add automated verification across contract checks,
   construction-output checks, integration checks, and test-based verification.
   - Create the `spec/examples/` input files for scenarios 1, 2, 3, 5, and 6
     (unblocked). Scenario 4 depends on MR1. See `TODO.md` item 2.
   - Turn the scenarios in `doc/TEST_EXAMPLES.md` into executable acceptance
     cases for start-from-scratch, add, remove, replace, breaking-gate,
     config-only, and combined-change flows.
   - Verify each authored SKILL using the packaging and review expectations in
     `doc/SKILL_AUTHORING_PLAN.md` before treating it as ready for orchestration.

10. **[Not started]** Build one business module end to end using the generator app,
    app builder, SKILLS, and wrappers together.

11. **[Not started]** Add audit logging, health checks, generator verification, and
    staging smoke tests.
