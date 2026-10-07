# Command-mapping plan

Plan for making `build_app` command translation consume the machine-readable
`command-mapping.json` that `angular-django2` (ngdj) ships since 0.6.3. This is a
plan, not an implementation: nothing in `django_angular3/` changes with it.

Ownership follows [`ARCHITECTURE.md` §3.4](../ARCHITECTURE.md#34-ngdj): ngdj owns which
command handles which OpenUI node type and which operations it supports; djng owns how
a Change selects a step, the step order, and the Tool and wrapper identities. djng must
read the mapping, not copy it.

## 1. Starting point

### 1.1 What the upstream mapping says (`angular-django2@0.7.0`, `mappingVersion` 1)

- `openuiSpecVersion` is `0.12.1`; the file validates against
  `command-mapping.schema.json`, published beside it.
- `ui.commands` has 16 commands, `api.commands` has `openapi-setup` and `data-service`,
  `tooling.commands` has 4. `ui.nodes` has 32 node types, 13 `root` (a command compiles
  them) and 19 `embedded` (compiled as part of a root). `scopes` has 54 entries
  (23 `direct`, 24 `tracked`, 3 `not-planned`, 3 `cross-cutting`, 1 `conceptual`).
- Each command and node lists a status per operation (`create`, `update`, `delete`,
  `move`): `supported`, `partial`, `indirect`, `tooling-only` or `unsupported`, with a
  `reason` and a `gap` issue for every `unsupported`.
- **Create is supported for every root node type. Update is supported only for
  `Application` (`material-app`) and `html`/`link` (`workspace-setup`); `complex-component`
  is `partial`; every other update, and every delete, is `unsupported`. `move` is
  unsupported everywhere**, and the Change Model emits no `move`.
- `onExisting` says what a second run does (`skip`, `reject`, `refuse-modified`,
  `rewrite`, `delegated`, `no-op`), which decides whether a create can be re-planned.

### 1.2 What djng had when this work started

This is the state found before steps 5 to 8; those steps changed it as described there.

- `command_translation.py`: the project-config translators are implemented
  ([#222](https://github.com/shlomoa/django-angular3/pull/222)): `project.name` and
  `artifacts.angularWorkspace` select the workspace and application foundation steps,
  the two source selectors select no step, and `delete` and `move` fail explicitly.
  The OpenAPI, static-config and OpenUI translator maps are still empty `TODO` stubs.
  `translate_changes` sorts steps by `exec_order`, `change_op`, domain, name, and
  rejects only an empty change list.
- Five tests are still `expectedFailure` ([#204](https://github.com/shlomoa/django-angular3/issues/204)):
  3 in `test_command_translation.py`, 2 in `test_build_app.py`. They need the OpenAPI,
  static-config or OpenUI maps, and use Skill-layer `name_id` values
  (`angular-page-composition`).
- `APP_BUILDER_REQUIREMENTS.md` § Change-to-command mapping defines the project-config
  rows (since #222) and still marks every OpenUI row "not yet defined", and `AUTOMATION_PLAN.md` step 8.2 forbids claiming an undefined
  OpenUI wrapper as supported.
- OpenUI Changes come from `external_comparisons.py` with `subject = "openui:" + path`
  (the upstream comparison path, which may end at an attribute inside an element).
- Wrappers exist for `page`, `component`, `complex-component`, `reactive-form`,
  `material-app`, `material-setup`, `openapi-setup`, `data-service`. None exists for
  `tabs`, `dialog`, `stepper`, `table`, `form-field`, `field-component`.

### 1.3 Consequence

With the current mapping, change-driven `build_app` can honestly support first builds
(create), `Application` updates and `html`/`link` updates. Every other update or delete
must fail explicitly, as the requirements already demand ("must not silently omit
them"), naming the upstream reason and gap issue. The plan does not widen this.

## 2. Decisions

Settled by the owner on 2026-10-07, plus what the documentation already fixes:

1. **Step identity: TOOL contract names.** `ARCHITECTURE.md` §3.6.3 classifies "generate an
   Angular page or reactive form from validated OpenUI" as a deterministic TOOL whose
   contract is not yet defined, and §3.6.4 requires every selected deterministic operation
   to use a TOOL name. Step 1 therefore defines the missing contracts, following the
   `ngdj_add_component` pattern: `ngdj_add_page`, `ngdj_add_reactive_form`,
   `ngdj_add_complex_component` and `ngdj_add_data_service`. The existing
   `ngdj_add_component`, `angular_app_scaffold` and `angular_workspace_scaffold` gain
   optional `document` and `node_id` inputs. The new OpenUI steps use these Tool names.
   The project-config steps merged in #222 keep their Skill names: their `update` runs
   through the workspace and application modification wrappers, for which no Tool contract
   exists (`angular_workspace_scaffold` only scaffolds a fresh workspace), so a rename
   would claim a contract that is not there.
2. **Node type: enrich at derivation.** `external_comparisons.py` records the element id and
   type in each OpenUI Change's evidence; `translate_changes` stays a pure function of the
   Changes.
3. **Mapping source: the installed package.** Read
   `<workspace>/node_modules/angular-django2/schematics/command-mapping.json` at run time,
   and fail when its version differs from `tool.ngAddPackage`.
4. **New wrappers: deferred.** Node types whose command has no djng wrapper (`tabs`,
   `dialog`, `stepper`, `table`, `form-field`, `field-component`) fail as "no wrapper".
5. **Unsupported update or delete: fail explicitly**, as the requirements already state.

Commit granularity: one commit per step below, each with its own tests and doc updates,
so the branch can be split into its own PR.

## 3. Steps

1. **Contracts and requirements first** (docs only).
   1. Add the four Tool contracts of decision 1 to `TOOL_CONTRACTS.md`, add the `document`
      and `node_id` inputs to the three existing OpenUI-capable Tools, and update the
      §3.6.4.1 crosswalk, the §3.6.3 worked example and the `ngdj-scaffold` Plugin list.
   2. In `APP_BUILDER_REQUIREMENTS.md`, replace each OpenUI "not yet defined" row that the
      mapping now defines with the node-type, operation and status rule, citing the
      upstream mapping instead of restating it, and state the stage of each Tool.
   3. Update `AUTOMATION_PLAN.md` 8.2 to say which OpenUI operations are now defined.
2. **Mapping loader** (`django_angular3/ngdj_command_mapping.py`).
   1. Locate and load the file (decision 3); validate it with `jsonschema` against the
      shipped schema (already installed through `openapi-spec-validator`); check
      `mappingVersion` is supported (checked before the schema, so a newer mapping names
      both versions) and `openuiSpecVersion` has the same major and minor as the installed
      `openui_spec.__version__`; a patch difference changes no spec content.
   2. Typed read-only accessors only, no copied inventory: `root_command(node_type)`,
      `operation_status(node_type, operation)`, `embedded_owner(node_type)`,
      `on_existing(command)`. A missing file or version mismatch raises one error that
      names both versions.
   3. Tests against a fixture copied from the pinned upstream file by a script, not
      written by hand, plus a drift test against the sibling checkout when present, like
      `test_ngdj_requirements.py`.
3. **OpenUI Change enrichment** (`external_comparisons.py`, decision 2).
   1. For each upstream entry, walk its path through the candidate document (the
      reference document for a delete) and record the `id` and `type` of every enclosing
      element, root element first, as evidence records of the Change
      (`openui_change_elements` reads them). The enrichment knows nothing of the mapping:
      resolving an `embedded` node to the root node that compiles it (`compiled_by`) is
      done by the step 5 translator.
   2. Root-level changes (`/attrs`, `/children`, `/type`) belong to the root element.
4. **Forward the OpenUI document from the wrappers.** None of the djng wrappers
   (`ng_workspace`, `ng_gen_app`, `ng_page`, `ng_component`, `ng_complex_component`,
   `ng_reactive_form`) passed `--document` or `--node-id`, which every OpenUI-driven
   schematic takes; `ng_reactive_form` still passed the deprecated `--definition`.
   Each now accepts an optional `--document` (workspace-relative, as ngdj resolves it)
   and, except `ng_workspace`, `--node-id` (requires `--document`), in the CLI and the
   management command, and default invocations are unchanged. The ngdj rules are kept:
   `ng_reactive_form` takes exactly one of `--document` and `--definition`, and
   `ng_complex_component` takes a document only with `--mode create`. `ng_data_service`
   is not changed, as its Tool contract has no document input. Because the path is
   workspace-relative, the `build_app` execution (step 7) must make the project's OpenUI
   document readable inside the Angular workspace before it runs a step. This is the
   djng-owned argument translation of `ARCHITECTURE.md` §3.4.
5. **OpenUI translators** (`command_translation.py`).
   1. `translate_changes` takes the loaded `CommandMapping`. One translator keyed by the
      resolved node type, not by path: look up the status for the Change's operation
      (an element's own creation or deletion, or an update for a change inside it), emit
      the step for `supported`, and raise
      `CommandTranslationError` for `partial`, `unsupported` and for a command without a
      djng wrapper, quoting the mapping's `reason` and `gap` where it has one.
   2. Give each OpenUI Tool an `exec_order` between the existing stages (components 7,
      complex components 8, forms 9, pages 10; stage 11 stays unassigned, as a navigation
      change is an `Application` update at stage 2); the `AppBuildStep` docstring and the
      requirements say so together.
   3. The step's `change_reason` names the command and its `onExisting` outcome. Whether
      the target exists is only known at execution, so it is not decided here. A step
      also carries the `node_id` of the element it compiles, which the wrapper takes as
      `--node-id`. `html` and `link` (workspace-setup) get no Tool: their update runs
      through `ng_workspace_modify`, which has no Tool contract.
6. **API translators.** Every `openapi` change selects `angular_api_client_generate`
   (stage 3). A `path` create also selects `ngdj_add_data_service` (stage 4). A change to
   an operation, and the `update` or `delete` of a path or schema, would have to update or
   delete data services, which the mapping's `data-service` does not support, so it fails
   with the mapping's reason and gap. `project_config` is already done (#222) and keeps
   its behavior. `static_config` follows a subject-to-command table researched from how
   each setting is consumed and from the scenario specification (`angular.workspace.style`
   runs the workspace modification only); it is recorded in the requirements, and
   `create` and `update` are supported, `delete` and `move` fail explicitly.
   `openapi-setup` (`ng_openapi_setup`) has no dedicated Tool; the generic
   `ngdj_run_schematic` Tool can run it. The translators do not plan it yet: a step names
   a Tool but carries no schematic name, so planning it through `ngdj_run_schematic`
   needs the step to carry one. That is a design decision for the owner.
7. **Wire into `build_app`** (`management/commands/build_app.py`): load the mapping when
   an OpenUI or OpenAPI Change exists, pass it to the translation, print the ordered
   steps in `--dry-run` as JSON, report an unsupported change or a missing package as a
   `CommandError`, and keep the command marked work in progress until step 8 passes.
   Running the steps is not part of this plan: the executor hand-off already raised
   `TypeError` before this work (`command_execution.execute` takes no `force` or
   `dry_run`, and a step is not an executable command), so a real run still fails.
8. **Close the expected failures.** Rewrite the five remaining `expectedFailure` tests
   against the decided identities and remove each decorator only when its assertions pass
   (the rule in #204); run ruff check and format, the full unittest suite and the Sphinx
   docs build. Done: four tests were rewritten to the decided design (Tool names, a
   path create instead of a schema update, a project name update instead of a move, and a
   mapping that supports deleting a page to test the delete-before-create rule, because
   ngdj supports no OpenUI delete today). The fifth, an empty change set, passes with a
   code change: an empty change list now plans no commands. It raised an error with an
   empty message, a leftover of the original scaffold that #202 narrowed but kept.
9. **Document the boundary** in `README.md`, `docs/commands.md` and `CONTRIBUTING.md`:
   what `build_app` supports from the mapping and what it refuses.

## 4. Risks

- **A first build cannot plan its OpenUI and OpenAPI steps.** The mapping comes from the
  installed package, and the package is installed by the plan's own foundation steps, so
  a workspace that does not exist yet has no mapping. Running a plan will need two
  phases (foundation first, then the rest once the package is there), or the owner can
  revisit decision 3. `tool.ngAddPackage` must also be a registry name, not a path, for
  the package directory to be found.
- **Static-configuration changes are never detected.** `ChangeDetector.detect_changes`
  leaves that domain empty, so the static translators have no caller yet; detecting them
  needs a baseline for `django-angular3.json`, which is not defined.
- **Running a plan.** A step has no arguments for its wrapper: the document path must be
  made workspace-relative (see step 4), and the wrapper options come from the Change.

- The mapping marks most updates and deletes unsupported, so `build_app` stays mostly
  create-only until upstream closes gaps such as
  `shlomoa/angular-django2#194`, `#198` and `#199`. Do not paper over this locally.
- This work is much larger than #224's current diff. Land it as one commit per step so
  it can be reviewed or split into its own PR without rework.
- A mapping update upstream (`mappingVersion` 2) must fail loudly in step 2, not parse
  partially.
