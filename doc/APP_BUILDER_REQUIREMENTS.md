# App Builder Requirements

## Purpose

The app builder is a high-level orchestrator command in djng:

```bash
django-admin build-app <config> [options]
# or equivalently:
python manage.py build-app <config> [options]
```

Given a current OpenAPI schema and app configuration, and optionally the
previous versions of both, it:

1. Detects what changed between the current and previous state.
2. Classifies each change into a typed change set.
3. Maps the change set to an ordered sequence of djng skills.
4. Emits a deterministic build plan — an ordered list of commands — that the
   caller can review, approve, and execute.

The app builder does **not** execute commands itself. It produces the plan.
Execution is a separate, explicit step. This separates planning from side effects
and makes the pipeline auditable and reversible.

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

## Change Detection

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

## Skill and Command Mapping

The builder maps each change type to a set of skills using the dependency
order defined in `doc/SKILL_AUTHORING_PLAN.md`.

### Schema change → skills

| Schema change type | Skills invoked | Notes |
|---|---|---|
| `start-from-scratch` | 1, 2, 3, 4, then config-derived skills | Full pipeline |
| `no-change` | None (schema-derived) | Config-derived skills still run if config changed |
| `add-things` | 3 (`ng-api`), 4 (`ng-data-service`) for new resources, then component/page skills for new resources | Existing workspace and app untouched |
| `remove-things` | 3 (`ng-api`), 4 (`ng-data-service`) in delete mode, component/page skills for removed resources in delete mode | |
| `replace-things` | Same as remove-things for removed resources, then add-things for new resources | Order: remove first, then add |
| `breaking` | Blocked — see Breaking change gate above | |

### Config change → skills

| Config change | Skill | Mode |
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

### Execution order

The builder always respects the skill dependency chain:

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

Skills not triggered by any change in the current run are omitted from the
plan. Skills that must run in delete mode for removed resources precede
skills that run in create/add mode for new resources at the same dependency
level.

---

## Output: Build Plan

The app builder emits an ordered build plan. Each entry in the plan is an
invocable djng command or skill invocation.

### JSON format (default)

```json
{
  "generated_at": "2026-04-30T12:00:00Z",
  "config": "path/to/django-angular3.json",
  "change_set": { ... },
  "steps": [
    {
      "step": 1,
      "skill": "ng-api",
      "mode": "create",
      "reason": "New resource 'Order' added to schema",
      "command": "django-admin ng_openapi_gen path/to/django-angular3.json",
      "dry_run_command": "django-admin ng_openapi_gen path/to/django-angular3.json --dry-run"
    },
    {
      "step": 2,
      "skill": "ng-data-service",
      "mode": "create",
      "reason": "New resource 'Order' requires data service",
      "command": "invoke skill ng-data-service --mode=create --resource=Order",
      "dry_run_command": "invoke skill ng-data-service --mode=create --resource=Order --dry-run"
    }
  ]
}
```

### Constraints on output

- Steps are strictly ordered by the dependency chain.
- Each step includes `reason` — a human-readable explanation of why the step
  is included.
- Steps include both the execution command and the dry-run command.
- The plan is deterministic: the same inputs always produce the same plan.
- The plan is self-contained: it can be executed by replaying each `command`
  in order without further input.

---

## Functional Requirements

### FR-1: Change detection

- The builder must detect schema changes using `oasdiff`.
- The builder must halt on breaking schema changes unless `--acknowledge-breaking` is set.
- The builder must detect config changes by diffing the `django-angular3.json` files.
- If no previous state is available, the builder treats the run as
  `start-from-scratch`.

### FR-2: Plan generation

- The plan must be deterministic for the same inputs.
- The plan must respect the skill dependency order.
- The plan must include a `reason` for every step.
- The plan must not include steps for skills that are not affected by any change.

### FR-3: Dry run

- `--dry-run` must print the plan without writing to disk or executing any command.
- Each step in the plan must include a dry-run variant of the command.

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

- When both schema and config change, schema-derived steps are ordered before
  config-derived steps at the same dependency level.

---

## Non-Functional Requirements

- The builder must run in under 30 seconds for typical schema/config sizes
  (excluding `oasdiff` execution time, which is treated as an external process).
- The builder must be testable with mock oasdiff output so `oasdiff` does not
  need to be installed to run the test suite.
- The builder must emit machine-readable output (JSON/YAML) so it can be
  consumed by CI pipelines.

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

4. **Execution model**: Does the plan include only djng CLI commands, or can it
   also include direct `ng generate angular-django2:*` commands for skills that
   have not yet been given a djng wrapper?

---

## Relationship to Existing Commands

| Existing command | Relationship to app builder |
|---|---|
| `build` | Lower-level; produces a static build artifact plan from config. App builder replaces it for end-to-end orchestration. |
| `ng_new`, `ng_add`, `ng_config` | App builder emits these as steps in the plan when `ng-workspace` skill is triggered. |
| `ng_gen_app` | App builder emits this as a step when `ng-app` skill is triggered. |
| `ng_openapi_gen` | App builder emits this as a step when `ng-api` skill is triggered. |
| `ng_build` | App builder may emit this as a final verification step. |
