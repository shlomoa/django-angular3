## Angular Material site generation

**Skill Name**: `ng-site`

### YAML Frontmatter

```yaml
---
name: ng-site
description: Orchestrate Angular Material site generation across app shell, routing, OpenAPI clients, pages, forms, theme, and auth infrastructure
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---
```

### Purpose

The `ng-site` skill coordinates complete Angular Material site generation for an application that already has an Angular workspace and app scaffold available. It acts as an orchestrator across app shell creation, route setup, OpenAPI client generation, page generation, reactive form generation, Material theming, and application-wide auth wiring. Use this skill when the agent needs to build or reshape the overall site structure rather than a single page or form in isolation.

### Inputs

**From invocation context**:
- **`workspacePath`** (string, required): Absolute path to the Angular workspace root
- **`appName`** (string, optional): Angular application name when the workspace contains more than one app and for validation commands
- **`uiSpecPath`** (string, optional): Path to a UI specification directory, typically under `spec/ui/`, used to discover pages, navigation structure, and forms
- **`openapi_source_path`** (string, optional): Path to the OpenAPI source used by `ng-api` for client generation
- **`defaults`** (object, optional): Fallback definitions to use when no UI spec is provided, such as default pages, route prefixes, or auth requirements

### Modes

All skills support three operational modes:

#### Create

Create a complete Angular Material site by orchestrating the existing Angular generation skills in the correct order and then wiring shared site-level infrastructure.

**Input Requirements**:
- `workspacePath` must point to an existing Angular workspace
- `appName` is required when the workspace contains multiple applications
- `uiSpecPath` is optional; when provided it should point at the UI spec root or `spec/ui/`
- `openapi_source_path` is optional; when provided it should resolve to a valid OpenAPI document

**Process (Create Mode)**:

1. **Verify workspace and app exist before orchestration**
   - Confirm `workspacePath` exists and contains `angular.json`
   - Confirm the target Angular application already exists in the workspace
   - If either the workspace or application is missing, stop and instruct the caller to run `ng-workspace` first and then `ng-app`

2. **Read UI spec when provided**
   - If `uiSpecPath` is supplied, read `spec/ui/` (or the supplied equivalent) to determine:
     - top-level pages
     - route structure
     - navigation labels
     - workflow or form-backed screens
   - If no UI spec is provided, derive a minimal default site map from `defaults` or create a small starter set such as `home`, `dashboard`, and one authenticated workflow page

3. **Create the application shell**
   - Create or update `app.component.ts` as the Material site shell
   - Use `MatSidenav`, `MatToolbar`, `MatNavList`, and `RouterOutlet` for the top-level layout
   - Create or update the root route configuration in `app.routes.ts`
   - Ensure the shell exposes a stable place for feature navigation and authenticated child routes

4. **Invoke `ng-api` when an OpenAPI source is available**
   - If `openapi_source_path` is present, pass it through to `ng-api` as `openapi_source_path` and generate or refresh Angular API clients before page or form generation
   - Reuse the generated models and services as the typed foundation for resource-backed pages and forms

5. **Invoke `ng-page` for each site page**
   - For every page discovered from the UI spec, invoke `ng-page` in sequence
   - If no UI spec exists, invoke `ng-page` for the default page set
   - Pass through page type, route path, feature ownership, authentication needs, and navigation metadata

6. **Invoke `ng-reactive-form` for each form definition**
   - For every form discovered in the UI spec, invoke `ng-reactive-form`
   - Prefer generated OpenAPI models when available
   - Attach generated forms to the relevant workflow or detail pages after form generation completes

7. **Set up the Material theme in `styles.scss`**
   - Create or update the application `styles.scss` file with Angular Material theme setup
   - Ensure the site-level styles cover shell layout, sidenav sizing, toolbar spacing, and global typography

8. **Set up `AuthGuard` in `core/guards/`**
   - Create or update `core/guards/auth.guard.ts`
   - Use the guard for authenticated routes discovered from the UI spec or required by defaults
   - Register guard references in the root or feature route tree as needed

9. **Set up an HTTP interceptor in `core/interceptors/` for CSRF**
   - Create or update a CSRF-focused interceptor under `core/interceptors/`
   - Register it in the app-wide HTTP client configuration
   - Ensure generated API traffic and reactive form submissions use the shared CSRF handling path

10. **Compile verification**
    - Run a full compile check after orchestration completes
    - Confirm the site shell, routing, generated pages, generated forms, auth guard, interceptor, and theme wiring build cleanly together

**Output**:
- Site-level `app.component.ts` shell with `MatSidenav` layout
- Root route configuration wired for generated pages and auth protection
- Generated OpenAPI clients when `openapi_source_path` is provided
- Generated Angular Material pages for each discovered or default page
- Generated reactive forms for each discovered form definition
- Global Material theme in `styles.scss`
- `AuthGuard` under `core/guards/`
- CSRF HTTP interceptor under `core/interceptors/`

#### Modify

Update an existing Angular Material site without regenerating the entire application.

**Supported Modification Variants**:
- **Theme** — update Material palettes, typography, density, or global shell styles in `styles.scss`
- **Navigation** — update `MatSidenav` items, labels, grouping, or top-level layout behavior in `app.component.ts`
- **Routing** — add, remove, reorder, or protect routes in the root route configuration and connected feature routes
- **Auth** — update `AuthGuard` behavior, route protection coverage, or CSRF interceptor registration

**Process**:
1. Identify the requested modification variant: `theme`, `navigation`, `routing`, or `auth`
2. Read the current app shell, root routes, styles, guard, and interceptor files
3. Apply only the requested site-level modification:
   - `theme`: update the Material theme definition and global layout styling
   - `navigation`: update sidenav structure, nav labels, route bindings, or shell responsiveness
   - `routing`: update root route composition, lazy route entries, redirects, and guard references
   - `auth`: update `AuthGuard`, protected route coverage, and CSRF interceptor/provider wiring
4. Re-run compile validation and a dry-run build

**Output**:
- Updated site-level shell, routes, theme, and/or auth infrastructure
- Change summary showing which site-wide concern was modified

#### Delete

Remove the Angular application that owns the generated site from the workspace.

**Input Requirements**:
- Existing `workspacePath`
- Existing `appName`
- Explicit confirmation before removal

**Process**:
1. Confirm the target application exists in the workspace
2. Remove the site by invoking the equivalent `ng-app` delete flow for the application
3. Remove site-level files that are unique to the app, including shell, routes, theme, guards, and interceptors if they are not shared elsewhere
4. Confirm the workspace remains valid after app removal

**Output**:
- Angular application removed from the workspace
- Site-specific shell, route, theme, and auth artifacts removed with the app

### Context Files

{{context:../../shared/angular-conventions.md}}
{{context:../../shared/angular-material-patterns.md}}
{{context:../../shared/openapi-integration.md}}

### Supporting Files

- `templates/app-shell.ts.tpl` — Root site shell template used for `app.component.ts` generation with `MatSidenav` layout
- `context/angular-conventions.md` — Angular standalone application and DI conventions for app shell and route orchestration
- `context/angular-material-patterns.md` — Material sidenav, toolbar, navigation, and theme guidance used by the generated site shell
- `context/openapi-integration.md` — OpenAPI client generation and usage guidance for `ng-api`-driven pages and forms

### Validation

**Post-Create/Modify/Delete Validation**:

1. **Full compile**:
   ```bash
   ng build <appName> --configuration=development
   ```
   - Confirm the complete generated site compiles successfully

2. **Dry-run build**:
   ```bash
   django-angular3 ng_build django-angular3.json --dry-run
   ```
   - Confirm the dry-run build preview is valid without executing a full deployment build

3. **Manual route review**:
   - Confirm the app shell exposes the expected navigation structure
   - Confirm authenticated routes reference `AuthGuard`
   - Confirm forms and API-backed pages are reachable from the generated route tree

### Error Handling

**Common Errors**:

1. **Workspace or app missing**:
   - Resolution: run `ng-workspace` first, then `ng-app`, before invoking `ng-site`

2. **UI spec missing or incomplete**:
   - Resolution: fall back to defaults or stop and request a valid `spec/ui/` source when page/form inference is required

3. **OpenAPI source unavailable**:
   - Resolution: skip `ng-api` orchestration when no OpenAPI source is provided, or request a valid source path before generating resource-backed pages/forms

4. **Dependent page or form skill unavailable**:
   - Resolution: ensure `ng-page` and `ng-reactive-form` are available before site orchestration, then retry the failed step

5. **Auth or interceptor wiring fails compile validation**:
   - Resolution: review route guard imports, HTTP provider registration, and CSRF header handling before rerunning validation

### Dependencies

**Required Skills**:

1. **ng-workspace** — Angular workspace must exist before site orchestration starts
2. **ng-app** — Target Angular application must already exist so the site shell has a home

**Orchestrated Skills**:

- **ng-api** — Generates OpenAPI clients when `openapi_source_path` is provided
- **ng-page** — Generates each page discovered from the UI spec or defaults
- **ng-reactive-form** — Generates each form discovered from the UI spec

**Common Supporting Skills**:

- **ng-complex-component** — Useful when generated pages need richer reusable widgets inside dashboards or workflows

### Examples

**Example 1: Create a site from UI spec and OpenAPI**

```json
{
  "workspacePath": "/workspace/admin-portal",
  "appName": "admin-portal",
  "uiSpecPath": "spec/ui/",
  "openapi_source_path": "spec/openapi.yaml"
}
```

**Process**:
1. Verify the workspace and app already exist
2. Read `spec/ui/` to discover pages and forms
3. Create the Material app shell and root routes
4. Invoke `ng-api`
5. Invoke `ng-page` for each discovered page
6. Invoke `ng-reactive-form` for each discovered form
7. Wire theme, `AuthGuard`, CSRF interceptor, and compile validation

**Example 2: Modify site navigation**

```json
{
  "workspacePath": "/workspace/admin-portal",
  "appName": "admin-portal",
  "change": "navigation"
}
```

**Process**:
1. Read the existing app shell and root route tree
2. Update the `MatSidenav` navigation entries and bindings
3. Re-run compile validation and dry-run build

---

