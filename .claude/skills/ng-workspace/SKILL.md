---
name: ng-workspace
description: Create, modify, or delete an Angular Material workspace configured with angular-django2 schematics (standalone components, signals, SCSS theming). Invoke when a generated app needs its Angular workspace initialised, reconfigured, or removed.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# ng-workspace

## Purpose

Manage the Angular workspace container for a generated app. This is the
foundation skill: all other Angular skills require a workspace created by this
one. It does not generate any Angular application — that is `ng-app` (skill 2).

Skills call the djng Python CLI (`django-admin <command>`).
They do not invoke Angular CLI directly.

## Modes

### Create

Initialise a new Angular workspace and register the `angular-django2`
schematics collection.

**Input requirements**

Read the generated app's `django-angular3.json`. Required keys:

| Key | Section | Notes |
|---|---|---|
| `project.name` | `project` | Used as workspace name if `angular.workspace.name` is absent |
| `angular.output` | `angular` | Absolute or relative path for the workspace root |
| `angular.workspace.name` | `angular.workspace` | Optional override for workspace name |
| `angular.workspace.packageManager` | `angular.workspace` | Optional; default `pnpm` |
| `angular.workspace.style` | `angular.workspace` | Optional; default `scss` |
| `angular.workspace.routing` | `angular.workspace` | Optional; default `true` |

The `angular.workspace` block may be absent; apply defaults from `settings.py`
when it is. A missing `angular.workspace` block is not an error.

**Pre-flight checks**

Run the bundled pre-flight script before issuing any commands:

```bash
python scripts/preflight.py <path-to-django-angular3.json>
```

All checks must PASS before proceeding:
1. `angular.output` does not exist or is an empty directory.
2. `django-angular3.json` is present and parseable.
3. Confirm `django-admin ng_new --help` succeeds (djng reachable).

**Process**

1. Create the workspace (no application inside):

   ```bash
   django-admin ng_new <path-to-django-angular3.json> --dry-run
   ```

   Review the planned command, then execute without `--dry-run` when approved.

2. Register the `angular-django2` schematics collection:

   ```bash
   django-admin ng_add <path-to-django-angular3.json> --dry-run
   ```

   Default package is `angular-django2`. Execute without `--dry-run` when
   approved.

3. Apply workspace-level defaults (package manager, style format, routing):

   ```bash
   django-admin ng_config <path-to-django-angular3.json> --dry-run
   ```

   Execute without `--dry-run` when approved.

**ngdj requirement surfaced**

`ng_add` runs `ng add angular-django2 --skip-confirmation`. The ngdj `ng-add`
schematic must register `angular-django2` in `angular.json`'s
`cli.schematicCollections` array. Verify this is still the behaviour before
trusting it; the current implementation may evolve.

**Output**

```
<angular.output>/
  angular.json            # workspace config; angular-django2 registered in cli.schematicCollections
  package.json
  pnpm-lock.yaml          # or lock file for the configured package manager
  tsconfig.json
  .editorconfig
  .gitignore
  node_modules/           # present after install
```

No application exists inside the workspace yet. The `src/` tree is produced
by `ng-app` (skill 2).

### Modify

Update the workspace configuration or register an additional Angular package.

**Supported modification targets**

| Target | Command |
|---|---|
| Change package manager, style, or routing defaults | `ng_config` |
| Add an Angular package (`ng add <pkg>`) | `ng_add --package <pkg>` |

**Process**

For `ng_config` changes:
1. Edit the `angular.workspace` block in `django-angular3.json`.
2. Run `django-admin ng_config <path> --dry-run`.
3. Execute without `--dry-run` when approved.

For additional `ng add`:
```bash
django-admin ng_add <path> --package <package-name> --dry-run
```
Execute without `--dry-run` when approved.

**Output**

Modified `angular.json` with updated configuration.

### Delete

Remove the workspace directory.

**Input requirements**

- `angular.output` must exist and contain `angular.json`.
- Explicit confirmation from the orchestrator is required before deletion.

**Pre-flight checks**

1. `angular.output/angular.json` exists.
2. Check for uncommitted Git changes: `git -C <angular.output> status --porcelain`.
   Warn and stop if output is non-empty — do not delete a workspace with
   uncommitted work without explicit re-confirmation.

**Process**

```bash
rm -rf <angular.output>
```

Verify deletion: confirm `angular.output` no longer exists.

**Output**

Workspace directory removed. Report the deleted path.

## Context Files

{{context:angular-conventions.md}}

## Validation

After **Create**, run the bundled verification script:

```bash
python scripts/verify_workspace.py <path-to-django-angular3.json>
```

All checks must PASS:
1. `<angular.output>/angular.json` exists.
2. `angular.json` contains `angular-django2` in `cli.schematicCollections`.
3. `<angular.output>/node_modules` exists (packages installed).
4. `package.json` and `tsconfig.json` present.

After **Modify**:

1. The modified key is present in `angular.json` with the expected value.
2. No new TypeScript or lint errors (run `ng build --dry-run` if available).

## Error Handling

| Error | Cause | Resolution |
|---|---|---|
| `django-angular3.json` missing or unparseable | Wrong working directory or malformed JSON | Confirm path; fix JSON |
| `django-admin ng_new` not found | djng not installed or not in `INSTALLED_APPS` | `pip install -e .` in the djng repo; add `django_angular3` to `INSTALLED_APPS` |
| `ng_new` fails — directory not empty | Target workspace path already has files | Delete or choose a different `angular.output` path |
| `ng_add` fails — `angular.json` not found | `ng_new` was not run first | Run Create mode from step 1 |
| `ng_add` fails — package not found | Package name wrong or registry unavailable | Verify package name; check network |

## Dependencies

**Skill dependencies**: none — this is the foundation skill.

**djng commands used**:

| Command | Purpose |
|---|---|
| `ng_new` | Creates workspace with `--no-create-application` |
| `ng_add` | Runs `ng add <package> --skip-confirmation` |
| `ng_config` | Sets `cli.packageManager`, style, and routing workspace defaults |

**ngdj requirements** (as of `ng-workspace` skill, 2026-04-30):

| # | Requirement | Status |
|---|---|---|
| R1 | `ng-add` schematic registers `angular-django2` in `cli.schematicCollections` | Exists — verify before trusting |
| R2 | `application` schematic should default `style` to `scss` | Gap — tracked for `ng-app` skill |
| R3 | `ng_gen_app` (djng) should call `ng generate angular-django2:application` | djng gap — tracked for `ng-app` skill |

## Examples

**Create workspace for a generated app:**

```bash
# Assuming django-angular3.json at /projects/crm-app/django-angular3.json
# with angular.output = "frontend"

django-admin ng_new /projects/crm-app/django-angular3.json --dry-run
# Review, then:
django-admin ng_new /projects/crm-app/django-angular3.json

django-admin ng_add /projects/crm-app/django-angular3.json --dry-run
django-admin ng_add /projects/crm-app/django-angular3.json

django-admin ng_config /projects/crm-app/django-angular3.json --dry-run
django-admin ng_config /projects/crm-app/django-angular3.json
```

**Add Angular Material to an existing workspace:**

```bash
django-admin ng_add /projects/crm-app/django-angular3.json \
  --package @angular/material --dry-run
django-admin ng_add /projects/crm-app/django-angular3.json \
  --package @angular/material
```

## Test Prompts

Use these prompts to iteratively verify the `ng-workspace` skill functionality. Execute them from the repository root. Ensure you have activated `wenv` first.

1. **Verify Create Mode**:
   > Use the ng-workspace skill to create the workspace for `spec/examples/01_simple_crm/django-angular3.json`. Verify using the scripts.

2. **Verify Modify Mode** (Requires Create Mode to have succeeded):
   > Use the ng-workspace skill to add `@angular/material` to the workspace defined in `spec/examples/01_simple_crm/django-angular3.json`.

3. **Verify Delete Mode** (Requires Create Mode to have succeeded):
   > Use the ng-workspace skill to delete the workspace defined in `spec/examples/01_simple_crm/django-angular3.json`. Please force deletion if required.
