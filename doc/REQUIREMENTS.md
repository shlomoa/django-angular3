# Requirements

## Purpose

`django-angular3` enables seamless integration of Django, Django REST Framework
(DRF), and Angular Material. This document defines the baseline requirements
for the full-stack application platform that integration targets.

The package bridges the DRF backend and the Angular frontend through a
contract-first pipeline: it validates OpenAPI artifacts exported from Django,
plans Angular workspace setup and client code-generation commands, and produces
deterministic build artifacts that connect both stacks without manual glue work.

Because the business domain is not yet specified, these requirements describe a
reusable application platform that supports authentication, administration,
auditing, and modular business features. Domain-specific modules can be added
on top of this foundation without changing the core architecture.

## Product Vision

Build a production-ready business application with:

- Django as the primary backend framework
- DRF as the API layer
- Angular as the single-page application frontend
- Angular Material as the design system and component library
- OpenAPI as the contract source of truth for CRM-facing functionality
- Reusable Angular integration artifacts generated from the OpenAPI contract
- A separate structured input source for non-CRM pages and reactive forms
- Tight frontend/backend integration for local development and production

## Goals

- Deliver a maintainable full-stack application foundation
- Support secure authenticated access for multiple user roles
- Enable rapid delivery of business modules through reusable CRUD patterns
- Provide a clean, responsive, accessible UI for desktop-first workflows with
  mobile support
- Make the platform observable, testable, and ready for staged deployment

## Assumptions

- The application is first-party software owned by one organization
- Users access the product through a web browser
- PostgreSQL is the primary relational database
- The first release is focused on internal or partner-facing workflows rather
  than anonymous public traffic
- At least one business module will be implemented in the MVP, but the platform
  must support more modules later

## Platform Responsibilities

### Django + DRF

- Own the data model, persistence layer, and backend business logic
- Own authenticated APIs, authentication services, authorization enforcement,
  and backend integrations
- Own administrative capabilities for data administration, reference data, and
  operational tooling
- May provide data administration services through Django-native or DRF-backed
  administrative interfaces where appropriate
- Own backend packaging and deployment-facing server artifacts

### Angular Material Frontend

- Own the user-facing application experience
- Own page layout, navigation, forms, tables, dialogs, and interaction design
- Own end-user application routing
- Consume Django and DRF APIs as the backend contract surface
- Do not replace Django + DRF responsibility for data administration services

## User Roles

- Anonymous user: can access the login screen and other explicitly public pages
- Authenticated user: can use permitted business features
- Manager or supervisor: can review broader data sets and approve sensitive
  actions when the business domain requires it
- Administrator: can manage users, roles, reference data, and system
  configuration
- Support or operations user: can inspect logs, audit history, and system state
  within approved permissions

## Functional Requirements

### 1. Authentication and Identity

- Users must be able to sign in and sign out securely
- The system must support password-based authentication at minimum
- The system should be designed to add SSO later without major rewrites
- Password reset and account recovery flows must be supported
- Session expiration and idle timeout behavior must be configurable

### 2. Authorization

- Access must be restricted to authenticated users unless a route is explicitly
  public
- The system must support role-based access control
- Permissions must be enforceable on both API endpoints and UI navigation
- Sensitive actions must be restricted by role and, where needed, object-level
  ownership or scope

### 3. User Management

- Administrators must be able to create, activate, deactivate, and update users
- Administrators must be able to assign roles or permission groups
- Users must be able to view and update their own profile details
- The system must track basic account status metadata such as creation date,
  last login, and active state

### 4. Application Shell and Navigation

- The frontend must provide a consistent shell with top-level navigation,
  breadcrumbs, and page titles
- The frontend must own client-side routing for the user-facing application
- Navigation items must be shown or hidden based on permissions
- The UI must support a responsive layout across standard desktop and mobile
  breakpoints
- Global feedback patterns must exist for loading, success, warning, and error
  states
- User-facing product screens should be implemented in Angular Material

### 5. Business Module Pattern

- The platform must support modular feature areas with isolated backend apps and
  frontend feature modules
- Each business module should support list, detail, create, update, and
  deactivate or delete flows where appropriate
- List screens must support filtering, sorting, and pagination
- Detail views must show key metadata and related records where relevant
- Forms must include client-side and server-side validation

### 6. Search and Data Discovery

- Users must be able to search records by primary identifying fields
- Filters must support common business cases such as status, owner, date range,
  and free text
- Large result sets must be paginated
- Default sorting must be deterministic

### 7. Auditability

- The application must record important security and business events
- Changes to sensitive data should capture who made the change and when
- Audit history must be viewable by authorized users
- Authentication events such as login, logout, failed login, and password reset
  should be traceable

### 8. Notifications

- The platform should support system notifications for important events
- Email delivery should be supported for account and workflow notifications
- In-app notifications are desirable but not required for the first release

### 9. File Handling

- The platform should support file attachments for business records where needed
- File upload validation must enforce size and type restrictions
- Download access must respect record-level permissions

### 10. Administration and Reference Data

- The system must provide administrative screens for core configuration
- Reference data used across business modules must be centrally manageable
- Administrative changes must be audited
- Administrative tooling is part of the Django + DRF responsibility boundary and
  may use Django-native administration capabilities, DRF-backed tools, or other
  backend-oriented administration interfaces

### 11. API Requirements

- DRF must expose a versioned API namespace
- API endpoints must support authenticated access, validation, and standard HTTP
  semantics
- List endpoints must support filtering, sorting, and pagination
- API errors must return a predictable structure usable by the Angular client
- The backend must expose a stable OpenAPI schema for downstream tooling and
  generated CRM-facing content
- API schema generation and browsable documentation should be available in
  non-production environments

### 12. Content Source Strategy

- In this document, CRM-facing content means resource-oriented application
  content derived from the OpenAPI contract
- OpenAPI must be the source of truth for CRM-facing content, contracts, and
  generated Angular integration artifacts
- The project must use a reproducible OpenAPI-based code generation toolchain,
  with `ng-openapi-gen` as the Angular client generator
- CRM list, detail, and standard form experiences should be derived from the
  OpenAPI contract where practical instead of being duplicated by hand
- Angular-related integration functionality shared across modules must be
  generated or maintained as reusable Angular integration artifacts
- Angular client generation may use `ng-openapi-gen` when its Angular-native
  output is a better fit than the baseline generator path
- The delivery process must support an agent chain with defined handoff
  artifacts between schema generation, client generation, UI assembly, and app
  integration
- Non-CRM content such as bespoke reactive forms, standalone pages, and custom
  workflows must come from a separate structured input source
- The non-CRM input source must be versioned, validated, and able to reference
  shared UI primitives and API contracts without becoming the CRM source of
  truth

### 13. Error Handling and Recovery

- Validation errors must be presented clearly at field and form level
- Unexpected server errors must be logged and surfaced with user-safe messages
- Users must not lose unsaved form state because of recoverable UI errors

## Non-Functional Requirements

### Security

- Use secure defaults for authentication, cookies, CSRF, headers, and secret
  management
- Do not store sensitive tokens in browser local storage
- Enforce server-side permission checks even if the UI hides an action
- Use encrypted transport in non-local environments

### Performance

- Standard list and detail API responses should feel interactive under normal
  business usage
- The UI should render common screens quickly on modern desktop browsers
- Expensive tasks such as bulk imports, exports, and email batches should be
  offloaded to background processing when implemented

### Reliability

- The application must expose health checks for application and database status
- Failures in one module should not corrupt unrelated data
- Production deployments must support rollback or fast redeploy

### Maintainability

- The codebase must be modular, readable, and covered by automated tests
- Shared backend and frontend patterns should be reused instead of duplicated
- Configuration must be environment-driven

### Accessibility

- The UI must meet baseline accessibility expectations for keyboard use, focus
  visibility, labels, and color contrast
- Angular Material components should be used in accessible configurations

### Observability

- Application logs must be structured and environment-appropriate
- Errors and warnings must be traceable to a request, user, or background job
  where possible
- Basic operational metrics should be collectable in staging and production

### Internationalization and Time

- The system must store timestamps in UTC
- The UI must render dates and times in the user or deployment timezone
- Text and formatting should be designed so localization can be added later

## MVP Scope

The first implementation should include:

- Backend project setup with Django and DRF
- Angular frontend setup with Angular Material
- Generated Angular integration artifacts for shared Angular/Django integration
  logic
- Authentication and role-based authorization
- User profile and user administration
- OpenAPI export and consumption flow for CRM-facing features
- OpenAPI generator configuration committed to the repository and runnable in CI
- A structured non-CRM content input source for reactive forms and pages
- One complete business module implemented end to end
- Shared list, detail, and form patterns
- Audit logging for key actions
- Error handling, health checks, and baseline automated tests
- Local development workflow plus staging-ready deployment setup

## First-Time Use Case

The initial authoring and build flow must support this sequence:

1. A user designs or updates the OpenAPI specification in Swagger Studio
   (SmartBear's API design tooling, historically associated with SwaggerHub)
2. The user exports or dumps the OAS artifact into the repository
3. The user adds non-CRM changes such as bespoke reactive forms, page
   definitions, or workflow-specific UI content
4. The user fires a build
5. The build validates inputs, generates CRM-facing artifacts, assembles the
   Angular app, and reports any contract or input errors clearly

For this first-time flow:

- The repository must provide a clear location for the source OAS artifact
- The repository must provide a separate location for non-CRM content inputs
- The build must fail fast when the OpenAPI contract is invalid or incompatible
  with generation
- The build must fail fast when non-CRM content inputs are invalid
- The build must produce deterministic outputs from the same OAS and non-CRM
  inputs
- The build must allow a first-time user to understand which stage failed:
  contract validation, code generation, non-CRM input validation, or final app
  assembly

## Out of Scope for Initial Release

- Native mobile applications
- Public multi-tenant marketplace behavior
- Complex workflow engine features unless demanded by the first business module
- Real-time collaboration
- Advanced analytics or BI dashboards beyond operational summaries

## Acceptance Criteria

The platform is ready for implementation handoff when:

- The backend/frontend integration model is agreed
- Authentication, authorization, and audit expectations are explicit
- OpenAPI and non-CRM content inputs have clear ownership and boundaries
- The MVP scope includes one full business module and the shared platform
  services it needs
- Non-functional requirements are concrete enough to guide engineering choices
- The architecture supports adding future modules without reworking the core
  stack
