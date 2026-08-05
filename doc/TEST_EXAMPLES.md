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
- **Django app name / Angular app name**: `shop` — all twelve examples use the same
  primary app. None of the schema, project-configuration, or OpenUI changes
  replace the app itself; they evolve the generated app within the same `shop`
  app.
- The expected executed command sequence
- The aspect of the solution it demonstrates

Example 1 is bundled in the package under `django_angular3/examples/01_simple_crm/` and
can be installed locally via `django-angular3 install-tutorial`. Future examples follow the
`spec/examples/<example-name>/` convention and can be run via:

```bash
django-admin build_app spec/examples/<example-name>/django-angular3.json \
  [--previous-schema spec/examples/<example-name>/previous-schema.yaml] \
  [--previous-config spec/examples/<example-name>/previous-config.json] \
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

### Input: `app.openui.json`

The non-CRM input is the OpenUI concrete UI document selected by `openui.source`.
It conforms to `openui.schema.json` and uses the vocabulary in `openui.json`
from [shlomoa/openui-spec](https://github.com/shlomoa/openui-spec). Use the
[per-scope examples](https://openui-spec.readthedocs.io/en/latest/examples/)
as the vocabulary reference; the local `spec/openui/app.openui.json` fixture is a
repository example.

### Input: `django-angular3.json`

```json
{
  "project": { "name": "simple_crm" },
  "app": { "name": "shop" },
  "openapi": { "source": "schema.yaml" },
  "openui": { "source": "app.openui.json" },
  "angular": {
    "output": "build/examples/01_simple_crm",
    "workspace": { "packageManager": "pnpm", "style": "scss", "routing": true }
  }
}
```

### Expected ChangeSet

```json
{
  "config": { "type": "start-from-scratch" },
  "schema": { "type": "start-from-scratch" },
  "openui": { "type": "start-from-scratch" }
}
```

### Expected executed command sequence (ordered)

Deterministic TOOL commands (see `GENERATE_AI_AUTOMATIONS.md` §Tool
Contracts Catalog) precede the SKILL sessions:

1. `openapi_schema_export` *(tool)* — produce the current OpenAPI artifact at
   `openapi.source`
2. `validate_openapi_schema` *(tool)* — validate the freshly exported schema
3. `angular_workspace_scaffold` *(tool)* — scaffold the Angular workspace at
   `angular.output`
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
    `APP_BUILDER_REQUIREMENTS.md` FR-10) consuming the structured outputs of
    the TOOL commands above

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
  "config": { "type": "no-change" },
  "schema": {
    "type": "add-things",
    "affected_resources": ["Order"],
    "breaking": false
  },
  "openui": { "type": "no-change" }
}
```

### Expected executed command sequence

Deterministic TOOL commands precede the schema-derived SKILL sessions:

1. `openapi_schema_export` *(tool)* — re-export the schema; archive previous version
2. `validate_openapi_schema` *(tool)* — validate the new schema
3. `oasdiff_diff` *(tool)* — produce the structured diff feeding the
   `ChangeSet` above (`change_type: add-things`, no breaking changes)
4. `angular_api_client_generate` *(tool)* — regenerate the typed Angular API client to
   include the new `Order` endpoints
5. `angular-api-integration` *(skill)* — integrate the regenerated API client (new `Order`
   endpoints)
6. `angular-data-service-composition` *(skill)* — generate data service for `Order`
7. *(verification)* — terminal verification command (per FR-10)

No workspace, app, or existing component steps — they are not affected.

---

## Example 3: Schema Evolution — Breaking Change Blocked

**Demonstrates**: oasdiff breaking-change gate. The builder halts before
executing construction commands. Verifies the `--acknowledge-breaking` bypass.

### Scenario

The `Customer.email` field (previously required, string) is removed from the
schema. oasdiff classifies this as a breaking change.

### Input: `schema.yaml`

Example 1's schema with `email` removed from `Customer.required` and
`Customer.properties`.

### Expected ChangeSet (before gate)

```json
{
  "config": { "type": "no-change" },
  "schema": {
    "type": "breaking",
    "breaking": true,
    "affected_resources": ["Customer"]
  },
  "openui": { "type": "no-change" }
}
```

### Expected builder output

The breaking-change gate is implemented by the `breaking-change` hook
contract (see `GENERATE_AI_AUTOMATIONS.md` §Hook Contracts Catalog), fed by
the `oasdiff_diff` tool contract (see `GENERATE_AI_AUTOMATIONS.md` §Tool
Contracts Catalog). `oasdiff_diff` itself exits zero and returns its
structured `breaking` array; the `breaking-change` `PreToolUse` hook
consumes that output and halts the run (Claude Code: exit `2` to block; `build_app`: breaking-change exit code per FR-4):

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

```json
{
  "project": { "name": "simple_crm" },
  "app": { "name": "shop" },
  "openapi": { "source": "schema.yaml" },
  "openui": { "source": "app.openui.json" },
  "angular": {
    "output": "build/examples/01_simple_crm",
    "workspace": { "packageManager": "pnpm", "style": "css", "routing": true }
  }
}
```

### Input: previous `django-angular3.json`

Example 1's configuration, with `angular.workspace.style` set to `scss`.

### Expected ChangeSet

```json
{
  "config": {
    "type": "modify-things",
    "affected_keys": ["angular.workspace.style"]
  },
  "schema": { "type": "no-change" },
  "openui": { "type": "no-change" }
}
```

### Expected executed command sequence

1. `angular-workspace-foundation` *(modify)* — apply the changed workspace
   style setting through the workspace-modification wrapper
2. *(verification)* — validate the resulting workspace configuration and
   generated application

Schema-derived and OpenUI-derived commands must not run.

---

## Example 5: OpenUI-Source Configuration Change

**Demonstrates**: An `openui.source` configuration change. This is distinct
from a structural change inside an OpenUI document: the `config` lane records
the selected input path, while the `openui` lane compares the selected document
with its own prior `.previous` artifact.

### Scenario

The project changes `openui.source` from `legacy.openui.json` to
`app.openui.json`. The current `app.openui.previous.json` is structurally
identical to `app.openui.json`, so selection changes but no OpenUI-derived
artifact changes are required.

### Expected ChangeSet

```json
{
  "config": {
    "type": "modify-things",
    "affected_keys": ["openui.source"]
  },
  "schema": { "type": "no-change" },
  "openui": { "type": "no-change" }
}
```

### Expected executed command sequence

1. *(verification)* — validate the newly selected OpenUI document and record
   it as the source for subsequent OpenUI comparisons

The builder must not infer a document-tree change solely from a source-path
change. Schema-derived and OpenUI-derived construction commands must not run
when the selected document has no structural diff.

---

## Example 6: OpenUI Change — Add Page (No Schema Change)

**Demonstrates**: OpenUI-only change path. The OpenAPI schema is identical to
Example 1; only OpenUI-derived automation commands run.

### Scenario

A dashboard page is added to `app.openui.json`. No schema change.

### Input: current `app.openui.json`

Example 1's OpenUI document plus `dashboardPage`, `customerSummary`, and
`productSummary` nodes, authored using the vocabulary defined by
[shlomoa/openui-spec](https://github.com/shlomoa/openui-spec).

### Input: previous `app.openui.json`

Example 1's OpenUI document before those nodes were added.

### Expected ChangeSet

```json
{
  "config": { "type": "no-change" },
  "schema": { "type": "no-change" },
  "openui": {
    "type": "add-things",
    "affected_nodes": ["dashboardPage", "customerSummary", "productSummary"]
  }
}
```

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

### Expected ChangeSet

```json
{
  "config": { "type": "no-change" },
  "schema": {
    "type": "add-things",
    "affected_resources": ["Invoice"],
    "breaking": false
  },
  "openui": {
    "type": "add-things",
    "affected_nodes": ["invoiceListPage"]
  }
}
```

### Expected executed command sequence (order matters)

1. `angular-api-integration` — regenerate API client (new `Invoice` endpoints) ← schema step
2. `angular-data-service-composition` — generate `Invoice` data service ← schema step
3. `angular-component-composition` — generate `Invoice` list component ← schema step
4. `angular-page-composition` — generate `invoice-list` page ← OpenUI step (depends on step 3)

---

## Example 8: Full Replacement — Remove Resource, Add Resource

**Demonstrates**: `replace-things` change type. One resource is removed
(`Product`) and one is added (`Supplier`). Remove steps precede add steps at
the same dependency level.

### Expected ChangeSet

```json
{
  "config": { "type": "no-change" },
  "schema": {
    "type": "replace-things",
    "affected_resources": ["Product", "Supplier"],
    "breaking": false
  }
}
```

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

### Expected ChangeSet

```json
{
  "config": { "type": "no-change" },
  "schema": { "type": "no-change" },
  "openui": { "type": "no-change" }
}
```

### Expected executed command sequence

1. *(verification)* — validate the configured inputs and confirm the existing
   generated app remains valid

No construction command may run.

---

## Example 10: Combined Project-Configuration and OpenAPI Change

**Demonstrates**: A configuration modification and an OpenAPI change in the
same run, without an OpenUI document change.

### Scenario

Starting from Example 1, the project changes `angular.workspace.style` from
`scss` to `css` and adds the `Order` resource to the OpenAPI schema. The
OpenUI document is unchanged.

### Expected ChangeSet

```json
{
  "config": {
    "type": "modify-things",
    "affected_keys": ["angular.workspace.style"]
  },
  "schema": {
    "type": "add-things",
    "affected_resources": ["Order"],
    "breaking": false
  },
  "openui": { "type": "no-change" }
}
```

### Expected executed command sequence

1. `angular-workspace-foundation` *(modify)* — apply the changed workspace
   style setting
2. `angular-api-integration` *(modify)* — regenerate the API client for
   `Order`
3. `angular-data-service-composition` *(create)* — generate the `Order` data
   service
4. *(verification)* — validate the workspace and generated application

OpenUI-derived construction commands must not run.

---

## Example 11: Combined Project-Configuration and OpenUI Change

**Demonstrates**: A configuration modification and a structural OpenUI change
in the same run, without an OpenAPI change.

### Scenario

Starting from Example 1, the project changes `angular.workspace.style` from
`scss` to `css` and adds `dashboardPage`, `customerSummary`, and
`productSummary` to `app.openui.json`. The OpenAPI schema is unchanged.

### Expected ChangeSet

```json
{
  "config": {
    "type": "modify-things",
    "affected_keys": ["angular.workspace.style"]
  },
  "schema": { "type": "no-change" },
  "openui": {
    "type": "add-things",
    "affected_nodes": ["dashboardPage", "customerSummary", "productSummary"]
  }
}
```

### Expected executed command sequence

1. `angular-workspace-foundation` *(modify)* — apply the changed workspace
   style setting
2. `angular-field-component-composition` *(create)* — generate
   `customer-summary`
3. `angular-field-component-composition` *(create)* — generate
   `product-summary`
4. `angular-page-composition` *(create)* — generate the `dashboard` page
5. *(verification)* — validate the workspace and generated application

Schema-derived construction commands must not run.

---

## Example 12: Combined Project-Configuration, OpenAPI, and OpenUI Change

**Demonstrates**: All three independent change lanes active in one run.

### Scenario

Starting from Example 2, the project changes `angular.workspace.style` from
`scss` to `css`, adds the `Invoice` resource to the OpenAPI schema, and adds an
`invoiceListPage` node to `app.openui.json`.

### Expected ChangeSet

```json
{
  "config": {
    "type": "modify-things",
    "affected_keys": ["angular.workspace.style"]
  },
  "schema": {
    "type": "add-things",
    "affected_resources": ["Invoice"],
    "breaking": false
  },
  "openui": {
    "type": "add-things",
    "affected_nodes": ["invoiceListPage"]
  }
}
```

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

The configuration command runs before dependent construction. Schema-derived
commands run before the dependent OpenUI page command.

---

## Running the Examples

Once the `build_app` command is implemented, all examples can be run
sequentially to verify each use case:

```bash
# Example 1: start from scratch
django-admin build_app \
  django_angular3/examples/01_simple_crm/django-angular3.json \
  --dry-run

# Example 2: add resource (schema change only)
django-admin build_app \
  spec/examples/02-add-order/django-angular3.json \
  --previous-schema django_angular3/examples/01_simple_crm/schema.yaml \
  --previous-config django_angular3/examples/01_simple_crm/django-angular3.json \
  --dry-run

# Example 3: breaking change blocked
django-admin build_app \
  spec/examples/03-breaking-change/django-angular3.json \
  --previous-schema django_angular3/examples/01_simple_crm/schema.yaml \
  --dry-run
# Expected: non-zero exit; no construction command executes

# Example 3b: breaking change acknowledged
django-admin build_app \
  spec/examples/03-breaking-change/django-angular3.json \
  --previous-schema django_angular3/examples/01_simple_crm/schema.yaml \
  --acknowledge-breaking \
  --dry-run

# Example 4: project-configuration-only change
django-admin build_app \
  spec/examples/04-workspace-style/django-angular3.json \
  --previous-schema django_angular3/examples/01_simple_crm/schema.yaml \
  --previous-config django_angular3/examples/01_simple_crm/django-angular3.json \
  --dry-run

# Example 5: OpenUI-source configuration change
django-admin build_app \
  spec/examples/05-openui-source/django-angular3.json \
  --previous-schema django_angular3/examples/01_simple_crm/schema.yaml \
  --previous-config django_angular3/examples/01_simple_crm/django-angular3.json \
  --dry-run

# Example 6: OpenUI-only document change (illustrative until OpenUI diffing is implemented)
django-admin build_app \
  spec/examples/06-add-dashboard/django-angular3.json \
  --previous-schema django_angular3/examples/01_simple_crm/schema.yaml \
  --previous-openui django_angular3/examples/01_simple_crm/app.openui.json \
  --dry-run

# Example 7: combined schema + OpenUI (OpenUI side illustrative until diffing is implemented)
django-admin build_app \
  spec/examples/07-combined-change/django-angular3.json \
  --previous-schema spec/examples/02-add-order/schema.yaml \
  --previous-openui spec/examples/02-add-order/app.openui.json \
  --dry-run

# Example 8: replace resource
django-admin build_app \
  spec/examples/08-replace-resource/django-angular3.json \
  --previous-schema spec/examples/02-add-order/schema.yaml \
  --dry-run

# Examples 9–12: use the corresponding prior inputs for the three-lane matrix
# cases. The scenario fixtures are pending implementation.
```

---

## Three-Lane Change Matrix

The following matrix covers every Boolean combination of incremental changes
in the `config`, `schema`, and `openui` lanes. A check mark means the lane has
a change; a blank means `no-change`. Examples 1, 3, 5, and 8 provide
additional coverage for first-run, breaking, source-selection, and replacement
semantics respectively.

| Config change | OpenAPI change | OpenUI change | Required example |
|:---:|:---:|:---:|---|
| | | | 9 No Change |
| ✓ | | | 4 Workspace Configuration |
| | ✓ | | 2 Add Resource |
| | | ✓ | 6 OpenUI Change |
| ✓ | ✓ | | 10 Configuration + OpenAPI |
| ✓ | | ✓ | 11 Configuration + OpenUI |
| | ✓ | ✓ | 7 OpenAPI + OpenUI |
| ✓ | ✓ | ✓ | 12 Configuration + OpenAPI + OpenUI |

### Additional scenario coverage

| Concern | Example |
|---|---|
| Start from scratch | 1 Simple CRM |
| Breaking OpenAPI change | 3 Breaking Change |
| `openui.source` selection without structural OpenUI change | 5 OpenUI-Source Configuration |
| OpenAPI replacement | 8 Full Replacement |
