# Generated Application Functional Requirements

## Purpose and scope

This document defines the functional requirements for the generated
application platform and its governed input and verification capabilities.
Product context, actors, journeys, and system acceptance are defined in
[REQUIREMENTS.md].

This document defines required outcomes only. [SPECIFICATIONS.md] owns exact
platform structures and technical behavior, [CONTRACTS.md] owns shared
normative boundaries, [APP_BUILDER_REQUIREMENTS.md] owns detailed `build_app`
behavior, and [AI_AUTOMATION_REQUIREMENTS.md] owns AI automation requirements.
Architectural terms and rationale are defined in [ARCHITECTURE.md].

## 4. Functional Requirements

### 4.1. API Requirements

These requirements elaborate `ARCHITECTURE.md` §§ 8.3 and 11.1-11.4.

- The platform must not require API-level namespace versioning as the contract
  versioning mechanism
- API endpoints must support authenticated access, validation, and standard HTTP
  semantics
- List endpoints must support filtering, sorting, and pagination
- API errors must return a predictable structure usable by the Angular client
- The backend must expose a durable, versioned OpenAPI schema artifact for
  downstream tooling and generated API-contract-derived content; schema versioning is the
  contract versioning mechanism that drives frontend alignment
- `oasdiff` must be used as the OpenAPI schema diff and change detection tool
- `oasdiff` must run as part of the contract normalization stage to identify
  changes between schema versions
- API schema generation and browsable documentation should be available in
  non-production environments

### 4.2. Configuration and change handling

- The platform must distinguish tool configuration, generated-app project
  configuration, OpenAPI input, and OpenUI input.
- Each setting must have one authority; duplicated runtime-setting authority
  is not permitted.
- Configuration loading must reject missing required clauses, invalid field
  types, and invalid values before the affected command runs.
- `djng` must represent supported input differences consistently so command
  selection and validation can consume them deterministically.

[SPECIFICATIONS.md] §2 defines the exact configuration categories,
relationships, and validation structure. [CONTRACTS.md] §2 defines the
canonical Change Model contract.

### 4.4. Authentication and Identity

- Users must be able to sign in and sign out securely
- The system must support password-based authentication at minimum
- The system should be designed to add SSO later without major rewrites
- Password reset and account recovery flows must be supported
- Session expiration and idle timeout behavior must be configurable

### 4.5. Authorization

- Access must be restricted to authenticated users unless a route is explicitly
  public
- The system must support role-based access control
- Permissions must be enforceable on both API endpoints and UI navigation
- Sensitive actions must be restricted by role and, where needed, object-level
  ownership or scope

### 4.6. User Management

- Administrators must be able to create, activate, deactivate, and update users
- Administrators must be able to assign roles or permission groups
- Users must be able to view and update their own profile details
- The system must track basic account status metadata such as creation date,
  last login, and active state

### 4.7. Application Shell and Navigation

- The frontend must provide a consistent shell with top-level navigation,
  breadcrumbs, and page titles
- The frontend must own client-side routing for the user-facing application
- Navigation items must be shown or hidden based on permissions
- The UI must support a responsive layout across standard desktop and mobile
  breakpoints
- Global feedback patterns must exist for loading, success, warning, and error
  states
- User-facing product screens should be implemented in Angular Material

### 4.8. Business Module Pattern

- The platform must support modular feature areas with isolated backend apps and
  frontend feature modules
- Each business module should support list, detail, create, update, and
  deactivate or delete flows where appropriate
- List screens must support filtering, sorting, and pagination
- Detail views must show key metadata and related records where relevant
- Forms must include client-side and server-side validation

### 4.9. Search and Data Discovery

- Users must be able to search records by primary identifying fields
- Filters must support common business cases such as status, owner, date range and free text
- Large result sets must be paginated
- Default sorting must be deterministic

### 4.10. Auditability

- The application must record important security and business events
- Changes to sensitive data should capture who made the change and when
- Audit history must be viewable by authorized users
- Authentication events such as login, logout, failed login, and password reset should be traceable

### 4.11. Notifications

- The platform should support system notifications for important events
- Email delivery should be supported for account and workflow notifications
- In-app notifications are desirable but not required for the first release

### 4.12. File Handling

- The platform should support file attachments for business records where needed
- File upload validation must enforce size and type restrictions
- Download access must respect record-level permissions

### 4.13. Administration and Reference Data

- The system must provide administrative screens for core configuration
- Reference data used across business modules must be centrally manageable
- Administrative changes must be audited

### 4.14. Input Artifact Strategy

See `ARCHITECTURE.md` §§ 8.2-8.5 and 10.2 for the related architectural
content-boundary and generated-artifact model.

- OpenAPI contract and Angular integration artifact terminology uses the
  definitions in `ARCHITECTURE.md` §§ 2.9-2.10.
- The OpenAPI contract must be the source of truth for API-contract-derived content,
  contracts, and generated Angular integration artifacts
- API-contract-derived list, detail, and standard form experiences should be derived from the
  OpenAPI contract where practical instead of being duplicated by hand
- Angular-related integration functionality shared across modules must be
  generated or maintained as reusable Angular integration artifacts
- Angular client generation may use `ng-openapi-gen` when its Angular-native
  output is a better fit than the baseline generator path
- The OpenUI concrete UI document must be the structured source for pages,
  forms, navigation, layouts, workflows, and related UI-description concerns
- The OpenUI input must be versioned and validated and may reference shared UI
  primitives and API contracts
- OpenAPI and OpenUI must remain separate versioned artifacts with distinct
  API-contract and UI-description roles; they may describe complementary
  aspects of the same feature and must be checked for cross-input consistency
- The Angular application must be assembled from outputs derived from both
  artifacts without treating either artifact as a substitute for the other
- Angular integration artifacts must include OpenAPI-derived typed API clients,
  API-contract-derived resource adapters, shared Angular Material integration patterns
  for list, detail, and standard form experiences, and authentication, CSRF,
  and transport helpers needed for Django integration
- Angular integration artifacts must not own product-specific application shell
  decisions, fully bespoke pages that are not OpenAPI-derived, business content
  that belongs to the main frontend application, or backend data administration
  concerns that belong to Django and DRF

### 4.15. Error Handling and Recovery

- Validation errors must be presented clearly at field and form level
- Unexpected server errors must be logged and surfaced with user-safe messages
- Users must not lose unsaved form state because of recoverable UI errors

### 4.16. Development Experience and Tooling

- When the generated app's Django server runs with `DEBUG=True`, any failure
  during app generation must surface through Django's standard error reporting
  rather than being swallowed or reported only to stdout.
- The generated app must provide development-only Angular build-health
  diagnostics and a build retrigger capability; these diagnostics must never
  be exposed in production.

[SPECIFICATIONS.md] §3 defines the exact development error-reporting and build-
diagnostics behavior.

### 4.17. Verification Requirements

See `ARCHITECTURE.md` §7.3 for the architectural verification model.

Verification must occur throughout construction and integration, not only as a
final check. The platform must support the following verification categories:

- **Contract verification**: the OpenAPI contract and OpenUI input must be
  validated before downstream construction proceeds; invalid or incompatible
  inputs must block the corresponding stage.
- **Construction-output verification**: generated and assembled outputs must be
  inspectable so they can be corrected, refined, or reused across iterations;
  emitted artifacts must not be treated as opaque or assumed correct without
  review.
- **Integration verification**: alignment between backend behavior, generated
  Angular integration artifacts, and frontend composition must be verified
  after schema changes, business-record changes, and each build or
  verification cycle.
- **Test-based verification**: automated tests must cover backend, frontend,
  and composed application flows and must be linked to the staged verification
  model rather than treated as a separate final phase.

### 4.18. Generated Application Structure

See `ARCHITECTURE.md` §§ 9-10 for the architectural structure model.

- The generated backend and frontend must use bounded areas with isolated,
  explicit responsibilities.
- Shared platform behavior must remain separate from domain-specific business
  modules.
- The main frontend product experience must not depend on Django template
  rendering or DRF UI facilities.
- Reusable UI and workflow patterns must be standardized rather than
  reimplemented independently per feature.

[SPECIFICATIONS.md] §4 defines the exact backend, frontend, and UI-pattern
structure.

[AI_AUTOMATION_REQUIREMENTS.md]: AI_AUTOMATION_REQUIREMENTS.md
[APP_BUILDER_REQUIREMENTS.md]: APP_BUILDER_REQUIREMENTS.md
[ARCHITECTURE.md]: ../ARCHITECTURE.md
[CONTRACTS.md]: ../contracts/CONTRACTS.md
[REQUIREMENTS.md]: REQUIREMENTS.md
[SPECIFICATIONS.md]: ../specifications/SPECIFICATIONS.md
