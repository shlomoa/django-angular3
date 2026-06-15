## Angular component generation

**Skill Name**: `angular-component-composition`

### YAML Frontmatter

```yaml
---
name: angular-component-composition
description: Create, modify, or delete Angular Material components (display, container, or dialog types) with standalone architecture and Material theming
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

The `angular-component-composition` skill manages the creation, modification, and deletion of Angular components within an existing Angular Material application. Components are generated following modern Angular conventions (standalone components, signals, Material Design patterns) and can be one of three types: **display** (presentational with Material layout), **container** (smart component with service injection and Observable data binding), or **dialog** (Material dialog with data injection and action buttons). This skill should be used after the workspace and application have been created.

### Inputs

**From invocation context**:
- **`componentName`** (string, required): Name of the component in kebab-case (e.g., `user-profile`, `product-card`)
- **`targetPath`** (string, required): Relative path from app source directory where component will be created (e.g., `src/app/features/users`, `src/app/shared/components`)
- **`type`** (enum, required): Component type (`display` | `container` | `dialog`)
- **`workspacePath`** (string, required): Absolute path to the Angular workspace root directory
- **`appName`** (string, optional): Name of the application within workspace (required for multi-app workspaces)

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular component from scratch when it doesn't exist.

**Input Requirements**:
- `componentName`: Must be valid kebab-case identifier (lowercase, hyphenated)
- `targetPath`: Must be valid directory path within the application
- `type`: Must be one of: `display`, `container`, or `dialog`
- `workspacePath`: Must point to valid Angular workspace
- `appName`: Optional, defaults to default project in workspace

**Pre-flight Checks**:

Before creating the component, verify:

1. Workspace exists and contains `angular.json`
2. Target application exists (if `appName` specified)
3. Target directory exists or can be created
4. Component with same name doesn't already exist at target path
5. Angular CLI is accessible (`ng version`)

**Process (Create Mode)**:

The creation process varies based on component `type`:

##### Type: Display

**Display components** are presentational components that receive data via input signals and emit events via output signals. They use Material Card layout with structured header, content, and actions sections.

1. **Generate component scaffold**:
   ```bash
   cd <workspacePath>
   ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<appName>
   ```

2. **Replace component TypeScript file** using `{{template:component-display.ts.tpl}}`:
   ```typescript
   import { Component, input, output } from '@angular/core';
   import { CommonModule } from '@angular/common';
   import { MatCardModule } from '@angular/material/card';
   import { MatButtonModule } from '@angular/material/button';

   @Component({
     selector: 'app-{{COMPONENT_NAME_KEBAB}}',
     standalone: true,
     imports: [
       CommonModule,
       MatCardModule,
       MatButtonModule,
     ],
     templateUrl: './{{COMPONENT_NAME_KEBAB}}.component.html',
     styleUrl: './{{COMPONENT_NAME_KEBAB}}.component.scss'
   })
   export class {{COMPONENT_NAME_PASCAL}}Component {
     // Input signals
     title = input<string>('');
     subtitle = input<string>('');
     data = input<any>(null);

     // Output signals
     actionClicked = output<void>();

     handleAction(): void {
       this.actionClicked.emit();
     }
   }
   ```

3. **Replace component template** using `{{template:component-display.html.tpl}}`:
   ```html
   <mat-card>
     <mat-card-header>
       <mat-card-title>{{ title() }}</mat-card-title>
       @if (subtitle()) {
         <mat-card-subtitle>{{ subtitle() }}</mat-card-subtitle>
       }
     </mat-card-header>

     <mat-card-content>
       @if (data()) {
         <p>{{ data() }}</p>
       } @else {
         <p>No data available</p>
       }
     </mat-card-content>

     <mat-card-actions align="end">
       <button mat-button (click)="handleAction()">
         Action
       </button>
     </mat-card-actions>
   </mat-card>
   ```

4. **Replace component styles** using `{{template:component-display.scss.tpl}}`:
   ```scss
   @use '@angular/material' as mat;

   :host {
     display: block;

     mat-card {
       mat-card-header {
         background-color: mat.get-theme-color(primary, 50);
         padding: 1rem;
         margin: -1rem -1rem 1rem -1rem;
       }

       mat-card-title {
         color: mat.get-theme-color(primary, 700);
         font-weight: mat.get-theme-typography(headline-6, font-weight);
       }

       mat-card-subtitle {
         color: mat.get-theme-color(primary, 500);
       }

       mat-card-content {
         padding: 1rem;
       }

       mat-card-actions {
         padding: 0.5rem 1rem 1rem;
       }
     }
   }
   ```

5. **Replace placeholders**:
   - Replace `{{COMPONENT_NAME_KEBAB}}` with `componentName` (e.g., `user-profile`)
   - Replace `{{COMPONENT_NAME_PASCAL}}` with PascalCase version (e.g., `UserProfile`)

##### Type: Container

**Container components** are smart components that inject services, manage state, and interact with backend APIs. They use `toSignal()` to convert Observables to signals for reactive data binding.

1. **Generate component scaffold** (same as display):
   ```bash
   ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<appName>
   ```

2. **Replace component TypeScript file** using `{{template:component-container.ts.tpl}}`:
   ```typescript
   import { Component, inject } from '@angular/core';
   import { CommonModule } from '@angular/common';
   import { toSignal } from '@angular/core/rxjs-interop';
   import { MatCardModule } from '@angular/material/card';
   import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
   import { MatButtonModule } from '@angular/material/button';

   @Component({
     selector: 'app-{{COMPONENT_NAME_KEBAB}}',
     standalone: true,
     imports: [
       CommonModule,
       MatCardModule,
       MatProgressSpinnerModule,
       MatButtonModule,
     ],
     templateUrl: './{{COMPONENT_NAME_KEBAB}}.component.html',
     styleUrl: './{{COMPONENT_NAME_KEBAB}}.component.scss'
   })
   export class {{COMPONENT_NAME_PASCAL}}Component {
     // Inject services using inject() function
     // private dataService = inject(DataService);

     // Convert Observable to signal using toSignal()
     // data = toSignal(this.dataService.getData$(), { initialValue: null });
     // loading = toSignal(this.dataService.loading$(), { initialValue: false });

     handleRefresh(): void {
       // Trigger data refresh
       // this.dataService.refresh();
     }
   }
   ```

3. **Replace component template** using `{{template:component-container.html.tpl}}`:
   ```html
   <mat-card>
     <mat-card-header>
       <mat-card-title>{{COMPONENT_NAME_TITLE}}</mat-card-title>
     </mat-card-header>

     <mat-card-content>
       @if (loading()) {
         <div class="loading-spinner">
           <mat-spinner diameter="40"></mat-spinner>
         </div>
       } @else if (data()) {
         <!-- Display data here -->
         <p>{{ data() }}</p>
       } @else {
         <p>No data available</p>
       }
     </mat-card-content>

     <mat-card-actions align="end">
       <button mat-button (click)="handleRefresh()">
         Refresh
       </button>
     </mat-card-actions>
   </mat-card>
   ```

4. **Replace component styles** using `{{template:component-container.scss.tpl}}`:
   ```scss
   @use '@angular/material' as mat;

   :host {
     display: block;

     mat-card {
       mat-card-content {
         min-height: 200px;
         position: relative;

         .loading-spinner {
           display: flex;
           justify-content: center;
           align-items: center;
           height: 200px;
         }
       }
     }
   }
   ```

5. **Replace placeholders**:
   - Replace `{{COMPONENT_NAME_KEBAB}}` with `componentName` (e.g., `user-list`)
   - Replace `{{COMPONENT_NAME_PASCAL}}` with PascalCase version (e.g., `UserList`)
   - Replace `{{COMPONENT_NAME_TITLE}}` with Title Case version (e.g., `User List`)

##### Type: Dialog

**Dialog components** are Material dialogs that receive data via `MAT_DIALOG_DATA` injection and close with results via `MatDialogRef`. They include confirm and cancel action buttons.

1. **Generate component scaffold** (same as display):
   ```bash
   ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<appName>
   ```

2. **Replace component TypeScript file** using `{{template:component-dialog.ts.tpl}}`:
   ```typescript
   import { Component, inject } from '@angular/core';
   import { CommonModule } from '@angular/common';
   import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
   import { MatButtonModule } from '@angular/material/button';
   import { MatFormFieldModule } from '@angular/material/form-field';
   import { MatInputModule } from '@angular/material/input';

   export interface {{COMPONENT_NAME_PASCAL}}DialogData {
     title: string;
     message: string;
   }

   @Component({
     selector: 'app-{{COMPONENT_NAME_KEBAB}}',
     standalone: true,
     imports: [
       CommonModule,
       MatDialogModule,
       MatButtonModule,
       MatFormFieldModule,
       MatInputModule,
     ],
     templateUrl: './{{COMPONENT_NAME_KEBAB}}.component.html',
     styleUrl: './{{COMPONENT_NAME_KEBAB}}.component.scss'
   })
   export class {{COMPONENT_NAME_PASCAL}}Component {
     // Inject dialog data and dialog reference
     data = inject<{{COMPONENT_NAME_PASCAL}}DialogData>(MAT_DIALOG_DATA);
     dialogRef = inject(MatDialogRef<{{COMPONENT_NAME_PASCAL}}Component>);

     onCancel(): void {
       this.dialogRef.close();
     }

     onConfirm(): void {
       this.dialogRef.close({ confirmed: true });
     }
   }
   ```

3. **Replace component template** using `{{template:component-dialog.html.tpl}}`:
   ```html
   <h2 mat-dialog-title>{{ data.title }}</h2>

   <mat-dialog-content>
     <p>{{ data.message }}</p>
   </mat-dialog-content>

   <mat-dialog-actions align="end">
     <button mat-button (click)="onCancel()">Cancel</button>
     <button mat-raised-button color="primary" (click)="onConfirm()">
       Confirm
     </button>
   </mat-dialog-actions>
   ```

4. **Replace component styles** using `{{template:component-dialog.scss.tpl}}`:
   ```scss
   @use '@angular/material' as mat;

   :host {
     display: block;

     mat-dialog-content {
       min-width: 300px;
       padding: 1.5rem 1rem;
     }

     mat-dialog-actions {
       padding: 0.5rem 1rem 1rem;
     }
   }
   ```

5. **Replace placeholders**:
   - Replace `{{COMPONENT_NAME_KEBAB}}` with `componentName` (e.g., `confirm-delete`)
   - Replace `{{COMPONENT_NAME_PASCAL}}` with PascalCase version (e.g., `ConfirmDelete`)

**Output (all types)**:
- Component files created at `<targetPath>/<componentName>/`:
  - `<componentName>.component.ts` - Component class
  - `<componentName>.component.html` - Component template
  - `<componentName>.component.scss` - Component styles
  - `<componentName>.component.spec.ts` - Component unit tests
- Confirmation message with component location and next steps

#### Modify

Update an existing Angular component with changes to template, services, or type conversion.

**Input Requirements**:
- `componentName`: Must reference existing component
- `targetPath`: Must point to existing component directory
- `workspacePath`: Must point to valid Angular workspace
- `modifications` (required): Object describing changes to make:
  - `template`: HTML changes to apply to template
  - `services`: Array of service injections to add/remove
  - `convertType`: New component type to convert to (`display` | `container` | `dialog`)
  - `styles`: SCSS rules to add or modify

**Process**:

1. **Validate component exists**:
   - Verify `<targetPath>/<componentName>/<componentName>.component.ts` exists
   - Verify component follows standalone architecture
   - Read existing component files

2. **Apply template modifications**:
   - If `modifications.template` specified:
     - Read existing `<componentName>.component.html`
     - Apply requested template changes using Edit tool
     - Preserve Material component usage and new control flow syntax (`@if`, `@for`)

3. **Add or remove service injections**:
   - If `modifications.services` specified:
     - Read existing component TypeScript file
     - For each service to add:
       ```typescript
       // Add import at top of file
       import { ServiceName } from './path/to/service';

       // Add injection in component class
       private serviceName = inject(ServiceName);
       ```
     - For each service to remove:
       - Remove injection line
       - Remove import if no longer used
     - Update template if service methods were used

4. **Convert component type**:
   - If `modifications.convertType` specified:
     - Backup current component files
     - Apply type-specific template from Create mode process
     - Preserve existing input/output signals where applicable
     - Update imports based on new type requirements
     - Notify user of manual adjustments needed

5. **Apply style modifications**:
   - If `modifications.styles` specified:
     - Read existing `<componentName>.component.scss`
     - Append new styles or update existing rules
     - Maintain Material theme token usage (`mat.get-theme-color()`)

6. **Verify compilation**:
   ```bash
   ng build <appName> --configuration=development
   ```

**Output**:
- Updated component files at `<targetPath>/<componentName>/`
- List of modifications applied
- Compilation confirmation

#### Delete

Remove an Angular component completely, including all files and references in parent components or routes.

**Input Requirements**:
- `componentName`: Must reference existing component to delete
- `targetPath`: Must point to existing component directory
- `workspacePath`: Must point to valid Angular workspace
- `confirm` (required): Boolean confirmation flag (must be `true`)

**Process**:

1. **Validate component exists**:
   - Verify `<targetPath>/<componentName>/` directory exists
   - Check for any imports or references to this component

2. **Search for component references**:
   ```bash
   cd <workspacePath>
   grep -r "{{COMPONENT_NAME_PASCAL}}Component" --include="*.ts" --include="*.html"
   grep -r "app-{{COMPONENT_NAME_KEBAB}}" --include="*.html"
   ```

3. **Remove component from imports/routes**:
   - For each file that imports the component:
     - Remove import statement
     - Remove from component imports array (if used)
     - Remove from route definitions (if lazy-loaded)
   - For each template that uses the component:
     - Remove component selector usage
     - Notify user of template references to be updated manually

4. **Delete component directory**:
   ```bash
   rm -rf <targetPath>/<componentName>
   ```

5. **Update barrel exports** (if applicable):
   - If `<targetPath>/index.ts` exists:
     - Remove export statement for deleted component

6. **Verify compilation**:
   ```bash
   ng build <appName> --configuration=development
   ```

**Output**:
- Component directory removed
- List of files that referenced the component (requiring manual cleanup)
- Confirmation of deletion

### Context Files

{{context:../../shared/angular-conventions.md}}

{{context:../../shared/angular-material-patterns.md}}

### Templates

- `component-display.ts.tpl` — Display component TypeScript with input/output signals, Material Card layout
- `component-display.html.tpl` — Display component template with MatCard, header, content, and actions
- `component-display.scss.tpl` — Display component styles using Material theme tokens
- `component-container.ts.tpl` — Container component TypeScript with service injection and `toSignal()` usage
- `component-container.html.tpl` — Container component template with loading spinner and data display
- `component-container.scss.tpl` — Container component styles with loading state
- `component-dialog.ts.tpl` — Dialog component TypeScript with `MAT_DIALOG_DATA` and `MatDialogRef`
- `component-dialog.html.tpl` — Dialog component template with title, content, and action buttons
- `component-dialog.scss.tpl` — Dialog component styles

### Validation

Steps to validate successful execution of the skill:

1. **Verify component files exist**:
   ```bash
   ls -la <targetPath>/<componentName>/
   # Should contain: *.component.ts, *.component.html, *.component.scss, *.component.spec.ts
   ```

2. **Verify standalone architecture**:
   ```bash
   cat <targetPath>/<componentName>/<componentName>.component.ts | grep "standalone: true"
   # Should return standalone: true in decorator
   ```

3. **Verify correct type implementation**:
   - For `display`: Check for input/output signals, no service injections
   - For `container`: Check for service injection with `inject()`, `toSignal()` usage
   - For `dialog`: Check for `MAT_DIALOG_DATA` and `MatDialogRef` injections

4. **Verify Material imports**:
   ```bash
   cat <targetPath>/<componentName>/<componentName>.component.ts | grep "@angular/material"
   # Should contain Material module imports appropriate for type
   ```

5. **Verify SCSS uses theme tokens**:
   ```bash
   cat <targetPath>/<componentName>/<componentName>.component.scss | grep "mat.get-theme-color"
   # Should use Material theme functions, not hardcoded colors
   ```

6. **Compile check**:
   ```bash
   ng build <appName> --configuration=development
   # Should complete without errors
   ```

7. **Run unit tests**:
   ```bash
   ng test <appName> --include='**/<componentName>.component.spec.ts'
   # Should pass with no failures
   ```

### Error Handling

Common errors and their resolution strategies:

**Error**: `Component <componentName> already exists at <targetPath>`
- **Cause**: Attempting to create a component that already exists
- **Resolution**: Use Modify mode to update existing component, or Delete mode first to recreate

**Error**: `Target path does not exist: <targetPath>`
- **Cause**: Invalid or non-existent target directory
- **Resolution**: Create target directory first or use valid path within app structure

**Error**: `Invalid component name: <componentName>`
- **Cause**: Component name doesn't follow kebab-case convention
- **Resolution**: Provide valid kebab-case name (lowercase, hyphenated)

**Error**: `Cannot find module '@angular/material/<module>'`
- **Cause**: Required Material module not installed
- **Resolution**: Ensure Angular Material is installed in the application (`ng add @angular/material`)

**Error**: `Compilation failed: Type 'WritableSignal<T>' is not assignable`
- **Cause**: Incorrect signal usage or TypeScript version mismatch
- **Resolution**: Verify Angular version is 17+ which supports signals natively

**Error**: `SCSS compilation failed: Undefined function 'mat.get-theme-color'`
- **Cause**: Material theme not properly configured or SCSS not using `@use` syntax
- **Resolution**: Ensure `styles.scss` contains Material theme setup with `@use '@angular/material' as mat;`

**Error**: `Dialog component not opening`
- **Cause**: Dialog component not properly registered or MatDialog service not provided
- **Resolution**: Verify `provideAnimations()` is in app.config.ts providers array

**Error**: `No provider for MAT_DIALOG_DATA`
- **Cause**: Dialog component used outside of MatDialog.open() context
- **Resolution**: Only instantiate dialog components via `MatDialog.open()`, not directly in templates

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1 - ng-workspace) — Workspace must exist
2. **Angular Material app boilerplate** (Skill 2 - ng-app) — Application must exist before creating components
3. **Angular CLI** — Must be installed and accessible
4. **Angular Material** — Must be installed in the target application

Optional dependencies:

- **Angular API generation** (Skill 3 - ng-api-gen) — If component needs to consume API services
- **Angular data model Service** (Skill 4) — If container component needs data service injection

### Examples

**Example 1: Create a display component for product card**

```typescript
// Inputs
{
  componentName: "product-card",
  targetPath: "src/app/shared/components",
  type: "display",
  workspacePath: "/workspace/my-project",
  appName: "admin-dashboard"
}

// Executes:
// 1. ng generate component src/app/shared/components/product-card --standalone
// 2. Replaces files using component-display templates
// 3. Replaces {{COMPONENT_NAME_KEBAB}} with "product-card"
// 4. Replaces {{COMPONENT_NAME_PASCAL}} with "ProductCard"
// 5. Runs: ng build admin-dashboard --configuration=development

// Output: Display component created at src/app/shared/components/product-card/
// Usage: <app-product-card [title]="product.name" [data]="product" (actionClicked)="onBuy()" />
```

**Example 2: Create a container component for user list**

```typescript
// Inputs
{
  componentName: "user-list",
  targetPath: "src/app/features/users",
  type: "container",
  workspacePath: "/workspace/my-project"
}

// Executes:
// 1. ng generate component src/app/features/users/user-list --standalone
// 2. Replaces files using component-container templates
// 3. Adds service injection placeholder comments
// 4. Adds toSignal() usage examples
// 5. Runs: ng build --configuration=development

// Output: Container component created at src/app/features/users/user-list/
// Next step: Inject UserService and bind data using toSignal()
```

**Example 3: Create a dialog component for confirmation**

```typescript
// Inputs
{
  componentName: "confirm-delete",
  targetPath: "src/app/shared/dialogs",
  type: "dialog",
  workspacePath: "/workspace/my-project"
}

// Executes:
// 1. ng generate component src/app/shared/dialogs/confirm-delete --standalone
// 2. Replaces files using component-dialog templates
// 3. Adds MAT_DIALOG_DATA and MatDialogRef injections
// 4. Adds cancel and confirm action buttons
// 5. Runs: ng build --configuration=development

// Output: Dialog component created at src/app/shared/dialogs/confirm-delete/
// Usage: this.dialog.open(ConfirmDeleteComponent, { data: { title: 'Delete?', message: 'Are you sure?' } })
```

**Example 4: Modify existing component to add service injection**

```typescript
// Inputs
{
  componentName: "user-list",
  targetPath: "src/app/features/users",
  workspacePath: "/workspace/my-project",
  modifications: {
    services: [
      {
        action: "add",
        serviceName: "UserService",
        importPath: "../../core/services/user.service",
        binding: "users$ = toSignal(this.userService.getUsers$(), { initialValue: [] })"
      }
    ]
  }
}

// Executes:
// 1. Reads src/app/features/users/user-list/user-list.component.ts
// 2. Adds: import { UserService } from '../../core/services/user.service';
// 3. Adds: private userService = inject(UserService);
// 4. Adds: users$ = toSignal(this.userService.getUsers$(), { initialValue: [] });
// 5. Runs: ng build --configuration=development

// Output: Component updated with UserService injection and signal binding
```

**Example 5: Delete a component and clean up references**

```typescript
// Inputs
{
  componentName: "old-widget",
  targetPath: "src/app/shared/components",
  workspacePath: "/workspace/my-project",
  confirm: true
}

// Executes:
// 1. Searches for references to OldWidgetComponent in codebase
// 2. Removes component from parent component imports (if found)
// 3. Deletes: rm -rf src/app/shared/components/old-widget
// 4. Updates: src/app/shared/components/index.ts (removes export)
// 5. Runs: ng build --configuration=development

// Output: Component deleted. Manual cleanup needed in:
//   - src/app/pages/dashboard/dashboard.component.html (remove <app-old-widget>)
```
