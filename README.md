# django-angular3

Angular Material integration for Django REST framework.

The starting point for this project is Django REST framework. `django-angular3`
is intended for applications where:

- Django + DRF own data, authentication, APIs, and data administration services
- Angular Material owns the user-facing application and client-side routing
- OpenAPI is the source of truth for CRM-facing functionality
- non-CRM pages, reactive forms, and bespoke workflows come from a separate
  structured input source

* * *

## Overview

`django-angular3` is a contract-first integration package for teams building
Angular Material frontends on top of Django REST framework backends.

Some reasons you might want to use it:

- Start from a DRF backend instead of inventing a parallel backend model.
- Keep Django responsible for data, authentication, and data administration.
- Keep Angular responsible for the end-user application and route tree.
- Use OpenAPI to drive CRM-facing client-side integration.
- Support non-CRM pages and workflows without forcing them into the OpenAPI
  path.

## Requirements

To use this package as intended, your application should have:

- a Django REST framework backend
- an OpenAPI specification exported from that backend
- an Angular Material frontend for the user-facing product
- a separate input source for non-CRM UI definitions

## Installation

Installation instructions are not available yet because the runnable package
implementation has not been scaffolded or published.

## Example

A typical usage flow looks like this:

1. Start with a Django REST framework application.
2. Expose or export the OpenAPI specification from the DRF backend.
3. Use `django-angular3` to support Angular-side integration for CRM-facing
   functionality.
4. Add non-CRM pages, forms, and bespoke workflows through a separate input
   source.
5. Run the application with Django serving API, authentication, and data
   administration services, and Angular serving the user-facing SPA.

## Documentation

Public usage documentation is not available yet.

Current project documents:

- [Requirements](doc/REQUIREMENTS.md)
- [Architecture](doc/ARCHITECTURE.md)

## Status

This project is still in the design and architecture phase. The repository does
not yet contain the runnable package implementation, published artifacts, or
execution scripts.
