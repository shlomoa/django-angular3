# Change Model Contracts

## 1. Purpose and scope

This document defines normative data and interface boundaries shared by
`djng` components for change modeling.
It does not define product requirements, platform structure, architecture,
automation contracts, or implementation sequencing.

The requirements corpus is indexed by [REQUIREMENTS.md]. Exact platform
structures are defined in [SPECIFICATIONS.md]. Tool, Hook, Provider Adapter,
Plugin, and Skill contracts are defined in:

- [TOOL_CONTRACTS.md]
- [HOOK_CONTRACTS.md]
- [PROVIDER_ADAPTER_CONTRACTS.md]
- [PLUGIN_CONTRACTS.md]
- [SKILL_CONTRACTS.md]

The `build_app` command requirements and command translation behavior are
defined in [APP_BUILDER_REQUIREMENTS.md].
Exact AI automation realization is defined in
[AI_AUTOMATION_SPECIFICATIONS.md].
The documented build-scenario case boundary is defined in
[TEST_SCENARIO_CONTRACTS.md].

OpenAPI and OpenUI are external input contracts governed by their own
specifications; this document does not redefine them.

## 2. Change Model contract

This section is the canonical definition of the Change Model. It governs how
`djng` represents differences between accepted prior inputs and candidate
inputs for construction and validation command selection.
[APP_BUILDER_REQUIREMENTS.md] defines the resulting command translation; it
must not define a competing Change Model.

### 2.1. Change

A **Change** is an immutable, typed statement that a supported input's
normalized semantic state differs between an accepted **baseline** and a
**candidate**. It is neither a command nor a build plan.

| Field | Contract |
|---|---|
| `domain` | One of `static_config`, `project_config`, `openapi`, or `openui`. |
| `subject` and `path` | A stable semantic identity and JSON Pointer-like path for the changed item. |
| `operation` | One of `create`, `delete`, `update`, or `move`. |
| `before` and `after` | Normalized values or content fingerprints. |
| `affected` | Typed identities that support command selection. |
| `evidence` | Source locations, structured diff fragments, and/or validation results supporting the change. |

An atomic `Change` must not use `no_change`. An empty atomic-change list means
there is no change in that domain; `no_change` is permitted only as a computed
summary. The model has no compatibility, breaking-change, or regeneration-
impact classification. Command translation is the sole authority that derives
required regeneration and validation from each atomic change.

### 2.2. Domain comparison semantics

The four domains compare normalized semantic state rather than raw file bytes:

| Domain | Compared semantic state | Identity requirement |
|---|---|---|
| `static_config` | Schema-supported fields in `django-angular3.json` | Validated configuration paths. |
| `project_config` | Project identity and artifact selectors in `django-angular3-<project_name>.json` | Project configuration paths; selector changes remain distinct from selected-content changes. |
| `openapi` | Structured `oasdiff` contract detail | Stable OpenAPI subject identity, not a final URL segment heuristic. |
| `openui` | Structural diff emitted by [OpenUI comparison] | Declared node `id`; identified-list reordering is not a change. |

`djng` must invoke the upstream [OpenUI comparison] utility with the accepted
reference document first and the candidate document second. It translates the
utility's `remove`, `add`, and `change` entries into `delete`, `create`, and
`update` Changes respectively. `djng` must not implement a competing OpenUI
comparison algorithm.

`move` is reserved for identity-preserving relocation. If identity cannot be
established, comparison must emit `delete` plus `create` instead. Invalid or
unknown input must fail validation; it must not be represented as an unknown
change.

A missing baseline initializes the relevant domain and emits `create` changes
for the candidate state. For project artifact selectors, the selector change
and the selected OpenAPI or OpenUI content change are separate facts.

### 2.3. ChangeSet

A `ChangeSet` carries domain-specific atomic changes and a computed summary:

```json
{
  "version": 1,
  "baseline": {
    "projectConfig": "django-angular3-portal.previous.json"
  },
  "candidate": {
    "projectConfig": "django-angular3-portal.json"
  },
  "domains": {
    "static_config": { "changes": [] },
    "project_config": { "changes": [] },
    "openapi": { "changes": [] },
    "openui": { "changes": [] }
  },
  "summary": { "hasChanges": true }
}
```

[AI_AUTOMATION_SPECIFICATIONS.md]: ../specifications/AI_AUTOMATION_SPECIFICATIONS.md
[APP_BUILDER_REQUIREMENTS.md]: ../requirements/APP_BUILDER_REQUIREMENTS.md
[HOOK_CONTRACTS.md]: HOOK_CONTRACTS.md
[OpenUI comparison]: https://openui-spec.readthedocs.io/en/latest/tooling/comparison/
[PLUGIN_CONTRACTS.md]: PLUGIN_CONTRACTS.md
[PROVIDER_ADAPTER_CONTRACTS.md]: PROVIDER_ADAPTER_CONTRACTS.md
[REQUIREMENTS.md]: ../requirements/REQUIREMENTS.md
[SKILL_CONTRACTS.md]: SKILL_CONTRACTS.md
[SPECIFICATIONS.md]: ../specifications/SPECIFICATIONS.md
[TEST_SCENARIO_CONTRACTS.md]: TEST_SCENARIO_CONTRACTS.md
[TOOL_CONTRACTS.md]: TOOL_CONTRACTS.md
