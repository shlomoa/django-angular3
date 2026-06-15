## Angular Material page generation

**Skill Name**: `angular-page-composition`

### YAML Frontmatter

```yaml
---
name: angular-page-composition
description: Create, modify, or delete Angular Material pages with lazy standalone routing, sidenav navigation, and authenticated route guard support
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

The `angular-page-composition` skill manages top-level Angular Material pages inside an existing feature area. It covers page scaffolding, route registration, optional sidenav navigation, and page-specific layout patterns for common application screens. Use this skill after the Angular workspace and app exist, and after supporting skills such as data services, shared components, and reactive forms are available when the requested page depends on them.

### Inputs

**From invocation context**:
- **`pageName`** (string, required): Page component name in kebab-case (for example `users-list`, `order-detail`, `team-dashboard`)
- **`routePath`** (string, required): Route path segment to register in the feature route file (for example `users`, `orders/:id`, `dashboard`)
- **`pageType`** (enum, required): Page type (`list` | `detail` | `dashboard` | `workflow`)
- **`featureName`** (string, required): Feature area that owns the route and page files (for example `users`, `orders`, `admin`)
- **`appName`** (string, optional): Angular application name used when the workspace contains more than one application and for compile validation commands

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular Material page from scratch, register it in the feature route tree, and wire navigation when the page is top-level.

**Input Requirements**:
- `pageName` must be a valid kebab-case component/page identifier
- `routePath` must be valid for the target feature route file
- `pageType` must be one of: `list`, `detail`, `dashboard`, `workflow`
- `featureName` must map to an existing feature directory

**Pre-flight Checks**:
1. Verify the feature route file exists
2. Verify a page with the same name does not already exist
3. Verify required supporting skills exist for the requested page type:
   - `list`/`detail`: data service available if page is resource-backed
   - `workflow`: reactive form support available for form steps
4. Identify whether the page is top-level and should appear in the sidenav
5. Identify whether the page requires authentication and a `CanActivate` guard reference

**Process (Create Mode)**:

1. **Create the standalone page component** in the feature page directory using the appropriate template files.
2. **Generate the page layout based on `pageType`**:

   ##### Type: List

   Create a resource list page using:
   - `MatTable` for rows and displayed columns
   - `MatPaginator` for pagination
   - `MatSort` for sortable column headers
   - `MatProgressBar` for loading state
   - Row click navigation to the matching detail page
   - A `"New"` button that routes to the create form/workflow page

   ##### Type: Detail

   Create a single-resource detail page using:
   - `MatCard` layout for the record summary and sections
   - Read-only presentation of one resource
   - Edit and delete actions in the card action area

   ##### Type: Dashboard

   Create a summary dashboard using:
   - A responsive grid of `MatCard` widgets
   - Summary metrics, shortcuts, or status blocks per card

   ##### Type: Workflow

   Create a multi-step workflow page using:
   - `MatStepper` for sequential workflow steps
   - Reactive form step components or inline reactive form groups for each step
   - Next/back/submit actions aligned to the stepper flow

3. **Register the feature route**:
   - Add a lazy standalone route entry in the feature route file
   - Use `loadComponent` rather than eager imports
   - Example:
     ```typescript
     {
       path: '<routePath>',
       loadComponent: () =>
         import('./pages/<pageName>/<pageName>.component').then(
           (m) => m.<PageName>Component
         ),
       canActivate: [authGuard],
     }
     ```
   - Add the `CanActivate` guard reference when the page is authenticated

4. **Update sidenav navigation**:
   - If the page is top-level, add a `MatNavList` item in the app or feature sidenav
   - Link the nav item to the new route

5. **Report generated artifacts**:
   - `<feature>/pages/<pageName>/<pageName>.component.ts`
   - `<feature>/pages/<pageName>/<pageName>.component.html`
   - Route entry added to the feature route file
   - Sidenav item added when applicable

**Output**:
- New standalone page component registered with `loadComponent`
- Page layout matching the requested Angular Material page type
- Optional authenticated route guard reference
- Optional top-level sidenav navigation item

#### Modify

Update an existing page to change its visible structure or route protection without rebuilding the feature from scratch.

**Supported Modifications**:
- Add or remove table columns on `list` pages
- Change the applied `CanActivate` guard for authenticated pages
- Update the page layout (for example card sections, widget arrangement, step content)

**Process**:
1. Locate the existing page component and its feature route entry
2. Apply the requested page-specific layout change:
   - `list`: add/remove displayed columns, update table header/cell definitions
   - `detail`: adjust `MatCard` sections or action placement
   - `dashboard`: update card grid composition
   - `workflow`: update step order, form step wiring, or button flow
3. Update the route definition if the guard changes
4. Update sidenav metadata if navigation label or visibility changes
5. Re-run compile validation

**Output**:
- Updated page component files
- Updated feature route definition when required
- Updated navigation entry when required

#### Delete

Remove a page and clean up routing and navigation references.

**Input Requirements**:
- Existing `pageName`
- Existing `featureName`
- Explicit confirmation before removal

**Process**:
1. Remove the standalone page component files
2. Remove the matching route from the feature route file
3. Remove the `MatNavList` item when the page is top-level
4. Check for remaining references from related pages (for example list-to-detail links)
5. Re-run compile validation

**Output**:
- Removed page component
- Removed route registration
- Removed sidenav navigation item when applicable

### Context Files

{{context:../../shared/angular-material-patterns.md}}

Context references use the document's `{{context:...}}` inclusion syntax and follow the same relative skill-path convention used by the other sections in this document. For example, `../../shared/angular-material-patterns.md` resolves to the shared `angular-material-patterns.md` context file in the sibling `shared/` skill context area.

### Supporting Files

- `templates/list-page.ts.tpl` — Standalone Angular Material list-page TypeScript scaffold
- `templates/list-page.html.tpl` — Angular Material list-page template with table and loading state
- `context/angular-material-patterns.md` — Repo-facing supporting-file label for the same shared Material context referenced above via `{{context:../../shared/angular-material-patterns.md}}`

List-page templates act as the canonical scaffold for page generation. Detail, dashboard, and workflow pages are fully supported by the mode definitions above. Those non-list page types are generated from the documented mode rules and shared context even when dedicated template files are not listed separately in this section.

### Validation

**Post-Create/Modify/Delete Validation**:

1. **Route reachable**:
   - Start or inspect the application route tree and confirm the new or modified route is registered correctly
   - For lazy routes, verify `loadComponent` points at the generated standalone page component

2. **Compile check**:
   ```bash
   ng build <appName> --configuration=development
   ```
   - Confirm the page component, route file, and optional sidenav changes compile without errors

### Error Handling

**Common Errors**:

1. **Feature route file not found**:
   - Resolution: create or identify the owning feature route file before generating the page

2. **Authenticated page missing guard reference**:
   - Resolution: import and register the correct `CanActivate` guard in the route entry

3. **Workflow page missing reactive form dependencies**:
   - Resolution: run the `angular-reactive-form-composition` skill first for the required step forms (see Dependencies below), then retry page generation

### Dependencies

**Required Skills**:

1. **ng-workspace** — Workspace and Angular Material foundation must exist
2. **ng-app** — Application shell and route structure must exist

**Common Upstream Skills**:

- **ng-data-service** — Needed for resource-backed list/detail pages
- **ng-component** — Useful for reusable dashboard widgets and nested page content
- **ng-reactive-form** — Needed for workflow steps and create/edit form flows

### Examples

**Example 1: Create a top-level users list page**

```json
{
  "pageName": "users-list",
  "routePath": "users",
  "pageType": "list",
  "featureName": "users"
}
```

**Process**:
1. Create a standalone list page with `MatTable`, `MatPaginator`, `MatSort`, and `MatProgressBar`
2. Add row-click navigation to the user detail route
3. Add a `"New"` button to route to the create workflow/form
4. Register the page in the users feature routes with `loadComponent`
5. Add a `MatNavList` item because the page is top-level

**Example 2: Create an authenticated workflow page**

```json
{
  "pageName": "order-checkout",
  "routePath": "checkout",
  "pageType": "workflow",
  "featureName": "orders"
}
```

**Process**:
1. Create a standalone `MatStepper` page backed by reactive form steps
2. Register the route with `loadComponent`
3. Add `CanActivate` guard reference for authenticated checkout access
4. Validate that the route is reachable and the app still compiles
