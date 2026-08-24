---
name: ngdj integration task
about: Track integrating an angular-django2 (ngdj) schematic or command into djng
title: "[ngdj]: integrate <schematic-or-command>"
labels: ["ngdj-integration"]
assignees: []
---

## Schematic / command

<!-- e.g. angular-django2:page, angular-django2:reactive-form, angular-django2:site -->

## Current djng status

- [ ] No wrapper yet
- [ ] Documented only (`doc/ngdj_commands.md`) — Pending
- [ ] Invocation builder present (`_COMMAND_BUILDERS` in `angular.py`)
- [ ] Management command wrapper present
- [ ] Contract test present (`tests/test_ngdj_requirements.py`)

## Scope of this task

<!-- Which layers should this issue deliver? -->

- [ ] Add `build_ng_<schematic>_invocations` to `angular.py` (invocation SSOT)
- [ ] Add dry-run management command wrapper
- [ ] Add contract / drift test
- [ ] Wire into `command_translation.py` selection
- [ ] Update `doc/ngdj_commands.md`

## ngdj reference

- ngdj version: `angular-django2@0.4.1`
- Schematic options (from `collection.json` / `schema.json`):

```text
<paste relevant options>
```

## Notes / dependencies

<!-- e.g. blocked on build_app orchestrator, SSOT decision on skills vs .tpl. -->
