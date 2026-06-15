## Angular Material app boiler plate

```yaml
---
name: angular-app-composition
description: Manage Angular Material application within a workspace - create app structure with Material theme, modify providers and routing, or delete app
when_to_use: Use when build_app dispatches an app-creation, app-modification, or app-deletion procedure node, or when a user runs /angular-app-composition to scaffold or update an Angular Material application inside an existing workspace.
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

Generate and manage Angular Material applications within an existing Angular workspace. This skill creates a complete application scaffold with Material Design theming, standalone component architecture, proper directory structure, and routing configuration. Use this skill after the workspace has been created but before generating individual components or pages.

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular Material application inside the workspace with complete directory structure, theme configuration, and standalone bootstrap setup.

**Input Requirements** (all from `django-angular3.json`):
- `project.name` (required): Name of the application
- `angular.output` (required): Absolute path to the Angular workspace root directory
- `angular.workspace.prefix` (optional): Component selector prefix (defaults to `app`)
- `angular.workspace.routing` (optional): Whether to include routing configuration (defaults to `true`)

Note: `standalone: true` is a fixed Angular convention and is not configurable.

**Process**:

1. **Validate workspace exists**
   - Check that `angular.output` exists and contains `angular.json`
   - Verify workspace is initialized and valid
   - Confirm `project.name` doesn't already exist in workspace

2. **Generate application scaffold via djng wrapper**:
   ```bash
   django-admin ng_gen_app django-angular3.json --dry-run
   ```
   When `ng_gen_app` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_gen_app django-angular3.json
   ```

   > **Note**: `ng_gen_app` is not in `command_allowlist` by default. See `django_angular3/settings.py`.

3. **Create standard directory structure**
   - Create `projects/<project.name>/src/app/core/` - Core services and guards
   - Create `projects/<project.name>/src/app/shared/components/` - Shared components
   - Create `projects/<project.name>/src/app/shared/pipes/` - Shared pipes
   - Create `projects/<project.name>/src/app/features/` - Feature modules/routes
   - Create barrel exports (`index.ts`) in each directory

4. **Wire Angular Material theme**
   - Angular Material is already installed at the workspace level by `angular-workspace-foundation`.
   - Update `projects/<project.name>/src/styles.scss` with app-level theme configuration using Edit tool:
     ```scss
     @use '@angular/material' as mat;
     @include mat.core();

     $primary: mat.define-palette(mat.$indigo-palette);
     $accent: mat.define-palette(mat.$pink-palette, A200, A100, A400);
     $warn: mat.define-palette(mat.$red-palette);

     $theme: mat.define-light-theme((
       color: (
         primary: $primary,
         accent: $accent,
         warn: $warn,
       ),
       typography: mat.define-typography-config(),
       density: 0,
     ));

     @include mat.all-component-themes($theme);

     html, body { height: 100%; }
     body { margin: 0; font-family: Roboto, "Helvetica Neue", sans-serif; }
     ```

5. **Set up standalone bootstrap configuration**
   - Create/update `projects/<project.name>/src/app/app.config.ts`:
     ```typescript
     import { ApplicationConfig } from '@angular/core';
     import { provideRouter } from '@angular/router';
     import { provideAnimations } from '@angular/platform-browser/animations';
     import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
     import { routes } from './app.routes';

     export const appConfig: ApplicationConfig = {
       providers: [
         provideRouter(routes),
         provideAnimations(),
         provideHttpClient(withInterceptorsFromDi()),
       ]
     };
     ```

   - Update `projects/<project.name>/src/main.ts` to use standalone bootstrap:
     ```typescript
     import { bootstrapApplication } from '@angular/platform-browser';
     import { AppComponent } from './app/app.component';
     import { appConfig } from './app/app.config';

     bootstrapApplication(AppComponent, appConfig)
       .catch((err) => console.error(err));
     ```

6. **Generate application shell using template**
   - Use `{{template:app-shell.ts}}` to create root `AppComponent`
   - Use `{{template:app-shell.html}}` for component template
   - Replace `{{APP_NAME}}` placeholder with actual app name
   - Create responsive navigation shell with Material sidenav

7. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

**Output**:
- Complete Angular Material application created in `projects/<project.name>/`
- Directory structure with `core/`, `shared/`, `features/` folders
- Material theme configured in `styles.scss`
- Standalone bootstrap with `app.config.ts`
- Application shell with responsive navigation
- Entry added to `angular.json` for the new application

#### Modify

Update an existing Angular Material application with changes to providers, global styles, or routing configuration.

**Input Requirements**:
- `project.name` (from `django-angular3.json`, required): Name of the existing application to modify
- `angular.output` (from `django-angular3.json`, required): Absolute path to the Angular workspace
- `modifications` (from procedure inputs, required): Object describing changes to make:
  - `providers`: Array of provider configurations to add/remove
  - `styles`: CSS/SCSS rules to add to global styles
  - `routes`: Route definitions to register (lazy-loaded or eager)
  - `dependencies`: NPM packages to add/remove

**Process**:

1. **Validate application exists**
   - Verify `projects/<project.name>/` exists
   - Check `angular.json` contains configuration for `<project.name>`
   - Confirm application is using standalone architecture

2. **Update providers in app.config.ts**
   - Read existing `projects/<project.name>/src/app/app.config.ts`
   - Parse provider array
   - Add new providers to the `providers` array:
     ```typescript
     // Example: Adding authentication provider
     import { provideAuth } from './core/auth';

     export const appConfig: ApplicationConfig = {
       providers: [
         // ... existing providers
         provideAuth({ apiUrl: environment.apiUrl }),
       ]
     };
     ```
   - Remove specified providers if requested
   - Maintain formatting and import statements

3. **Update global styles**
   - Read `projects/<project.name>/src/styles.scss`
   - Append new styles to end of file (or update existing theme if modifying theme)
   - Example modifications:
     ```scss
     // Custom utility classes
     .full-width { width: 100%; }
     .center-content { display: flex; justify-content: center; align-items: center; }

     // Custom Material overrides
     .mat-mdc-card { border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
     ```

4. **Register lazy routes**
   - Read `projects/<project.name>/src/app/app.routes.ts`
   - Add new route definitions:
     ```typescript
     import { Routes } from '@angular/router';

     export const routes: Routes = [
       { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
       {
         path: 'dashboard',
         loadComponent: () => import('./features/dashboard/dashboard.component')
           .then(m => m.DashboardComponent)
       },
       // ... new routes added here
     ];
     ```
   - Maintain route ordering and guard configurations

5. **Update dependencies**
   - If `dependencies` specified:
     ```bash
     pnpm install <package>@<version>
     # or
     pnpm uninstall <package>
     ```

6. **Verify compilation**:
   ```bash
   django-admin ng_build django-angular3.json
   ```

**Output**:
- Updated `app.config.ts` with new providers
- Modified `styles.scss` with additional styles or theme changes
- Updated `app.routes.ts` with new route registrations
- Updated `package.json` and `node_modules` if dependencies changed
- Confirmation of successful modification with list of changes made

#### Delete

Remove an Angular Material application completely from the workspace, including all source files and configuration.

**Input Requirements** (all from `django-angular3.json`):
- `project.name` (required): Name of the application to delete
- `angular.output` (required): Absolute path to the Angular workspace

**Process**:

1. **Validate application exists**
   - Verify `<angular.output>/projects/<project.name>/` exists
   - Check `angular.json` contains configuration for `<project.name>`
   - Confirm no other applications depend on this one

2. **Remove application directory** using Bash tool:
   ```bash
   rm -rf <angular.output>/projects/<project.name>
   ```

3. **Update `angular.json`** using Read and Edit tools:
   - Remove entry from `projects` object for `<project.name>`
   - Remove any build configurations, serve targets, and test targets
   - Update default project if this was the default

4. **Clean up dependencies (optional)**:
   - Check if Angular Material is used by other apps
   - If this was the only app using Material, optionally remove:
     ```bash
     pnpm uninstall @angular/material @angular/cdk
     ```

5. **Verify workspace integrity**: Read `angular.json` and confirm it is valid JSON with no remaining references to `<project.name>`.

**Output**:
- Application directory `projects/<project.name>/` removed
- Entry removed from `angular.json`
- Workspace remains valid and functional
- Confirmation message listing what was deleted

### Context Files

{{context:../../shared/angular-conventions.md}}

{{context:../../shared/angular-material-patterns.md}}

### Templates

- `app-shell.ts.tpl` — Root AppComponent with Material sidenav navigation shell, responsive breakpoint handling, and routing outlet
- `app-shell.html.tpl` — MatSidenav container template with toolbar, navigation list, and content area
- `app.config.ts.tpl` — Standalone application configuration with standard providers (router, animations, HTTP client)
- `app.routes.ts.tpl` — Initial route configuration with empty routes array and typed Routes import

### Validation

Steps to validate successful execution of the skill:

1. **Verify directory structure**
   ```bash
   ls -la projects/<project.name>/src/app/
   # Should contain: core/, shared/, features/, app.component.ts, app.config.ts, app.routes.ts
   ```

2. **Verify Material theme is wired**
   ```bash
   cat projects/<project.name>/src/styles.scss | grep "@angular/material"
   # Should contain Material theme imports and configuration
   ```

3. **Verify standalone bootstrap**
   ```bash
   cat projects/<project.name>/src/main.ts | grep "bootstrapApplication"
   # Should use bootstrapApplication() not platformBrowserDynamic()
   ```

4. **Compile check**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   Expected: Build completes without errors

5. **Serve and verify**:
   ```bash
   pnpm exec ng serve <project.name>
   ```
   Navigate to `http://localhost:4200` and verify Material components render

### Error Handling

Common errors and their resolution strategies:

**Error**: Application with name `<project.name>` already exists
- **Cause**: Attempting to create an app with a name that's already in use
- **Resolution**: Use Delete mode first, or choose a different app name

**Error**: `Workspace path does not contain angular.json`
- **Cause**: Invalid workspace path or workspace not initialized
- **Resolution**: Verify workspace path is correct; if needed, run workspace creation skill first

**Error**: `Cannot find module '@angular/material'`
- **Cause**: Angular Material not installed or installation failed
- **Resolution**: Run `django-admin ng_add django-angular3.json` to install Material at workspace level

**Error**: `Compilation failed: Cannot find module './app/app.config'`
- **Cause**: Standalone bootstrap not properly configured
- **Resolution**: Verify `app.config.ts` exists and is properly imported in `main.ts`

**Error**: `SCSS compilation failed`
- **Cause**: Invalid SCSS syntax in theme configuration
- **Resolution**: Validate SCSS syntax in `styles.scss`; ensure `@use` statements are at the top

**Error**: `Port 4200 is already in use`
- **Cause**: Another application is already running on default port
- **Resolution**: Stop other dev servers or use `pnpm exec ng serve <project.name> --port=4201`

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1) — Workspace must exist before creating an application within it
2. **Node.js and npm** — Required to run Angular CLI commands
3. **Angular CLI** — Must be installed globally or in workspace (`@angular/cli`)

Optional dependencies:

- If using OpenAPI integration, **Angular API generation** (Skill 3) should be executed after app creation
### Examples

**Example 1: Create a new admin dashboard application**

```typescript
// Inputs from django-angular3.json:
//   project.name = "admin-dashboard"
//   angular.output = "/workspace/my-project"
// Procedure-level: prefix = "admin"

// Executes:
// 1. django-admin ng_gen_app django-angular3.json
// 2. Creates core/, shared/, features/ directories
// 3. Configures theme in projects/admin-dashboard/src/styles.scss
// 4. Sets up app.config.ts with providers
// 5. Generates responsive nav shell from app-shell templates
// 6. django-admin ng_build django-angular3.json

// Output: Application ready at projects/admin-dashboard/
```

**Example 2: Modify existing app to add authentication provider**

```typescript
// Inputs from django-angular3.json:
//   project.name = "admin-dashboard"
//   angular.output = "/workspace/my-project"
// Procedure-level: add provideAuth provider + styles

// Executes:
// 1. Reads projects/admin-dashboard/src/app/app.config.ts
// 2. Adds import: import { provideAuth } from './core/auth';
// 3. Adds to providers: provideAuth({ apiUrl: 'https://api.example.com' })
// 4. Appends custom styles to projects/admin-dashboard/src/styles.scss
// 5. django-admin ng_build django-angular3.json

// Output: Updated app.config.ts and styles.scss
```

**Example 3: Register lazy-loaded feature route**

```typescript
// Inputs from django-angular3.json:
//   project.name = "admin-dashboard"
//   angular.output = "/workspace/my-project"

// Executes:
// 1. Reads projects/admin-dashboard/src/app/app.routes.ts
// 2. Adds new route definition to routes array
// 3. django-admin ng_build django-angular3.json

// Output: Updated app.routes.ts with new lazy route
```

**Example 4: Delete an application**

```typescript
// Inputs from django-angular3.json:
//   project.name = "old-admin"
//   angular.output = "/workspace/my-project"
// Procedure-level: confirm = true

// Executes:
// 1. Verifies projects/old-admin/ exists
// 2. Removes: rm -rf projects/old-admin
// 3. Updates angular.json to remove "old-admin" project entry

// Output: Application "old-admin" removed from workspace
```
