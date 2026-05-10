# App Builder Requirements

## Purpose

**`rapp`** is the resulting integrated Django-Angular application — the artifact
`build_app` receives, modifies, and delivers.

djng provides two categories of Django admin commands for producing `rapp`:

- **Deterministic commands**: produce correct-by-construction outputs without
  iteration — schema extraction from DRF models, direct ngdj wrapper calls,
  and similar bounded operations.
- **`build_app`**: the SKILLS-based orchestration command that drives
  change-detected construction of `rapp`.

`build_app` is invoked as:

```bash
django-admin build_app <config> [options]
# or equivalently:
python manage.py build_app <config> [options]
```

`build_app` takes an existing `rapp` (initially empty on first run), two
OpenAPI schemas (current and previous, previous initially empty on first run),
and a configuration file. It operates through three internal layers:

**Layer 1 — Change derivation**: Compares the current schema against the
previous schema using `oasdiff`, and the current config against the previous
config. Produces a typed `ChangeSet` and maps it to the set of SKILLS that
must be invoked and in what mode.

**Layer 2 — Procedure graph**: Translates the Layer 1 output into a directed
graph of procedures. Each procedure represents a unit of construction work.
The graph encodes the SKILLS dependency chain and ordering constraints derived
from the ChangeSet (delete before create at the same dependency level).

**Layer 3 — SKILLS execution**: Each procedure in the graph prepares the
inputs for a Claude Code Python SDK API call that invokes one or more SKILLS.
SKILLS are three-phase wrapper scripts that: (1) call ngdj schematics to
generate code, (2) modify the generated code as required, and (3) integrate
it into `rapp`.

---

## Inputs

### Required

| Input | Source | Format | Notes |
|---|---|---|---|
| App configuration | `django-angular3.json` in the generated app root | JSON, hierarchical settings schema | Must contain `project.name`, `openapi.source`, `angular.output` |
| OpenAPI schema | Path from `openapi.source` in config | YAML or JSON (OAS 3.x) | The current schema version |

### Optional

| Input | Flag | Notes |
|---|---|---|
| Previous schema | `--previous-schema <path>` | OAS file from prior build. If absent, the builder treats the run as start-from-scratch. |
| Previous config | `--previous-config <path>` | Prior `django-angular3.json`. If absent, config change detection is skipped. |
| Output format | `--output-format json\|yaml\|text` | Format for the emitted build plan. Default: `json`. |
| Dry run | `--dry-run` | Print the plan without writing it to disk. |
| Plan output path | `--output <dir>` | Write the plan to `<dir>/build-plan.<ext>`. Default: `build/`. |
| Force mode | `--force start-from-scratch` | Override change detection; treat as start-from-scratch regardless of diff. |

### Configuration keys read by the app builder

From the generated app's `django-angular3.json`:

| Key | Required | Purpose |
|---|---|---|
| `project.name` | yes | Workspace and app name |
| `openapi.source` | yes | Path to the current OpenAPI schema |
| `angular.output` | yes | Workspace root path |
| `angular.workspace.*` | no | Workspace settings (package manager, style, routing) |
| `ui.source` | no | Path to the non-CRM UI definition file |
| `ui.pages` | no | Inline page definitions (alternative to `ui.source`) |
| `ui.components` | no | Inline component definitions |
| `ui.forms` | no | Inline reactive form definitions |

---

## Layer 1: Change Derivation

### Schema change detection

Schema comparison uses `oasdiff`. The builder runs:

```bash
oasdiff diff <previous-schema> <current-schema> --format json
```

oasdiff output is parsed to classify each difference.

If `--previous-schema` is not supplied, or the previous schema file does not
exist, the change type is `start-from-scratch` for all schema-derived skills.

#### Schema change types

| Type | oasdiff signal | Meaning |
|---|---|---|
| `start-from-scratch` | No previous schema | First build; generate everything |
| `no-change` | oasdiff diff is empty | Schema identical; skip all schema-driven skills |
| `add-things` | Only additions in oasdiff output | New endpoints, resources, or properties added |
| `remove-things` | Only removals | Endpoints, resources, or properties deleted |
| `replace-things` | Both additions and removals | Existing things modified (treated as remove + add at the resource level) |
| `breaking` | oasdiff reports breaking changes | Breaking changes present; builder emits a warning and halts unless `--acknowledge-breaking` flag is set |

#### Breaking change gate

When oasdiff reports breaking changes, the app builder must stop and output:

```
Breaking schema changes detected. Review the oasdiff report before proceeding.
Re-run with --acknowledge-breaking to continue.
```

This matches the contract normalization requirement in `doc/REQUIREMENTS.md`.

### Config change detection

Config comparison is a structural diff of the two `django-angular3.json` files.
The builder diffs the following sections:

| Section | Change meaning |
|---|---|
| `angular.workspace.*` | Workspace-level reconfiguration |
| `ui.pages` / `ui.source` (page definitions) | Pages added, removed, or modified |
| `ui.components` | Standalone components added, removed, or modified |
| `ui.forms` | Reactive forms added, removed, or modified |
| `project.name` | Workspace/app rename — treated as start-from-scratch |

If `--previous-config` is not supplied, config change detection is skipped and
config-derived skills are treated as `no-change` (they run only if triggered by
schema changes).

---

## Change Classification Summary

The builder produces a `ChangeSet` object:

```json
{
  "schema": {
    "type": "add-things | remove-things | replace-things | start-from-scratch | no-change | breaking",
    "affected_resources": ["Customer", "Order"],
    "breaking": false,
    "oasdiff_report": "<path-to-report>"
  },
  "config": {
    "type": "add-things | remove-things | replace-things | no-change",
    "affected_pages": ["dashboard"],
    "affected_components": [],
    "affected_forms": ["customer-edit"]
  }
}
```

---

## Layer 1 Output: Change-to-SKILLS Mapping

Layer 1 maps each change type to the set of SKILLS to invoke, using the
dependency order defined in `doc/SKILL_AUTHORING_PLAN.md`.

### Schema change → SKILLS

| Schema change type | SKILLS invoked | Notes |
|---|---|---|
| `start-from-scratch` | 1, 2, 3, 4, then config-derived SKILLS | Full pipeline |
| `no-change` | None (schema-derived) | Config-derived SKILLS still run if config changed |
| `add-things` | 3 (`ng-api`), 4 (`ng-data-service`) for new resources, then component/page SKILLS for new resources | Existing workspace and app untouched |
| `remove-things` | 3 (`ng-api`), 4 (`ng-data-service`) in delete mode, component/page SKILLS for removed resources in delete mode | |
| `replace-things` | Same as remove-things for removed resources, then add-things for new resources | Order: remove first, then add |
| `breaking` | Blocked — see Breaking change gate above | |

### Config change → SKILLS

| Config change | SKILL | Mode |
|---|---|---|
| Page added | 10 (`ng-page`) | create |
| Page modified | 10 (`ng-page`) | modify |
| Page removed | 10 (`ng-page`) | delete |
| Standalone component added | 7 (`ng-component`) | create |
| Standalone component modified | 7 (`ng-component`) | modify |
| Complex component added | 8 (`ng-complex-component`) | create |
| Reactive form added | 9 (`ng-reactive-form`) | create |
| Reactive form modified | 9 (`ng-reactive-form`) | modify |
| Site navigation changed | 11 (`ng-site`) | modify |
| Workspace settings changed | 1 (`ng-workspace`) | modify |

## Layer 2: Procedure Graph

Layer 2 translates the Layer 1 SKILLS mapping into a directed acyclic graph of
procedures. Each node in the graph is a procedure: a SKILL name, invocation
mode, reason, SDK inputs, and its dependency edges. The graph encodes the
following SKILLS dependency chain:

```
1  ng-workspace   (foundation)
2  ng-app         (depends on 1)
3  ng-api         (depends on 2)
4  ng-data-service (depends on 3)
5  ng-small-field  (depends on 2)
6  ng-form-field   (depends on 2)
7  ng-component    (depends on 2)
8  ng-complex-component (depends on 2)
9  ng-reactive-form (depends on 2, 6; optionally 4)
10 ng-page         (depends on 2; composes 4, 7, 8, 9)
11 ng-site         (composes 2–10)
```

SKILLS not triggered by any change in the current run are omitted from the
graph. Procedures that invoke a SKILL in delete mode for removed resources
precede procedures that invoke in create/add mode for new resources at the
same dependency level.

### JSON representation (default)

```json
{
  "generated_at": "2026-04-30T12:00:00Z",
  "config": "path/to/django-angular3.json",
  "change_set": { ... },
  "procedures": [
    {
      "id": "ng-api-create-Order",
      "skill": "ng-api",
      "mode": "create",
      "reason": "New resource 'Order' added to schema",
      "inputs": {
        "resource": "Order",
        "config": "path/to/django-angular3.json"
      },
      "depends_on": []
    },
    {
      "id": "ng-data-service-create-Order",
      "skill": "ng-data-service",
      "mode": "create",
      "reason": "New resource 'Order' requires data service",
      "inputs": {
        "resource": "Order",
        "config": "path/to/django-angular3.json"
      },
      "depends_on": ["ng-api-create-Order"]
    }
  ]
}
```

### Constraints on the procedure graph

- The graph is a directed acyclic graph: no circular dependencies.
- Each procedure includes `reason` — a human-readable explanation of why it
  is included.
- The graph is deterministic: the same inputs always produce the same graph.
- Procedures not triggered by any change in the current run are omitted.
- Layer 3 traverses the graph in dependency order, invoking each procedure
  via the Claude Code Python SDK.

---

## Functional Requirements

### FR-1: Change detection

- The builder must detect schema changes using `oasdiff`.
- The builder must halt on breaking schema changes unless `--acknowledge-breaking` is set.
- The builder must detect config changes by diffing the `django-angular3.json` files.
- If no previous state is available, the builder treats the run as
  `start-from-scratch`.

### FR-2: Procedure graph generation

- The procedure graph must be deterministic for the same inputs.
- The graph must encode the SKILLS dependency chain as dependency edges.
- Each procedure must include a `reason` for its inclusion.
- Procedures not triggered by any change in the current run must be omitted.

### FR-3: Dry run

- `--dry-run` must emit the procedure graph without invoking any SKILLS or
  executing any SDK calls.
- The emitted graph must be inspectable and human-readable.

### FR-4: Breaking change gate

- When oasdiff detects breaking changes, the builder must stop, print the
  oasdiff report summary, and exit with a non-zero code.
- Breaking changes must only be bypassed with `--acknowledge-breaking`.

### FR-5: Start-from-scratch mode

- `--force start-from-scratch` overrides change detection and schedules all
  eleven skills in dependency order.

### FR-6: Config-only changes

- When the schema has not changed (`no-change`) but the config has changed,
  only config-derived skills are included in the plan.
- Schema-derived skills are not re-run unless triggered by a schema change.

### FR-7: Combined changes

- When both schema and config change, schema-derived procedures are ordered
  before config-derived procedures at the same dependency level.

### FR-8: SKILLS execution

- Layer 3 must traverse the procedure graph in dependency order.
- Each procedure must be executed via a Claude Code Python SDK API call
  invoking the specified SKILL with the specified inputs.
- SKILLS must follow the three-phase contract: (1) call ngdj schematics,
  (2) modify generated output, (3) integrate into `rapp`.

---

## Non-Functional Requirements

- Layers 1 and 2 (change derivation and procedure graph construction) must
  complete in under 30 seconds for typical schema/config sizes, excluding
  `oasdiff` execution time which is treated as an external process. Layer 3
  execution time is unbounded as it depends on Claude Code SDK call duration.
- The builder must be testable with mock oasdiff output so `oasdiff` does not
  need to be installed to run the test suite.
- The procedure graph must be emitted in machine-readable format (JSON/YAML)
  so it can be inspected by CI pipelines before or after execution.

---

## Open Questions

1. **Schema format**: The current djng config uses `openapi.source` pointing to
   a JSON file. The app builder should support both YAML and JSON OpenAPI files.
   Confirm whether the user always provides YAML (`schema.yaml`) or whether
   both formats must be accepted.

2. **UI definition format**: The `ui.source` currently points to a JSON file
   (`spec/ui/example.ui.json`). Define the schema for inline `ui.pages`,
   `ui.components`, and `ui.forms` in `django-angular3.json` before
   implementing config change detection.

3. **Previous-state storage**: How is the previous schema/config stored?
   Options: (a) git — the builder diffs HEAD vs working tree or two commits;
   (b) a committed baseline file (e.g., `spec/openapi/previous.json`);
   (c) an explicit `--previous-schema` path. Confirm approach.

4. **Execution model**: ~~Does the plan include only djng CLI commands, or can
   it also include direct `ng generate angular-django2:*` commands for skills
   that have not yet been given a djng wrapper?~~ Resolved: Layer 3 executes
   SKILLS via Claude Code Python SDK API calls. SKILLS invoke ngdj schematics
   internally. No direct CLI command strings in the procedure graph.

5. **Repair/refinement loop placement**: ARCHITECTURE.md §7.2 requires ≥1
   iterations per construction stage, terminating on deterministic acceptance
   criteria. Where in the three-layer architecture does this loop live — inside
   the SKILL, inside the SDK call, or as a retry at the Layer 3 procedure
   level? This must be decided before the repair loop can be specified.

---

## Relationship to Existing Commands

| Existing command | Relationship to app builder |
|---|---|
| `build` | Deterministic command: produces a correct-by-construction build artifact plan from config. Belongs to djng's deterministic command category. `build_app` is the SKILLS-based orchestration command. They serve different purposes within djng's two-category command surface; neither replaces the other. |
| `ng_new`, `ng_add`, `ng_config` | App builder emits these as steps in the plan when `ng-workspace` skill is triggered. |
| `ng_gen_app` | App builder emits this as a step when `ng-app` skill is triggered. |
| `ng_openapi_gen` | App builder emits this as a step when `ng-api` skill is triggered. |
| `ng_build` | App builder may emit this as a final verification step. |
