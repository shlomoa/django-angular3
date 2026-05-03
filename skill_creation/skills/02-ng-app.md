## Angular Material app boiler plate

```yaml
---
name: ng-app
description: Manage Angular Material application within a workspace - create app structure with Material theme, modify providers and routing, or delete app
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

**Input Requirements**:
- `appName` (required): Name of the application (e.g., `my-app`, `admin-dashboard`)
- `workspacePath` (required): Absolute path to the Angular workspace root directory
- `prefix` (optional): Component selector prefix (defaults to `app`)
- `routing` (optional): Whether to include routing configuration (defaults to `true`)
- `standalone` (optional): Whether to use standalone components (defaults to `true`)

**Process**:

1. **Validate workspace exists**
   - Check that `workspacePath` exists and contains `angular.json`
   - Verify workspace is initialized and valid
   - Confirm `appName` doesn't already exist in workspace

2. **Generate application using the ngdj composite schematic**

   Invoke through the djng wrapper (`django-admin ng_gen_app`) which calls:
   ```bash
   cd <workspacePath>
   ng generate angular-django2:ng-app <appName> --style=scss --routing
   ```

   The `angular-django2:ng-app` schematic handles all of the following in one step:
   - Generates the Angular application via `@schematics/angular:application`
   - Adds `@angular/material` and `@angular/cdk` to `package.json`
   - Configures the selected Material prebuilt theme in `angular.json` and `styles.scss`
   - Adds animation providers to `app.config.ts`
   - Creates the standard directory structure (`core/`, `shared/components/`, `shared/pipes/`, `features/`)
     with barrel `index.ts` exports in each directory
   - Writes a Material sidenav app-shell into `app.component.ts/html/scss`

3. **Verify compilation**
   ```bash
   ng build <appName> --configuration=development
   ```

**Output**:
- Complete Angular Material application created in `projects/<appName>/`
- Directory structure with `core/`, `shared/`, `features/` folders
- Material theme configured in `styles.scss` and `angular.json`
- Standalone bootstrap with `app.config.ts` including animation provider
- Material sidenav app shell in `app.component.*`
- Entry added to `angular.json` for the new application
- Confirmation message with next steps (e.g., "Run `ng serve <appName>` to start development server")

#### Modify

Update an existing Angular Material application with changes to providers, global styles, or routing configuration.

**Input Requirements**:
- `appName` (required): Name of the existing application to modify
- `workspacePath` (required): Absolute path to the Angular workspace
- `modifications` (required): Object describing changes to make:
  - `providers`: Array of provider configurations to add/remove
  - `styles`: CSS/SCSS rules to add to global styles
  - `routes`: Route definitions to register (lazy-loaded or eager)
  - `dependencies`: NPM packages to add/remove

**Process**:

1. **Validate application exists**
   - Verify `projects/<appName>/` exists
   - Check `angular.json` contains configuration for `<appName>`
   - Confirm application is using standalone architecture

2. **Update providers in app.config.ts**
   - Read existing `projects/<appName>/src/app/app.config.ts`
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
   - Read `projects/<appName>/src/styles.scss`
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
   - Read `projects/<appName>/src/app/app.routes.ts`
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
   - If `dependencies` specified, update `package.json`:
     ```bash
     cd <workspacePath>
     npm install <package>@<version>
     # or
     npm uninstall <package>
     ```

6. **Verify compilation**
   ```bash
   ng build <appName> --configuration=development
   ```

**Output**:
- Updated `app.config.ts` with new providers
- Modified `styles.scss` with additional styles or theme changes
- Updated `app.routes.ts` with new route registrations
- Updated `package.json` and `node_modules` if dependencies changed
- Confirmation of successful modification with list of changes made

#### Delete

Remove an Angular Material application completely from the workspace, including all source files and configuration.

**Input Requirements**:
- `appName` (required): Name of the application to delete
- `workspacePath` (required): Absolute path to the Angular workspace
- `confirm` (required): Boolean confirmation flag (must be `true`)

**Process**:

1. **Validate application exists**
   - Verify `projects/<appName>/` exists
   - Check `angular.json` contains configuration for `<appName>`
   - Confirm no other applications depend on this one

2. **Remove application directory**
   ```bash
   rm -rf <workspacePath>/projects/<appName>
   ```

3. **Update angular.json**
   - Read `angular.json`
   - Remove entry from `projects` object for `<appName>`
   - Remove any build configurations, serve targets, and test targets
   - Update default project if this was the default

4. **Clean up dependencies (optional)**
   - Check if Angular Material is used by other apps
   - If this was the only app using Material, optionally remove:
     ```bash
     npm uninstall @angular/material @angular/cdk
     ```

5. **Verify workspace integrity**
   ```bash
   ng build --help  # Confirm workspace still valid
   ```

**Output**:
- Application directory `projects/<appName>/` removed
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
   ls -la projects/<appName>/src/app/
   # Should contain: core/, shared/, features/, app.component.ts, app.config.ts, app.routes.ts
   ```

2. **Verify Material theme is wired**
   ```bash
   cat projects/<appName>/src/styles.scss | grep "@angular/material"
   # Should contain Material theme imports and configuration
   ```

3. **Verify standalone bootstrap**
   ```bash
   cat projects/<appName>/src/main.ts | grep "bootstrapApplication"
   # Should use bootstrapApplication() not platformBrowserDynamic()
   ```

4. **Compile check**
   ```bash
   ng build <appName> --configuration=development
   # Should complete without errors
   ```

5. **Serve and verify**
   ```bash
   ng serve <appName>
   # Navigate to http://localhost:4200 and verify Material components render
   ```

### Error Handling

Common errors and their resolution strategies:

**Error**: `Application <appName> already exists`
- **Cause**: Attempting to create an app with a name that's already in use
- **Resolution**: Use Delete mode first, or choose a different app name

**Error**: `Workspace path does not contain angular.json`
- **Cause**: Invalid workspace path or workspace not initialized
- **Resolution**: Verify workspace path is correct; if needed, run workspace creation skill first

**Error**: `Cannot find module '@angular/material'`
- **Cause**: Angular Material not installed or installation failed
- **Resolution**: Run `ng add @angular/material --project=<appName>` manually

**Error**: `Compilation failed: Cannot find module './app/app.config'`
- **Cause**: Standalone bootstrap not properly configured
- **Resolution**: Verify `app.config.ts` exists and is properly imported in `main.ts`

**Error**: `SCSS compilation failed`
- **Cause**: Invalid SCSS syntax in theme configuration
- **Resolution**: Validate SCSS syntax in `styles.scss`; ensure `@use` statements are at the top

**Error**: `Port 4200 is already in use`
- **Cause**: Another application is already running on default port
- **Resolution**: Stop other dev servers or use `ng serve <appName> --port=4201`

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1) — Workspace must exist before creating an application within it
2. **Node.js and npm** — Required to run Angular CLI commands
3. **Angular CLI** — Must be installed globally or in workspace (`@angular/cli`)

Optional dependencies:

- If using OpenAPI integration, **Angular API generation** (Skill 3) should be executed after app creation
- If creating multi-app workspace, this skill can be executed multiple times with different `appName` values

### Examples

**Example 1: Create a new admin dashboard application**

```typescript
// Inputs
{
  appName: "admin-dashboard",
  workspacePath: "/workspace/my-project",
  prefix: "admin",
  routing: true,
  standalone: true
}

// Executes via djng wrapper:
// 1. ng generate angular-django2:ng-app admin-dashboard --style=scss --routing
//    (schematic handles: app generation, Material deps, theme, directory structure, app shell)
// 2. ng build admin-dashboard --configuration=development

// Output: Application ready at projects/admin-dashboard/
```

**Example 2: Modify existing app to add authentication provider**

```typescript
// Inputs
{
  appName: "admin-dashboard",
  workspacePath: "/workspace/my-project",
  modifications: {
    providers: [
      {
        action: "add",
        provider: "provideAuth",
        import: "./core/auth",
        config: { apiUrl: "https://api.example.com" }
      }
    ],
    styles: `
      .authenticated { border-left: 3px solid green; }
      .unauthenticated { border-left: 3px solid red; }
    `
  }
}

// Executes:
// 1. Reads projects/admin-dashboard/src/app/app.config.ts
// 2. Adds import: import { provideAuth } from './core/auth';
// 3. Adds to providers: provideAuth({ apiUrl: 'https://api.example.com' })
// 4. Appends custom styles to projects/admin-dashboard/src/styles.scss
// 5. Runs: ng build admin-dashboard --configuration=development

// Output: Updated app.config.ts and styles.scss
```

**Example 3: Register lazy-loaded feature route**

```typescript
// Inputs
{
  appName: "admin-dashboard",
  workspacePath: "/workspace/my-project",
  modifications: {
    routes: [
      {
        path: "users",
        loadComponent: () => import("./features/users/users-list.component")
          .then(m => m.UsersListComponent),
        title: "User Management"
      }
    ]
  }
}

// Executes:
// 1. Reads projects/admin-dashboard/src/app/app.routes.ts
// 2. Adds new route definition to routes array
// 3. Runs: ng build admin-dashboard --configuration=development

// Output: Updated app.routes.ts with new lazy route
```

**Example 4: Delete an application**

```typescript
// Inputs
{
  appName: "old-admin",
  workspacePath: "/workspace/my-project",
  confirm: true
}

// Executes:
// 1. Verifies projects/old-admin/ exists
// 2. Removes: rm -rf projects/old-admin
// 3. Updates angular.json to remove "old-admin" project entry
// 4. Verifies workspace: ng build --help

// Output: Application "old-admin" removed from workspace
```

