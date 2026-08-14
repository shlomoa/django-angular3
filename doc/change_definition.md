# Change Model Implementation Plan

`REQUIREMENTS.md` §4.2.9 is the sole normative definition of the Change Model,
including `Change`, `ChangeSet`, domains, operations, identity rules, and
baseline/candidate semantics. This document records the implementation plan and
must not restate or redefine that model.

## Implementation plan

### 1. Establish the specification first

Update the canonical requirements documentation before implementation:

- Add **Change Model** terminology to `REQUIREMENTS.md`.
- Define `Change`, `ChangeOperation`, domain names, identity rules, and baseline/candidate semantics.
- Revise `APP_BUILDER_REQUIREMENTS.md`:
  - replace the single string `type` model with atomic changes plus summaries;
  - remove legacy category-model definitions; and
  - reference the canonical `ChangeSet` schema in `REQUIREMENTS.md` §4.2.9.
- Keep `ARCHITECTURE.md` at the architectural level: it should state that construction is driven by typed changes, not Python implementation mechanics.

### 2. Audit and establish a single domain model

#### 2.1. Inventory existing behavior

Before adding or moving code, inventory all existing change/diff models,
dataclasses, dictionaries, enums, helpers, serializers, durable artifacts, and
tests. Trace their producers and consumers, including `build_app`,
`_extract_resources()`, `_evaluate_schema_changes()`, configuration loading and
validation, OpenAPI diff handling, and OpenUI handling.

#### 2.2. Classify and reconcile findings

For each inventory finding, decide and document one outcome:

- retain unchanged because it already implements the canonical model;
- adapt it into the canonical model;
- remove it because it is stale, invalid, duplicate, or superseded; or
- defer it to its documented external owner, such as OpenUI semantics in
  `openui-spec`.

Do not allow a legacy category model and the atomic Change Model to coexist.

#### 2.3. Select the canonical ownership boundary

Only after reconciliation, decide whether an existing module can own the
canonical model without coupling or duplication. Add a dedicated module such
as `django_angular3/changes.py` only when no existing owner is appropriate.

The selected implementation must provide:

- `ChangeDomain` enum;
- `ChangeOperation` enum: `create`, `delete`, `update`, `move`;
- immutable `Change`, `ChangeEvidence`, `ChangeDomainResult`, and `ChangeSet`
  dataclasses; and
- deterministic serialization and stable identifier generation.

#### 2.4. Migrate and protect the boundary

Replace superseded representations and update their consumers. Add or revise
tests for retained behavior, changed behavior, and removed pathways so stale
representations cannot silently survive.

### 3. Build common comparison infrastructure

Implement shared utilities:

- canonical JSON normalization;
- JSON Pointer-like semantic paths;
- deterministic scalar/list/map comparison;
- content digest calculation;
- ordered-list comparison for OpenUI;
- explicit unsupported-key and invalid-input handling.

This shared layer must not infer OpenAPI or OpenUI meaning; it only provides normalized comparison primitives.

### 4. Implement static configuration change derivation

#### 4.1. Audit existing static-configuration behavior

Inventory existing static configuration loading, validation, comparison, and
invocation derivation. Identify schema-supported fields, existing consumers,
and any overlapping or stale change-related behavior before adding a comparator.

#### 4.2. Reconcile the static-configuration boundary

Retain, adapt, or remove the audited behavior according to the canonical Change
Model. Ensure the validated static configuration schema remains the sole
authority for supported semantic paths.

#### 4.3. Implement the comparator

Add a static-config comparator only after the audit and reconciliation steps.
It must:

- load and validate both static configurations;
- compare only schema-supported fields;
- treat allowlist entries as set members;
- derive downstream invocation changes; and
- reject unknown or untranslatable configuration changes.

This must include the pending/declared `oasdiff` configuration field, rather than silently omitting it because the current checked-in `django-angular3.json` lacks that clause.

#### 4.4. Verify migration and derivation

Add tests for every supported static field, retained behavior, rejected unknown
keys, and removed or superseded pathways.

### 5. Implement project configuration change derivation

Add a project-config comparator that:

- compares the four canonical project fields;
- classifies selectors separately from selected content;
- records path relocation without conflating it with content change;
- requires baseline configuration explicitly or derives it through the documented `.previous.json` rule.

Also correct `ProjectConfig` to align with §4.2.4 before treating it as a complete source of typed changes: it currently accepts values that should be constrained by the requirements and has an invalid `dataclass` + `dict` inheritance design.

### 6. Derive and compare invocation snapshots

For each wrapper:

1. resolve the canonical project/static settings;
2. generate an `InvocationSnapshot` containing wrapper name, `argv`, `cwd`, derived-file content, effective executable, and allowlist status;
3. compare baseline and candidate snapshots;
4. emit `invocation` changes linked back to their source changes.

This produces explainable dry-run output without creating a second configuration source.

### 7. Replace path-only OpenAPI summarization

Replace `_extract_resources()` and `_evaluate_schema_changes()` with an OpenAPI evaluator that:

- maps supported oasdiff JSON detail into atomic OpenAPI changes;
- records affected OpenAPI subjects and source oasdiff evidence;
- derives resource/module hints only after preserving full contract identity;
- treats unsupported oasdiff output shape as an explicit error, never as “no change.”

The current private helper may remain temporarily as a summary projection of the richer OpenAPI change list, but it must not be the source of truth.

### 8. Implement OpenUI structural changes

Use the OpenUI document’s declared `id`, `type`, `attrs`, and ordered `children` to emit node-level changes:

- node creation/deletion;
- attribute-level updates;
- type changes;
- parent/ordering moves;
- OAS-reference dependency impacts.

Missing, duplicate, or invalid node identities must fail validation before comparison.

### 9. Translate typed changes to commands and gates

Replace broad category branching with a mapping from:

```text
(domain, subject, operation) → commands, order, validation
```

Examples:

- OpenAPI response-schema `update`  
  → targeted dependent client/UI commands and validation.
- `ngOpenApiGen.serviceSuffix` update  
  → regenerate API client, validate generated imports.
- OpenUI node `move`  
  → targeted page/site composition update, not a full rebuild.
- `tool.commandAllowlist` deletion  
  → reject any selected command that is no longer authorized.

Every mapping must be explicit; unhandled combinations must fail before execution.

### 10. Test at every layer

Add tests for:

- atomic model serialization/stable IDs;
- static setting changes for every supported field;
- every project configuration field;
- all invocation snapshot dimensions;
- OpenAPI create/delete/update/mixed cases;
- OpenUI node/attribute/type/order/parent changes;
- missing baseline / start-from-scratch behavior;
- unsupported fields and unknown diff structures;
- deterministic same-input results;
- command/gate selection from each supported change type.

Only after these tests exist should `build_app` stop raising `NotImplementedError` and use the ChangeSet in its public flow.
