# Generated Application Quality Requirements

## Purpose and scope

This document defines the non-functional quality requirements for the
generated application platform. Product context, actors, journeys, and system
acceptance are defined in [REQUIREMENTS.md]. Generated-application capabilities
are defined in [APPLICATION_FUNCTIONAL_REQUIREMENTS.md].

This document defines required outcomes only. [SPECIFICATIONS.md] owns exact
platform structures and technical behavior, and [ARCHITECTURE.md] owns
architecture and design rationale.

## 5. Non-Functional Requirements

### 5.1. Architecture Constraints

The applicable architecture constraints are defined as requirements in the
focused sections below. Their structure and rationale remain owned by
[ARCHITECTURE.md].

### 5.2. Security

These requirements elaborate `ARCHITECTURE.md` §§ 13-16.

- Use secure defaults for authentication, cookies, CSRF, headers, and secret
  management
- Do not store sensitive tokens in browser local storage
- Enforce server-side permission checks even if the UI hides an action
- Use encrypted transport in non-local environments

### 5.3. Performance

- Standard list and detail API responses should feel interactive under normal
  business usage
- The UI should render common screens quickly on modern desktop browsers
- Expensive tasks such as bulk imports, exports, and email batches should be
  offloaded to background processing when implemented

### 5.4. Reliability

- The application must expose health checks for application and database status
- Failures in one module should not corrupt unrelated data
- Production deployments must support rollback or fast redeploy

### 5.5. Maintainability

- The codebase must be modular, readable, and covered by automated tests
- Shared backend and frontend patterns should be reused instead of duplicated
- Configuration must be environment-driven

### 5.6. Accessibility

- The UI must meet baseline accessibility expectations for keyboard use, focus
  visibility, labels, and color contrast
- Angular Material components should be used in accessible configurations

### 5.7. Observability

- Application logs must be structured and environment-appropriate
- Errors and warnings must be traceable to a request, user, or background job
  where possible
- Basic operational metrics should be collectable in staging and production

### 5.8. Internationalization and Time

- The system must store timestamps in UTC
- The UI must render dates and times in the user or deployment timezone
- Text and formatting should be designed so localization can be added later

### 5.9. Deployment Topology

See `ARCHITECTURE.md` §5 for the architectural deployment model.

- The generated application must support a same-origin production deployment.
- It must also support separate Django and Angular development servers with
  distinct frontend and backend route ownership.

[SPECIFICATIONS.md] §5 defines the exact production and local-development
topologies.

[APPLICATION_FUNCTIONAL_REQUIREMENTS.md]: APPLICATION_FUNCTIONAL_REQUIREMENTS.md
[ARCHITECTURE.md]: ../ARCHITECTURE.md
[REQUIREMENTS.md]: REQUIREMENTS.md
[SPECIFICATIONS.md]: ../specifications/SPECIFICATIONS.md
