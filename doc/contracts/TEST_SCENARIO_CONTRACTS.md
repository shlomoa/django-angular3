# Test Scenario Contracts

## 1. Purpose and scope

This document defines the canonical boundary between a documented `build_app`
scenario, its fixture inputs, and its expected test oracles. It does not define
scenario storage, invocation, or coverage topology; those realization details
are specified in [TEST_SCENARIO_SPECIFICATIONS.md]. Concrete scenario values
and expected outcomes are documented in [TEST_EXAMPLES.md].

This contract does not redefine the `Change`, `ChangeSet`, automation, OpenAPI,
or OpenUI contracts. Scenario records consume those contracts from
[CHANGE_MODEL_CONTRACTS.md], [TOOL_CONTRACTS.md], [HOOK_CONTRACTS.md],
[SKILL_CONTRACTS.md], [PROVIDER_ADAPTER_CONTRACTS.md], and the upstream OpenAPI and
OpenUI specifications.

## 2. Scenario case contract

Every documented scenario case has these elements:

| Element | Contract |
|---|---|
| Identity | A unique scenario number and stable descriptive name. |
| Purpose | The behavior, change combination, or boundary demonstrated by the scenario. |
| Inputs | The current and, when applicable, baseline project configuration, static tool configuration, OpenAPI document, and OpenUI document selected for the case. |
| Expected changes | Atomic changes expressed using the canonical `Change` operations, domains, and `ChangeSet` boundary in [CHANGE_MODEL_CONTRACTS.md] §2. |
| Expected commands | The ordered command identities, modes, affected subjects, and verification step expected from command translation. They must conform to [APP_BUILDER_REQUIREMENTS.md] and the canonical automation identities in [TOOL_CONTRACTS.md], [HOOK_CONTRACTS.md], [SKILL_CONTRACTS.md], and [PROVIDER_ADAPTER_CONTRACTS.md]. |

A scenario may refer to a shared fixture or a prior scenario rather than repeat
an unchanged input. The resulting selected current and baseline inputs must
remain unambiguous.

## 3. Contract-instance boundary

OpenAPI, OpenUI, and project-configuration blocks embedded in a scenario are
concrete test inputs. They do not define or extend their underlying schemas.
Likewise, expected atomic changes and command sequences are test oracles for
that input combination; they do not create new Change operations, domains,
command modes, Tool identities, Hook identities, or Skill identities.

If a scenario needs an identity, field, operation, mode, or consequence not
owned by an existing contract, the owning contract must be updated before the
scenario may use it as an expected result.

[CHANGE_MODEL_CONTRACTS.md]: CHANGE_MODEL_CONTRACTS.md
[HOOK_CONTRACTS.md]: HOOK_CONTRACTS.md
[PROVIDER_ADAPTER_CONTRACTS.md]: PROVIDER_ADAPTER_CONTRACTS.md
[SKILL_CONTRACTS.md]: SKILL_CONTRACTS.md
[TOOL_CONTRACTS.md]: TOOL_CONTRACTS.md
[APP_BUILDER_REQUIREMENTS.md]: ../requirements/APP_BUILDER_REQUIREMENTS.md
[TEST_EXAMPLES.md]: ../TEST_EXAMPLES.md
[TEST_SCENARIO_SPECIFICATIONS.md]: ../specifications/TEST_SCENARIO_SPECIFICATIONS.md
