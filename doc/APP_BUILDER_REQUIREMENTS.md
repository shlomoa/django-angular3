# App Builder Requirements

## Purpose

The **generated app** is the resulting integrated Django-Angular application —
the artifact `build_app` receives, modifies, and delivers.

djng provides two categories of Django admin commands for producing the
generated app:

- **Deterministic commands**: produce correct-by-construction outputs without
  iteration — schema extraction from DRF models, direct ngdj wrapper calls,
  and similar bounded operations.
- **`build_app`**: the SKILLS-based orchestration command that drives
  change-detected construction of the generated app.

`build_app` is invoked as:

```bash
django-admin build_app <config> [options]
# or equivalently:
python manage.py build_app <config> [options]
```

`build_app` takes:
- An existing generated app: initially empty on first run.
- `django-angular3.json`: the djng tool configuration. Read as current; always authoritative. Not diffed; changes take effect on the next run without being tracked.
- Two OpenAPI schemas: current and previous (previous absent on first run).
- Two `<project>.project.json` files: current and previous (previous absent on first run). `<project>.project.json` is the generated app configuration — name is a placeholder pending schema definition.

### It operates through three phases:

**Change derivation**: Two-fold:
- **CRM**: Compares the current OpenAPI schema against the previous schema using `oasdiff`.
- **Non-CRM**: Compares the current configuration file against the previous configuration file using an equivalent config diff function. ⚠️ The config diff function is not yet defined — it depends on the `django-angular3.json` schema (particularly `ui.*` sections) being finalised first. See Open Questions.

Produces a typed `ChangeSet` and maps it to the set of SKILLS that must be invoked and in what mode.

**Procedure graph construction**: Translates the change derivation output into
a directed graph of procedures. Each procedure represents a unit of
construction work. The graph encodes the SKILLS dependency chain and ordering
constraints derived from the ChangeSet (delete before create at the same
dependency level).

**Procedure execution**: `build_app` traverses the procedure graph in dependency
order. For each procedure node, it makes a Claude Agent SDK `query()` call with
the specified SKILL(s) enabled, the procedure inputs as the prompt, and the
working directory set to the generated app workspace. The agent carries out the
construction work within each guided agent session.

---

## Inputs

### Required

| Input | Source | Format | Notes |
|---|---|---|---|
| `django-angular3.json` | Tool configuration file | JSON | Must contain `project.name`, `openapi.source`, `angular.output`. Read as current; always authoritative. |
| Current OpenAPI schema | Path from `openapi.source` in `django-angular3.json` | YAML or JSON (OAS 3.x) | The current schema version. |
| Previous OpenAPI schema | `--previous-schema <path>` | YAML or JSON (OAS 3.x) | OAS file from prior build. Absent on first run — treated as empty; builder uses `start-from-scratch`. |
| Current `<project>.project.json` | Generated app configuration file (name is a placeholder) | JSON (schema TBD) | Defines the generated app's UI artifacts: pages, components, forms. |
| Previous `<project>.project.json` | `--previous-project-config <path>` | JSON (schema TBD) | Prior generated app configuration. Absent on first run — non-CRM change detection is skipped. |

### Optional

Items marked `[DEBUG]` are available for inspection and troubleshooting; they
are not required for normal operation.

| Input | Flag | Notes |
|---|---|---|
| Output format | `--output-format json\|yaml\|text` | `[DEBUG]` Format for the emitted procedure graph. Default: `json`. |
| Dry run | `--dry-run` | `[DEBUG]` Emit the procedure graph without invoking any SKILLS or writing to disk. |
| Graph output path | `--output <dir>` | `[DEBUG]` Write the procedure graph to `<dir>/procedure-graph.<ext>`. Default: `build/`. |
| Force mode | `--force start-from-scratch` | Override change detection; treat as start-from-scratch regardless of diff. |

### Configuration keys read from `django-angular3.json`

| Key | Required | Purpose |
|---|---|---|
| `project.name` | yes | Workspace and app name |
| `openapi.source` | yes | Path to the current OpenAPI schema |
| `angular.output` | yes | Workspace root path |
| `angular.workspace.*` | no | Workspace settings (package manager, style, routing) |

---

## Change Derivation

### Schema change detection

Schema comparison uses `oasdiff`. The builder runs:

```bash
oasdiff diff <previous-schema> <current-schema> --format json
```

oasdiff output is parsed to classify each difference.

If the previous schema is absent (first run), the change type is `start-from-scratch` for all schema-derived skills.

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

This matches the contract normalization requirement in `REQUIREMENTS.md`.

### Generated app config change detection

⚠️ The config diff function and the `<project>.project.json` schema are not yet defined. See Open Questions.

Generated app config comparison is a structural diff of the two `<project>.project.json` files.
The builder diffs the following sections (subject to revision once `<project>.project.json` schema is defined):

| Section | Change meaning |
|---|---|
| `pages` | Pages added, removed, or modified |
| `components` | Standalone components added, removed, or modified |
| `forms` | Reactive forms added, removed, or modified |

If the previous `<project>.project.json` is absent (first run), non-CRM change detection is skipped and
config-derived skills are treated as `no-change` (they run only if triggered by schema changes).

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
    "type": "add-things | remove-things | replace-things | no-change | start-from-scratch",
    "affected_pages": ["dashboard"],
    "affected_components": [],
    "affected_forms": ["customer-edit"]
  }
}
```

⚠️ The `config` block structure is preliminary — the `affected_pages`, `affected_components`, and `affected_forms` keys depend on the `<project>.project.json` schema being finalised. See Open Questions.

---

## Change-to-SKILLS Mapping

Change derivation maps each change type to the set of SKILLS to invoke, using
the dependency order defined in `GENERATE_SKILLS.md`.

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

| `<project>.project.json` change | SKILL | Mode |
|---|---|---|
| Page added | 10 (`ng-page`) | create |
| Page modified | 10 (`ng-page`) | modify |
| Page removed | 10 (`ng-page`) | delete |
| Standalone component added | 7 (`ng-component`) | create |
| Standalone component modified | 7 (`ng-component`) | modify |
| Standalone component removed | 7 (`ng-component`) | delete |
| Complex component added | 8 (`ng-complex-component`) | create |
| Complex component modified | 8 (`ng-complex-component`) | modify |
| Complex component removed | 8 (`ng-complex-component`) | delete |
| Reactive form added | 9 (`ng-reactive-form`) | create |
| Reactive form modified | 9 (`ng-reactive-form`) | modify |
| Reactive form removed | 9 (`ng-reactive-form`) | delete |
| Site navigation changed | 11 (`ng-site`) | modify |

## Procedure Graph

Procedure graph construction translates the change-to-SKILLS mapping into a
directed acyclic graph of procedures. Each node in the graph is a procedure:
a SKILL name, invocation mode, reason, SDK inputs, and its dependency
edges. The graph encodes the following SKILLS dependency chain:

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

The final node(s) in the graph are always verification procedures. Verification
is `build_app`'s responsibility: it is not a separate command and is not
optional. The verification procedures confirm that the generated app is in a correct and
consistent state after all construction procedures have completed.

⚠️ The specific verification procedures and their acceptance criteria are not yet defined. See Open Questions.

### JSON representation `[DEBUG]`

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
        "config": "path/to/django-angular3.json",
        "previous_schema": "path/to/previous-schema.yaml",
        "project_config": "path/to/<project>.project.json",
        "previous_project_config": "path/to/previous-<project>.project.json"
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
        "config": "path/to/django-angular3.json",
        "previous_schema": "path/to/previous-schema.yaml",
        "project_config": "path/to/<project>.project.json",
        "previous_project_config": "path/to/previous-<project>.project.json"
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
- `build_app` traverses the graph in dependency order, running each procedure
  as a guided agent session via the Claude Agent SDK.

---

## Durable Artifacts

The durable artifact of each `build_app` run is the set of generated application
files produced by the Claude Code Python SDK API calls:

| Artifact | Format | Storage path |
|---|---|---|
| Generated application files — Angular source files accumulated across each SDK API call (components, services, API clients, routes, configuration) | TypeScript / HTML / SCSS / JSON | `angular.output` workspace root (from `django-angular3.json`) |

The following internal artifacts are produced for `[DEBUG]` and validation
purposes only:

| Internal artifact | Format | Storage path |
|---|---|---|
| oasdiff diff report | YAML | `build/oasdiff-report.yaml` |
| `ChangeSet` | JSON | `build/changeset.json` |
| Procedure graph | JSON or YAML | `build/procedure-graph.json` |

---

## Functional Requirements

### FR-1: Change detection

- The builder must detect schema changes using `oasdiff`.
- The builder must halt on breaking schema changes unless `--acknowledge-breaking` is set.
- The builder must detect non-CRM changes by diffing the `<project>.project.json` files.
  ⚠️ Not yet implementable — depends on the `<project>.project.json` schema being finalised. See Open Questions.
- If no previous state is available, the builder treats the run as
  `start-from-scratch`.

### FR-2: Procedure graph generation

- The procedure graph must be deterministic for the same inputs.
- The graph must encode the SKILLS dependency chain as dependency edges.
- Each procedure must include a `reason` for its inclusion.
- Procedures not triggered by any change in the current run must be omitted.

### FR-3: Dry run `[DEBUG]`

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
  only config-derived SKILLS are included in the procedure graph.
- Schema-derived SKILLS are not re-run unless triggered by a schema change.

### FR-7: Combined changes

- When both schema and config change, schema-derived procedures are ordered
  before config-derived procedures at the same dependency level.

### FR-8: Procedure graph traversal and SDK invocation

- `build_app` must traverse the procedure graph in dependency order.
- For each procedure node, `build_app` must make a Claude Agent SDK `query()` call
  with the specified SKILL(s) enabled, the procedure inputs as the prompt, and
  the working directory set to the generated app workspace (`angular.output` from
  `django-angular3.json`).

---

## Non-Functional Requirements

- Change derivation and procedure graph construction must complete in under 30
  seconds for typical schema/config sizes, excluding `oasdiff` execution time
  which is treated as an external process. Guided agent session duration is
  unbounded as it depends on Claude Agent SDK call duration.
- The builder must be testable with mock oasdiff output so `oasdiff` does not
  need to be installed to run the test suite.
- `[DEBUG]` The procedure graph must be emittable in machine-readable format
  (JSON/YAML) for inspection and CI consumption.

---

## Open Questions

1. **Schema format**: The current djng config uses `openapi.source` pointing to
   a JSON file. The app builder should support both YAML and JSON OpenAPI files.
   Confirm whether the user always provides YAML (`schema.yaml`) or whether
   both formats must be accepted.

2. **Generated app config format**: Define the schema and final name for
   `<project>.project.json` — the generated app's configuration file that
   describes UI artifacts (pages, components, forms). This schema must be
   finalised before non-CRM change detection can be implemented.

3. **Previous-state storage**: How is the previous schema/config stored?
   Options: (a) git — the builder diffs HEAD vs working tree or two commits;
   (b) a committed baseline file (e.g., `spec/openapi/previous.json`);
   (c) an explicit `--previous-schema` path. Confirm approach.

4. **Execution model**: ~~Does the plan include only djng CLI commands, or can
   it also include direct `ng generate angular-django2:*` commands for skills
   that have not yet been given a djng wrapper?~~ Resolved: `build_app` makes Claude Agent SDK `query()` calls; the agent uses
   SKILLS to carry out each guided agent session. The agent uses the knowledge
   in the SKILL to invoke ngdj calls to generate schematics internally. No
   direct CLI command strings in the procedure graph.

6. **Verification procedures**: The procedure graph always ends with verification
   procedures, but the specific checks, acceptance criteria, and failure behavior
   are not yet defined. Define what constitutes a successful `build_app` run
   (e.g., Angular build succeeds, generated files pass lint, API client matches
   schema).

5. ~~**Repair/refinement loop placement**~~: **Resolved — Option B.** The
   Claude Code SDK call IS the repair/refinement loop. The agent executing the
   SKILL is the loop controller. `build_app` makes one SDK call per procedure;
   the agent iterates natively (call tool → read result → decide → repeat)
   until the acceptance criteria embedded in the SKILL instructions are
   satisfied. ARCHITECTURE.md §7.2's ≥1-iteration requirement is fulfilled
   inside the agent session, not at the `build_app` level.

---

## Glossary

For authoritative definitions see `ARCHITECTURE.md` §2 and §19.

| Term | Definition | See |
|---|---|---|
| **`djng`** | The `django-angular3` solution — this repository, the Django package, and the tool. Contains the agent, SKILLS, `build_app`, and all configuration files. | `ARCHITECTURE.md` §2.5 |
| **`ngdj`** | The `angular-django2` companion Angular package. Provides the Angular-side schematics and templates invoked during construction. | `ARCHITECTURE.md` §2.6 |
| **`build_app`** | The `djng` Django management command. Entry point that drives the agent through the procedure graph. The subject of this document. | §Purpose |
| **the agent** | The agentic orchestrator bundled in `djng`. At implementation level, driven by the Claude Agent SDK via `query()` calls. | `ARCHITECTURE.md` §2.16 |
| **SKILLS** | Bounded AI skills (`SKILL.md` files) bundled in `djng` that guide the agent within each guided agent session. | `ARCHITECTURE.md` §2.14, `GENERATE_SKILLS.md` |
| **procedure graph** | The directed acyclic graph of construction procedures derived from the ChangeSet. Each node is a guided agent session. | §Procedure Graph |
| **guided agent session** | A single Claude Agent SDK `query()` call in which the agent carries out one procedure, guided by the specified SKILL(s). | `ARCHITECTURE.md` §2.13 |
| **ChangeSet** | The typed record of schema and config changes produced by change derivation, used to construct the procedure graph. | §Change Derivation |

---
