## Angular Material small field level component generation

```yaml
---
name: ng-field-component
description: Create, modify, or delete Angular Material small field-level components with typed input/output signals, Material imports, and ARIA accessibility
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

Generate and manage small, reusable Angular Material field-level components (e.g., custom buttons, chips, badges, status indicators, icons with tooltips). These are lightweight standalone components that use Angular signals for inputs/outputs, import only required Material modules, include ARIA attributes for accessibility, and utilize modern control flow syntax (`@if`/`@for`). Unlike form fields (skill 6) which implement `ControlValueAccessor`, these components are simple presentational or interactive elements used within larger components or pages.

### Modes

All skills support three operational modes:

#### Create

Generate a standalone Angular Material small field-level component from scratch with typed signals, Material imports, ARIA attributes, and test harness.

**Input Requirements**:
- `componentName` (string, required): Name of the component in kebab-case (e.g., `status-badge`, `action-button`)
- `workspacePath` (string, required): Absolute path to the Angular workspace root directory
- `appName` (string, required): Name of the application within the workspace (e.g., `my-app`, `admin-dashboard`)
- `placement` (string, required): Where to place the component:
  - `shared` — Place in `projects/<appName>/src/app/shared/components/` (for reusable components)
  - `feature/<feature-name>` — Place in `projects/<appName>/src/app/features/<feature-name>/components/` (for feature-specific components)
- `componentType` (string, optional): Type of component to scaffold. Defaults to `generic`:
  - `button` — Action button with icon support
  - `chip` — Material chip with removable option
  - `badge` — Status or notification badge
  - `icon-tooltip` — Icon with Material tooltip
  - `generic` — Basic component scaffold
- `materialModules` (array, optional): List of Material modules to import (e.g., `['MatButtonModule', 'MatIconModule']`). Auto-selected based on `componentType` if not provided

**Process**:

1. **Validate prerequisites**:
   - Verify workspace exists at `workspacePath` and contains `angular.json`
   - Verify application `appName` exists in `projects/<appName>/`
   - Confirm workspace uses standalone component architecture
   - Validate `componentName` follows naming conventions (lowercase, hyphenated)
   - Check component doesn't already exist at target path

2. **Determine target directory**:
   - If `placement` is `shared`:
     - Target: `projects/<appName>/src/app/shared/components/<componentName>/`
   - If `placement` is `feature/<feature-name>`:
     - Target: `projects/<appName>/src/app/features/<feature-name>/components/<componentName>/`
   - Create directory if it doesn't exist:
     ```bash
     mkdir -p <targetDirectory>
     ```

3. **Generate component TypeScript file** using `{{template:component.ts.tpl}}`:
   - Create `<componentName>.component.ts` with:
     - `@Component` decorator with `standalone: true`
     - Typed input signals using `input<T>()` with appropriate types
     - Typed output signals using `output<T>()` with appropriate types
     - Import only required Material modules based on `componentType` or `materialModules`
     - Import `CommonModule` for built-in directives
     - Component class with PascalCase naming: `<ComponentName>Component`
     - Selector: `app-<component-name>`
   - Placeholders to replace:
     - `{{COMPONENT_NAME_KEBAB}}` → e.g., `status-badge`
     - `{{COMPONENT_NAME_PASCAL}}` → e.g., `StatusBadge`
   - Customize based on `componentType`:
     - **button**: Add `MatButtonModule`, `MatIconModule`; input for `label`, `icon`, `disabled`; output for `clicked`
     - **chip**: Add `MatChipsModule`; input for `label`, `removable`; output for `removed`
     - **badge**: Add `MatBadgeModule`, `MatIconModule`; input for `count`, `color`
     - **icon-tooltip**: Add `MatIconModule`, `MatTooltipModule`; input for `icon`, `tooltip`
     - **generic**: Add `MatCardModule`, `MatButtonModule`; basic input/output signals

4. **Generate component HTML template** using `{{template:component.html.tpl}}`:
   - Create `<componentName>.component.html` with:
     - Material component markup based on `componentType`
     - Use `@if` for conditional rendering (not `*ngIf`)
     - Use `@for` for list rendering (not `*ngFor`)
     - Add ARIA attributes: `aria-label`, `role`, `aria-describedby`, etc.
     - Bind to signals using signal call syntax: `{{ title() }}`
     - Event bindings to component methods
   - Ensure accessibility:
     - Add `role` attributes where appropriate
     - Add `aria-label` for icon-only buttons
     - Add `tabindex` for keyboard navigation
     - Add `aria-hidden="true"` for decorative elements

5. **Generate component SCSS file** using `{{template:component.scss.tpl}}`:
   - Create `<componentName>.component.scss` with:
     - `:host` selector for component-level styles
     - Material theme token usage via `mat.get-theme-color()` and `mat.get-theme-typography()`
     - No hardcoded colors or typography (use theme tokens)
     - Responsive sizing using relative units
   - Example structure:
     ```scss
     @use '@angular/material' as mat;

     :host {
       display: inline-block;

       .component-wrapper {
         // Use theme tokens
         color: mat.get-theme-color(primary, 700);
         background: mat.get-theme-color(primary, 50);
       }
     }
     ```

6. **Generate component spec file**:
   - Create `<componentName>.component.spec.ts` with:
     - Angular Testing Library setup (if available) or ComponentFixture
     - Material test harness imports (e.g., `MatButtonHarness`)
     - Test suite structure:
       - `should create` test
       - Input signal tests (verify signals update correctly)
       - Output signal tests (verify events emit correctly)
       - Material component interaction tests using harnesses
       - ARIA attribute tests
     - Example test structure:
       ```typescript
       import { ComponentFixture, TestBed } from '@angular/core/testing';
       import { HarnessLoader } from '@angular/cdk/testing';
       import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';
       import { MatButtonHarness } from '@angular/material/button/testing';
       import { StatusBadgeComponent } from './status-badge.component';

       describe('StatusBadgeComponent', () => {
         let component: StatusBadgeComponent;
         let fixture: ComponentFixture<StatusBadgeComponent>;
         let loader: HarnessLoader;

         beforeEach(async () => {
           await TestBed.configureTestingModule({
             imports: [StatusBadgeComponent]
           }).compileComponents();

           fixture = TestBed.createComponent(StatusBadgeComponent);
           component = fixture.componentInstance;
           loader = TestbedHarnessEnvironment.loader(fixture);
           fixture.detectChanges();
         });

         it('should create', () => {
           expect(component).toBeTruthy();
         });

         it('should display input signal value', () => {
           fixture.componentRef.setInput('status', 'active');
           fixture.detectChanges();
           // Test implementation
         });

         it('should emit output signal on interaction', async () => {
           const button = await loader.getHarness(MatButtonHarness);
           // Test implementation
         });
       });
       ```

7. **Update barrel export** (if in shared directory):
   - Read `projects/<appName>/src/app/shared/components/index.ts`
   - If file doesn't exist, create it
   - Add export: `export * from './<componentName>/<componentName>.component';`
   - Maintain alphabetical ordering

8. **Verify compilation**:
   ```bash
   cd <workspacePath>
   ng build <appName> --configuration=development
   ```
   - Confirm build completes without errors
   - Check for TypeScript errors

9. **Run component tests**:
   ```bash
   ng test <appName> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Confirm all tests pass

**Output**:
- Complete standalone component created at target directory:
  - `<componentName>.component.ts` — Component TypeScript with typed signals
  - `<componentName>.component.html` — Template with ARIA attributes and modern control flow
  - `<componentName>.component.scss` — Styles using Material theme tokens
  - `<componentName>.component.spec.ts` — Test suite with Material test harnesses
- Updated barrel export in `index.ts` (if applicable)
- Compilation verification successful
- Tests passing
- Confirmation message with component location and usage example

#### Modify

Update an existing Angular Material small field-level component by adding/removing inputs/outputs, updating template, or modifying styles.

**Input Requirements**:
- `componentName` (string, required): Name of the existing component to modify
- `workspacePath` (string, required): Absolute path to the Angular workspace
- `appName` (string, required): Name of the application within the workspace
- `placement` (string, required): Current placement location (`shared` or `feature/<feature-name>`)
- `modifications` (object, required): Changes to apply:
  - `addInputs`: Array of input signals to add with type information
    - Format: `[{ name: 'newInput', type: 'string', default: "''" }]`
  - `removeInputs`: Array of input signal names to remove
  - `addOutputs`: Array of output signals to add with type information
    - Format: `[{ name: 'newAction', type: 'void' }]`
  - `removeOutputs`: Array of output signal names to remove
  - `updateTemplate`: HTML string to replace or modify template sections
  - `updateStyles`: SCSS rules to add or modify
  - `addMaterialModules`: Array of Material module names to import
  - `removeMaterialModules`: Array of Material module names to remove

**Process**:

1. **Validate component exists**:
   - Determine target directory from `placement`
   - Verify component files exist:
     - `<componentName>.component.ts`
     - `<componentName>.component.html`
     - `<componentName>.component.scss`
     - `<componentName>.component.spec.ts`

2. **Modify TypeScript component**:
   - If `addInputs` specified:
     - Read `<componentName>.component.ts`
     - Add new input signals to component class:
       ```typescript
       newInput = input<string>(''); // with default value
       ```
     - Add TypeScript imports if needed for new types
   - If `removeInputs` specified:
     - Remove input signal declarations
     - Search template for usage and warn if still referenced
   - If `addOutputs` specified:
     - Add new output signals:
       ```typescript
       newAction = output<void>();
       ```
     - Add corresponding emit methods if needed
   - If `removeOutputs` specified:
     - Remove output signal declarations
     - Search template for event bindings and remove
   - If `addMaterialModules` specified:
     - Add imports to `imports` array in `@Component` decorator
     - Add import statement at top of file
   - If `removeMaterialModules` specified:
     - Remove from `imports` array
     - Remove import statement (if no longer used)
     - Warn if template still uses removed module components

3. **Modify HTML template**:
   - If `updateTemplate` specified:
     - Read `<componentName>.component.html`
     - Apply template modifications:
       - Add new elements
       - Update existing elements
       - Remove elements
     - Ensure ARIA attributes remain present
     - Verify modern control flow syntax (`@if`/`@for`)
     - Update signal bindings if inputs changed

4. **Modify SCSS styles**:
   - If `updateStyles` specified:
     - Read `<componentName>.component.scss`
     - Append new styles or modify existing selectors
     - Ensure theme token usage (no hardcoded colors)
     - Maintain `:host` selector pattern

5. **Update tests**:
   - Read `<componentName>.component.spec.ts`
   - Add tests for new inputs/outputs
   - Update existing tests if template/behavior changed
   - Remove tests for removed inputs/outputs
   - Ensure Material test harness usage updated

6. **Verify compilation**:
   ```bash
   ng build <appName> --configuration=development
   ```

7. **Run updated tests**:
   ```bash
   ng test <appName> --watch=false --include='**/<componentName>.component.spec.ts'
   ```

**Output**:
- Modified component files with requested changes
- Updated tests reflecting new behavior
- Compilation successful
- All tests passing
- Change summary listing what was modified

#### Delete

Remove an Angular Material small field-level component completely, including all files and references.

**Input Requirements**:
- `componentName` (string, required): Name of the component to delete
- `workspacePath` (string, required): Absolute path to the Angular workspace
- `appName` (string, required): Name of the application within the workspace
- `placement` (string, required): Current placement location
- `confirmDelete` (boolean, required): Safety confirmation (must be `true`)

**Process**:

1. **Validate component exists**:
   - Determine target directory from `placement`
   - Verify component directory exists

2. **Check for component usage**:
   - Search for imports of the component across the application:
     ```bash
     cd projects/<appName>/src/app
     grep -r "import.*<ComponentName>Component" --include="*.ts"
     ```
   - If component is imported anywhere, list usage locations and warn:
     - "Component is used in X file(s). Remove imports before deletion or use --force flag."
   - For `--force` mode, automatically remove imports from detected files

3. **Remove from barrel exports**:
   - If component was in `shared/components/`:
     - Read `projects/<appName>/src/app/shared/components/index.ts`
     - Remove export line: `export * from './<componentName>/<componentName>.component';`
   - If component was in feature directory, check for feature-level barrel exports

4. **Delete component directory**:
   ```bash
   rm -rf <targetDirectory>/<componentName>
   ```

5. **Remove from any imports arrays** (if referenced in other components):
   - Search for component usage in `imports` arrays
   - Remove from component imports
   - This step only executes if `--force` flag used or no usages found

6. **Verify compilation after deletion**:
   ```bash
   ng build <appName> --configuration=development
   ```
   - Confirm build succeeds (no broken imports)

7. **Run tests**:
   ```bash
   ng test <appName> --watch=false
   ```
   - Confirm no failing tests due to missing component

**Output**:
- Component directory removed
- Barrel exports updated
- All component imports removed from codebase
- Compilation successful
- Confirmation message with deletion summary

### Context Files

{{context:../../shared/angular-conventions.md}}

{{context:../../shared/angular-material-patterns.md}}

### Templates

- `component.ts.tpl` — Standalone component TypeScript scaffold with typed input/output signals, Material imports, and signal-based state management
- `component.html.tpl` — Component template with Material components, ARIA attributes, and modern control flow (`@if`/`@for`)
- `component.scss.tpl` — Component styles using Material theme tokens and `:host` selector pattern

### Validation

Steps to validate successful execution of the skill:

**Post-Create Validation**:
1. **Verify directory structure**:
   ```bash
   ls -la <targetDirectory>/<componentName>/
   ```
   - Should contain: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`

2. **Verify component is standalone**:
   ```bash
   grep "standalone: true" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should return match

3. **Verify signal usage**:
   ```bash
   grep -E "input<|output<" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find typed input/output signals

4. **Verify ARIA attributes**:
   ```bash
   grep -E "aria-|role=" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should find ARIA attributes in template

5. **Verify modern control flow**:
   ```bash
   grep -E "@if|@for" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should use `@if`/`@for` (not `*ngIf`/`*ngFor`)

6. **Compile check**:
   ```bash
   ng build <appName> --configuration=development
   ```
   - Should complete without errors

7. **Run specs**:
   ```bash
   ng test <appName> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Should pass all tests

8. **Check Material test harness usage**:
   ```bash
   grep "Harness" <targetDirectory>/<componentName>/<componentName>.component.spec.ts
   ```
   - Should find Material test harness imports and usage

**Post-Modify Validation**:
1. **Verify requested changes applied**:
   - Check TypeScript file for added/removed inputs/outputs
   - Check template for updated markup
   - Check styles for new SCSS rules

2. **Compile and test** (same as create mode steps 6-7)

**Post-Delete Validation**:
1. **Verify component removed**:
   ```bash
   [ ! -d <targetDirectory>/<componentName> ] && echo "Component deleted"
   ```

2. **Verify no broken imports**:
   ```bash
   ng build <appName> --configuration=development
   ```
   - Should compile successfully

### Error Handling

Common errors and their resolution strategies:

**Error**: `Component <componentName> already exists`
- **Cause**: Attempting to create a component with a name that already exists
- **Resolution**: Use Modify mode to update existing component, or Delete mode first, or choose a different name

**Error**: `Application <appName> not found in workspace`
- **Cause**: Invalid `appName` or workspace path
- **Resolution**: Verify workspace path contains `angular.json` and application exists in `projects/`

**Error**: `Invalid placement path: feature/<feature-name> does not exist`
- **Cause**: Feature directory doesn't exist
- **Resolution**: Create feature directory first or use `placement: 'shared'`

**Error**: `Component name must be in kebab-case`
- **Cause**: Component name uses PascalCase, camelCase, or contains invalid characters
- **Resolution**: Convert name to kebab-case (e.g., `MyComponent` → `my-component`)

**Error**: `Material module <ModuleName> not found`
- **Cause**: Specified Material module doesn't exist or isn't installed
- **Resolution**: Verify Material is installed (`@angular/material` in `package.json`) and module name is correct

**Error**: `Compilation failed: Cannot find name '<SignalName>'`
- **Cause**: Signal used in template but not declared in component
- **Resolution**: Verify all template bindings correspond to declared input/output signals

**Error**: `Component is still imported in X files`
- **Cause**: Attempting to delete component that's still in use
- **Resolution**: Remove imports from listed files first, or use `--force` flag to auto-remove

**Error**: `Tests failing after modification`
- **Cause**: Tests not updated to reflect component changes
- **Resolution**: Update test file to match new component inputs/outputs/behavior

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1) — Workspace must exist with Angular Material installed
2. **Angular Material app boilerplate** (Skill 2) — Application must exist in workspace with proper directory structure

Optional dependencies:

- None — This skill is independent and can be executed once workspace and app exist

Dependent skills (use this skill before):

- **Angular Material form field generation** (Skill 6) — May use field components as building blocks
- **Angular component generation** (Skill 7) — May compose field components into larger components
- **Angular Material page generation** (Skill 10) — Pages may use field components

### Examples

**Example 1: Create a status badge component in shared**

```json
{
  "mode": "create",
  "componentName": "status-badge",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "shared",
  "componentType": "badge",
  "materialModules": ["MatBadgeModule", "MatIconModule"]
}
```

**Execution**:
1. Validate workspace and app exist
2. Create directory: `projects/admin-dashboard/src/app/shared/components/status-badge/`
3. Generate TypeScript component with:
   - Input: `status = input<'active' | 'inactive' | 'pending'>('active')`
   - Input: `count = input<number>(0)`
   - Output: `clicked = output<void>()`
4. Generate HTML template:
   ```html
   <div class="status-badge"
        [class.active]="status() === 'active'"
        [class.inactive]="status() === 'inactive'"
        [class.pending]="status() === 'pending'"
        role="status"
        [attr.aria-label]="'Status: ' + status()">
     @if (count() > 0) {
       <mat-icon [matBadge]="count()" matBadgeColor="warn">notifications</mat-icon>
     } @else {
       <mat-icon>check_circle</mat-icon>
     }
   </div>
   ```
5. Generate SCSS with theme tokens
6. Generate spec with Material test harness
7. Update `shared/components/index.ts`: `export * from './status-badge/status-badge.component';`
8. Compile and test

**Output**: Status badge component created at `projects/admin-dashboard/src/app/shared/components/status-badge/`

**Example 2: Create an action button in a feature**

```json
{
  "mode": "create",
  "componentName": "export-button",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "feature/reports",
  "componentType": "button"
}
```

**Execution**:
1. Create directory: `projects/admin-dashboard/src/app/features/reports/components/export-button/`
2. Generate component with:
   - Input: `label = input<string>('Export')`
   - Input: `icon = input<string>('download')`
   - Input: `disabled = input<boolean>(false)`
   - Output: `clicked = output<void>()`
3. Generate template with Material button, icon, and ARIA attributes
4. Compile and test

**Output**: Export button component created in reports feature

**Example 3: Modify existing component to add new input**

```json
{
  "mode": "modify",
  "componentName": "status-badge",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "shared",
  "modifications": {
    "addInputs": [
      { "name": "size", "type": "'small' | 'medium' | 'large'", "default": "'medium'" }
    ],
    "updateStyles": ".status-badge.small { font-size: 12px; }\n.status-badge.large { font-size: 20px; }"
  }
}
```

**Execution**:
1. Read existing component files
2. Add to TypeScript: `size = input<'small' | 'medium' | 'large'>('medium')`
3. Update HTML: Add `[class.small]="size() === 'small'"` and `[class.large]="size() === 'large'"`
4. Append SCSS rules for size variants
5. Update tests to verify size input
6. Compile and test

**Output**: Status badge component updated with size variants

**Example 4: Delete component**

```json
{
  "mode": "delete",
  "componentName": "old-badge",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "shared",
  "confirmDelete": true
}
```

**Execution**:
1. Check for usage (find no imports)
2. Remove from `shared/components/index.ts`
3. Delete directory: `projects/admin-dashboard/src/app/shared/components/old-badge/`
4. Verify compilation succeeds

**Output**: Component deleted successfully

