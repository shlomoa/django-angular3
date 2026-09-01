# ngdj command github issues

## Review basis

`doc/ARCHITECTURE.md` §2.6 is the django-angular3 authority for ngdj identity,
ownership, and upstream-source resolution. This review records alignment only;
it does not maintain an ngdj command, option, implementation, or test inventory.

## Direct ngdj issues

| Issue                                                                                                       | Verdict     | Findings                                                                                                                                                                                                                                                                |
| ----------------------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [#56 — Track ngdj construction capabilities](https://github.com/shlomoa/django-angular3/issues/56)          | **Aligned** | Cites §2.6, marks upstream #24–#26 complete, leaves #27 open, and tracks only djng consumption and coordination.                                                                                                                                                        |
| [#57 — Complete generation entry points and wrappers](https://github.com/shlomoa/django-angular3/issues/57) | **Aligned** | Separates the executable djng wrapper registry, djng command documentation, Tool catalog, builder requirements, and upstream ngdj authority. It correctly leaves the operation-support matrix, canonical Tool identities, and OpenUI atomic-change mappings unresolved. |
| [#58 — Execute governed construction through Skills](https://github.com/shlomoa/django-angular3/issues/58)  | **Aligned** | Keeps canonical Skills and provider renderings under djng while resolving every ngdj-dependent fact through §2.6. It does not assign deterministic Tool or ngdj behavior to Skills.                                                                                     |
| [#66 — Consume ngdj frontend structure](https://github.com/shlomoa/django-angular3/issues/66)               | **Aligned** | Uses current requirement references, records upstream #25 as complete, and limits remaining work to djng consumption and generated-app acceptance.                                                                                                                      |
| [#74 — Assemble OpenAPI and OpenUI input streams](https://github.com/shlomoa/django-angular3/issues/74)     | **Aligned** | Preserves separate, composable source identities; distinguishes the package-local site assembly definition from canonical OpenUI; and separates upstream #26 delivery from the unresolved #27 boundary.                                                                 |
| [#84 — Implement staged verification](https://github.com/shlomoa/django-angular3/issues/84)                 | **Aligned** | Assigns schematic verification to ngdj and wrapper, composition, cross-input, and generated-app acceptance to djng. It explicitly rejects a competing ngdj test surface.                                                                                                |
| [#139 — Provider-neutral automation foundation](https://github.com/shlomoa/django-angular3/issues/139)      | **Aligned** | Cites §2.6, keeps controlled ngdj invocation within djng-owned validation and allowlisting, and preserves direct Tool/Hook/acceptance authority independently of provider adapters.                                                                                     |

## Remaining issues

These generated-app requirements do not define ngdj commands, options,
schemas, or implementation and are therefore **aligned/not directly
affected**:

- #67, #69, #72, #73, #75, #79, #83

These contain no material ngdj contract claims and are **not directly
applicable**:

- #60–#65
- #68, #70–#71
- #76–#78
- #80–#82

For the provider-neutral phase issues:

- #156 is foundation decision work and contains no ngdj contract definition;
  its prior-input wording must follow the resolved current/previous
  project-configuration pair in `doc/APP_BUILDER_REQUIREMENTS.md` rather than
  introduce a separate previous-OpenUI input;
- #157–#161 implement and verify provider-neutral execution foundations
  without defining ngdj behavior;
- #162 implements catalogued djng Tool contracts only after #57 resolves the
  missing construction contracts and reconciles the existing generic/additive
  contracts; every ngdj-dependent implementation fact must resolve through
  §2.6;
- #163 implements Hook contracts around Tools and must not duplicate their
  ngdj invocation behavior;
- #164 owns direct `build_app` selection and execution against the approved
  wrapper/Tool boundaries; and
- #165 owns guided-session adapters and correctly prohibits bypass of direct
  Tool, Hook, and terminal-validation authority.

## Remaining upstream alignment

The earlier command/status conflicts are resolved:

- [`angular-django2#24`](https://github.com/shlomoa/angular-django2/issues/24)
  records all originally tracked construction targets as delivered and is
  closed.
- Upstream #25 and #26 are closed, and downstream #56 marks them complete.
- Downstream issues now distinguish wrapper availability from Tool,
  `build_app`, Skill, and generated-app acceptance work.

Upstream #27 remains open for the canonical OpenUI-to-construction-input
transformation boundary. Its title and description now distinguish the
canonical OpenUI concrete UI document selected by djng from ngdj's
package-local site assembly definition and use the approved source and
construction terminology. Current implementation and maintained documentation
remain authoritative.

## Next actions

1. Resolve #27's deterministic transformation from validated canonical OpenUI
   atomic changes to explicit ngdj construction inputs without treating the
   package-local site assembly definition as a canonical OpenUI concrete UI
   document.
2. Complete #57's operation-support and canonical Tool-contract decisions,
   reconcile the existing generic/additive Tool contracts, and align the
   authoritative crosswalk, Tool catalog, builder mapping, and phased plan
   before #162 or #164 implements them.
3. Keep future issue updates referential: upstream ngdj facts through §2.6,
   djng Tool contracts through `doc/GENERATE_AI_AUTOMATIONS.md`, and direct
   build behavior through `doc/APP_BUILDER_REQUIREMENTS.md`.
