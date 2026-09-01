# Requirements

## 1. Introduction

### 1.1. Purpose of the Document

This document defines the baseline requirements for the full-stack application
platform and the governed construction model that the integration targets.

The terms `djng` and `ngdj` use the definitions in [ARCHITECTURE.md]
§§ 2.5-2.6.

This document defines `djng` integration requirements; it does not define
`ngdj` commands, options, or behavior. All such facts use the upstream-source
policy in `ARCHITECTURE.md` §2.6.

The terms `AI automations`, `SKILLS`, `TOOLS`, `HOOKS`, `PLUGINS`, and
`AI-automation-based construction` use the definitions in
`ARCHITECTURE.md` §§ 2.13-2.14, §3.6, and §19 (see [Claude Skills]).

The term `the agent` uses the definition in `ARCHITECTURE.md` §2.15.

Related architectural context: see `ARCHITECTURE.md` §§ 1, 3, and 7.

### 1.2. Business Problem Being Solved

Organizations need a repeatable way to connect [Django], [DRF - Django REST Framework]
(DRF), and [Angular Material] into a single full-stack application without
manual glue work between backend contracts, frontend generation, and
user-facing UI assembly.

They also need a governed way to derive and evolve full-stack outputs from
separate OpenAPI contract and OpenUI description inputs, rather than
coordinating those changes manually across tools and layers.

Because the business domain is not yet specified, the platform must provide a
maintainable, reusable, and modular foundation for business applications so
teams can deliver new business modules rapidly without reworking the core
architecture.

### 1.3. System Scope and Boundaries

These requirements are derived from and must remain aligned with
`ARCHITECTURE.md`.

This document defines requirements only. It does not define architecture,
specifications, contracts, authoring processes, implementation plans, or test
examples. [ARCHITECTURE.md] owns architecture and design rationale,
[SPECIFICATIONS.md] owns exact platform structures, and [CONTRACTS.md] owns
shared normative interface boundaries. [AI_AUTOMATION_CONTRACTS.md] owns AI
automation contracts, [AI_AUTOMATION_REQUIREMENTS.md] owns AI automation
product and quality requirements, and [SKILL_AUTHORING_PLAN.md] owns the
per-Skill authoring and verification cadence.

[APP_BUILDER_REQUIREMENTS.md] owns detailed `build_app` requirements and
command translation. [TEST_EXAMPLES.md] owns scenario-by-scenario examples.

**Out of initial release scope:**

- Native mobile applications
- Public multi-tenant marketplace behavior
- Complex workflow engine features unless demanded by the first business module
- Real-time collaboration
- Advanced analytics or BI dashboards beyond operational summaries

### 1.4. Assumptions

- The application is first-party software owned by one organization
- Users access the product through a web browser
- The first release is focused on internal or partner-facing workflows rather
  than anonymous public traffic
- At least one business module will be implemented in the MVP, but the platform
  must support more modules later

## 2. Business/System Overview

### 2.1. System context and vision

`django-angular3` enables seamless integration of Django, Django REST
Framework (DRF), and Angular Material.

The system context is a production-ready full-stack business application in
which Django is the primary backend framework, DRF is the API layer, [Angular]
is the single-page application frontend, Angular Material is the design system
and component library, and OpenAPI is the contract source of truth for
API-contract-derived functionality.

Within that context, `djng` governs the backend contract lifecycle and derives
Angular-side work from contract and configuration inputs, while `ngdj`
provides the Angular-side construction capabilities needed for workspace and
application assembly and for generation from explicit construction inputs.

These requirements therefore address the generated application platform
together with the governance and construction surfaces needed to support tight
frontend/backend integration for local development and production.

### 2.2. Business goals and expected value

The platform must support secure, role-based workflows for multiple user
types, provide a clean and accessible user experience for desktop-first
business work, and remain observable, testable, and ready for staged
deployment.

It must also support maintainable and rapid delivery of business modules
through shared patterns, generated integration artifacts, and one complete
end-to-end module implementation in the first scope of delivery.

The expected value is reduced manual integration effort between backend and
frontend work, faster iteration when adding or changing modules, safer change
handling through reusable patterns and governed generation, and stronger
deployment readiness through baseline automated tests, health checks, and
clear local-development and staging paths.

### 2.3. Major subsystems and external dependencies

The major subsystems in scope are the generated application platform, the
`djng` governance and construction surface, and the `ngdj` Angular-side
construction substrate consumed by governed construction.

The generated application depends on a durable, versioned OpenAPI schema as
its API-contract input and on a separate OpenUI concrete UI document as its
UI-description input. Their roles are distinct, but they may describe
complementary aspects of the same feature.

`djng` provides the Django/Python-side governance of the backend contract
lifecycle and derives Angular-side work from contract and configuration
inputs, while `ngdj` provides workspace assembly, application assembly, and
generation capabilities invoked with explicit inputs selected by `djng` from
OpenAPI- and OpenUI-derived changes.

External dependencies and services include:

- Swagger Studio / SwaggerHub-style authoring flow for designing or updating
  the OpenAPI specification before export
- versioned OpenAPI schema artifacts (see [OpenAPI 3.1 Specification]) selected
  by the project configuration's `artifacts.openapiSchema` path. OAS 3.1 is
  the pinned version; the toolchain ([drf-spectacular], [oasdiff],
  [ng-openapi-gen]) does not yet support OAS 3.2.
- project-owned OpenUI concrete UI documents selected through
  `artifacts.openuiSpecification`
- [oasdiff] for OpenAPI schema diffing and change detection
- [ng-openapi-gen] (source: [ng-openapi-gen-github]) where Angular-native client generation is required
- [datamodel-code-generator] (source: [datamodel-code-generator-github]; online playground: [datamodel-code-generator-playground]) for the contract-first use case: generating the Django data model from an existing OpenAPI Schema, using djng-owned custom Django templates, when no Django model exists yet (see [ARCHITECTURE.md] §§ 2.21 and 11.2)
- a web browser as the primary client environment
- an email delivery service when account or workflow notifications are enabled

### 2.4. High-level capabilities

At a high level, the platform must provide:

- authentication, authorization, and user-administration capabilities for
  secure role-based access
- a consistent application shell, navigation model, and responsive user-facing
  experience
- modular business features with reusable list, detail, create, update, and
  deactivate or delete patterns
- search, auditability, notifications, file handling, and administrative
  support capabilities needed for business operations
- contract-driven integration between backend and frontend through durable
  OpenAPI artifacts, generated Angular integration artifacts, and governed
  change handling
- support for UI-description-driven pages, reactive forms, navigation, and
  workflows through an OpenUI concrete UI document
- baseline health, error-handling, observability, automated-testing, and
  deployment-readiness capabilities suitable for local development and staged
  delivery

## 3. Use Cases / User Journeys

### 3.1. Roles and Actors

#### 3.1.1. End-User Roles, Administrative and Operational Roles, permissions, and responsibilities

The platform must distinguish end-user, administrative, and operational roles
and apply role-based permissions consistently across UI navigation, API
endpoints, and administrative functions.

- Anonymous user: may access the login screen and other explicitly public
  pages only.
- Authenticated user: may use permitted business features and must be able to
  view and update personal profile details.
- Manager or supervisor: may review broader data sets and approve sensitive
  actions when required by the business domain.
- Administrator: may create, activate, deactivate, and update users; assign
  roles or permission groups; manage core configuration and centrally managed
  reference data; and perform administrative actions subject to audit.
- Support or operations user: may inspect logs, audit history, and system
  state within approved permissions.

Permission and responsibility expectations:

- access must be restricted to authenticated users unless a route is
  explicitly public
- role-based access control must be enforced on both API endpoints and UI
  navigation
- sensitive actions must be restricted by role and, where needed, object-level
  ownership or scope
- administrative changes must be auditable

#### 3.1.2. External systems and services

The platform interacts with external systems and services that provide
contract inputs, generation support, delivery support, and client access.

- OpenAPI authoring and export system: users may design or update the API
  contract in Swagger Studio / SwaggerHub-style tooling before exporting the
  schema artifact to the path selected by `artifacts.openapiSchema` in the
  project configuration.
- OpenAPI schema artifacts: durable, versioned schema files are external input
  artifacts consumed by downstream validation and generation flows.
- Schema diff tool: `oasdiff` must participate in contract change detection
  between schema versions.
- Angular code generation tool: `ng-openapi-gen` may be used when Angular-
  native client generation is required for contract-derived artifacts.
- Email service: external email delivery may be used for account and workflow
  notifications when notification features are enabled.
- Web browser client: users access the generated application primarily through
  a browser-based client environment.
- External identity provider: if single sign-on is added later, an external
  authentication provider may participate as a federated identity service.

#### 3.1.3. Actor goals and expectations

Each actor must be able to achieve the outcomes associated with that role and
must be able to judge success through secure access, predictable navigation,
effective task completion, and traceable system behavior.

- Anonymous user: expects access to the login screen and any explicitly public
  pages, with a clear boundary between public and protected functionality.
- Authenticated user: expects to sign in securely, recover account access when
  needed, navigate the application easily, search and filter records, and
  complete routine business tasks through responsive list, detail, and form
  workflows.
- Manager or supervisor: expects broader visibility into relevant records and
  the ability to review or approve sensitive actions when required by the
  business domain.
- Administrator: expects to manage users, roles, permission group assignment,
  and reference data efficiently while relying on audited administrative
  actions and clear account status information.
- Support or operations user: expects to inspect logs, authentication events,
  audit history, and system state so issues can be diagnosed and operational
  activity can be traced.

From the actor perspective, success means the system provides secure identity
handling, permission-appropriate navigation and access, reusable business
module workflows, deterministic search behavior, and auditable business and
security events.

#### 3.1.4. Trust and security boundaries

The platform must make trust and security boundaries explicit for all actors
and must enforce those boundaries through authenticated access, role-based
permissions, and server-side authorization controls.

- Anonymous users may access only explicitly public pages and must not gain
  access to protected routes, APIs, or administrative functions.
- Authenticated users may access only the routes, records, and actions allowed
  by their role and, where required, by object-level ownership or scope.
- Administrative and operational users may perform elevated actions only
  within approved permissions and with audit visibility for those actions.
- API endpoints must require authenticated access unless explicitly public and
  must enforce validation, authorization, and standard HTTP semantics on the
  server side.
- The Angular frontend may guide navigation and presentation behavior, but it
  must not be the final trust boundary for security decisions; backend
  enforcement in Django and DRF remains authoritative.
- The frontend/backend separation must preserve Angular as the user-facing
  route and interaction layer while Django and DRF remain responsible for
  backend business logic, service endpoints, authentication services,
  authorization enforcement, and administrative capabilities.
- Secure defaults must be maintained for cookies, CSRF, headers, transport,
  and secret handling, and sensitive tokens must not be stored in browser
  local storage.

### 3.2. Primary user workflows

The platform must support the following primary user workflows:

- **Sign in / sign out**: a user authenticates securely, accesses permitted
  application areas, and ends the session explicitly when work is complete.
- **Manage own profile**: an authenticated user views and updates personal
  profile details and maintains current account information.
- **Administer users and permissions**: an administrator creates, activates,
  deactivates, and updates users, assigns roles or permission groups, and
  manages related access configuration.
- **Browse, search, and filter business records**: an authorized user opens
  list views, applies filtering and sorting, pages through results, and finds
  relevant records for review or action.
- **Create, update, and deactivate a business record**: an authorized user
  completes list-detail-form workflows to create, edit, validate, and where
  appropriate deactivate or delete business records.
- **Manage administrative and reference data**: an authorized administrator
  maintains core configuration and centrally managed reference data used across
  business modules.
- **Run the first-time build from OpenAPI and UI inputs**: a user exports the
  OpenAPI artifact to the project configuration's `artifacts.openapiSchema`
  path, provides the OpenUI concrete UI document selected by
  `artifacts.openuiSpecification`, triggers the build, and receives
  stage-specific feedback from validation, generation, and final assembly.

### 3.3. Preconditions and postconditions

Unless a route is explicitly public, the primary workflows assume a browser-
based client, authenticated access, role-appropriate permissions, and API
endpoints that enforce validation and authorization on the server side.

- **Sign in / sign out**
  - Preconditions: the login route is publicly reachable; the user accesses
    the application through a supported web browser; protected routes and APIs
    require authentication.
  - Postconditions: a successful sign-in establishes access only to permitted
    routes and API operations; sign-out ends that protected access.

- **Manage own profile**
  - Preconditions: the user is authenticated and permitted to access profile
    functionality.
  - Postconditions: profile changes are accepted through validated API
    requests, or predictable validation errors are returned.

- **Administer users and permissions**
  - Preconditions: the actor holds administrative permissions for user and
    access management.
  - Postconditions: user, role, and permission changes are applied only
    through authorized operations and remain within the defined access model.

- **Browse, search, and filter business records**
  - Preconditions: the actor is authorized to access the relevant records; the
    API supports authenticated access plus filtering, sorting, and pagination.
  - Postconditions: the user receives deterministic result sets and predictable
    API responses for the selected filters and sort order.

- **Create, update, and deactivate a business record**
  - Preconditions: the actor has permission to perform the requested action;
    the target API endpoint validates authenticated access and request data.
  - Postconditions: the record change is accepted through standard HTTP and
    validation behavior, or a predictable validation error is returned.

- **Manage administrative and reference data**
  - Preconditions: the actor is authorized for administrative configuration or
    reference-data maintenance.
  - Postconditions: approved configuration or reference-data changes are
    committed through validated administrative operations.

- **Run the first-time build from OpenAPI and UI inputs**
  - Preconditions: a versioned OpenAPI schema artifact is available at the
    project configuration's `artifacts.openapiSchema` path; an OpenUI input is
    available at the project configuration's `artifacts.openuiSpecification`
    path; the OpenAPI contract is valid and generation-compatible; and the
    OpenUI input is valid.
  - Postconditions: the build either produces generated API-contract-derived artifacts,
    assembled application outputs, and stage results for valid inputs, or it
    fails fast with stage-specific feedback identifying contract validation,
    code generation, OpenUI input validation, or final app assembly.

### 3.4. Normal interaction sequences

The platform must support normal interaction sequences that are predictable,
role-appropriate, and validated through backend-enforced operations.

- **Sign in / sign out**
  1. The user opens the login page.
  2. The user submits credentials.
  3. The backend authenticates the request and establishes the permitted
    session.
  4. The frontend exposes only the routes and navigation items allowed for the
    authenticated role.
  5. The user signs out and protected access ends.

- **Administer users and permissions**
  1. An administrator opens the user-management area.
  2. The administrator creates, updates, activates, or deactivates a user.
  3. The administrator assigns or changes roles and permission groups.
  4. The backend validates and persists the authorized change.
  5. The updated access model becomes effective for subsequent interactions.

- **Browse, search, and filter business records**
  1. An authorized user opens a list view for a business module.
  2. The user applies search text, filters, sort order, or pagination.
  3. The frontend issues the corresponding API request.
  4. The backend returns the permitted, filtered, and ordered result set.
  5. The user reviews the returned records and selects one for further action
    where needed.

- **Create, update, and deactivate a business record**
  1. An authorized user opens a create, detail, or edit view.
  2. The user enters or modifies record data in the form workflow.
  3. The frontend submits the validated request to the backend.
  4. The backend validates, accepts, and stores the change, or returns
    validation errors.
  5. The user is returned to the updated detail or list context with the new
    record state reflected.

- **Run the first-time build from OpenAPI and UI inputs**
  1. A user designs or updates the OpenAPI specification in the authoring
    tool.
  2. The user exports the schema artifact to the path selected by
    `artifacts.openapiSchema` in the project configuration.
  3. The user provides the OpenUI concrete UI document at the path selected by
     `artifacts.openuiSpecification`.
  4. The user triggers the build from the repository.
  5. The build validates the contract and OpenUI input, generates API-contract-derived
    artifacts, assembles the Angular application, and reports the stage
    outcome.

### 3.5. Alternative and failure flows

The platform must make alternative and failure flows explicit so users and
operators can identify what failed, why it failed, and whether the issue is
recoverable.

- **Invalid login or denied access**: when authentication fails or a user
  attempts an unauthorized route or action, access must be denied cleanly and
  protected functionality must remain unavailable.
- **Validation failure**: invalid form submissions or invalid API requests must
  return predictable validation errors that can be surfaced at field and form
  level.
- **Contract invalid**: if the OpenAPI contract is invalid or incompatible
  with generation, the build must fail fast before downstream construction
  continues.
- **OpenUI input invalid**: if the OpenUI input selected by
  `artifacts.openuiSpecification` is invalid, the build must fail fast and
  identify the OpenUI input stage as the point of failure.
- **Build failure**: when generation or assembly fails, the flow must surface
  which stage failed — contract validation, code generation, OpenUI input
  validation, or final app assembly — rather than reporting a generic error.
- **Recoverable UI or server failure**: recoverable UI errors must not cause
  users to lose unsaved form state, and unexpected server errors must be
  logged while surfacing user-safe messages.
- **Development-time generation failure**: when app generation fails during
  development with `DEBUG=True`, the failure must surface through Django's
  standard error reporting path rather than being swallowed silently or shown
  only in console output.

### 3.6. State transitions and synchronization points

The platform must define the state transitions and synchronization points that
keep authentication state, business-record state, contract-derived outputs,
and assembled application outputs aligned.

- **Anonymous → authenticated → signed out**: a successful sign-in must move a
  user from anonymous access to an authenticated session with role-appropriate
  permissions, and sign-out or session expiry must return that user to a
  non-authenticated state.
- **Business-record lifecycle states**: where a module uses draft, active, and
  deactivated record states, transitions between those states must occur only
  through authorized and validated operations, and the visible UI state must
  match the persisted backend state.
- **Authentication and audit synchronization**: login, logout, failed-login,
  password-reset, and sensitive administrative actions must produce auditable
  events that remain consistent with the effective user and record state.
- **Contract change detected → generation continued**: when the OpenAPI schema
  changes, `oasdiff` must identify the change before downstream construction
  uses the current contract.
- **Generated artifacts → assembled app → verified app**: for valid inputs,
  construction must move from validated OpenAPI and OpenUI sources to
  generated API-contract-derived artifacts, then to an assembled application, and then
  to verified outputs that satisfy the required acceptance checks.
- **Backend, frontend, and generated-output synchronization points**: the
  backend contract, generated Angular integration artifacts, and frontend
  composition must remain synchronized after authentication changes, schema
  changes, business-record changes, and each build or verification cycle so
  the application behavior stays aligned with the current contract and
  permissions model.

## 4. Requirements Corpus

The files in this folder form one requirements corpus. Each requirement has one
owner:

- [REQUIREMENTS.md] owns product context, actors, user journeys, and system
  acceptance.
- [APPLICATION_FUNCTIONAL_REQUIREMENTS.md] owns generated-application
  capabilities and governed input and verification requirements.
- [APPLICATION_QUALITY_REQUIREMENTS.md] owns generated-application quality
  attributes and deployment requirements.
- [APP_BUILDER_REQUIREMENTS.md] owns detailed `build_app` behavior.
- [AI_AUTOMATION_REQUIREMENTS.md] owns AI automation subsystem outcomes and
  quality requirements.

The corpus does not redefine architecture, specifications, contracts,
implementation plans, or test examples. Those concerns remain with their
linked source documents.

[SPECIFICATIONS.md] owns generated-platform realization, and
[AI_AUTOMATION_SPECIFICATIONS.md] owns AI automation realization.

## 6. Acceptance Criteria

### 6.1. System Acceptance Requirements

See `ARCHITECTURE.md` §§ 7.3, 14, and 17 for the related verification,
testing, and architectural decision model.

The generated platform is acceptable when:

- The OpenAPI contract and OpenUI input pass the required validation
  gates for downstream construction
- Generated and assembled outputs are sufficient to produce a runnable,
  integrated application rather than only isolated artifacts
- Backend behavior, generated Angular integration artifacts, and frontend
  composition remain aligned with the governing contract and ownership
  boundaries
- Required verification categories have passed, including contract
  verification, construction-output verification, integration verification,
  and test-based verification
- The assembled application satisfies the MVP scope expected for the current
  implementation stage, including one complete business module and the shared
  platform services it depends on
- Blocking failures are surfaced explicitly through the construction and
  verification flow rather than being hidden or silently ignored

## Appendix

### A. Terminology

Authoritative terminology is defined in [ARCHITECTURE.md] §§2 and 19. The
requirements corpus references those definitions instead of maintaining a
competing glossary.

### B. Examples

- [TEST_EXAMPLES.md] — scenario definitions and expected outputs.
- [django_angular3/examples/01_simple_crm/] — runnable example workspace with schema,
  UI, and build artifacts.
- [tests/fixtures/artifacts/openapi/example.openapi.json] — example OpenAPI source input.
- [tests/fixtures/artifacts/openui/example.openui.json] — example OpenUI input.

### C. References

Labels used in this document are defined in the link-definitions block at the end of this file. Internal labels for other files in this repository are owned here. External labels mirror `ARCHITECTURE.md` §20 — update both files when changing an external URL.

<!-- External URLs below mirror ARCHITECTURE.md §20 — update both files when changing an external URL. -->
[ARCHITECTURE.md]: ../ARCHITECTURE.md
[APPLICATION_FUNCTIONAL_REQUIREMENTS.md]: APPLICATION_FUNCTIONAL_REQUIREMENTS.md
[APPLICATION_QUALITY_REQUIREMENTS.md]: APPLICATION_QUALITY_REQUIREMENTS.md
[APP_BUILDER_REQUIREMENTS.md]: APP_BUILDER_REQUIREMENTS.md
[AI_AUTOMATION_CONTRACTS.md]: ../contracts/AI_AUTOMATION_CONTRACTS.md
[AI_AUTOMATION_REQUIREMENTS.md]: AI_AUTOMATION_REQUIREMENTS.md
[AI_AUTOMATION_SPECIFICATIONS.md]: ../specifications/AI_AUTOMATION_SPECIFICATIONS.md
[CONTRACTS.md]: ../contracts/CONTRACTS.md
[SKILL_AUTHORING_PLAN.md]: ../SKILL_AUTHORING_PLAN.md
[SPECIFICATIONS.md]: ../specifications/SPECIFICATIONS.md
[TEST_EXAMPLES.md]: ../TEST_EXAMPLES.md
[django_angular3/examples/01_simple_crm/]: ../../django_angular3/examples/01_simple_crm/
[tests/fixtures/artifacts/openapi/example.openapi.json]: ../../tests/fixtures/artifacts/openapi/example.openapi.json
[tests/fixtures/artifacts/openui/example.openui.json]: ../../tests/fixtures/artifacts/openui/example.openui.json
[Django]: https://www.djangoproject.com/
[DRF - Django REST Framework]: https://www.django-rest-framework.org/
[Angular]: https://angular.dev/
[Angular Material]: https://material.angular.dev/
[OpenAPI 3.1 Specification]: https://spec.openapis.org/oas/v3.1.0.html
[OpenUI comparison]: https://openui-spec.readthedocs.io/en/latest/tooling/comparison/
[oasdiff]: https://www.oasdiff.com/
[oasdiff-github]: https://github.com/oasdiff/oasdiff
[ng-openapi-gen]: https://www.npmjs.com/package/ng-openapi-gen
[ng-openapi-gen-github]: https://github.com/cyclosproject/ng-openapi-gen
[datamodel-code-generator]: https://pypi.org/project/datamodel-code-generator/
[datamodel-code-generator-github]: https://github.com/koxudaxi/datamodel-code-generator
[datamodel-code-generator-playground]: https://datamodel-code-generator.koxudaxi.dev/playground/
[Claude Skills]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
