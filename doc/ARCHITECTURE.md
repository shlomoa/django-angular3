# Architecture

## 1. Purpose and scope

This document describes the architecture of `django-angular3` (package: [django-angular3]; source: [django-angular3-github]) as a contract-driven, agentically orchestrated, AI-automation-based system for generating and integrating Angular application building blocks against a [Django] and [Django REST Framework (DRF)][DRF - Django REST Framework] backend. The backend contract is expressed as a structured [OpenAPI contract (Schema)][OpenAPI 3.1 Specification], which serves as the integration boundary and the source of truth for CRM-facing functionality.

This solution is not an application and not a general development environment. It is an architecture for constructing and evolving generated applications. Construction may be non-deterministic, but acceptance is deterministic: the generated application is considered correct only when it assembles into a working whole and passes the defined validations and tests.

`django-angular3` extends Django/DRF with contract-driven Angular integration. It governs the construction process, uses agentic orchestration to coordinate iterative bounded construction through SKILLS, TOOLS, HOOKS, and PLUGINS, and integrates generated building blocks into a working application while preserving architectural boundaries between backend, frontend, generated artifacts, and non-CRM content.

This document covers:
- Architectural principles, architectural actors, system components, and integration workflows.
- The construction, control, and acceptance model used to generate and integrate application building blocks.
- Architectural decisions and directions and the rationale behind them.

This document does not cover:
- Detailed implementation guidance for Django, DRF, or Angular development
- OpenAPI specification and API design.
- General web application development principles or architecture

---

## 2. Terms and Definitions

### 2.1 [Django]

A high-level Python web framework that encourages rapid development and clean, pragmatic design. It provides an ORM, authentication, admin interface, and a robust ecosystem of packages. Source: [Django-github].

### 2.2 [Django REST Framework (DRF)][DRF - Django REST Framework]

A powerful and flexible toolkit for building Web APIs in Django. It provides serializers, viewsets, authentication, permissions, and schema generation capabilities. Source: [DRF-github].

### 2.3 [Angular]
A TypeScript-based open-source web application framework led by the Angular Team at Google. It provides a component-based architecture, powerful templating, and a rich ecosystem for building dynamic single-page applications.

### 2.4 [Angular Material]
A UI component library for Angular that implements Google's Material Design. It provides pre-built components for layout, forms, navigation, and more, with a consistent design language.

### 2.5 djng
The `django-angular3` solution — this repository, the Django package, and the
tool. Contains the agent, the AI automation subsystem, `build_app`, and all configuration files
required for construction. See §19 Glossary.

### 2.6 ngdj
The `angular-django2` companion package: the Angular-side construction substrate in this architecture. It provides schematics, templates, and workspace/application assembly helpers used to materialize Angular-side outputs derived by `djng`.

### 2.7 [OpenAPI]
A specification for building APIs that allows both humans and computers to understand the capabilities of a service without access to source code. It serves as a contract between the backend and frontend in this architecture.

### 2.8 CRM
CRM stands for Customer Relationship Management. In this architecture, it is shorthand for contract-derived business-domain content represented by the backend schema and API. It is not limited to a literal customer-sales system.

### 2.9 non-CRM content
Content that is not directly derived from the OpenAPI contract, such as bespoke reactive form definitions, standalone page layouts, and workflow-specific UI metadata. This content is defined in a separate structured input source and complements the CRM-derived Angular integration artifacts.

### 2.10 [OpenAPI contract - Schema][OpenAPI 3.1 Specification]
The versioned OpenAPI schema exported from the DRF layer, serving as the source of truth for CRM-facing functionality and the basis for generating Angular integration artifacts.

### 2.11 Angular integration artifacts
Generated Angular outputs derived from the OpenAPI contract and related tooling, including typed API clients, resource adapters, transport helpers, reusable Angular Material-oriented integration helpers, and supporting metadata.

### 2.12 [Claude Agent SDK][Claude Agent SDK - Python]
Anthropic's official agent-construction SDK. The agent (§2.16) uses it to run each procedure as a guided agent session via `query()` calls. Installed as `pip install claude-agent-sdk`. Implementation repository: [Claude Agent SDK - Python - GitHub].

### 2.13 agentic orchestration
An orchestration model in which the orchestrator delegates construction work to
an AI agent rather than executing it through a fixed procedural pipeline. The
orchestrator derives a procedure graph from change requirements and configuration,
then executes each procedure through the appropriate automation primitive or
combination of primitives. Guided agent sessions carry out AI-guided
construction work guided by the specified SKILL(s); deterministic TOOLS handle
bounded operations; HOOKS enforce lifecycle gates and mandatory side effects.

### 2.14 [SKILLS][Claude Skills]
Bounded AI skills that guide the agent within each guided agent session. Each SKILL encapsulates a constrained generation, modification, or integration capability used to create and glue application building blocks while remaining within architectural and contract-defined boundaries.

The formal skill format is defined by Anthropic: see [Claude Skills] for the conceptual overview, [Claude Code Skills] for the CLI-facing reference (extended frontmatter, invocation control, dynamic context injection), and [Claude Agent SDK Skills] for SDK-side discovery and invocation. Authoring guidance is at [Claude Skills Best Practices].

SKILLS are one primitive family within the broader AI automation subsystem of `django-angular3`. That automation subsystem architecture is defined in `doc/GENERATE_AI_AUTOMATIONS.md`, and the implementation and authoring plan for the SKILLS subset is defined in `doc/SKILL_AUTHORING_PLAN.md`. This document defines the role of SKILLS in the overall architecture and does not restate their internal design.

### 2.15 AI-automation-based construction
A construction model in which bounded AI automations are the execution units for generating, modifying, validating, and integrating application building blocks. In this model, SKILLS provide AI-guided generation and integration behavior, TOOLS provide deterministic bounded operations, HOOKS enforce lifecycle gates and mandatory side effects, and PLUGINS package coherent capability bundles for reuse. This model allows controlled generative freedom while keeping construction within architectural, contract-defined, and validation-defined boundaries.

The normative selection rule for classifying a new capability as a SKILL, TOOL, HOOK, or PLUGIN is defined in `doc/GENERATE_AI_AUTOMATIONS.md` §Primitive-selection policy. New capabilities added to the automation subsystem MUST be classified through that policy before implementation begins.

### 2.16 agent
The agentic orchestrator in this architecture, bundled in `djng`. It consumes
change requirements, configuration files, and contract-derived inputs, derives a
procedure graph, and coordinates the execution of each procedure to build the
generated application. For AI-guided procedures it runs guided agent sessions;
for deterministic procedures it relies on tool contracts and lifecycle hooks.
At implementation level, driven by the Claude Agent SDK.
The `build_app` Django management command is its entry point.

### 2.17 correct working application
An application that assembles into a runnable whole and satisfies the deterministic validations and tests defined by this architecture. Individual generated artifacts alone do not establish correctness.

### 2.18 correct-by-construction
An architectural goal in which bounded construction, architectural constraints, contract-defined rules, and deterministic validation gates drive generation toward a correct working application, even when the internal construction path is not deterministic.

### 2.19 non-deterministic generation
Generation in which the internal construction path, intermediate decisions, or exact emitted outputs may vary across valid runs. This variation is allowed as long as the resulting application still satisfies the architecture's deterministic acceptance criteria.

### 2.20 deterministic acceptance
An acceptance model in which correctness is decided by explicit validations and tests. Regardless of how generation proceeds internally, acceptance criteria remain stable and repeatable.

### 2.21 Django Project vs Django App

A **Django project** is the root configuration container: it holds `settings.py`,
the root `urls.py`, `wsgi.py`/`asgi.py`, and `manage.py`. There is exactly one
project per deployed application.

A **Django app** is a self-contained domain module within a project. It owns its
own models, views, serializers, admin registrations, and migrations. A project
contains one or more apps. App names are domain-driven (e.g. `shop`, `accounts`,
`inventory`) and must be distinct from the project name.

In `django-angular3.json`:
- `project.name` — names the Django project and the Angular workspace.
- `app.name` — names the primary Django app **and** the Angular application
  generated inside that workspace. Both share this name by convention.

### 2.22 model-first and contract-first backend origination

Two distinct ways the backend data model and its OpenAPI contract come into
existence. They are alternative origination paths, not competing sources of
truth.

- **Model-first (DRF-first):** a Django data model already exists. DRF
  elaboration produces the API, and the OpenAPI contract is *exported from* the
  DRF layer via [drf-spectacular]. This is the steady-state mode once a backend
  exists.
- **Contract-first (OpenAPI-first):** no Django data model exists yet. An
  existing [OpenAPI contract][OpenAPI 3.1 Specification] is the origination
  input, and the Django data model is *generated from* it using
  [datamodel-code-generator] driven by djng-owned custom Django templates. DRF
  elaboration (serializers, views, authentication, permissions) is then layered
  on the generated model.

Both modes converge on the same invariant: once a backend exists, the OpenAPI
contract is the source of truth for CRM-facing functionality (§11.1). See §11.2
for the generation toolchain and §17 for the corresponding decision.

### 2.23 Automation naming layers

Four distinct naming layers appear in the `djng`/`ngdj` automation subsystem.
Each layer has a different owner, stability contract, and purpose. Keeping them
separate prevents name collision between the CLI surface, the agent API, and
the AI-guided session API.

- **Concern key** — A stable, dot-namespaced semantic identifier for a
  construction concern. Used in planning and documentation only; never appears
  in filenames, code identifiers, or command names. The canonical concern keys
  are:

  *Angular construction:*

  | Concern key | Construction concern |
  |---|---|
  | `angular.workspace` | Workspace scaffold and configuration |
  | `angular.app` | Application scaffold |
  | `angular.api-client` | Typed API client generation from OpenAPI |
  | `angular.data-service` | Data service layer |
  | `angular.field-component` | Reusable form field components |
  | `angular.form-field` | CVA-backed form field boilerplate |
  | `angular.component` | Standalone components |
  | `angular.complex-component` | Composite/complex components |
  | `angular.reactive-form` | Typed reactive forms |
  | `angular.page` | Routed page components |
  | `angular.site` | Site shell and route tree |

  *Contract lifecycle:*

  | Concern key | Construction concern |
  |---|---|
  | `contract.schema-export` | OpenAPI schema extraction from DRF |
  | `contract.schema-validate` | Schema validation (OAS 3.1 conformance) |
  | `contract.schema-diff` | Schema diff and change detection |
- **CLI wrapper command** — The Django management command name for a `djng`
  wrapper (e.g. `ng_workspace`, `ng_openapi_gen`, `export_schema`). Frozen:
  these names are part of the public operator interface and MUST NOT be renamed
  without a deprecation cycle.
- **TOOL contract** — The deterministic operation name exposed to the agent and
  the procedure graph (e.g. `angular_workspace_scaffold`,
  `angular_api_client_generate`, `openapi_schema_export`). Defined in
  `doc/GENERATE_AI_AUTOMATIONS.md` §Tool Contracts Catalog. The `tool` field
  of every `tool` procedure node MUST equal one of these names.
- **SKILL name** — The AI-guided session name passed to `build_app`'s
  `query(skills=[...])` call (e.g. `angular-workspace-foundation`,
  `angular-app-composition`, `angular-api-integration`). Defined in
  `doc/GENERATE_AI_AUTOMATIONS.md` §Skills Catalog. The `skill` field of every
  `skill-session` procedure node MUST equal one of these names.

The complete mapping of all four layers for every construction concern is
maintained in `doc/GENERATE_AI_AUTOMATIONS.md` §Automation Naming Crosswalk.

---

## 3. Toolchain Design

### 3.1 Inputs

|Input|Description|
|:-|:-|
|DRF model (model-first)|A Django model with DRF elaboration including endpoints, at least: serializers, views, authentication, and permissions. Origination input in the model-first mode (§2.22)|
|OpenAPI Schema (contract-first)|An existing OpenAPI Schema used as the backend origination input when no Django model exists yet; the Django data model is generated from it (§2.22, §11.2)|
|Project configuration|A json file describing the project, apps, UI parts, and other configuration details|
|Non-CRM Angular content|Bespoke reactive form definitions, standalone page layouts, and workflow-specific UI metadata defined in a separate structured input source|

### 3.2 Generated artifacts

|Artifact|Description|
|:-|:-|
|`OpenAPI contract`|A versioned OpenAPI schema exported from the DRF layer, serving as the source of truth for CRM-facing functionality|
|Angular integration artifacts|Generated Angular code including typed API clients, resource adapters, and reusable Angular Material-oriented integration helpers derived from the OpenAPI contract|


### 3.3 djng

`djng` is the `django-angular3` solution — this repository, the Django package,
and the tool. It contains the agent, the AI automation subsystem, `build_app`, and all configuration
files. See §2.5 and §19 Glossary.

- Purpose: The backend owner.
  - Govern the overall integration process
  - Manage the backend contract, and derive Angular-side work.
    - Manage Python/Django/DRF side of integration.
    - Define the work that must be carried out by the orchestrator and construction subsystems.
- Responsibilities:
  - djng-o-1: Provide a set of complementing django-admin commands:
    - For creating, building, and modifying Angular UI.
    - Manage OpenAPI contract lifecycle, including: contract extraction from DRF, validation, versioning
  - djng-o-2: Define, author, and evolve the AI automations required for building, generating, validating, and integrating Angular building blocks.
    - SKILLS for AI-guided generation and integration work.
    - TOOLS for deterministic construction and contract operations.
    - HOOKS for lifecycle enforcement, audit, and mandatory side effects.
    - PLUGINS for reusable capability bundles where distribution boundaries matter.
  - djng-o-3: Manage and drive Angular app change requirements through:
    - Detection of change requirements.
    - Converting change requirements into procedure graph inputs
  - djng-o-4: Provide the orchestration entry points and work definitions consumed by the agent:
    - The agent runs each procedure as a guided agent session to generate Angular building blocks.
    - The agent integrates those building blocks into an [Angular Material] frontend app using the DRF `contract`.

- `djng` defines and governs the work to be performed; the agent derives the procedure graph and runs each procedure as a guided agent session.

### 3.4 ngdj

implemented in [angular-django2-github] and deployed to [angular-django2] npm package.

- Purpose: A companion [Angular] ([npmjs] package) that provides the Angular-side construction substrate used to materialize required outputs.
- Responsibilities:
  - ngdj-o-1: Provide a set of commands for managing and assembling the Angular application, including workspace, project layout, application layout.
  - ngdj-o-2: Provide Angular schematics and code generation templates for generating Angular building blocks from OpenAPI contracts.
  - ngdj-o-3: Provide a set of Angular schematics and code generation templates for generating Angular building blocks from non-CRM content definitions.


### 3.5 Toolchain components

- A contract-governing, work-deriving component - in `djng`.
- The agent: the agentic orchestrator that derives the procedure graph and coordinates the execution of each procedure.
- An AI automation subsystem containing SKILLS, TOOLS, HOOKS, and PLUGINS used to guide, execute, enforce, and package construction work.
- An Angular-side construction substrate and application generator - in `ngdj`.
- An OpenAPI schema extraction process - in `djng`.
- An OpenAPI TypeScript generation process - in `ngdj`.
- A structured UI definition management system - in `djng`.
- Requirements for the AI automation subsystem and `ngdj` are derived from `djng`.

---

## 4. Separation of Responsibilities

Applicable to the application built with the help of this system

### 4.1 Backend responsibilities

Django and DRF are responsible for:

- Data models and persistence
- Business logic and workflow enforcement on the server
- Authentication, authorization, and audit enforcement
- Data administration and operational admin tooling
- Backend packaging, API delivery, and server-side deployment artifacts

### 4.2 Frontend responsibilities

Angular Material is responsible for:

- The user-facing application shell
- End-user pages, workflows, forms, dialogs, and tables
- End-user application routing
- Presentation logic and client-side interaction behavior
- Consuming backend APIs for the user-facing application experience

### 4.3 Ownership boundary

- Django templates, Django admin, and DRF-backed interfaces may be used for data
  administration services and operator workflows
- Django serves API, authentication, and administration endpoints
- Angular owns the user-facing route tree and navigation behavior
- Angular Material remains the primary UI system for the user-facing
  application
- Angular Material is the default and preferred UI system for all user-facing
  functionality
  
---

## 5. Deployment Model

Applicable to the application built with the help of this system

### 5.1 Recommended Production Model

Use a same-origin deployment:

- Angular Material App is built into static assets
- Django serves the API under `/api/`
- Django serves authentication and administration endpoints under backend-owned
  routes
- Static assets are served either by Django plus a static file layer or by a
  reverse proxy in front of Django
- The browser talks to one origin for both UI and API
- User-facing application routes resolve to the Angular entry point

This model simplifies:

- Authentication via secure cookies and CSRF protection
- Removal of most CORS concerns
- Local reasoning about routing and deployment
- A clean split where Django serves backend capabilities and Angular serves the
  user-facing experience

### 5.2 Local Development Model

- Django runs as the backend development server
- Angular runs its local development server
- The Angular dev server proxies API traffic to Django
- The Angular dev server owns user-facing route handling during development
- Frontend routes and backend routes remain distinct

---

## 6. Architectural Principles

- Prefer proven framework conventions over custom infrastructure
- Keep frontend and backend decoupled at the API boundary, but integrated in
  deployment
- Optimize for maintainability and incremental delivery
- Make security, testing, and observability part of the default design
- Keep the first version simple; add complexity only when a real feature
  requires it

---

## 7. Integration Workflow

The integration process is an agentic construction flow. `djng` governs contract
lifecycle, validation, and work derivation; the agent derives the procedure graph
and executes a mixed automation flow toward an acceptable application state.
Guided agent sessions handle AI-guided work, TOOLS handle deterministic bounded
operations, and HOOKS enforce lifecycle gates and mandatory side effects.

The workflow is not a one-pass pipeline. The stages below describe the
architectural work domains involved in construction. Within each guided agent
session, the agent iterates as needed to satisfy the procedure's acceptance
criteria.

### 7.1 Control-loop stages

1. Backend contract stage: Django models, serializers, and DRF endpoints define
   the business contract and emit an OpenAPI artifact
2. Contract normalization stage: the OpenAPI artifact is validated, diffed
   against the previous version to detect breaking and non-breaking changes, 
   versioned, and prepared for CRM-facing generation
3. Angular integration artifacts generation stage: the OpenAPI contract produces typed
   clients, resource adapters, and reusable Angular Material-oriented
   integration helpers
4. Non-CRM content stage: a separate structured input source provides bespoke
   reactive forms, standalone pages, and workflow definitions
5. Application assembly stage: the Angular app composes CRM-derived outputs from
   generated integration artifacts with the non-CRM content stream
6. Verification stage: generated artifacts, contracts, and app integration are
   validated through automated tests and review

Each stage should produce durable artifacts that can be inspected, tested, and
reused across iterations without hidden assumptions.

### 7.2 Repair and refinement loop

A typical construction cycle is:

1. Derive required work from contract changes, configuration, and structured inputs
2. Execute each procedure through the required automation primitive(s): guided
  agent session, deterministic tool call, lifecycle hook, or an explicit
  combination of them
3. Within each guided agent session, inspect emitted artifacts and validation results
4. Within each guided agent session, repair, refine, or retry construction when
   outputs are incomplete, inconsistent, or invalid
5. Within each guided agent session, continue until the procedure's acceptance
   criteria are satisfied or a blocking issue is surfaced explicitly

This loop is part of the architecture, not an implementation accident. Convergence
within each session, and the composition of all sessions, produce a correct
working application.

Local acceptance by a guided agent session is necessary but not sufficient for
global correctness. A session can satisfy its own acceptance criteria while the
composed generated app is still incorrect because of cross-session interface
drift, stale backend-contract/client alignment, or runtime integration failure.
The architecture therefore requires a distinct global acceptance gate after all
guided sessions, deterministic tool procedures, and lifecycle hooks complete.
That gate is owned by terminal verification procedures, not by any individual
Skill, and a run is a correct working application only when the global gate
passes.

### 7.3 Verification categories

Verification in this architecture occurs throughout construction and integration. The main categories are:

- Contract verification: validate the OpenAPI contract and detect breaking changes before downstream construction proceeds.
- Construction-output verification: inspect generated and assembled outputs so they can be corrected, refined, or reused in later iterations.
- Integration verification: verify alignment between backend behavior, generated integration artifacts, and frontend composition.
- Test-based verification: use automated tests and smoke tests to verify expected behavior across backend, frontend, and composed application flows.

Terminal verification applies these categories to the complete generated app.
It consumes recorded construction results from deterministic tools and guided
sessions, then fails the run if local procedure success does not compose into
cross-Skill interface consistency, backend-contract / Angular-client alignment,
and runnable application flows.

### 7.4 Example Build Flow

A representative construction run should follow this architectural flow:

1. Contract-derived and non-CRM inputs are made available to construction.
2. The contract is validated, diffed, and normalized for downstream use.
3. Contract-derived Angular integration artifacts are generated.
4. Non-CRM content definitions are validated and prepared for assembly.
5. Generated and non-generated inputs are assembled into the Angular
  application.
6. Verification categories are applied throughout construction and integration,
  with repair and refinement as needed.
7. Construction emits stage-specific errors or an acceptable output.

The flow should remain explicit, inspectable, and free of hidden handoff
assumptions between construction stages.

---

## 8. Integration Boundaries

### 8.1 Data Architecture

- Database design is outside the scope of this system
- Timestamps in data transport are UTC and localized to the user's timezone in the frontend.

### 8.2 Content Sources

The application has two distinct input sources:

- CRM content source: the OpenAPI contract exported by Django and consumed by
  the generated Angular integration artifacts
- Non-CRM content source: a separate structured definition set for reactive
  forms, standalone pages, and bespoke workflows

Here, CRM content means contract-derived resource content, not a narrow
customer-sales domain assumption.

These two streams must remain separate so contract-derived CRM functionality
does not get mixed with manually-authored UI definitions.

### 8.3 Contract Rules

- API contracts must be versioned, with versioning in the backend's responsibility.
- The frontend must treat the backend as the source of truth for permissions and
  data content.
- Shared enumerations and reference data should come from the API, not be hard
  coded in the client
- CRM-facing Angular content should always be generated or configured from OpenAPI
- Non-CRM content definitions should be version-controlled and validated
  separately from the OpenAPI contract
- The user-facing product UI remains frontend-owned, while backend data
  administration services remain Django + DRF-owned

### 8.4 HTTP Integration

- Use an Angular HTTP interceptor for CSRF, auth-related redirects, and common
  error handling
- Centralize API base URL configuration by environment

### 8.5 Non-CRM Input Source

Use a dedicated structured input source under a path such as `spec/ui/` for
non-CRM content.

This source should define:

- Reactive form metadata that is not directly derivable from OpenAPI
- Standalone page definitions
- Workflow-specific layouts or interaction rules

It should be machine-readable, versioned in the repository, and able to
reference API resources exposed through the OpenAPI contract.

---

## 9. Backend Architecture

### 9.1 `common`

- Shared base models and utilities
- Reusable pagination, filtering, and exception helpers
- Shared API response behavior where needed

### 9.2 `accounts` 

- Management of user accounts, authentication, and authorization

### 9.3 `access`

- Roles, groups, and permission mapping
- Object-level authorization helpers if required

### 9.4 Administrative UI

- Use Django admin or equivalent backend-native admin tooling for internal data
  administration when it improves operational efficiency
- DRF-backed administrative interfaces are also acceptable when they support
  data administration and backend operations
- Keep administrative tooling clearly distinguished from the Angular end-user
  application

## 10. Frontend Architecture

### 10.1 Angular Application Shape

The frontend should be an Angular application with:

- No dependency on Django template rendering or DRF UI facilities for the main
  product experience

### 10.2 Angular Integration Artifacts

The Angular integration artifacts are not the whole frontend application.

Their responsibilities should include:

- OpenAPI-derived typed API clients
- Wrapping or normalizing generated code.
- CRM-oriented resource adapters and data-access helpers
- Shared Angular Material integration patterns for list, detail, and standard
  form experiences.
- Authentication, CSRF, and transport helpers needed for Django integration
- Reusable metadata or generation outputs consumed by the main Angular app

It should not own:

- Product-specific application shell decisions
- Fully bespoke pages that are not OpenAPI-derived
- Business content that belongs to the main frontend application
- Backend data administration concerns that belong to Django and DRF


### 10.3 Frontend Responsibilities

#### 10.3.1 `core`

- Application bootstrap
- Authentication state
- HTTP interceptors
- Shell layout and global navigation
- Route guards and app-wide services

#### 10.3.2 `shared`

- Reusable UI components
- Common form helpers
- Table wrappers, dialogs, and utility code

#### 10.3.3 `features`

- Page components
- Feature routing
- API service wrappers for the module
- Feature-specific models and forms

### 10.4 State Management

- Start with Angular services and RxJS streams
- Keep server state close to the feature that owns it
- Introduce heavier state tooling only if cross-feature complexity demands it

### 10.5 UI Patterns

- Standardize table, list, detail, form, dialog, snackbar, and confirmation patterns

---

## 11. API Architecture

### 11.1 OpenAPI Contract

- Assumption: schema extractor and Angular code generator are aligned to OpenAPI specification and match in API.
- DRF must publish a versioned OpenAPI schema as the contract source of truth
  for CRM-facing functionality.
- The exported schema should be stored as a durable build artifact so downstream
  agent-chain stages can consume it deterministically.
- Change detection must be run as part of the contract normalization stage to detect
  breaking changes between the current and previous schema versions.
- Breaking changes must block downstream generation until
  explicitly acknowledged or resolved.
- Contract changes should be reviewed as part of normal API change management.

### 11.2 Generation Toolchain

- Backend origination follows one of two modes (see §2.22):
  - **Model-first:** an existing Django model is the starting point; the OpenAPI
    contract is exported from DRF via [drf-spectacular].
  - **Contract-first:** no Django model exists yet; the Django data model is
    generated from an existing OpenAPI Schema using [datamodel-code-generator]
    driven by djng-owned custom Django templates (`--custom-template-dir`).
    [datamodel-code-generator]'s native outputs are Pydantic, dataclasses,
    `TypedDict`, and `msgspec` models; Django model emission is a deliberate
    custom-template capability owned and maintained by djng. DRF elaboration
    (serializers, views, authentication, permissions) is layered on the
    generated model, after which the backend proceeds in model-first steady
    state with the OpenAPI contract as the source of truth (§11.1).
- Any datamodel change creating a Django database migration file (after makemigrations) will force an OpenAPI schema extraction via [drf-spectacular].
- Run the schema diff and change detection tool:
  - Run it after exporting the OpenAPI schema from DRF.
  - Run it before any generation step to surface breaking changes early
- Run the Angular generation tool for contract-driven artifacts
- Django backend code should remain authored in DRF; OpenAPI generation on the
  backend side is limited to supporting artifacts, custom templates, or
  project-specific scaffolding
- Generator configuration files must be version-controlled and executable in CI
- Generated output must be deterministic enough to review in pull requests or
  re-create reliably in build pipelines

### 11.3 API Concerns

- Validation belongs in serializers and domain services
- Authorization belongs in the backend, will initially use DRF permission classes plus domain checks
- Filtering should use a standard mechanism across modules
- Errors should be normalized so the Angular client can map them to forms and
  notifications consistently

### 11.4 Versioning

- No API level versioning
- Schema versioning is the contract versioning; the backend updates the schema version and drives the necessary frontend changes.
- Use `oasdiff` to detect API changes and force frontend alignment.

## 12. Authentication and Authorization

### 12.1 Recommended Approach

Use whatever backend specifies to be documented in the contract.

### 12.2 Flow

- User signs in through a DRF-authenticated endpoint
- Django sets secure session cookies
- Angular includes CSRF tokens on unsafe requests
- Angular route guards control navigation within the user-facing route tree
- Route guards and API permissions enforce access at both layers

### 12.3 Permission Model

- Use backend permissions, Django groups and permissions as baseline
- Authentication and authorization are the backend's responsibility; frontend access follows the same roles and rules defined in the backend.
- Enforce critical permissions server-side regardless of frontend state

---



## 13. Observability

### 13.1 Logging

Applied to both `djng` and `ngdj`, and to the applications they help build:
- Use structured application logs
- Include request identifiers where possible
- Distinguish user errors, validation errors, and system failures

### 13.2 Health and Monitoring

- Track integration related exceptions.

## 14. Testing Strategy

Testing is part of the verification model of this architecture. Test results provide feedback during iterative construction and help verify that backend behavior, Angular-side outputs, and the composed application remain aligned with the contract and architectural boundaries.

### 14.1 `djng`

- Unit tests for services, permissions, and model behavior
- API tests for serializers, endpoints, authentication, and contract-producing behavior
- Database-backed tests for critical workflows

### 14.2 `ngdj`

- Unit tests for services and utility logic
- Component tests for forms, tables, route-protected pages, and generated UI behavior
- End-to-end tests for login and the main business module workflows

### 14.3 Integration

- Verify frontend/backend alignment through automated coverage across contract, integration, and composed application behavior
- Include smoke tests in staging before production release
- End-to-end tests covering main use cases across backend, generated integration artifacts, and frontend composition.

## 15. Security Considerations

- Enforce HTTPS outside local development
- Enable CSRF protection for authenticated browser traffic
- Limit admin capabilities to explicit roles

## 16. Environments

The generated project should support at least:

- Django development server with hot reload
- Angular development server with hot reload

Configuration should be environment-driven and must not require code changes to
switch environments.

## 17. Architectural Decisions

- Same-origin deployment is the default production target
- Django session authentication will be the initial first-party auth model.
- Will begin prototyping with sqlite, next will be PostgreSQL
- OpenAPI is the source of truth for CRM-facing contracts.
- Contract validation and `oasdiff`-based change detection are required before downstream construction continues.
- [oasdiff] is the OpenAPI schema diff and change detection tool (source: [oasdiff-github]).
- [ng-openapi-gen] is the Angular client OpenAPI code-generation tool (source: [ng-openapi-gen-github]).
- [datamodel-code-generator] is the contract-first backend generator (source: [datamodel-code-generator-github]; online playground: [datamodel-code-generator-playground]). For the use case where no Django model exists yet, it generates the Django data model from an existing OpenAPI Schema using djng-owned custom Django templates. This is the inverse origination path to the model-first [drf-spectacular] export; see §2.22.
- Verification occurs throughout construction and integration using contract checks, construction-output checks, integration checks, and automated tests.
- Generated Angular integration artifacts are the boundary for reusable
  Angular/Django integration code in the current scaffold
- Non-CRM content is supplied by a separate structured input source
- Modular backend apps and frontend feature areas are the scaling strategy

## 18. Implementation Roadmap

Implementation sequencing is documented in `TODO.md`.

## 19. Glossary

Key actors and terms. Full definitions are in §2.

| Term | Definition | See |
|---|---|---|
| **AI automations** | The full automation model used by `djng`: SKILLS, TOOLS, HOOKS, and PLUGINS working together for bounded construction and integration. | `doc/GENERATE_AI_AUTOMATIONS.md` |
| **`djng`** | The `django-angular3` solution — this repository, the Django package, and the tool. Contains the agent, the AI automation subsystem, `build_app`, and all configuration files. | §2.5 |
| **`ngdj`** | The `angular-django2` companion Angular package. Provides the Angular-side schematics and templates used during construction. | §2.6 |
| **`build_app`** | The `djng` Django management command. Entry point that drives the agent through the procedure graph. | `doc/APP_BUILDER_REQUIREMENTS.md` |
| **the agent** | The agentic orchestrator bundled in `djng`. At implementation level, driven by the Claude Agent SDK. | §2.16 |
| **SKILLS** | Bounded AI skills (`SKILL.md` files) bundled in `djng` that guide the agent within each guided agent session. | §2.14, `doc/GENERATE_AI_AUTOMATIONS.md` |
| **TOOLS** | Deterministic callable capabilities used for bounded operations without requiring AI judgment inside the operation itself. | `doc/GENERATE_AI_AUTOMATIONS.md` |
| **HOOKS** | Deterministic lifecycle-triggered automations that enforce gates, logging, cleanup, and other mandatory side effects. | `doc/GENERATE_AI_AUTOMATIONS.md` |
| **PLUGINS** | Packaging and distribution bundles that group coherent SKILLS, TOOLS, HOOKS, and related agent capabilities for reuse across projects or teams. | `doc/GENERATE_AI_AUTOMATIONS.md` |
| **procedure graph** | The directed acyclic graph of construction procedures derived from the ChangeSet. Nodes may represent guided agent sessions, deterministic tool steps, verification steps, or other governed automation procedures. | `doc/APP_BUILDER_REQUIREMENTS.md` §Procedure Graph |
| **guided agent session** | A single agent session in which the agent carries out one procedure, guided by the specified SKILL(s). | §2.13 |

## 20. References

[Django]: https://www.djangoproject.com/
[Django-github]: https://github.com/django/django
[angular-django2]: https://www.npmjs.com/package/angular-django2
[angular-django2-github]: https://github.com/shlomoa/angular-django2
[django-angular3]: https://pypi.org/project/django-angular3/
[django-angular3-github]: https://github.com/shlomoa/django-angular3
[ng-openapi-gen]: https://www.npmjs.com/package/ng-openapi-gen
[ng-openapi-gen-github]: https://github.com/cyclosproject/ng-openapi-gen
[datamodel-code-generator]: https://pypi.org/project/datamodel-code-generator/
[datamodel-code-generator-github]: https://github.com/koxudaxi/datamodel-code-generator
[datamodel-code-generator-playground]: https://datamodel-code-generator.koxudaxi.dev/playground/
[Claude Agent SDK - Python]: https://platform.claude.com/docs/en/agent-sdk/python
[Claude Agent SDK - Python - GitHub]: https://github.com/anthropics/claude-agent-sdk-python
[Claude Skills]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
[Claude Code Skills]: https://code.claude.com/docs/en/skills
[Claude Agent SDK Skills]: https://code.claude.com/docs/en/agent-sdk/skills
[Claude Skills Best Practices]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
[oasdiff]: https://www.oasdiff.com/
[oasdiff-github]: https://github.com/oasdiff/oasdiff
[DRF - Django REST Framework]: https://www.django-rest-framework.org/
[DRF-github]: https://github.com/encode/django-rest-framework
[Angular]: https://angular.dev/
[Angular Material]: https://material.angular.dev/
[npmjs]: https://www.npmjs.com/
[OpenAPI]: https://www.openapis.org/
[OpenAPI 3.1 Specification]: https://spec.openapis.org/oas/v3.1.0.html
[drf-spectacular]: https://drf-spectacular.readthedocs.io/en/latest/
