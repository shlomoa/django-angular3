# Test Scenario Specifications

## 1. Purpose and scope

This document defines the exact realization of the `build_app` scenario suite:
shared fixture conventions, storage locations, invocation, input selection, and
coverage axes. Scenario-specific input documents, expected atomic changes, and
expected command sequences remain examples in [TEST_EXAMPLES.md].

The required boundary between each scenario, its selected inputs, and its
expected test oracles is defined in [TEST_SCENARIO_CONTRACTS.md].

This document does not define product behavior, the Change Model, command
translation, automation contracts, or implementation sequencing. Those are
owned by [APP_BUILDER_REQUIREMENTS.md], [CHANGE_MODEL_CONTRACTS.md], the
automation contract owners under `doc/contracts/`, and the [Automation Plan].

## 2. Scenario organization

The suite contains twelve numbered scenarios:

- Example 1 is the packaged tutorial fixture at
  `django_angular3/examples/01_simple_crm/`. It is installable through
  `django-angular3 install-tutorial`.
- Examples 2–12 are development fixtures under
  `tests/fixtures/scenarios/<scenario-id>/`.
- `tests/fixtures/scenarios/scenario-matrix.json` maps development scenario IDs
  to their active coverage axes and optional shared static-configuration
  snapshots.

All scenarios use `shop` as the primary Django app and Angular app. Project
names may vary. A project-configuration, OpenAPI, OpenUI, or static-tool
configuration change evolves that app; it does not replace the app identity.

The exact project-configuration discovery, previous-configuration derivation,
and relative artifact resolution rules are defined in [SPECIFICATIONS.md]
§2.2. The Change Model is defined in [CHANGE_MODEL_CONTRACTS.md] §2, and command selection
and ordering are defined in [APP_BUILDER_REQUIREMENTS.md].

## 3. Scenario invocation

After `build_app` planning is implemented, a development fixture is exercised
from its scenario directory with explicit inputs:

```bash
cd tests/fixtures/scenarios/<scenario-id>
django-admin build_app \
  --current-config current-project-configuration.json \
  --previous-config previous-project-configuration.json \
  --dry-run
```

Arguments may be omitted to exercise the discovery and derivation rules in
[SPECIFICATIONS.md] §2.2. A missing derived previous project configuration
selects the first-run path. The current planner is not implemented, so the
scenario suite specifies target verification rather than runnable current
behavior.

The matrix validation test verifies each fixture's selected inputs. It also
verifies the current/previous fixture pairs required by schema-removal and
OpenUI-source-selection scenarios.

## 4. Shared static-configuration snapshots

Examples 4, 10, 11, and 12 select these snapshots through
`tests/fixtures/scenarios/scenario-matrix.json`:

| Role | Fixture |
|---|---|
| Accepted baseline | `tests/fixtures/scenarios/shared/static-config/workspace-style-scss.json` |
| Candidate | `tests/fixtures/scenarios/shared/static-config/workspace-style-css.json` |

These fixtures exercise `compare_static_config()` directly. They do not define
a public static-configuration path argument or the pending `build_app`
accepted-state persistence mechanism.

## 5. Provider-adapter verification boundary

Scenario tests verify change derivation and generated-app construction. They do
not replace provider-adapter conformance tests.

When a scenario crosses an adapter boundary, it uses a provider-independent
stub. Real credentials are used only by the selected provider's opted-in
runtime integration suite. The provider-neutral behavior is defined in
[PROVIDER_ADAPTER_CONTRACTS.md] §Provider adapter contracts, and its test
sequencing is defined in the [Automation Plan].

## 6. Three-axis coverage matrix

The incremental suite covers every Boolean combination of changes to the
configuration, OpenAPI, and OpenUI scenario axes. These coverage axes are not
the four canonical Change Model domains.

| Configuration change | OpenAPI change | OpenUI change | Scenario |
|:---:|:---:|:---:|---|
| | | | 9 No Change |
| ✓ | | | 4 Workspace Configuration |
| | ✓ | | 2 Add Resource |
| | | ✓ | 6 OpenUI Change |
| ✓ | ✓ | | 10 Configuration + OpenAPI |
| ✓ | | ✓ | 11 Configuration + OpenUI |
| | ✓ | ✓ | 7 OpenAPI + OpenUI |
| ✓ | ✓ | ✓ | 12 Configuration + OpenAPI + OpenUI |

Additional scenario coverage is:

| Concern | Scenario |
|---|---|
| Start from scratch | 1 Simple CRM |
| OpenAPI removal | 3 Schema Removal |
| OpenUI source selection without structural OpenUI change | 5 OpenUI-Source Configuration |
| OpenAPI replacement | 8 Full Replacement |

[APP_BUILDER_REQUIREMENTS.md]: ../requirements/APP_BUILDER_REQUIREMENTS.md
[CHANGE_MODEL_CONTRACTS.md]: ../contracts/CHANGE_MODEL_CONTRACTS.md
[Automation Plan]: ../plan/AUTOMATION_PLAN.md#dependency-ordered-implementation-phases
[PROVIDER_ADAPTER_CONTRACTS.md]: ../contracts/PROVIDER_ADAPTER_CONTRACTS.md
[SPECIFICATIONS.md]: SPECIFICATIONS.md
[TEST_EXAMPLES.md]: ../TEST_EXAMPLES.md
[TEST_SCENARIO_CONTRACTS.md]: ../contracts/TEST_SCENARIO_CONTRACTS.md
