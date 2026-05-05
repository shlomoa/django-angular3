# Architecture

## Purpose and scope

This document describes the architecture of `django-angular3` as a contract-driven, agentically orchestrated, SKILLS-based system for generating and integrating Angular application building blocks against a [Django] and [Django REST Framework (DRF)][DRF - Django REST Framework] backend. The backend contract is expressed as a structured [OpenAPI contract (Schema)][OpenAPI 3.1 Specification], which serves as the integration boundary and the source of truth for CRM-facing functionality.

This solution is not an application and not a general development environment. It is an architecture for constructing and evolving generated applications. Construction may be non-deterministic, but acceptance is deterministic: the generated application is considered correct only when it assembles into a working whole and passes the defined validations and tests.

`django-angular3` extends Django/DRF with contract-driven Angular integration. It governs the construction process, uses agentic orchestration to coordinate iterative bounded SKILLS-based construction, and integrates generated building blocks into a working application while preserving architectural boundaries between backend, frontend, generated artifacts, and non-CRM content.

This document covers:
- Architectural principles, architectural actors, system components, and integration workflows.
- The construction, control, and acceptance model used to generate and integrate application building blocks.
- Architectural decisions and directions and the rationale behind them.

This document does not cover:
- Detailed implementation guidance for Django, DRF, or Angular development
- OpenAPI specification and API design.
- General web application development principles or architecture

---

## Terms and Definitions

### [Django]

A high-level Python web framework that encourages rapid development and clean, pragmatic design. It provides an ORM, authentication, admin interface, and a robust ecosystem of packages.

### [Django REST Framework (DRF)][DRF - Django REST Framework]

A powerful and flexible toolkit for building Web APIs in Django. It provides serializers, viewsets, authentication, permissions, and schema generation capabilities.

### [Angular]
A TypeScript-based open-source web application framework led by the Angular Team at Google. It provides a component-based architecture, powerful templating, and a rich ecosystem for building dynamic single-page applications.

### [Angular Material]
A UI component library for Angular that implements Google's Material Design. It provides pre-built components for layout, forms, navigation, and more, with a consistent design language.

### djng
The `django-angular3` package: the Django/Python-side component in this architecture. It is the contract-governing component responsible for backend-side validation, change interpretation, and Angular work derivation.

### ngdj
The `angular-django2` companion package: the Angular-side construction substrate in this architecture. It provides schematics, templates, and workspace/application assembly helpers used to materialize Angular-side outputs derived by `djng`.

### [OpenAPI]
A specification for building APIs that allows both humans and computers to understand the capabilities of a service without access to source code. It serves as a contract between the backend and frontend in this architecture.

### CRM
CRM stands for Customer Relationship Management. In this architecture, it is shorthand for contract-derived business-domain content represented by the backend schema and API. It is not limited to a literal customer-sales system.

### non-CRM content
Content that is not directly derived from the OpenAPI contract, such as bespoke reactive form definitions, standalone page layouts, and workflow-specific UI metadata. This content is defined in a separate structured input source and complements the CRM-derived Angular integration artifacts.

### [OpenAPI contract - Schema][OpenAPI 3.1 Specification]
The versioned OpenAPI schema exported from the DRF layer, serving as the source of truth for CRM-facing functionality and the basis for generating Angular integration artifacts.

### Angular integration artifacts
Generated Angular outputs derived from the OpenAPI contract and related tooling, including typed API clients, resource adapters, transport helpers, reusable Angular Material-oriented integration helpers, and supporting metadata.

### [Claude Code API][Claude Code Python SDK]
An API that allows developers to interact with the Claude AI assistant for coding tasks. It can be used to automate code generation, refactoring, and other programming-related activities as part of the integration workflow between Django/DRF and Angular Material.

### agentic orchestration
An orchestration model in which an AI agent drives construction and integration work using bounded architectural capabilities rather than a fixed linear pipeline. The orchestrator consumes change requirements, configuration files, and contract-derived inputs, applies SKILLS as needed, and iterates toward a correct working application.

### [SKILLS][Claude Skills]
Bounded construction units used by the agentic orchestrator in this architecture. Each SKILL encapsulates a constrained generation, modification, or integration capability used to create and glue application building blocks while remaining within architectural and contract-defined boundaries.

SKILLS are a core architectural subsystem of `django-angular3`. Their subsystem architecture is defined in `doc/GENERATE_SKILLS.md`, and their implementation and authoring plan is defined in `doc/SKILL_AUTHORING_PLAN.md`. This document defines the role of SKILLS in the overall architecture and does not restate their internal design.

### SKILLS-based construction
A construction model in which bounded SKILLS are the primary execution units for generating, modifying, and integrating application building blocks. This model allows controlled generative freedom while keeping construction within architectural, contract-defined, and validation-defined boundaries.

### angular-code-agent
The orchestrator in this architecture. It consumes change requirements, configuration files, and contract-derived inputs, applies SKILLS-based construction to generate and integrate the required building blocks, and drives the system toward a correct working application.

### correct working application
An application that assembles into a runnable whole and satisfies the deterministic validations and tests defined by this architecture. Individual generated artifacts alone do not establish correctness.

### correct-by-construction
An architectural goal in which bounded construction, architectural constraints, contract-defined rules, and deterministic validation gates drive generation toward a correct working application, even when the internal construction path is not deterministic.

### non-deterministic generation
Generation in which the internal construction path, intermediate decisions, or exact emitted outputs may vary across valid runs. This variation is allowed as long as the resulting application still satisfies the architecture's deterministic acceptance criteria.

### deterministic acceptance
An acceptance model in which correctness is decided by explicit validations and tests. Regardless of how generation proceeds internally, acceptance criteria remain stable and repeatable.

### Django Project vs Django App

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

---

## Toolchain Design

### Inputs

|Input|Description|
|:-|:-|
|DRF model|A Django model with DRF elaboration including endpoints, at least: serializers, views, authentication, and permissions|
|Project configuration|A json file describing the project, apps, UI parts, and other configuration details|
|Non-CRM Angular content|Bespoke reactive form definitions, standalone page layouts, and workflow-specific UI metadata defined in a separate structured input source|

### Generated artifacts

|Artifact|Description|
|:-|:-|
|`OpenAPI contract`|A versioned OpenAPI schema exported from the DRF layer, serving as the source of truth for CRM-facing functionality|
|Angular integration artifacts|Generated Angular code including typed API clients, resource adapters, and reusable Angular Material-oriented integration helpers derived from the OpenAPI contract|


### djng

[django-angular3] The package is the Django/Python-side governance and work-derivation component for contract-driven Angular Material frontend implementation against a `DRF` backend.

- Purpose: The backend owner.
  - Govern the overall integration process
  - Manage the backend contract, and derive Angular-side work.
    - Manage Python/Django/DRF side of integration.
    - Define the work that must be carried out by the orchestrator and construction subsystems.
- Responsibilities:
  - djng-o-1: Provide a set of complementing django-admin commands:
    - For creating, building, and modifying Angular UI.
    - Manage OpenAPI contract lifecycle, including: contract extraction from DRF, validation, versioning
  - djng-o-2: Define, author, and evolve the Claude SKILLS required for building, generating, and integrating Angular building blocks.
  - djng-o-3: Manage and drive Angular app change requirements through:
    - Detection of change requirements.
    - Converting change requirements into `prompts`
  - djng-o-4: Provide the orchestration entry points and work definitions consumed by `angular-code-agent`:
    - The orchestrator applies [SKILLS][Claude Skills] to generate Angular building blocks.
    - The orchestrator integrates those building blocks into an [Angular Material] frontend app using the DRF `contract`.

- `djng` defines and governs the work to be performed; `angular-code-agent` orchestrates iterative SKILLS-based construction to carry that work out.

### ngdj

implemented in [angular-django2-github] and deployed to [angular-django2] npm package.

- Purpose: A companion [Angular] ([npmjs] package) that provides the Angular-side construction substrate used to materialize required outputs.
- Responsibilities:
  - ngdj-o-1: Provide a set of commands for managing and assembling the Angular application, including workspace, project layout, application layout.
  - ngdj-o-2: Provide Angular schematics and code generation templates for generating Angular building blocks from OpenAPI contracts.
  - ngdj-o-3: Provide a set of Angular schematics and code generation templates for generating Angular building blocks from non-CRM content definitions.


### Toolchain components

- A contract-governing, work-deriving component - in `djng`.
- An agentic orchestrator that executes derived work through bounded capabilities - `angular-code-agent`.
- A SKILLS subsystem that provides bounded construction and integration capabilities used by the orchestrator.
- An Angular-side construction substrate and application generator - in `ngdj`.
- An OpenAPI schema extraction process - in `djng`.
- An OpenAPI TypeScript generation process - in `ngdj`.
- A structured UI definition management system - in `djng`.
- Requirements for `SKILLS` and `ngdj` are derived from `djng`.

---

## Separation of Responsibilities

Applicable to the application built with the help of this system

### Backend responsibilities

Django and DRF are responsible for:

- Data models and persistence
- Business logic and workflow enforcement on the server
- Authentication, authorization, and audit enforcement
- Data administration and operational admin tooling
- Backend packaging, API delivery, and server-side deployment artifacts

### Frontend responsibilities

Angular Material is responsible for:

- The user-facing application shell
- End-user pages, workflows, forms, dialogs, and tables
- End-user application routing
- Presentation logic and client-side interaction behavior
- Consuming backend APIs for the user-facing application experience

### Ownership boundary

- Django templates, Django admin, and DRF-backed interfaces may be used for data
  administration services and operator workflows
- Django serves API, authentication, and administration endpoints
- Angular owns the user-facing route tree and navigation behavior
- Angular Material remains the primary UI system for the user-facing
  application
- Angular Material is the default and preferred UI system for all user-facing
  functionality
  
---

## Deployment Model

Applicable to the application built with the help of this system

### Recommended Production Model

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

### Local Development Model

- Django runs as the backend development server
- Angular runs its local development server
- The Angular dev server proxies API traffic to Django
- The Angular dev server owns user-facing route handling during development
- Frontend routes and backend routes remain distinct

---

## Architectural Principles

- Prefer proven framework conventions over custom infrastructure
- Keep frontend and backend decoupled at the API boundary, but integrated in
  deployment
- Optimize for maintainability and incremental delivery
- Make security, testing, and observability part of the default design
- Keep the first version simple; add complexity only when a real feature
  requires it

---

## Integration Workflow

The integration process should be modeled as an agentic control loop with explicit handoff artifacts. `djng` governs contract lifecycle, validation, and work derivation; `angular-code-agent` orchestrates iterative SKILLS-based construction and integration toward an acceptable application state.

The workflow is not a one-pass pipeline. The stages below describe the architectural work domains and durable artifacts involved in construction, but the orchestrator may revisit them as needed while driving the application toward deterministic acceptance.

### Control-loop stages

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

### Repair and refinement loop

The orchestrator may invoke and re-invoke SKILLS as needed while construction is in progress. A typical control cycle is:

1. derive required work from contract changes, configuration, and structured inputs
2. invoke the relevant SKILLS to generate, modify, or integrate building blocks
3. inspect emitted artifacts and validation results
4. repair, refine, or retry construction when outputs are incomplete, inconsistent, or invalid
5. continue iterating until deterministic acceptance criteria are satisfied or a blocking issue is surfaced explicitly

This loop is part of the architecture, not an implementation accident. Generation may vary internally, but correction and convergence toward a correct working application are expected architectural behavior.

### Verification categories

Verification in this architecture occurs throughout construction and integration. The main categories are:

- Contract verification: validate the OpenAPI contract and detect breaking changes before downstream construction proceeds.
- Construction-output verification: inspect generated and assembled outputs so they can be corrected, refined, or reused in later iterations.
- Integration verification: verify alignment between backend behavior, generated integration artifacts, and frontend composition.
- Test-based verification: use automated tests and smoke tests to verify expected behavior across backend, frontend, and composed application flows.

### Example Build Flow

The first-time use case should follow this concrete repository-oriented flow:

1. The user authors the API contract in Swagger Studio
   (SmartBear's API design tooling, historically associated with SwaggerHub)
2. The user exports the OAS document into `spec/openapi/source/`
3. The user adds non-CRM content definitions into `spec/ui/`
4. The user runs the build
5. The build validates the OAS document
6. The build runs the configured OpenAPI generation steps
7. The build validates the non-CRM UI definitions
8. The build assembles the Angular application using both generated CRM
   artifacts and non-CRM inputs
9. The build emits clear stage-specific errors or a successful production-ready
   output

The build pipeline should be designed so a first-time contributor can follow
this flow without manual hidden steps between export, repository update, and
build execution.

---

## Integration Boundaries

### Data Architecture

- Database design is outside the scope of this system
- Timestamps in data transport are UTC and localized to the user's timezone in the frontend.

### Content Sources

The application has two distinct input sources:

- CRM content source: the OpenAPI contract exported by Django and consumed by
  the generated Angular integration artifacts
- Non-CRM content source: a separate structured definition set for reactive
  forms, standalone pages, and bespoke workflows

Here, CRM content means contract-derived resource content, not a narrow
customer-sales domain assumption.

These two streams should remain separate so contract-derived CRM functionality
does not get mixed with manually-authored UI definitions.

### Contract Rules

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

### HTTP Integration

- Use an Angular HTTP interceptor for CSRF, auth-related redirects, and common
  error handling
- Centralize API base URL configuration by environment

### Non-CRM Input Source

Use a dedicated structured input source under a path such as `spec/ui/` for
non-CRM content.

This source should define:

- Reactive form metadata that is not directly derivable from OpenAPI
- Standalone page definitions
- Workflow-specific layouts or interaction rules

It should be machine-readable, versioned in the repository, and able to
reference API resources exposed through the OpenAPI contract.

---

## Backend Architecture

### `common`

- Shared base models and utilities
- Reusable pagination, filtering, and exception helpers
- Shared API response behavior where needed

### `accounts` 

- Management of user accounts, authentication, and authorization

### `access`

- Roles, groups, and permission mapping
- Object-level authorization helpers if required

### Administrative UI

- Use Django admin or equivalent backend-native admin tooling for internal data
  administration when it improves operational efficiency
- DRF-backed administrative interfaces are also acceptable when they support
  data administration and backend operations
- Keep administrative tooling clearly distinguished from the Angular end-user
  application

## Frontend Architecture

### Angular Application Shape

The frontend should be an Angular application with:

- No dependency on Django template rendering or DRF UI facilities for the main
  product experience

### Angular Integration Artifacts

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


### Frontend Responsibilities

#### `core`

- Application bootstrap
- Authentication state
- HTTP interceptors
- Shell layout and global navigation
- Route guards and app-wide services

#### `shared`

- Reusable UI components
- Common form helpers
- Table wrappers, dialogs, and utility code

#### `features`

- Page components
- Feature routing
- API service wrappers for the module
- Feature-specific models and forms

### State Management

- Start with Angular services and RxJS streams
- Keep server state close to the feature that owns it
- Introduce heavier state tooling only if cross-feature complexity demands it

### UI Patterns

- Standardize table, list, detail, form, dialog, snackbar, and confirmation patterns

---

## API Architecture

### OpenAPI Contract

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

### Generation Toolchain

- Any datamodel change creating a Django database migration file (after makemigrations) will force an OpenAPI schema extraction.
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

### API Concerns

- Validation belongs in serializers and domain services
- Authorization belongs in the backend, will initially use DRF permission classes plus domain checks
- Filtering should use a standard mechanism across modules
- Errors should be normalized so the Angular client can map them to forms and
  notifications consistently

### Versioning

- No API level versioning
- Schema versioning is the contract versioning; the backend updates the schema version and drives the necessary frontend changes.
- Use `oasdiff` to detect API changes and force frontend alignment.

## Authentication and Authorization

### Recommended Approach

Use whatever backend specifies to be documented in the contract.

### Flow

- User signs in through a DRF-authenticated endpoint
- Django sets secure session cookies
- Angular includes CSRF tokens on unsafe requests
- Angular route guards control navigation within the user-facing route tree
- Route guards and API permissions enforce access at both layers

### Permission Model

- Use backend permissions, Django groups and permissions as baseline
- Authentication and authorization are the backend's responsibility; frontend access follows the same roles and rules defined in the backend.
- Enforce critical permissions server-side regardless of frontend state

---



## Observability

### Logging

Applied to both `djng` and `ngdj`, and to the applications they help build:
- Use structured application logs
- Include request identifiers where possible
- Distinguish user errors, validation errors, and system failures

### Health and Monitoring

- Track integration related exceptions.

## Testing Strategy

Testing is part of the verification model of this architecture. Test results provide feedback during iterative construction and help verify that backend behavior, Angular-side outputs, and the composed application remain aligned with the contract and architectural boundaries.

### `djng`

- Unit tests for services, permissions, and model behavior
- API tests for serializers, endpoints, authentication, and contract-producing behavior
- Database-backed tests for critical workflows

### `ngdj`

- Unit tests for services and utility logic
- Component tests for forms, tables, route-protected pages, and generated UI behavior
- End-to-end tests for login and the main business module workflows

### Integration

- Verify frontend/backend alignment through automated coverage across contract, integration, and composed application behavior
- Include smoke tests in staging before production release
- End-to-end tests covering main use cases across backend, generated integration artifacts, and frontend composition.

## Security Considerations

- Enforce HTTPS outside local development
- Enable CSRF protection for authenticated browser traffic
- Limit admin capabilities to explicit roles

## Environments

The generated project should support at least:

- Django development server with hot reload
- Angular development server with hot reload

Configuration should be environment-driven and must not require code changes to
switch environments.

## Implementation Notes

- The preferred generation path is `ng-openapi-gen`
- OpenAPI schema extraction is done with [drf-spectacular].
- Schema diff and change detection is done with [oasdiff].
  
## Architectural Decisions

- Same-origin deployment is the default production target
- Django session authentication will be the initial first-party auth model.
- Will begin prototyping with sqlite, next will be PostgreSQL
- OpenAPI is the source of truth for CRM-facing contracts.
- Contract validation and `oasdiff`-based change detection are required before downstream construction continues.
- `oasdiff` is the OpenAPI schema diff and change detection tool.
- `ng-openapi-gen` is the Angular client OpenAPI code-generation tool.
- Verification occurs throughout construction and integration using contract checks, construction-output checks, integration checks, and automated tests.
- Generated Angular integration artifacts are the boundary for reusable
  Angular/Django integration code in the current scaffold
- Non-CRM content is supplied by a separate structured input source
- Modular backend apps and frontend feature areas are the scaling strategy

## Implementation Roadmap

Implementation sequencing is documented in `doc/IMPLEMENTATION_PLAN.md`.

## References

[Django]: https://www.djangoproject.com/
[Django-github]: https://github.com/django/django
[angular-django2]: https://www.npmjs.com/package/angular-django2
[angular-django2-github]: https://github.com/shlomoa/angular-django2
[django-angular3]: https://pypi.org/project/django-angular3/
[django-angular3-github]: https://github.com/shlomoa/django-angular3
[ng-openapi-gen]: https://www.npmjs.com/package/ng-openapi-gen
[ng-openapi-gen-github]: https://github.com/cyclosproject/ng-openapi-gen
[Claude Code Python SDK]: https://platform.claude.com/docs/en/api/sdks/python
[Claude Skills]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration
[oasdiff]: https://www.oasdiff.com/
[oasdiff-github]: https://github.com/oasdiff/oasdiff
[DRF - Django REST Framework]: https://www.django-rest-framework.org/
[DRF-github]: https://github.com/encode/django-rest-framework
[Angular]: https://angular.io/
[Angular Material]: https://material.angular.io/
[npmjs]: https://www.npmjs.com/
[OpenAPI]: https://www.openapis.org/
[OpenAPI 3.1 Specification]: https://spec.openapis.org/oas/v3.1.0.html
[drf-spectacular]: https://drf-spectacular.readthedocs.io/en/latest/
