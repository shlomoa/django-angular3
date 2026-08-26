# ngdj command github issues

## Direct ngdj issues

| Issue | Verdict | Findings |
|---|---|---|
| [#56 — Track ngdj construction capabilities](https://github.com/shlomoa/django-angular3/issues/56) | **Not aligned** | Cites the obsolete §3.4 ownership statement instead of §2.6. Its unchecked dependencies include closed upstream issues #25 and #26. It relies on upstream #24, whose command/status inventory conflicts with current ngdj source. |
| [#57 — Complete generation entry points and wrappers](https://github.com/shlomoa/django-angular3/issues/57) | **Not aligned** | Repeatedly cites deleted temporary file `doc/ngdj_commands.md`; maintains a competing ngdj command inventory; reports 12 wrapper builders when code has 17; incorrectly reports missing wrappers now implemented for `component` and `material-setup`, and omits the new `page`, `reactive-form`, and `site` wrappers. |
| [#58 — Execute governed construction through Skills](https://github.com/shlomoa/django-angular3/issues/58) | **Partially aligned** | Correctly keeps deterministic execution under djng, but lacks §2.6 and depends on misaligned #56/#57. It does not itself redefine ngdj commands. |
| [#66 — Consume ngdj frontend structure](https://github.com/shlomoa/django-angular3/issues/66) | **Partially aligned** | Correctly treats Angular implementation as upstream, but lacks §2.6 and has obsolete requirement references (`§4.17.2`, `§4.2.1`). Upstream #25 is closed, so this should now describe only remaining djng consumption work. |
| [#74 — Assemble CRM/non-CRM streams](https://github.com/shlomoa/django-angular3/issues/74) | **Partially aligned** | Ownership boundary is conceptually correct, but §2.6 is absent. Upstream #26 is closed while #27 remains open; the tracker should distinguish delivered upstream behavior from remaining integration work. |
| [#84 — Implement staged verification](https://github.com/shlomoa/django-angular3/issues/84) | **Not aligned** | Says djng should “specify the ngdj test surface.” Under §2.6, ngdj tests and implementation are upstream-owned. djng should specify only cross-repository integration and generated-app acceptance requirements, linking upstream test evidence. |
| [#139 — Provider-neutral automation foundation](https://github.com/shlomoa/django-angular3/issues/139) | **Partially aligned** | Its “controlled ngdj invocation” is valid djng Tool behavior, but it lacks the mandatory §2.6 boundary. Child issues #156–#165 inherit this dependency when implementing invocation-related phases. |

## Remaining issues

These generated-app Angular requirements do not define ngdj commands, options, schemas, or implementation and are therefore **aligned/not directly affected**:

- #67, #69, #72, #73, #75, #79, #83

These contain no ngdj or Angular contract claims and are **not applicable**:

- #60–#65
- #68, #70–#71
- #76–#78
- #80–#82
- #156–#165

## Upstream conflicts found

The authoritative ngdj GitHub sources are themselves inconsistent:

- [`angular-django2#24`](https://github.com/shlomoa/angular-django2/issues/24) says five schematics remain missing, but current `collection.json` contains all five.
- Upstream #25 and #26 are closed, while downstream #56 still shows them unchecked.
- Upstream #27 says `site` has landed but retains unchecked delivery items.

Per §2.6, these conflicts must be corrected in `angular-django2`; djng issues should not invent a local replacement inventory.

## Recommended correction order

1. Publish the currently uncommitted §2.6 documentation changes so GitHub issues can link to a public section.
2. Rewrite #57, removing every `doc/ngdj_commands.md` reference and the upstream command inventory.
3. Correct upstream `angular-django2` #24 and #27 status before synchronizing #56/#74.
4. Update #56, #58, #66, #74, #84, and #139 to cite §2.6 and state only djng-owned integration behavior.
5. Reframe #84’s “ngdj test surface” as djng integration/acceptance coverage backed by upstream ngdj tests.
