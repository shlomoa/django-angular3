## Angular Material complex component generation

**Skill Name**: `angular-complex-component-composition`

### YAML Frontmatter

```yaml
---
name: angular-complex-component-composition
description: Create, modify, or delete Angular Material complex components with theme mixins, nested child components, content projection, and CDK overlay integration
when_to_use: Use when build_app dispatches a complex-component procedure node, or when a user runs /angular-complex-component-composition to scaffold a Material component requiring theme mixins, content projection, child components, or CDK overlay integration.
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

The `angular-complex-component-composition` skill manages Angular Material components that go beyond a single standalone component scaffold. It is used when a component needs one or more advanced composition features: a dedicated theme mixin, nested child components, typed content projection slots, or CDK overlay behavior. The skill keeps the component aligned with the simpler `angular-component-composition` conventions while expanding the generated structure to cover public API documentation, theming integration, and multi-file component composition.

### Inputs

**From invocation context**:
- **`componentName`** (string, required): Component name in kebab-case (e.g., `user-menu`, `filter-builder`)
- **`targetPath`** (string, required): Relative path from app source directory where the component directory will be created
- **`workspacePath`** (string, required): Absolute path to the Angular workspace root
- **`appName`** (string, optional): Angular application name, required for multi-app workspaces
- **`features`** (array, required): List of advanced features to enable. Allowed values:
  - `mixins`
  - `nested`
  - `projection`
  - `cdk-overlay`

### Modes

All skills support three operational modes:

#### Create

Generate a new Angular Material complex component from scratch.

**Input Requirements**:
- `componentName` must be valid kebab-case
- `targetPath` must resolve inside the Angular application source tree
- `workspacePath` must contain a valid Angular workspace
- `features` must contain one or more supported feature flags

**Pre-flight Checks**:

Before creating the component, verify:

1. `angular.json` exists under `workspacePath`
2. Target application exists if `appName` is specified
3. Angular Material and `@angular/cdk` are installed when `cdk-overlay` is requested
4. The target component directory does not already exist
5. Root theme entrypoint (typically `src/styles.scss`) exists and is writable when `mixins` is requested

**Process (Create Mode)**:

1. **Generate the parent standalone component scaffold**:
   ```bash
   cd <workspacePath>
   ng generate component <targetPath>/<componentName> --standalone --skip-tests=false --style=scss --project=<appName>
   ```

2. **Replace the generated parent component** with a Material-oriented complex component implementation that:
   - uses standalone imports
   - keeps Angular Material imports explicit
   - adds a top-level JSDoc block documenting the public API:
     - inputs
     - outputs
     - projection slots
   - exposes only the supported public surface

3. **Apply feature: `mixins`**:
   - Create `_<componentName>-theme.scss` in the component directory
   - Define a named mixin for the component theme contract, for example:
     ```scss
     @use '@angular/material' as mat;

     @mixin <componentName>-theme($theme) {
       .app-<componentName> {
         color: mat.get-theme-color($theme, primary, 500);
       }
     }
     ```
   - Update the application theme entrypoint (`styles.scss`) to import and include the mixin
   - Keep theme styling in the mixin file instead of duplicating theme token logic inline

4. **Apply feature: `nested`**:
   - Generate child components inside `<targetPath>/<componentName>/`
   - Use focused names for child components such as `header`, `content`, `actions`, or domain-specific names like `filter-panel` and `result-summary`
   - Import the generated child components into the parent component `imports` array
   - Keep the parent component responsible for composition and high-level orchestration only

5. **Apply feature: `projection`**:
   - Add one or more projection slots using explicit selectors:
     ```html
     <ng-content select="[slot=title]"></ng-content>
     <ng-content select="[slot=actions]"></ng-content>
     ```
   - Create typed marker directives for each supported slot so the public API is discoverable and template usage is constrained
   - Document each slot in the parent component JSDoc block

6. **Apply feature: `cdk-overlay`**:
   - Use Angular CDK overlay primitives, not ad hoc DOM manipulation
   - Inject and use:
     - `Overlay`
     - `OverlayRef`
     - `ComponentPortal`
   - Keep overlay creation, attachment, disposal, and teardown inside the parent component or a tightly scoped helper service/provider
   - Register only the providers needed for the generated overlay behavior

7. **Generate tests and support files consistent with the selected features**:
   - Parent component spec remains at `<componentName>.component.spec.ts`
   - Child component specs are generated when nested components are created
   - Overlay-enabled components verify attach/detach behavior at the unit level when spec coverage is present in the workspace

**Output**:
- Parent component directory created at `<targetPath>/<componentName>/`
- Parent component files:
  - `<componentName>.component.ts`
  - `<componentName>.component.html`
  - `<componentName>.component.scss`
  - `<componentName>.component.spec.ts`
- Optional feature files:
  - `_<componentName>-theme.scss`
  - child component directories under `<componentName>/`
  - typed slot directives
  - overlay-specific providers or support files when required

#### Modify

Update an existing complex component by adding advanced composition features without rebuilding the entire component.

**Input Requirements**:
- `componentName` must reference an existing component directory
- `targetPath` and `workspacePath` must point to valid existing paths
- `features` must describe the feature(s) to add or expand

**Process**:

1. Read the current parent component, template, styles, tests, and any existing child components
2. Preserve the existing public API unless the requested change explicitly expands it
3. For requested modifications:
   - **Add mixin**:
     - create `_<componentName>-theme.scss` if missing
     - extract theme-specific rules into the mixin
     - add the import/include in `styles.scss`
   - **Extract child**:
     - move a cohesive template region into a child component inside `<componentName>/`
     - add the child component to the parent `imports`
     - keep existing bindings flowing through typed inputs/outputs
   - **Add projection slot**:
     - add a new `<ng-content select="...">` slot
     - add the corresponding typed directive
     - extend the parent JSDoc block with the new slot contract
4. Re-run a compile check after modifications

**Output**:
- Existing component updated in place
- Public API documentation refreshed
- Theme, child component, or slot support added without deleting unaffected files

#### Delete

Remove a complex component and its advanced integrations completely.

**Input Requirements**:
- `componentName` must reference an existing complex component
- `targetPath` must resolve to the existing component directory
- `workspacePath` must point to the Angular workspace root
- `confirm` (required): Must be `true`

**Process**:

1. Verify the component directory exists and identify all references
2. Remove the full component directory tree:
   ```bash
   rm -rf <targetPath>/<componentName>
   ```
3. If `mixins` was enabled:
   - remove the theme mixin import from `styles.scss`
   - remove the `@include` statement for the component theme mixin
4. If `cdk-overlay` was enabled:
   - remove CDK overlay-specific providers or helper registrations introduced for the component
   - remove overlay portal imports that are now unused
5. Remove any parent-level imports, route references, or barrel exports that still reference the component or extracted children
6. Re-run a compile check to ensure all references were removed

**Output**:
- Component directory tree removed
- Theme mixin usage removed from `styles.scss`
- CDK providers and imports cleaned up
- Remaining manual cleanup locations reported if unrelated templates still reference the deleted selectors

### Context Files

{{context:../../shared/angular-conventions.md}}

{{context:../../shared/angular-material-patterns.md}}

### Templates

None

### Validation

Steps to validate successful execution of the skill:

1. **Verify the complex component directory structure**:
   ```bash
   ls -la <targetPath>/<componentName>/
   ```
   - Should include the parent component files
   - Should include child directories or `_<componentName>-theme.scss` when requested

2. **Compile check**:
   ```bash
   ng build <appName> --configuration=development
   ```
   - Should complete without TypeScript, template, or styling errors

3. **Theme injection verified**:
   ```bash
   grep -n "<componentName>-theme" <workspacePath>/src/styles.scss
   ```
   - Should show the mixin import/include when `mixins` is enabled
   - Should return no matches after Delete mode cleanup

4. **Projection slot verification**:
   ```bash
   grep -n '<ng-content select="' <targetPath>/<componentName>/<componentName>.component.html
   ```
   - Should show explicit projection slots when `projection` is enabled

5. **Nested component verification**:
   ```bash
   grep -n "imports:" <targetPath>/<componentName>/<componentName>.component.ts
   ```
   - Parent component should import generated child components when `nested` is enabled

6. **CDK overlay verification**:
   ```bash
   grep -E "Overlay|OverlayRef|ComponentPortal" <targetPath>/<componentName>/<componentName>.component.ts
   ```
   - Should show CDK overlay primitives when `cdk-overlay` is enabled

### Error Handling

Common errors and their resolution strategies:

**Error**: `Unsupported complex component feature: <feature>. Supported features are: mixins, nested, projection, cdk-overlay`
- **Cause**: The `features` list contains an unknown value
- **Resolution**: Restrict the feature list to `mixins`, `nested`, `projection`, and `cdk-overlay`

**Error**: `Theme entrypoint not found`
- **Cause**: `styles.scss` could not be located for theme mixin registration
- **Resolution**: Verify the workspace uses a writable global theme entrypoint before enabling `mixins`

**Error**: `Projection slot selector already exists`
- **Cause**: Attempting to add a duplicate slot
- **Resolution**: Reuse the existing slot or choose a different selector/directive name

**Error**: `Cannot find module '@angular/cdk/overlay'`
- **Cause**: CDK overlay support is requested but Angular CDK is not available
- **Resolution**: Install or restore Angular CDK before enabling `cdk-overlay`

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1 - ng-workspace)
2. **Angular Material app boilerplate** (Skill 2 - ng-app)
3. **Angular component generation** (Skill 7 - ng-component) conventions should already be understood and available for reuse

### Examples

**Example 1: Create a themed complex component with nested children**

```json
{
  "componentName": "user-menu",
  "targetPath": "src/app/shared/components",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "features": ["mixins", "nested", "projection"]
}
```

**Example 2: Add overlay behavior to an existing complex component**

```json
{
  "componentName": "filter-builder",
  "targetPath": "src/app/features/search",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "features": ["cdk-overlay"]
}
```
