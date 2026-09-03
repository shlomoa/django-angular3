# Test Examples

## Overview

Each example defines a concrete end-to-end `build_app` scenario and its
expected outcomes. Together they cover the full range of use cases described
in [APP_BUILDER_REQUIREMENTS.md].

Every example conforms to [TEST_SCENARIO_CONTRACTS.md]. Input blocks are
concrete contract instances, and expected atomic changes and command sequences
are test oracles; this document does not define schemas, operations, domains,
command modes, or automation identities.

The exact suite layout, shared fixture conventions, invocation model, static
snapshots, provider-adapter boundary, and coverage axes are defined in
[TEST_SCENARIO_SPECIFICATIONS.md]. Project-configuration discovery and baseline
resolution are defined in [SPECIFICATIONS.md] §2.2. The examples below retain
only scenario inputs and expected outcomes.

Automation sequencing is owned by the [Automation Plan]. Scenario-test work
and acceptance coverage are owned by the [Verification Plan]; this document
contains no planning tasks.

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

### Input: `app.openui.json`

The OpenUI input is the OpenUI concrete UI document selected by
`artifacts.openuiSpecification`.
Its role, grammar, and catalog relationship are defined by the
[OpenUI artifact-role SSOT](https://github.com/shlomoa/openui-spec/blob/main/spec/README.md#specification-artifacts-grammar-vs-catalog). Use the
[per-scope examples](https://openui-spec.readthedocs.io/en/latest/examples/)
as the vocabulary reference; the local
`tests/fixtures/artifacts/openui/example.openui.json` fixture is a repository
example.

### Input: configuration

```json
{
  "project": { "name": "simple_crm" },
  "artifacts": {
    "openapiSchema": "schema.yaml",
    "openuiSpecification": "app.openui.json",
    "angularWorkspace": "build/examples/01_simple_crm"
  }
}
```

The static `django-angular3.json` supplies the separate `djng` tool settings.

### Expected atomic changes

The missing baseline initializes each applicable domain. The builder emits
`create` changes for the candidate static configuration, project configuration,
OpenAPI contract, and OpenUI document.

### Expected executed command sequence (ordered)

Deterministic TOOL commands (see `TOOL_CONTRACTS.md` §Tool
Contracts Catalog) precede the SKILL sessions:

1. `openapi_schema_export` *(tool)* — produce the current OpenAPI artifact at
  `artifacts.openapiSchema`
2. `validate_openapi_schema` *(tool)* — validate the freshly exported schema
3. `angular_workspace_scaffold` *(tool)* — scaffold the Angular workspace at
  `artifacts.angularWorkspace`
4. `angular-workspace-foundation` *(skill)* — apply Angular Material workspace conventions on
   the scaffolded workspace `simple_crm`
5. `angular_app_scaffold` *(tool)* — add the Angular application `simple_crm` into
   the workspace
6. `angular-app-composition` *(skill)* — finalize the Angular Material application `simple_crm`
7. `angular_api_client_generate` *(tool)* — generate the typed Angular API client from
   `schema.yaml`
8. `angular-api-integration` *(skill)* — integrate the generated API client
9. `angular-data-service-composition` *(skill)* — generate data services for `Customer`,
   `Product`
10. `angular-component-composition` *(skill)* — generate list component for `Customer`
11. `angular-component-composition` *(skill)* — generate detail component for `Customer`
12. `angular-component-composition` *(skill)* — generate list component for `Product`
13. `angular-reactive-form-composition` *(skill)* — generate edit form for `Customer`
14. `angular-page-composition` *(skill)* — generate `customer-list` page
15. `angular-page-composition` *(skill)* — generate `customer-detail` page
16. `angular-page-composition` *(skill)* — generate `product-list` page
17. `angular-site-composition` *(skill)* — assemble site with navigation
18. *(verification)* — terminal verification command (per
    `doc/requirements/APP_BUILDER_REQUIREMENTS.md` FR-10) consuming the
    structured outputs of
    the TOOL commands above

---

## Example 2: Schema Evolution — Add Resource

**Demonstrates**: Incremental schema change. Previous state is Example 1.
Only new-resource skills run; existing workspace, app, and components are
untouched. The OpenAPI domain emits `create` changes for the new contract
subjects.

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

### Expected atomic changes

The OpenAPI domain emits `create` changes for the `Order` paths, operations,
and component schema. No other domain emits an atomic change.

### Expected executed command sequence

Deterministic TOOL commands precede the schema-derived SKILL sessions:

1. `openapi_schema_export` *(tool)* — re-export the schema; archive previous version
2. `validate_openapi_schema` *(tool)* — validate the new schema
3. `oasdiff_diff` *(tool)* — produce the structured diff evidence used to
  derive the OpenAPI `create` changes
4. `angular_api_client_generate` *(tool)* — regenerate the typed Angular API client to
   include the new `Order` endpoints
5. `angular-api-integration` *(skill)* — integrate the regenerated API client (new `Order`
   endpoints)
6. `angular-data-service-composition` *(skill)* — generate data service for `Order`
7. *(verification)* — terminal verification command (per FR-10)

No workspace, app, or existing component steps — they are not affected.

---

## Example 3: Schema Evolution — Removal

**Demonstrates**: incremental removal of a schema property and the dependent
construction commands it selects.

### Scenario

The `Customer.email` field (previously required, string) is removed from the
schema.

### Input: `schema.yaml`

Example 1's schema with `email` removed from `Customer.required` and
`Customer.properties`.

### Expected atomic changes

The OpenAPI domain emits `delete` changes for `Customer.email` and its
membership in the schema's `required` array. No other domain emits an atomic
change.

### Expected executed command sequence

The `oasdiff_diff` tool produces the report used for the ChangeSet. The
builder then executes the commands selected for the removed field:

1. `angular-api-integration` — regenerate API client
2. `angular-data-service-composition` — update `Customer` data service
3. `angular-reactive-form-composition` — update customer edit form (remove `email` field)
4. `angular-component-composition` — update customer detail component (remove `email` display)

---

## Example 4: Project-Configuration Change — Modify Workspace Style

**Demonstrates**: Project-configuration-only change path. The OpenAPI schema
and OpenUI document are unchanged; only project-level workspace configuration
is modified.

### Scenario

The project changes `angular.workspace.style` from `scss` to `css`. The
project name and output root remain unchanged, so this is a configuration
modification rather than a project replacement.

### Input: current `django-angular3.json`

The canonical static tool configuration from `SPECIFICATIONS.md` §2.1, with
`angular.workspace.style` set to `css`.

### Input: previous `django-angular3.json`

Example 1's configuration, with `angular.workspace.style` set to `scss`.

### Expected atomic changes

The `static_config` domain emits an `update` change for
`/angular/workspace/style`. No other domain emits an atomic change.

### Expected executed command sequence

1. `angular-workspace-foundation` *(modify)* — apply the changed workspace
   style setting through the workspace-modification wrapper
2. *(verification)* — validate the resulting workspace configuration and
   generated application

The expected sequence contains no schema-derived or OpenUI-derived command.

---

## Example 5: OpenUI-Source Configuration Change

**Demonstrates**: An `artifacts.openuiSpecification` configuration change. This
is distinct from a structural change inside an OpenUI document: the
`project_config` domain records the selected input path, while the `openui`
domain compares the documents selected by the current and previous project
configurations.

### Scenario

The project changes `artifacts.openuiSpecification` from `base.openui.json` to
`app.openui.json`. The previous configuration's `base.openui.json` is
structurally identical to the current configuration's `app.openui.json`, so
selection changes but no OpenUI-derived artifact changes are required.

### Expected atomic changes

The `project_config` domain emits an `update` change for
`/artifacts/openuiSpecification`. The selected OpenUI documents are identical,
so the `openui` domain emits no atomic change.

### Expected executed command sequence

1. *(verification)* — validate the newly selected OpenUI document and record
   it as the source for subsequent OpenUI comparisons

This expected result applies the selector/content separation defined in
[CHANGE_MODEL_CONTRACTS.md] §2.2 and [SPECIFICATIONS.md] §2.2.

---

## Example 6: OpenUI Change — Add Page (No Schema Change)

**Demonstrates**: OpenUI-only change path. The OpenAPI schema is identical to
Example 1; only OpenUI-derived automation commands run.

### Scenario

A dashboard page is added to `app.openui.json`. No schema change.

### Input: current `app.openui.json`

Example 1's OpenUI document plus `dashboardPage`, `customerSummary`, and
`productSummary` nodes, authored under the
[OpenUI specification](https://github.com/shlomoa/openui-spec/blob/main/spec/README.md).

### Input: previous `app.openui.json`

Example 1's OpenUI document before those nodes were added.

### Expected atomic changes

The `openui` domain emits `create` changes for `dashboardPage`,
`customerSummary`, and `productSummary`. No other domain emits an atomic
change.

### Expected executed command sequence

1. `angular-field-component-composition` — generate `customer-summary` component
2. `angular-field-component-composition` — generate `product-summary` component
3. `angular-page-composition` — generate `dashboard` page

---

## Example 7: Combined Schema and OpenUI Change

**Demonstrates**: Schema and OpenUI change in the same run. Both change paths
activate. Schema-derived commands run before OpenUI-derived commands at the
same dependency level.

### Scenario

Starting from Example 2's state (Customer, Product, Order):
- Schema: a new `Invoice` resource is added.
- OpenUI: a new `invoiceListPage` node is added to `app.openui.json`.

### Expected atomic changes

The `openapi` domain emits `create` changes for the `Invoice` contract
subjects, and the `openui` domain emits a `create` change for
`invoiceListPage`.

### Expected executed command sequence (order matters)

1. `angular-api-integration` — regenerate API client (new `Invoice` endpoints) ← schema step
2. `angular-data-service-composition` — generate `Invoice` data service ← schema step
3. `angular-component-composition` — generate `Invoice` list component ← schema step
4. `angular-page-composition` — generate `invoice-list` page ← OpenUI step (depends on step 3)

---

## Example 8: Full Replacement — Remove Resource, Add Resource

**Demonstrates**: Separate atomic deletion and creation. `Product` is removed
and `Supplier` is added. Delete commands precede create commands at the same
dependency level.

### Expected atomic changes

The `openapi` domain emits `delete` changes for the `Product` contract
subjects and `create` changes for the `Supplier` contract subjects.

### Expected executed command sequence

1. `angular-data-service-composition` — delete `Product` data service
2. `angular-component-composition` — delete `Product` list and detail components
3. `angular-page-composition` — delete `product-list` page
4. `angular-site-composition` — update navigation (remove Products link)
5. `angular-api-integration` — regenerate API client (no Product endpoints; new Supplier endpoints)
6. `angular-data-service-composition` — generate `Supplier` data service
7. `angular-component-composition` — generate `Supplier` list component
8. `angular-page-composition` — generate `supplier-list` page
9. `angular-site-composition` — update navigation (add Suppliers link)

---

## Example 9: No Change

**Demonstrates**: The accepted-state no-op. Current project configuration,
OpenAPI schema, and OpenUI document all match their respective prior inputs.

### Expected atomic changes

No domain emits an atomic change.

### Expected executed command sequence

1. *(verification)* — validate the configured inputs and confirm the existing
   generated app remains valid

The expected sequence contains no construction command.

---

## Example 10: Combined Project-Configuration and OpenAPI Change

**Demonstrates**: A configuration modification and an OpenAPI change in the
same run, without an OpenUI document change.

### Scenario

Starting from Example 1, the project changes `angular.workspace.style` from
`scss` to `css` and adds the `Order` resource to the OpenAPI schema. The
OpenUI document is unchanged.

### Expected atomic changes

The `static_config` domain emits an `update` for
`/angular/workspace/style`, and the `openapi` domain emits `create` changes
for the `Order` contract subjects.

### Expected executed command sequence

1. `angular-workspace-foundation` *(modify)* — apply the changed workspace
   style setting
2. `angular-api-integration` *(modify)* — regenerate the API client for
   `Order`
3. `angular-data-service-composition` *(create)* — generate the `Order` data
   service
4. *(verification)* — validate the workspace and generated application

The expected sequence contains no OpenUI-derived construction command.

---

## Example 11: Combined Project-Configuration and OpenUI Change

**Demonstrates**: A configuration modification and a structural OpenUI change
in the same run, without an OpenAPI change.

### Scenario

Starting from Example 1, the project changes `angular.workspace.style` from
`scss` to `css` and adds `dashboardPage`, `customerSummary`, and
`productSummary` to `app.openui.json`. The OpenAPI schema is unchanged.

### Expected atomic changes

The `static_config` domain emits an `update` for
`/angular/workspace/style`, and the `openui` domain emits `create` changes for
`dashboardPage`, `customerSummary`, and `productSummary`.

### Expected executed command sequence

1. `angular-workspace-foundation` *(modify)* — apply the changed workspace
   style setting
2. `angular-field-component-composition` *(create)* — generate
   `customer-summary`
3. `angular-field-component-composition` *(create)* — generate
   `product-summary`
4. `angular-page-composition` *(create)* — generate the `dashboard` page
5. *(verification)* — validate the workspace and generated application

The expected sequence contains no schema-derived construction command.

---

## Example 12: Combined Project-Configuration, OpenAPI, and OpenUI Change

**Demonstrates**: All three scenario axes active in one run.

### Scenario

Starting from Example 2, the project changes `angular.workspace.style` from
`scss` to `css`, adds the `Invoice` resource to the OpenAPI schema, and adds an
`invoiceListPage` node to `app.openui.json`.

### Expected atomic changes

The `static_config` domain emits an `update` for
`/angular/workspace/style`; the `openapi` domain emits `create` changes for
the `Invoice` contract subjects; and the `openui` domain emits a `create`
change for `invoiceListPage`.

### Expected executed command sequence (order matters)

1. `angular-workspace-foundation` *(modify)* — apply the changed workspace
   style setting
2. `angular-api-integration` *(modify)* — regenerate the API client for
   `Invoice`
3. `angular-data-service-composition` *(create)* — generate the `Invoice`
   data service
4. `angular-component-composition` *(create)* — generate the `Invoice` list
   component
5. `angular-page-composition` *(create)* — generate the `invoice-list` page
6. *(verification)* — validate the workspace and generated application

The expected order demonstrates the dependency and cross-domain ordering in
[APP_BUILDER_REQUIREMENTS.md] §Change Command Translation and Execution.

---

Suite invocation and the required coverage matrix are specified in
[TEST_SCENARIO_SPECIFICATIONS.md] §§3 and 6.

[APP_BUILDER_REQUIREMENTS.md]: requirements/APP_BUILDER_REQUIREMENTS.md
[CHANGE_MODEL_CONTRACTS.md]: contracts/CHANGE_MODEL_CONTRACTS.md
[Automation Plan]: plan/AUTOMATION_PLAN.md#dependency-ordered-implementation-phases
[SPECIFICATIONS.md]: specifications/SPECIFICATIONS.md
[TEST_SCENARIO_SPECIFICATIONS.md]: specifications/TEST_SCENARIO_SPECIFICATIONS.md
[TEST_SCENARIO_CONTRACTS.md]: contracts/TEST_SCENARIO_CONTRACTS.md
[Verification Plan]: plan/VERIFICATION_PLAN.md#scenario-coverage
