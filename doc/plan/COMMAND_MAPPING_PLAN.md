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

### 1.2 What djng has today

- `command_translation.py`: the four per-domain translator maps are empty `TODO` stubs.
  `translate_changes` already sorts steps by `exec_order`, `change_op`, domain, name.
- Five tests are `expectedFailure` ([#204](https://github.com/shlomoa/django-angular3/issues/204)):
  3 in `test_command_translation.py`, 2 in `test_build_app.py`. They use Skill-layer
  `name_id` values (`angular-page-composition`).
- `APP_BUILDER_REQUIREMENTS.md` § Change-to-command mapping marks every OpenUI row
  "not yet defined", and `AUTOMATION_PLAN.md` step 8.2 forbids claiming an undefined
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

## 2. Decisions needed before step 3

1. **Step identity.** `AppBuildStep.name_id` is documented as a Skill-layer name, but the
   requirements say deterministic selection uses TOOL contract names. Use TOOL names
   (recommended; the `expectedFailure` tests are rewritten to match) or keep Skill names?
2. **Element type for an OpenUI Change.** Translation needs the node type of the element
   a Change belongs to. Either enrich each OpenUI Change at derivation time, where both
   documents are loaded (recommended; `translate_changes` stays a pure function of the
   Changes), or pass the documents to `translate_changes`.
3. **Mapping source.** Read `command-mapping.json` at run time from the installed
   package (`<workspace>/node_modules/angular-django2/schematics/`), failing if its
   version differs from `tool.ngAddPackage` (recommended), or vendor a snapshot into djng.
4. **New wrappers.** Add wrappers and Tool contracts for `tabs`, `dialog`, `stepper`,
   `table`, `form-field`, `field-component` in this PR, or translate only node types
   whose wrapper already exists and fail the rest as "no wrapper"? Recommended: the
   second, then add wrappers in follow-up PRs, one per command.
5. **Unsupported update or delete.** Confirm fail-fast (the stated requirement) rather
   than planning a delete plus create.

## 3. Steps

1. **Contracts and requirements first** (docs only).
   1. In `APP_BUILDER_REQUIREMENTS.md`, replace each OpenUI "not yet defined" row that the
      mapping now defines with the node-type, operation and status rule, citing the
      upstream mapping instead of restating it. Rows still undefined stay marked so.
   2. In `TOOL_CONTRACTS.md` and the §3.6.4.1 crosswalk, add the Tool contract for each
      OpenUI command that will be translated (per decision 4), and the stage numbers.
   3. Update `AUTOMATION_PLAN.md` 8.2 to say which OpenUI operations are now defined.
2. **Mapping loader** (`django_angular3/ngdj_command_mapping.py`).
   1. Locate and load the file (decision 3); validate it with `jsonschema` against the
      shipped schema (already installed through `openapi-spec-validator`); check
      `mappingVersion` is supported and `openuiSpecVersion` equals the installed
      `openui_spec.__version__`.
   2. Typed read-only accessors only, no copied inventory: `root_command(node_type)`,
      `operation_status(node_type, operation)`, `embedded_owner(node_type)`,
      `on_existing(command)`. A missing file or version mismatch raises one error that
      names both versions.
3. **OpenUI Change enrichment** (`external_comparisons.py`, decision 2).
   1. For each upstream entry, walk the path up to the nearest element in the candidate
      (or reference, for a delete) document and record its `id` and `type` in the Change
      evidence. A change below an `embedded` node resolves to its root ancestor.
   2. Root-level changes (`Application`) resolve to the document root.
4. **OpenUI translators** (`command_translation.py`).
   1. One translator keyed by the resolved node type, not by path: look up the status for
      the Change's operation, emit the step for `supported`, and raise
      `CommandTranslationError` for `partial` and `unsupported`, quoting the mapping's
      `reason` and `gap`.
   2. Give each OpenUI command an `exec_order` between the existing stages (components 7,
      complex components 8, forms 9, pages 10, site navigation 11); new stages are
      added to the `AppBuildStep` docstring and the requirements together.
   3. A Change whose `onExisting` outcome is `reject` or `refuse-modified` and whose
      target already exists is reported in the step's `change_reason`, not hidden.
5. **API translators.** `openapi create` selects `openapi-setup` then `data-service`
   (stages 3 and 4) from the mapping's `api` section; `update` and `delete` fail with the
   mapping's reason. `project_config` and `static_config` rows follow the existing
   requirements table, which djng owns, and are done as a separate commit.
6. **Wire into `build_app`** (`management/commands/build_app.py`): pass the loader result
   in, print the ordered steps and unsupported-change failures in `--dry-run`, keep
   the command marked work in progress until step 7 passes.
7. **Tests.**
   1. Loader tests against a fixture copied from the pinned upstream file by a script
      (not written by hand), plus a drift test that compares it to the sibling checkout
      when present, like `test_ngdj_requirements.py`.
   2. Table tests: every (root node type, operation) pair in the fixture yields a step or
      the expected error, so a mapping change fails a test instead of drifting.
   3. Rewrite the five `expectedFailure` tests against the decided identities and remove
      each decorator only when its assertions pass (the rule in #204).
   4. Ruff check and format, the full unittest suite, and the Sphinx docs build.
8. **Document the boundary** in `README.md`, `docs/commands.md` and `CONTRIBUTING.md`:
   what `build_app` supports from the mapping and what it refuses.

## 4. Risks

- The mapping marks most updates and deletes unsupported, so `build_app` stays mostly
  create-only until upstream closes gaps such as
  `shlomoa/angular-django2#194`, `#198` and `#199`. Do not paper over this locally.
- This work is much larger than #224's current diff. Land it as one commit per step so
  it can be reviewed or split into its own PR without rework.
- A mapping update upstream (`mappingVersion` 2) must fail loudly in step 2, not parse
  partially.
