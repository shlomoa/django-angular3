# Architecture

## Purpose

This document describes the target architecture for a full-stack application
built with Django, DRF, and Angular Material. It is written for a greenfield
project and favors tight integration, clear module boundaries, and simple
production operations.

## Architectural Principles

- Prefer proven framework conventions over custom infrastructure
- Keep frontend and backend decoupled at the API boundary, but integrated in
  deployment and authentication
- Optimize for maintainability and incremental delivery
- Make security, testing, and observability part of the default design
- Keep the first version simple; add complexity only when a real feature
  requires it

## High-Level Design

The system consists of:

- A Django application for configuration, authentication, admin tooling, and 
  core business logic
- A DRF API layer exposed under a versioned namespace
- A versioned OpenAPI contract exported from the DRF layer
  Or a DRF layer built from an OpenAPI contract, if the project prefers a contract-first approach
- An Angular Material application for user workflows
- A generated Angular integration layer for typed clients and shared adapters
- A structured UI definition source for non-CRM pages and reactive forms
- PostgreSQL for primary persistence
- Optional Redis-backed background processing for asynchronous workloads
- Static asset hosting integrated into the same deployment boundary

## Separation of Responsibilities

### Django + DRF

Django and DRF are responsible for:

- Data models and persistence
- Business logic and workflow enforcement on the server
- Authentication, authorization, and audit enforcement
- Data administration and operational admin tooling
- Backend packaging, API delivery, and server-side deployment artifacts

### Angular Material

Angular Material is responsible for:

- The user-facing application shell
- End-user pages, workflows, forms, dialogs, and tables
- End-user application routing
- Presentation logic and client-side interaction behavior
- Consuming backend APIs for the user-facing application experience

### Boundary Rule

- Django templates, Django admin, and DRF-backed interfaces may be used for data
  administration services and operator workflows
- Django serves API, authentication, and administration endpoints
- Angular owns the user-facing route tree and navigation behavior
- Angular Material remains the primary UI system for the user-facing
  application
- Angular Material is the default and preferred UI system for all user-facing
  functionality

## Deployment Model

### Recommended Production Model

Use a same-origin deployment:

- Angular Material App is built into static assets
- Django serves the API under `/api/`
- Django serves authentication and administration endpoints under backend-owned
  routes
- Static assets are served either by Django plus a static file layer or by a
  reverse proxy in front of Django
- The browser talks to one origin for both UI and API
- User-facing application routes resolve to the Angular SPA entry point

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

## Logical Architecture

```text
Browser
  -> Angular SPA + Angular Material UI
  -> HTTP(S)
Django Application
  -> DRF API Layer
  -> Domain Services
  -> Django ORM
PostgreSQL

OpenAPI Contract
  -> generated Angular integration artifacts
  -> CRM-oriented generated clients and UI metadata

UI Definition Source
  -> Non-CRM forms and pages
  -> Angular SPA assembly

Optional:
  Django -> Redis -> Worker -> Email / file / background jobs
```

## Integration Workflow

The integration process should be modeled as an agent chain: a sequenced
automation pipeline with explicit handoff artifacts.

Recommended stages:

1. Backend contract stage: Django models, serializers, and DRF endpoints define
   the business contract and emit an OpenAPI artifact
2. Contract normalization stage: the OpenAPI artifact is validated, versioned,
   and prepared for CRM-facing generation
3. Angular integration generation stage: the OpenAPI contract produces typed
   clients, resource adapters, and reusable Angular Material-oriented
   integration helpers
4. Non-CRM content stage: a separate structured input source provides bespoke
   reactive forms, standalone pages, and workflow definitions
5. Application assembly stage: the Angular app composes CRM-derived outputs from
   generated integration artifacts with the non-CRM content stream
6. Verification stage: generated artifacts, contracts, and app integration are
   validated through automated tests and review

Each stage should produce durable artifacts that can be inspected, tested, and
handed off to the next stage without hidden assumptions.

## Initial Build Flow

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

## Backend Architecture

### Django Project Layers

The backend should be organized into clear layers:

- Project configuration: settings, URLs, ASGI/WSGI entry points, environment
  config
- Core apps: authentication, authorization, common utilities, audit, shared
  models
- Domain apps: isolated business modules
- API layer: serializers, viewsets, filters, permissions, schema
- Service layer: orchestration and business rules that should not live directly
  in models or views

### Recommended Backend Structure

```text
backend/
  manage.py
  pyproject.toml
  config/
    settings/
    urls.py
    asgi.py
    wsgi.py
  apps/
    common/
    accounts/
    access/
    audit/
    notifications/
    <domain_app_1>/
    <domain_app_2>/
  tests/
```

### Backend Responsibilities

#### `common`

- Shared base models and utilities
- Reusable pagination, filtering, and exception helpers
- Shared API response behavior where needed

#### `accounts`

- User model integration
- Authentication endpoints and profile management
- Password reset and session management support
- Administrative account management support for backend operators

#### `access`

- Roles, groups, and permission mapping
- Object-level authorization helpers if required

#### `audit`

- Audit event storage
- Model change logging hooks
- Query interfaces for authorized audit viewers

#### Administrative UI

- Use Django admin or equivalent backend-native admin tooling for internal data
  administration when it improves operational efficiency
- DRF-backed administrative interfaces are also acceptable when they support
  data administration and backend operations
- Keep administrative tooling clearly distinguished from the Angular end-user
  application

#### Domain apps

- Business entities
- Validation rules
- Service methods
- API serializers and viewsets for the module

## API Architecture

### API Style

- Use RESTful resources with DRF viewsets or generic views where appropriate
- Expose endpoints under `/api/v1/`
- Use standard HTTP methods and status codes
- Keep list responses compatible with DRF pagination conventions

Example patterns:

- `GET /api/v1/users/`
- `POST /api/v1/users/`
- `GET /api/v1/users/{id}/`
- `PATCH /api/v1/users/{id}/`

### OpenAPI Contract

- DRF must publish a versioned OpenAPI schema as the contract source of truth
  for CRM-facing functionality
- The exported schema should be stored as a durable build artifact so downstream
  agent-chain stages can consume it deterministically
- Contract changes should be reviewed as part of normal API change management

### Generation Toolchain

- Use `ng-openapi-gen` as the Angular client generation tool for contract-driven
  artifacts
- Django backend code should remain authored in DRF; OpenAPI generation on the
  backend side is limited to supporting artifacts, custom templates, or
  project-specific scaffolding
- Generator configuration files must be version-controlled and executable in CI
- Generated output must be deterministic enough to review in pull requests or
  re-create reliably in build pipelines

### API Concerns

- Validation belongs in serializers and domain services
- Authorization belongs in DRF permission classes plus domain checks
- Filtering should use a standard mechanism across modules
- Errors should be normalized so the Angular client can map them to forms and
  notifications consistently

### Versioning

- Start with URL-based versioning using `/api/v1/`
- Keep changes backward-compatible within a version where possible
- Introduce `/api/v2/` only for meaningful contract changes

## Authentication and Authorization

### Recommended Approach

Use Django-backed cookie/session authentication for the first-party web UI.

Reasons:

- Matches Django's strengths
- Works well with same-origin deployment
- Avoids storing long-lived tokens in browser storage
- Keeps CSRF protection straightforward

### Flow

- User signs in through a DRF-authenticated endpoint
- Django sets secure session cookies
- Angular includes CSRF tokens on unsafe requests
- Angular route guards control navigation within the user-facing route tree
- Route guards and API permissions enforce access at both layers

### Permission Model

- Use Django groups and permissions as the baseline
- Add application-specific roles where business language needs them
- Enforce critical permissions server-side regardless of frontend state

## Data Architecture

### Primary Database

- PostgreSQL is the system of record
- Use relational modeling with explicit foreign keys and constraints
- Prefer soft deletion only where business or audit needs justify it

### Data Modeling Guidance

- Keep shared cross-module entities in core apps only when truly shared
- Avoid a giant catch-all app for unrelated business concepts
- Use database indexes for frequent filter and lookup paths
- Store timestamps in UTC

### File Storage

- Local filesystem storage is acceptable for development
- Non-local environments should use durable object storage for user-uploaded
  files
- File metadata belongs in PostgreSQL; file binaries belong in storage

## Background Processing

Background jobs should be introduced for:

- Email delivery
- Bulk import and export
- Long-running integrations
- Scheduled maintenance jobs

Recommended pattern:

- Redis as broker/cache
- A Django-compatible worker system
- Jobs kept idempotent and observable

If the first release does not need these features, the codebase can start
without a worker and add it when the first asynchronous use case appears.

## Frontend Architecture

### Angular Application Shape

The frontend should be an Angular SPA with:

- Angular Material for layout, form controls, tables, dialogs, and feedback
- Lazy-loaded feature routes
- Standalone or feature-scoped components organized by responsibility
- Reactive forms for non-trivial create and edit workflows
- No dependency on Django template rendering or DRF UI facilities for the main
  product experience

### Angular Integration Layer

The Angular integration layer is not the whole frontend application.

Its responsibilities should include:

- OpenAPI-derived typed API clients
- Wrapping or normalizing code generated by OpenAPI Generator or
  `ng-openapi-gen`
- CRM-oriented resource adapters and data-access helpers
- Shared Angular Material integration patterns for list, detail, and standard
  form experiences
- Authentication, CSRF, and transport helpers needed for Django integration
- Reusable metadata or generation outputs consumed by the main Angular app

It should not own:

- Product-specific application shell decisions
- Fully bespoke pages that are not OpenAPI-derived
- Business content that belongs to the main frontend application
- Backend data administration concerns that belong to Django and DRF

### Recommended Frontend Structure

```text
frontend/
  src/
    app/
      core/
        auth/
        guards/
        interceptors/
        layout/
        services/
      shared/
        components/
        pipes/
        utils/
      features/
        accounts/
        admin/
        <domain_feature_1>/
        <domain_feature_2>/
  generated/
```

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

- Use Angular Material as the default component set
- Keep a single theme system with shared spacing, typography, and density rules
- Standardize list, detail, form, dialog, snackbar, and confirmation patterns

## Frontend and Backend Integration

### Content Sources

The application has two distinct input sources:

- CRM content source: the OpenAPI contract exported by Django and consumed by
  the generated Angular integration layer
- Non-CRM content source: a separate structured definition set for reactive
  forms, standalone pages, and bespoke workflows

Here, CRM content means contract-derived resource content, not a narrow
customer-sales domain assumption.

These two streams should remain separate so contract-derived CRM functionality
does not get mixed with manually-authored UI definitions.

### Contract Rules

- API contracts must be explicit and versioned
- The frontend must treat the backend as the source of truth for permissions and
  validation
- Shared enumerations and reference data should come from the API, not be hard
  coded in the client
- CRM-facing Angular content should be generated or configured from OpenAPI
  wherever practical
- The preferred generation path is `ng-openapi-gen` for its Angular-native
  output and ergonomics
- Non-CRM content definitions should be version-controlled and validated
  separately from the OpenAPI contract
- The user-facing product UI remains frontend-owned, while backend data
  administration services remain Django + DRF-owned

### HTTP Integration

- Use an Angular HTTP interceptor for CSRF, auth-related redirects, and common
  error handling
- Centralize API base URL configuration by environment
- Keep transport models close to feature services

### Non-CRM Input Source

Use a dedicated structured input source under a path such as `spec/ui/` for
non-CRM content.

This source should define:

- Reactive form metadata that is not directly derivable from OpenAPI
- Standalone page definitions
- Workflow-specific layouts or interaction rules

It should be machine-readable, versioned in the repository, and able to
reference API resources exposed through the OpenAPI contract.

## Observability

### Logging

- Use structured application logs
- Include request identifiers where possible
- Distinguish user errors, validation errors, and system failures

### Health and Monitoring

- Provide health endpoints for app and database readiness
- Track backend exceptions and frontend runtime errors
- Add metrics for request rates, latency, and background jobs when available

## Testing Strategy

### Backend

- Unit tests for services, permissions, and model behavior
- API tests for serializers, endpoints, and authentication
- Database-backed tests for critical workflows

### Frontend

- Unit tests for services and utility logic
- Component tests for forms, tables, and route-protected pages
- End-to-end tests for login and the main business module workflows

### Integration

- Verify frontend/backend contracts through automated test coverage
- Include smoke tests in staging before production release

## Security Considerations

- Keep secrets out of source control
- Enforce HTTPS outside local development
- Enable CSRF protection for authenticated browser traffic
- Validate and authorize every write operation on the server
- Sanitize file uploads and enforce type and size restrictions
- Limit admin capabilities to explicit roles

## Environments

The project should support at least:

- Local development
- Automated test environment
- Staging
- Production

Configuration should be environment-driven and must not require code changes to
switch environments.

## Suggested Repository Layout

```text
doc/
  REQUIREMENTS.md
  ARCHITECTURE.md
backend/
frontend/
spec/
  openapi/
    source/
    ng-openapi-gen/
  ui/
build/
  angular/
infra/
```

Where:

- `doc/` holds product and engineering design docs
- `backend/` holds the Django project
- `frontend/` holds the Angular application
- `spec/openapi/` holds exported or versioned OpenAPI artifacts
- `spec/openapi/source/` holds the dumped source OAS documents from Swagger
  Studio / SwaggerHub
- `spec/openapi/ng-openapi-gen/` holds Angular client generator configs and
  templates
- `spec/ui/` holds structured non-CRM page and reactive-form definitions
- `build/angular/` holds generated Angular integration artifacts in the current
  scaffold
- `infra/` holds deployment artifacts such as container, proxy, and CI files

## Decisions Captured Here

- Tight integration between Django and Angular is intentional
- Same-origin deployment is the default production target
- Django session authentication is the default first-party auth model
- PostgreSQL is the primary database
- Angular Material is the default UI system
- Django + DRF own backend data, administration, and packaging concerns
- Angular Material owns the user-facing application experience
- OpenAPI is the source of truth for CRM-facing contracts
- `ng-openapi-gen` is the Angular client code-generation tool
- Generated Angular integration artifacts are the boundary for reusable
  Angular/Django integration code in the current scaffold
- Non-CRM content is supplied by a separate structured input source
- Modular backend apps and frontend feature areas are the scaling strategy

## Next Technical Steps

After this architecture is accepted, implementation should proceed in this
order:

1. Scaffold repository structure for `backend/`, `frontend/`, `spec/`, and
   supporting build-output paths
2. Set up Django, DRF, and PostgreSQL configuration
3. Export and version the initial OpenAPI contract
4. Commit baseline generator configuration for `ng-openapi-gen`
5. Create the Angular integration layer and wire it to generated OpenAPI
   artifacts
6. Define the structured non-CRM input source for reactive forms and pages
7. Set up Angular and Angular Material with a shared shell that consumes both
   content streams
8. Implement authentication and authorization
9. Build one business module end to end
10. Add audit logging, health checks, generator verification, and automated
    tests
