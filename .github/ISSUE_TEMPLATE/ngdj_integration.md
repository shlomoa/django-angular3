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
- [ ] Documented only — Pending
- [ ] Invocation builder present (`_COMMAND_BUILDERS` in `angular.py`)
- [ ] Management command wrapper present
- [ ] Contract test present (`tests/test_ngdj_requirements.py`)

## Scope of this task

<!-- Which layers should this issue deliver? -->

- [ ] Add `build_ng_<schematic>_invocations` to `angular.py` (invocation SSOT)
- [ ] Add dry-run management command wrapper
- [ ] Add contract / drift test
- [ ] Wire into `command_translation.py` selection
- [ ] Update maintained command documentation

## ngdj reference

Use `doc/ARCHITECTURE.md` §2.6 and its upstream sources. Do not define or copy
an ngdj command inventory in this issue.

- Target ngdj version: `angular-django2@<version>`
- Upstream command or schema URL:
- Integration-specific options used by the djng wrapper:

```text
<list only the options translated or constrained by this wrapper>
```

## Notes / dependencies

<!-- e.g. blocked on build_app orchestrator, SSOT decision on skills vs .tpl. -->
