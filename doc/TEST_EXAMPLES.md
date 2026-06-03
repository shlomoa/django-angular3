# Test Examples

## Overview

Each example defines a concrete scenario that the app builder command can
execute end-to-end. Together they cover the full range of use cases described
in `APP_BUILDER_REQUIREMENTS.md`.

Each example consists of:
- A named scenario with a description
- Input files: OpenAPI schema and `django-angular3.json` config
- The expected `ChangeSet` output from the builder

### Shared conventions across all examples

- **Django project name**: varies per example (e.g. `simple_crm`)
- **Django app name / Angular app name**: `shop` — all six examples use the same
  primary app. None of the schema or config changes replace the app itself;
  they evolve the schema and UI configuration within the same `shop` app.
- The expected build plan / ordered procedure sequence
- The aspect of the solution it demonstrates

Examples are located under `spec/examples/<example-name>/` and can be run via:

```bash
django-admin build_app spec/examples/<example-name>/django-angular3.json \
  [--previous-schema spec/examples/<example-name>/previous-schema.yaml] \
  [--previous-project-config spec/examples/<example-name>/previous-project-config.json] \
  --dry-run
```

---

## Example 1: Simple CRM — Start from Scratch

**Demonstrates**: Full pipeline from a cold start. The skill-session subset
invokes all 11 skills in dependency order. Baseline for verifying the
complete automation chain.

### Scenario

A new project with no previous state. The schema defines two resources:
`Customer` and `Product`. The config defines one page per resource (list +
detail) and a site with top-level navigation.

### Input: `schema.yaml`

```yaml
openapi: 3.0.3
info:
  title: Simple CRM API
  version: 1.0.0
paths:
  /api/v1/customers/:
    get:
      operationId: customers_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - customers
      security:
      - cookieAuth: []
      - basicAuth: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedCustomerList'
          description: ''
    post:
      operationId: customers_create
      tags:
      - customers
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Customer'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Customer'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Customer'
        required: true
      security:
      - cookieAuth: []
      - basicAuth: []
      - {}
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Customer'
          description: ''
  /api/v1/customers/{id}/:
    get:
      operationId: customers_retrieve
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this customer.
        required: true
      tags:
      - customers
      security:
      - cookieAuth: []
      - basicAuth: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Customer'
          description: ''
    patch:
      operationId: customers_partial_update
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this customer.
        required: true
      tags:
      - customers
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PatchedCustomer'
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/PatchedCustomer'
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/PatchedCustomer'
      security:
      - cookieAuth: []
      - basicAuth: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Customer'
          description: ''
    delete:
      operationId: customers_destroy
      parameters:
      - in: path
        name: id
        schema:
          type: integer
        description: A unique integer value identifying this customer.
        required: true
      tags:
      - customers
      security:
      - cookieAuth: []
      - basicAuth: []
      - {}
      responses:
        '204':
          description: No response body
  /api/v1/products/:
    get:
      operationId: products_list
      parameters:
      - name: page
        required: false
        in: query
        description: A page number within the paginated result set.
        schema:
          type: integer
      tags:
      - products
      security:
      - cookieAuth: []
      - basicAuth: []
      - {}
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedProductList'
          description: ''
components:
  schemas:
    Customer:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 120
        email:
          type: string
          format: email
          maxLength: 254
        phone:
          type: string
          maxLength: 50
        active:
          type: boolean
      required:
      - email
      - id
      - name
    PaginatedCustomerList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/Customer'
    PaginatedProductList:
      type: object
      required:
      - count
      - results
      properties:
        count:
          type: integer
          example: 123
        next:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=4
        previous:
          type: string
          nullable: true
          format: uri
          example: http://api.example.org/accounts/?page=2
        results:
          type: array
          items:
            $ref: '#/components/schemas/Product'
    PatchedCustomer:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 120
        email:
          type: string
          format: email
          maxLength: 254
        phone:
          type: string
          maxLength: 50
        active:
          type: boolean
    Product:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          maxLength: 200
        price:
          type: number
          format: double
        sku:
          type: string
          maxLength: 100
      required:
      - id
      - name
      - price
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic
    cookieAuth:
      type: apiKey
      in: cookie
      name: sessionid
```

### Input: `<project>.project.json` (placeholder name — schema TBD)

> ⚠️ The generated app configuration file name and schema are not yet defined
> (see `TODO.md` item 1). The content and path shown below are illustrative;
> the actual file name and schema will be specified when that item is resolved.

```json
{
  "pages": [
    { "name": "customer-list",   "resource": "Customer", "type": "list" },
    { "name": "customer-detail", "resource": "Customer", "type": "detail" },
    { "name": "product-list",    "resource": "Product",  "type": "list" }
  ],
  "site": {
    "nav": [
      { "label": "Customers", "route": "/customers" },
      { "label": "Products",  "route": "/products" }
    ]
  }
}
```

### Input: `django-angular3.json`

```json
{
  "project": { "name": "simple_crm" },
  "app": { "name": "shop" },
  "openapi": { "source": "spec/examples/01_simple_crm/schema.yaml" },
  "angular": {
    "output": "build/examples/01_simple_crm",
    "workspace": { "packageManager": "pnpm", "style": "scss", "routing": true }
  }
}
```

### Expected ChangeSet

```json
{
  "schema": { "type": "start-from-scratch" },
  "config": { "type": "start-from-scratch" }
}
```

### Expected build plan steps (ordered)

Deterministic tool procedures (see `GENERATE_AI_AUTOMATIONS.md` §Tool
Contracts Catalog) precede the SKILL sessions:

1. `export_schema` *(tool)* — produce the current OpenAPI artifact at
   `openapi.source`
2. `validate_openapi_schema` *(tool)* — validate the freshly exported schema
3. `ngdj_create_workspace` *(tool)* — scaffold the Angular workspace at
   `angular.output`
4. `ng-workspace` *(skill)* — apply Angular Material workspace conventions on
   the scaffolded workspace `simple_crm`
5. `ngdj_create_app` *(tool)* — add the Angular application `simple_crm` into
   the workspace
6. `ng-app` *(skill)* — finalize the Angular Material application `simple_crm`
7. `ng_openapi_gen` *(tool)* — generate the typed Angular API client from
   `schema.yaml`
8. `ng-api` *(skill)* — integrate the generated API client
9. `ng-data-service` *(skill)* — generate data services for `Customer`,
   `Product`
10. `ng-component` *(skill)* — generate list component for `Customer`
11. `ng-component` *(skill)* — generate detail component for `Customer`
12. `ng-component` *(skill)* — generate list component for `Product`
13. `ng-reactive-form` *(skill)* — generate edit form for `Customer`
14. `ng-page` *(skill)* — generate `customer-list` page
15. `ng-page` *(skill)* — generate `customer-detail` page
16. `ng-page` *(skill)* — generate `product-list` page
17. `ng-site` *(skill)* — assemble site with navigation
18. *(verification)* — terminal verification procedure (per
    `APP_BUILDER_REQUIREMENTS.md` FR-10) consuming the structured outputs of
    the tool procedures above

---

## Example 2: Schema Evolution — Add Resource

**Demonstrates**: Incremental schema change. Previous state is Example 1.
Only new-resource skills run; existing workspace, app, and components are
untouched. Uses `add-things` change path.

### Scenario

The `Order` resource and its endpoints are added to the schema. No config
change.

### Input: `schema.yaml`

Example 1's schema plus:

```yaml
paths:
  /api/v1/orders/:
    get:
      operationId: order_list
      tags: [orders]
      responses:
        "200":
          content:
            application/json:
              schema:
                type: array
                items: { $ref: "#/components/schemas/Order" }
  /api/v1/orders/{id}/:
    get:
      operationId: order_retrieve
      tags: [orders]
      parameters:
        - { name: id, in: path, required: true, schema: { type: integer } }
      responses:
        "200":
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Order" }
components:
  schemas:
    Order:
      type: object
      required: [id, customer, total]
      properties:
        id:       { type: integer, readOnly: true }
        customer: { type: integer, description: "Customer ID" }
        total:    { type: number, format: float }
        status:   { type: string, enum: [draft, confirmed, shipped, closed] }
```

### Previous schema

Example 1's `schema.yaml`.

### Expected ChangeSet

```json
{
  "schema": {
    "type": "add-things",
    "affected_resources": ["Order"],
    "breaking": false
  },
  "config": { "type": "no-change" }
}
```

### Expected build plan steps

Deterministic tool procedures precede the schema-derived SKILL sessions:

1. `export_schema` *(tool)* — re-export the schema; archive previous version
2. `validate_openapi_schema` *(tool)* — validate the new schema
3. `oasdiff_diff` *(tool)* — produce the structured diff feeding the
   `ChangeSet` above (`change_type: add-things`, no breaking changes)
4. `ng_openapi_gen` *(tool)* — regenerate the typed Angular API client to
   include the new `Order` endpoints
5. `ng-api` *(skill)* — integrate the regenerated API client (new `Order`
   endpoints)
6. `ng-data-service` *(skill)* — generate data service for `Order`
7. *(verification)* — terminal verification procedure (per FR-10)

No workspace, app, or existing component steps — they are not affected.

---

## Example 3: Schema Evolution — Breaking Change Blocked

**Demonstrates**: oasdiff breaking-change gate. Builder halts before emitting
a plan. Verifies the `--acknowledge-breaking` bypass.

### Scenario

The `Customer.email` field (previously required, string) is removed from the
schema. oasdiff classifies this as a breaking change.

### Input: `schema.yaml`

Example 1's schema with `email` removed from `Customer.required` and
`Customer.properties`.

### Expected ChangeSet (before gate)

```json
{
  "schema": {
    "type": "breaking",
    "breaking": true,
    "affected_resources": ["Customer"]
  }
}
```

### Expected builder output

The breaking-change gate is fed by the `oasdiff_diff` tool contract (see
`GENERATE_AI_AUTOMATIONS.md` §Tool Contracts Catalog). `oasdiff_diff` itself
exits zero and returns its structured `breaking` array; the gate procedure
consumes that output and halts the run:

```
Breaking schema changes detected:
  - Customer: required property 'email' removed (breaking)

Review the oasdiff report at build/oasdiff-report.json before proceeding.
Re-run with --acknowledge-breaking to continue.
```

Exit code: non-zero (e.g., 2). This exit code is distinct from the tool
failure exit code required by `APP_BUILDER_REQUIREMENTS.md` FR-9.

### With `--acknowledge-breaking`

Builder proceeds. ChangeSet type becomes `remove-things` for the `email`
field. Steps include:

1. `ng-api` — regenerate API client
2. `ng-data-service` — update `Customer` data service
3. `ng-reactive-form` — update customer edit form (remove `email` field)
4. `ng-component` — update customer detail component (remove `email` display)

---

## Example 4: Config Change — Add Page (No Schema Change)

**Demonstrates**: Config-only change path. Schema is identical to Example 1.
Only config-derived automation procedures run. In the current examples, that
means the config-derived skill procedures. Uses `add-things` on the config
side.

> ⚠️ This example is blocked by `TODO.md` item 1. The `<project>.project.json`
> file name and schema are not yet defined; neither the config diff function
> nor the config-derived skill dispatch are implementable until they are. The
> inputs and expected output below are illustrative.

### Scenario

A dashboard page is added to the generated app configuration. No schema change.

### Input: `django-angular3.json`

Same as Example 1 — no change (this file is golden; it is never diffed).

### Input: current `<project>.project.json` (placeholder name — schema TBD)

Example 1's generated app configuration plus a new page and two new components:

```json
{
  "pages": [
    { "name": "customer-list",   "resource": "Customer", "type": "list" },
    { "name": "customer-detail", "resource": "Customer", "type": "detail" },
    { "name": "product-list",    "resource": "Product",  "type": "list" },
    { "name": "dashboard",       "type": "custom",       "components": ["customer-summary", "product-summary"] }
  ],
  "components": [
    { "name": "customer-summary", "type": "small-field", "resource": "Customer", "fields": ["name", "active"] },
    { "name": "product-summary",  "type": "small-field", "resource": "Product",  "fields": ["name", "price"] }
  ],
  "site": {
    "nav": [
      { "label": "Customers", "route": "/customers" },
      { "label": "Products",  "route": "/products" }
    ]
  }
}
```

### Input: previous `<project>.project.json`

Example 1's `<project>.project.json` (the state before this change).

### Expected ChangeSet

```json
{
  "schema": { "type": "no-change" },
  "config": {
    "type": "add-things",
    "affected_pages": ["dashboard"],
    "affected_components": ["customer-summary", "product-summary"]
  }
}
```

### Expected build plan steps

1. `ng-field-component` — generate `customer-summary` component
2. `ng-field-component` — generate `product-summary` component
3. `ng-page` — generate `dashboard` page

---

## Example 5: Combined Schema and Config Change

**Demonstrates**: Schema and config change in the same run. Both change paths
activate. Verifies that schema steps run before config steps at the same
dependency level, and that the plan correctly interleaves the two streams.

> ⚠️ The config-side portion of this example is blocked by `TODO.md` item 1.
> The schema-side portion (new `Invoice` resource) is unblocked and can be
> verified independently.

### Scenario

Starting from Example 2's state (Customer, Product, Order):
- Schema: a new `Invoice` resource is added.
- Config: a new `invoice-list` page is added to the generated app configuration.

### Expected ChangeSet

```json
{
  "schema": {
    "type": "add-things",
    "affected_resources": ["Invoice"],
    "breaking": false
  },
  "config": {
    "type": "add-things",
    "affected_pages": ["invoice-list"]
  }
}
```

### Expected build plan steps (order matters)

1. `ng-api` — regenerate API client (new `Invoice` endpoints) ← schema step
2. `ng-data-service` — generate `Invoice` data service ← schema step
3. `ng-component` — generate `Invoice` list component ← schema step
4. `ng-page` — generate `invoice-list` page ← config step (depends on step 3)

---

## Example 6: Full Replacement — Remove Resource, Add Resource

**Demonstrates**: `replace-things` change type. One resource is removed
(`Product`) and one is added (`Supplier`). Remove steps precede add steps at
the same dependency level.

### Expected ChangeSet

```json
{
  "schema": {
    "type": "replace-things",
    "affected_resources": ["Product", "Supplier"],
    "breaking": false
  }
}
```

### Expected build plan steps

1. `ng-data-service` — delete `Product` data service
2. `ng-component` — delete `Product` list and detail components
3. `ng-page` — delete `product-list` page
4. `ng-site` — update navigation (remove Products link)
5. `ng-api` — regenerate API client (no Product endpoints; new Supplier endpoints)
6. `ng-data-service` — generate `Supplier` data service
7. `ng-component` — generate `Supplier` list component
8. `ng-page` — generate `supplier-list` page
9. `ng-site` — update navigation (add Suppliers link)

---

## Running the Examples

Once the `build_app` command is implemented, all examples can be run
sequentially to verify each use case:

```bash
# Example 1: start from scratch
django-admin build_app \
  spec/examples/01_simple_crm/django-angular3.json \
  --dry-run

# Example 2: add resource (schema change only; previous project config passed to confirm no-change)
# Note: --previous-project-config path uses a placeholder name pending TODO.md item 1
django-admin build_app \
  spec/examples/02-add-order/django-angular3.json \
  --previous-schema spec/examples/01_simple_crm/schema.yaml \
  --previous-project-config spec/examples/01_simple_crm/simple_crm.project.json \
  --dry-run

# Example 3: breaking change blocked
django-admin build_app \
  spec/examples/03-breaking-change/django-angular3.json \
  --previous-schema spec/examples/01_simple_crm/schema.yaml \
  --dry-run
# Expected: non-zero exit, no plan emitted

# Example 3b: breaking change acknowledged
django-admin build_app \
  spec/examples/03-breaking-change/django-angular3.json \
  --previous-schema spec/examples/01_simple_crm/schema.yaml \
  --acknowledge-breaking \
  --dry-run

# Example 4: config-only change (blocked by TODO.md item 1 — illustrative only)
django-admin build_app \
  spec/examples/04-add-dashboard/django-angular3.json \
  --previous-schema spec/examples/01_simple_crm/schema.yaml \
  --previous-project-config spec/examples/01_simple_crm/simple_crm.project.json \
  --dry-run

# Example 5: combined schema + config (config side blocked by TODO.md item 1 — illustrative only)
django-admin build_app \
  spec/examples/05-combined-change/django-angular3.json \
  --previous-schema spec/examples/02-add-order/schema.yaml \
  --previous-project-config spec/examples/02-add-order/simple_crm.project.json \
  --dry-run

# Example 6: replace resource
django-admin build_app \
  spec/examples/06-replace-resource/django-angular3.json \
  --previous-schema spec/examples/02-add-order/schema.yaml \
  --dry-run
```

---

## Coverage Matrix

| Example | start-from-scratch | add-things | remove-things | replace-things | breaking gate | config-only | combined |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 Simple CRM | ✓ | | | | | | |
| 2 Add Resource | | ✓ | | | | | |
| 3 Breaking Change | | | | | ✓ | | |
| 4 Config Change | | | | | | ✓ | |
| 5 Combined | | ✓ | | | | | ✓ |
| 6 Replace Resource | | ✓ | ✓ | ✓ | | | |
