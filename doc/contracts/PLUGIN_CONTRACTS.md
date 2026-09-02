# Plugin contracts

This document specifies the canonical Plugin contracts used by `djng` to
package coherent bundles of SKILLS, TOOLS, and HOOKS. The automation subsystem
architecture, primitive-selection policy, relationship cardinality, and naming
crosswalk are defined in `ARCHITECTURE.md` §§2.22 and 3.6. Exact internal
module organization, persistence, execution, adapter, and rendering
realization are defined in
`doc/specifications/AI_AUTOMATION_SPECIFICATIONS.md`.

All `ngdj` command, option, and behavior facts used by these contracts follow
the upstream-source policy in `ARCHITECTURE.md` §2.6. This document defines
only `djng`-owned Plugin contracts and does not redefine the underlying `ngdj`
schematic surface.

The sibling automation contract owners are [TOOL_CONTRACTS.md],
[HOOK_CONTRACTS.md], [PROVIDER_ADAPTER_CONTRACTS.md], and
[SKILL_CONTRACTS.md]. The canonical Change Model is defined in
[CHANGE_MODEL_CONTRACTS.md].

---

## Plugins

Use PLUGINS to package coherent bundles of SKILLS, TOOLS, and HOOKS for reuse
or distribution. In the `djng` architecture, candidate bundles include the
djng Angular construction capability, the ngdj scaffold capability, and the
contract lifecycle capability.

Per-capability plugin contracts are defined in the
[Plugin Contracts Catalog](#plugin-contracts-catalog) below. Each contract
follows the same fixed shape — **name, purpose, bundled SKILLS, bundled TOOLS,
bundled HOOKS, distribution, versioning, dependencies, installation, and
implementation reference** — so consumers of a plugin can see at a glance what
it contains, where it ships from, and how it is brought into a project.

### Plugin contract shape

Every plugin contract in this document **MUST** specify:

| Field | Meaning |
|---|---|
| **Name** | The stable provider-neutral identifier the plugin is published under. Each provider rendering maps it to that provider's manifest or registry identifier. |
| **Purpose** | One-sentence statement of the coherent capability the plugin packages. The purpose MUST identify a single domain (Angular construction, Angular scaffold, contract lifecycle) so two plugins never claim the same scope. |
| **Bundled SKILLS** | The exact canonical Skill names from the [Skills Catalog](SKILL_CONTRACTS.md#skills-catalog). A plugin MAY ship zero Skills; if so, this field is `none` and the plugin packages only TOOLS, HOOKS, or provider integration configuration. |
| **Bundled TOOLS** | The exact list of tool contract names (from the [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog)) that the plugin exposes. A provider rendering maps those names to its native tool registration. A plugin MAY ship zero tools. |
| **Bundled HOOKS** | The exact list of hook contract names (from the [Hook Contracts Catalog](HOOK_CONTRACTS.md#hook-contracts-catalog)) that the plugin registers, including their provider-neutral lifecycle family. A plugin MAY ship zero hooks. |
| **Distribution** | How the canonical plugin contract is rendered and shipped for each provider. The field names the source repository, provider-specific published artifact, and consumer channel. |
| **Versioning** | The semantic-versioning policy the plugin follows, including which upstream packages (e.g. `django-angular3`, `angular-django2`, `oasdiff`) its version is coupled to and how breaking-change bumps are signalled. Provider manifests derive their version from this contract version. |
| **Dependencies** | Other plugins, MCP servers, CLI binaries, or runtime packages that MUST be present for the plugin's bundled SKILLS / TOOLS / HOOKS to function. Dependencies are declared explicitly so installation is deterministic and so a plugin cannot silently rely on capabilities outside its catalog entry. |
| **Installation** | The provider-specific command or configuration sequence that installs the derived package. The canonical contract does not prescribe a provider's package format or invocation syntax. |
| **Implementation reference** | Pointer to the concrete plugin source (repository path, planned ticket, or external package) that backs the contract today, so the contract and the implementation can be kept aligned. |

Contracts are normative. A plugin that ships SKILLS, TOOLS, or HOOKS not
listed in its catalog entry — or that omits a listed entry — is a bug in the
plugin, not in the contract.

#### Provider package rendering

The Plugin Contracts Catalog is the canonical plugin source. A provider
adapter renders a contract into that provider's manifest, registry entry, and
installation workflow; those rendered packages are derived artifacts. For
example, `.claude-plugin/plugin.json`, its `skills/` layout, and `/plugin`
commands apply only to the Claude rendering. They do not prescribe an OpenAI,
Gemini, or Copilot package format or invocation mechanism.

Every provider rendering MUST preserve the canonical plugin name, version,
bundled Skill, Tool, and Hook identities, dependencies, and lifecycle-family
bindings. Provider-package conformance tests MUST compare each rendered
package with its catalog contract and verify provider installation and a
generated-app smoke path before release.

#### Shape rationale

The fields are provider-neutral plugin-contract requirements, informed by the
Claude Code plugin model ([Claude Code Plugins][Claude Plugins]) and by the
responsibilities a plugin assumes in the `djng` architecture:

- **Name**, **Versioning**, and **Distribution** anchor the plugin to its
  published artifact. A consumer needs to know which name to install, which
  version maps to which combination of bundled capabilities, and where the
  artifact ships from, before any of the bundled SKILLS / TOOLS / HOOKS can be
  invoked.
- **Bundled SKILLS**, **Bundled TOOLS**, and **Bundled HOOKS** make the plugin
  contents explicit and verifiable. Each item in these lists MUST appear in the
  corresponding catalog ([Skills Catalog](SKILL_CONTRACTS.md#skills-catalog),
  [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog),
  [Hook Contracts Catalog](HOOK_CONTRACTS.md#hook-contracts-catalog)) so that
  the plugin's surface area can be audited without reading its source. This
  prevents two plugins from silently shipping divergent copies of the same
  SKILL or HOOK.
- **Purpose** enforces the single-domain rule from the primitive-selection
  policy in `ARCHITECTURE.md` §3.6.3: a plugin that
  claims more than one domain has either accidentally taken on a second
  capability or should be split. Stating the purpose in one sentence forces
  that scoping decision into the contract.
- **Dependencies** and **Installation** make the activation footprint
  deterministic. A consumer who reads the contract can predict exactly which
  CLIs, MCP servers, or upstream packages must be installed alongside the
  plugin, and what command brings the plugin into a project. Without these
  fields, plugins can rely on implicit environment assumptions that break on a
  fresh machine.
- **Implementation reference** links the normative contract to the concrete
  backing artifact (repository path, in-tree `.claude-plugin/` directory, or
  external package) so drift between the spec and the shipped plugin is
  detectable during review.

## Plugin Contracts Catalog

This catalog defines the plugin contracts. Each entry follows the
[plugin contract shape](#plugin-contract-shape) defined above.

The contracts are grouped by domain so the command-execution and project-setup
relationships are visually obvious: **construction-side plugins** (`djng`
Angular construction, `ngdj` scaffold) drive generation, and the
**contract-side plugin** (contract lifecycle) governs the OpenAPI boundary
between Django and Angular.

### Construction-side plugins

#### 1. `djng-angular-construction` — Angular construction bundle

**Name**: `djng-angular-construction`

**Purpose**: Package the full djng Angular construction capability — all
Angular SKILLS, the construction-side TOOLS, and the construction-time HOOKS —
as one provider-neutral capability bundle that each provider renderer can
package for installation.

**Bundled SKILLS** (from the [Skills Catalog](SKILL_CONTRACTS.md#skills-catalog) in [SKILL_CONTRACTS.md]):

| Skill name | Role |
|---|---|
| `angular-workspace-foundation` | Generate the Angular workspace shell. |
| `angular-app-composition` | Generate the Angular application inside the workspace. |
| `angular-api-integration` | Generate the OpenAPI-derived API integration layer. |
| `angular-data-service-composition` | Optionally interpret or refine data-service behavior beyond the structured schematic input. |
| `angular-field-component-composition` | Optionally interpret or refine field-component behavior beyond the structured schematic input. |
| `angular-form-field-composition` | Optionally interpret or refine form-field behavior beyond the structured schematic input. |
| `angular-component-composition` | Optionally interpret or refine standalone component behavior beyond the structured schematic input. |
| `angular-complex-component-composition` | Optionally interpret or refine complex-component behavior beyond the structured schematic input. |
| `angular-reactive-form-composition` | Optionally interpret or refine reactive-form behavior beyond the validated OpenUI definition. |
| `angular-page-composition` | Optionally interpret or refine routed-page behavior beyond the validated OpenUI definition. |
| `angular-site-composition` | Optionally interpret or refine site composition beyond the validated OpenUI definition. |

**Bundled TOOLS** (from the [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog)):

| Tool name | Role inside the plugin |
|---|---|
| `angular_api_client_generate` | Wrap workspace-local `ng-openapi-gen` for typed-client generation. |
| `validate_openapi_schema` | Provide the schema-validation callable used by both SKILLS and the wrapped HOOK. |

The Claude rendering exposes these tools through one `mcp-servers/` MCP-server
configuration. Other renderings expose the same canonical tool identities in
their provider-native form.

**Bundled HOOKS** (from the [Hook Contracts Catalog](HOOK_CONTRACTS.md#hook-contracts-catalog)):

| Hook name | Lifecycle event | Role inside the plugin |
|---|---|---|
| `pre-construction` | `pre-tool` on `angular_api_client_generate`, `angular_workspace_scaffold`, `angular_app_scaffold` | Block any construction tool until the OpenAPI schema is present and valid. |
| `post-generation` | `post-tool` on the construction tools above | Write structured verification logs after each generation step. |
| `session-stop` | `session-stop` | Archive `build/command-execution.*` and write the session summary. |

**Distribution**: The canonical contract is maintained in this repository
(`django-angular3`). Provider renderers produce derived installation artifacts.
The currently planned Claude rendering is an in-tree `.claude-plugin/`
directory and, once published, a Claude Code plugin-marketplace entry under
the same name.

**Versioning**: Semantic versioning coupled to the `django-angular3` Python
package version. A major bump in `django-angular3` MUST be accompanied by a
major bump of `djng-angular-construction`. Breaking changes to any bundled
SKILL / TOOL / HOOK contract surface are signalled by a major bump regardless
of the upstream Python package version.

**Dependencies**:

- `django-angular3` Python package installed in the project's virtualenv (for
  the `export_schema` and `validate-project` `django-admin` commands the
  bundled SKILLS and HOOKS invoke).
- `contract-lifecycle` plugin (§3 below) — the `pre-construction` hook
  bundled here depends on `validate_openapi_schema` and on the lifecycle
  artifacts the `contract-lifecycle` plugin guarantees.
- A workspace-local install of `ng-openapi-gen` (resolved via `pnpm exec`,
  consistent with the project principle that Angular tooling MUST NOT download
  packages at runtime).

**Installation**: Each provider rendering defines its own opt-in installation
workflow. For the planned Claude rendering, use `/plugin install
djng-angular-construction` (marketplace install) or `/plugin add
./path/to/django-angular3/.claude-plugin/djng-angular-construction` (local
install). After this Claude installation, no additional `settings.json`
registration is required because its rendered manifest declares its lifecycle
events.

**Implementation reference**: The planned Claude rendering is the
`.claude-plugin/djng-angular-construction/` directory in this repository,
sourcing its derived skills from the existing skill specifications in
[SKILL_CONTRACTS.md] (§Skills Catalog), its tools from
`django_angular3/management/commands/`, and its hooks from the
`pre-construction`, `post-generation`, and `session-stop` entries in the
[Hook Contracts Catalog](HOOK_CONTRACTS.md#hook-contracts-catalog).

#### 2. `ngdj-scaffold` — Angular schematics bundle

**Name**: `ngdj-scaffold`

**Purpose**: Package deterministic `ngdj` Angular workspace, application,
feature, and component schematics behind provider-neutral structured tool
calls usable directly by `build_app` or, optionally, by an agent.

**Bundled SKILLS**: none. `ngdj`'s scaffold operations are deterministic and
belong in TOOLS, not SKILLS; the AI-guided generation work that surrounds
them is owned by `djng-angular-construction` (§1) instead.

**Bundled TOOLS** (from the [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog)):

| Tool name | Role inside the plugin |
|---|---|
| `angular_workspace_scaffold` | Wrap the `ngdj` workspace-creation schematic. |
| `angular_app_scaffold` | Wrap the `ngdj` application-creation schematic. |
| `ngdj_add_feature` | Create a feature page, feature route, and application-route registration. |
| `ngdj_add_component` | Generate a standalone component with embedding hooks. |
| `ngdj_run_schematic` | Run an explicitly allowlisted ngdj schematic. |

The Claude rendering exposes the wrapped tools through an `mcp-servers/` MCP
server configuration pointing at the ngdj CLI. Other renderings expose the
same canonical tool identities in their provider-native form.

**Bundled HOOKS**: none. The lifecycle gates that protect `ngdj` invocations
(`pre-construction`, `post-generation`) are bundled inside
`djng-angular-construction` (§1) so they apply uniformly to every
construction tool regardless of which scaffold plugin actually backs the
call. `ngdj-scaffold` MUST NOT ship its own copies of those hooks.

**Distribution**: The canonical contract is maintained with the
`angular-django2` (`ngdj`) source. Provider renderers produce derived
installation artifacts. The currently planned Claude rendering is a
`.claude-plugin/` directory in that repository and, once published, a Claude
Code plugin-marketplace entry under the same name.

**Versioning**: Semantic versioning coupled to the `angular-django2` npm
package version. A major bump in `angular-django2` MUST be accompanied by a
major bump of `ngdj-scaffold`. Because `ngdj` schematics define the input
shape of the bundled tool contracts, any schematic argument change that is
not backward-compatible is a breaking change for this plugin.

**Dependencies**:

- `angular-django2` (`ngdj`) npm package installed as a workspace-local
  dependency of the generated app, invoked via `pnpm exec` (Angular tooling
  MUST NOT download packages at runtime).
- Node.js and `pnpm` available on the host running the construction agent.
- `djng` applies the documented lifecycle gates when these tools run through
  `build_app`. A rendered `djng-angular-construction` plugin may provide the
  equivalent gates inside an optional provider session, but it is not a
  dependency of `ngdj`, its schematics, or direct deterministic execution.

**Installation**: Each provider rendering defines its own opt-in installation
workflow. For the planned Claude rendering, use `/plugin install ngdj-scaffold`
(marketplace install). The `angular-django2` npm package must already be
installed in the workspace (`pnpm add -D angular-django2`) before the rendered
tools can succeed.

**Implementation reference**: The planned Claude rendering is the
`.claude-plugin/ngdj-scaffold/` directory in the `angular-django2` repository,
sourcing its tool wrappers from the
`angular_workspace_scaffold` and `angular_app_scaffold` contracts in the
[Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog) and its MCP
server configuration from the `ngdj` CLI entry point.

### Contract-side plugins

#### 3. `contract-lifecycle` — OpenAPI contract bundle

**Name**: `contract-lifecycle`

**Purpose**: Package the export → validate → diff lifecycle for the
OpenAPI contract as a self-contained provider-neutral capability bundle so
teams working only on the backend contract layer can install a rendered package
without pulling in the full Angular construction stack.

**Bundled SKILLS**: none. The contract lifecycle is fully deterministic; AI
judgment is not required between export, validate, and diff.

**Bundled TOOLS** (from the [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog)):

| Tool name | Role inside the plugin |
|---|---|
| `openapi_schema_export` | Trigger OpenAPI schema extraction from DRF. |
| `validate_openapi_schema` | Validate that the exported schema is well-formed OAS 3.1. |
| `oasdiff_diff` | Run `oasdiff` and return structured diff output (`changes`, `schema_changed`). |
| `oasdiff_changelog` | Generate the durable human-readable schema-change report. |

The Claude rendering exposes these tools through one `mcp-servers/` MCP-server
configuration. Other renderings expose the same canonical tool identities in
their provider-native form.

**Bundled HOOKS** (from the [Hook Contracts Catalog](HOOK_CONTRACTS.md#hook-contracts-catalog)):

| Hook name | Lifecycle event | Role inside the plugin |
|---|---|---|
| `migration-triggered` | `post-tool` on Django migration commands | Re-export the OpenAPI schema whenever models change. |

The `pre-construction` hook is NOT bundled here even though it invokes
`validate_openapi_schema`: that hook is scoped to construction-side tools
(`angular_api_client_generate`, `angular_workspace_scaffold`,
`angular_app_scaffold`) and therefore belongs to
`djng-angular-construction` (§1). `contract-lifecycle` provides the tool the
hook depends on, not the hook itself.

**Distribution**: The canonical contract is maintained in this repository
(`django-angular3`). Provider renderers produce derived installation artifacts.
The currently planned Claude rendering is an in-tree `.claude-plugin/`
directory and, once published, a Claude Code plugin-marketplace entry under
the same name. The canonical bundle is independent of
`djng-angular-construction` so backend-only projects can install a rendered
package on its own.

**Versioning**: Semantic versioning coupled to the `django-angular3` Python
package version for `export_schema` and `validate_openapi_schema`, and
additionally pinned to a tested `oasdiff` CLI major version for `oasdiff_diff`.
A breaking change in either upstream MUST be reflected as a major bump of
`contract-lifecycle`.

**Dependencies**:

- `django-angular3` Python package installed in the project's virtualenv (for
  the `export_schema` and `validate-project` `django-admin` commands the
  bundled tools and hooks invoke).
- `oasdiff` CLI binary available on the host `PATH`.
- No dependency on `djng-angular-construction` or `ngdj-scaffold`:
  `contract-lifecycle` is the lowest layer of the plugin stack and MUST be
  installable on its own.

**Installation**: Each provider rendering defines its own opt-in installation
workflow. For the planned Claude rendering, use `/plugin install
contract-lifecycle` (marketplace install) or `/plugin add
./path/to/django-angular3/.claude-plugin/contract-lifecycle` (local install).
The `oasdiff` binary must be installed separately (the rendered package does
not bundle it, per the project principle that tooling MUST NOT download
packages at runtime).

**Implementation reference**: The planned Claude rendering is the
`.claude-plugin/contract-lifecycle/` directory in this repository, sourcing
its tools from
`django_angular3/management/commands/export_schema.py` and the
`oasdiff_diff` / `validate_openapi_schema` contracts in the
[Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog), and its
hooks from the `migration-triggered` entry in the
[Hook Contracts Catalog](HOOK_CONTRACTS.md#hook-contracts-catalog).

### Contract compliance

- A plugin MUST ship exactly the SKILLS, TOOLS, and HOOKS listed in its
  catalog entry — no more and no less. A plugin found to bundle an
  un-catalogued capability, or to omit a listed one, is a bug in the plugin
  and MUST be corrected before release.
- Every SKILL listed in a plugin's `Bundled SKILLS` field MUST appear in the
  [Skills Catalog](SKILL_CONTRACTS.md#skills-catalog); every TOOL listed in
  `Bundled TOOLS` MUST appear in the
  [Tool Contracts Catalog](TOOL_CONTRACTS.md#tool-contracts-catalog);
  every HOOK listed in `Bundled HOOKS` MUST appear in the
  [Hook Contracts Catalog](HOOK_CONTRACTS.md#hook-contracts-catalog). Plugins
  MUST NOT introduce new capability contracts inline.
- Two plugins MUST NOT bundle the same HOOK contract under the same lifecycle
  event. When two domains both need a deterministic enforcement point, the
  hook belongs to the plugin that owns the scoped tool, and the other plugin
  declares the first as a dependency. The split of the `pre-construction`
  hook into `djng-angular-construction` (§1) — even though it invokes a tool
  bundled by `contract-lifecycle` (§3) — is the canonical example.
- New plugin bundles added to `djng` MUST be documented here using the
  [plugin contract shape](#plugin-contract-shape) before they may be
  rendered for any provider, listed in this catalog, or recommended in
  `doc/ARCHITECTURE.md` or
  `doc/requirements/APP_BUILDER_REQUIREMENTS.md`.

[Claude Plugins]: https://code.claude.com/docs/en/plugins
[CHANGE_MODEL_CONTRACTS.md]: CHANGE_MODEL_CONTRACTS.md
[HOOK_CONTRACTS.md]: HOOK_CONTRACTS.md
[PROVIDER_ADAPTER_CONTRACTS.md]: PROVIDER_ADAPTER_CONTRACTS.md
[SKILL_CONTRACTS.md]: SKILL_CONTRACTS.md
[TOOL_CONTRACTS.md]: TOOL_CONTRACTS.md
