## Angular Material form field generation

```yaml
---
name: angular-form-field-composition
description: Create, modify, or delete Angular Material form field components implementing ControlValueAccessor for seamless reactive forms integration with validation and error handling
when_to_use: Use when build_app dispatches a form-field-component procedure node, or when a user runs /angular-form-field-composition to scaffold a Material form-field component that implements ControlValueAccessor for reactive forms.
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

Generate and manage Angular Material form field components that implement `ControlValueAccessor` for seamless integration with Angular reactive forms. These components wrap Material form field elements (`MatFormField`, `MatInput`, `MatSelect`, `MatDatepicker`, `MatAutocomplete`, `MatTextarea`) with custom validation, error messages, labels, hints, and disabled state handling. Unlike simple field-level components (skill 5) which are presentational, form field components implement the full `ControlValueAccessor` interface (`writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`) and provide `NG_VALUE_ACCESSOR`, enabling them to work as custom form controls within `FormGroup` and `FormControl` contexts.

### Modes

All skills support three operational modes:

#### Create

Generate a standalone Angular Material form field component implementing `ControlValueAccessor` with Material form field wrapper, validation support, and test harness.

**Input Requirements**:
- `componentName` (string, required): Name of the form field component in kebab-case (e.g., `email-input`, `date-picker`, `country-select`)
- `workspacePath` (string, required): Absolute path to the Angular workspace root directory
- `appName` (string, required): Name of the application within the workspace (e.g., `my-app`, `admin-dashboard`)
- `placement` (string, required): Where to place the component:
  - `shared` — Place in `projects/<appName>/src/app/shared/form-fields/` (for reusable form fields)
  - `feature/<feature-name>` — Place in `projects/<appName>/src/app/features/<feature-name>/form-fields/` (for feature-specific form fields)
- `fieldType` (enum, required): Type of input field to scaffold:
  - `input` — Text input field (default, supports type="text|number|email|password|tel|url")
  - `textarea` — Multi-line text area
  - `select` — Dropdown select with options
  - `datepicker` — Material datepicker with date input
  - `autocomplete` — Material autocomplete with filtering
- `inputType` (string, optional): HTML input type for `fieldType: 'input'` (default: `'text'`). Options: `text`, `number`, `email`, `password`, `tel`, `url`
- `valueType` (string, optional): TypeScript type for the form control value (default: `string`). Common types: `string`, `number`, `Date`, `boolean`, or custom types
- `validators` (array, optional): List of Angular validators to include (e.g., `['required', 'email', 'minLength', 'maxLength', 'pattern']`). These generate corresponding error message blocks in the template

**Process**:

1. **Validate prerequisites**:
   - Verify workspace exists at `workspacePath` and contains `angular.json`
   - Verify application `appName` exists in `projects/<appName>/`
   - Confirm workspace uses standalone component architecture
   - Validate `componentName` follows naming conventions (lowercase, hyphenated)
   - Check component doesn't already exist at target path

2. **Determine target directory**:
   - If `placement` is `shared`:
     - Target: `projects/<appName>/src/app/shared/form-fields/<componentName>/`
   - If `placement` is `feature/<feature-name>`:
     - Target: `projects/<appName>/src/app/features/<feature-name>/form-fields/<componentName>/`
   - Create directory if it doesn't exist:
     ```bash
     mkdir -p <targetDirectory>
     ```

3. **Generate component TypeScript file** using `{{template:form-field.ts.tpl}}`:
   - Create `<componentName>.component.ts` with:
     - `@Component` decorator with `standalone: true`
     - Implement `ControlValueAccessor` interface with:
       - `writeValue(value: T): void` — Write new value to the component
       - `registerOnChange(fn: (value: T) => void): void` — Register callback for value changes
       - `registerOnTouched(fn: () => void): void` — Register callback for touch events
       - `setDisabledState(isDisabled: boolean): void` — Handle disabled state
     - Provide `NG_VALUE_ACCESSOR` in `providers` array using `forwardRef`
     - Import Material modules based on `fieldType`:
       - **input/textarea**: `MatFormFieldModule`, `MatInputModule`, `ReactiveFormsModule`, `CommonModule`
       - **select**: Add `MatSelectModule`
       - **datepicker**: Add `MatDatepickerModule`, `MatNativeDateModule`
       - **autocomplete**: Add `MatAutocompleteModule`
     - Input signals for configuration:
       - `label = input<string>('')` — Field label text
       - `placeholder = input<string>('')` — Placeholder text
       - `hint = input<string>('')` — Hint text below field
       - `required = input<boolean>(false)` — Required indicator
       - For **select**: `options = input<Array<{value: T, label: string}>>([])`
       - For **datepicker**: `minDate = input<Date | null>(null)`, `maxDate = input<Date | null>(null)`
       - For **autocomplete**: `options = input<Array<T>>([])`, `displayFn = input<(value: T) => string>(() => String)`
     - Internal state properties:
       - `value: T` — Current value
       - `disabled: boolean` — Disabled state
       - `onChange: (value: T) => void` — Change callback
       - `onTouched: () => void` — Touch callback
     - Value change handler:
       - `onValueChange(value: T): void` — Called on user input, propagates to form control
     - Component class with PascalCase naming: `<ComponentName>Component`
     - Selector: `app-<component-name>`
   - Placeholders to replace:
     - `{{FIELD_NAME_KEBAB}}` → e.g., `email-input`
     - `{{FIELD_NAME_PASCAL}}` → e.g., `EmailInput`
     - `{{VALUE_TYPE}}` → e.g., `string`, `number`, `Date`

4. **Generate component HTML template** using `{{template:form-field.html.tpl}}`:
   - Create `<componentName>.component.html` with:
     - Wrap input in `<mat-form-field>` with `appearance="outline"`
     - Add `<mat-label>` bound to `label()` signal
     - Add appropriate input element based on `fieldType`:
       - **input**: `<input matInput [type]="inputType" [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled" [placeholder]="placeholder()">`
       - **textarea**: `<textarea matInput [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled" [placeholder]="placeholder()"></textarea>`
       - **select**: `<mat-select [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled">` with `@for (option of options(); track option.value)` for options
       - **datepicker**: `<input matInput [matDatepicker]="picker" [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled" [min]="minDate()" [max]="maxDate()">` with `<mat-datepicker #picker></mat-datepicker>`
       - **autocomplete**: `<input matInput [matAutocomplete]="auto" [(ngModel)]="value" (ngModelChange)="onValueChange($event)" [disabled]="disabled">` with `<mat-autocomplete #auto="matAutocomplete">`
     - Add `<mat-hint>` bound to `hint()` signal
     - Add `<mat-error>` blocks for each validator:
       - **required**: `@if (formControl?.hasError('required')) { <mat-error>This field is required</mat-error> }`
       - **email**: `@if (formControl?.hasError('email')) { <mat-error>Please enter a valid email</mat-error> }`
       - **minlength**: `@if (formControl?.hasError('minlength')) { <mat-error>Minimum length is {{ formControl.errors?.['minlength'].requiredLength }}</mat-error> }`
       - **maxlength**: `@if (formControl?.hasError('maxlength')) { <mat-error>Maximum length is {{ formControl.errors?.['maxlength'].requiredLength }}</mat-error> }`
       - **pattern**: `@if (formControl?.hasError('pattern')) { <mat-error>Invalid format</mat-error> }`
     - Note: Error messages require access to parent form control. Pass via input: `formControl = input<FormControl | null>(null)`
     - Use modern control flow (`@if`, `@for`) instead of `*ngIf`, `*ngFor`
     - Add ARIA attributes: `[attr.aria-required]="required()"`, `[attr.aria-invalid]="formControl?.invalid && formControl?.touched"`

5. **Generate component SCSS file** using `{{template:component.scss.tpl}}`:
   - Create `<componentName>.component.scss` with:
     - `:host` selector with `display: block; width: 100%;`
     - Material theme token usage for colors
     - Responsive sizing
   - Example structure:
     ```scss
     @use '@angular/material' as mat;

     :host {
       display: block;
       width: 100%;

       mat-form-field {
         width: 100%;
       }
     }
     ```

6. **Generate component spec file**:
   - Create `<componentName>.component.spec.ts` with:
     - Import `ReactiveFormsModule` and `FormControl` for testing
     - Import Material test harnesses: `MatFormFieldHarness`, `MatInputHarness` (or appropriate harness for field type)
     - Test suite structure:
       - **should create** — Component initialization test
       - **ControlValueAccessor tests**:
         - `writeValue()` should update internal value
         - `registerOnChange()` should register callback
         - `registerOnTouched()` should register callback
         - `setDisabledState()` should disable/enable input
         - Value changes should call `onChange` callback
         - Blur events should call `onTouched` callback
       - **Reactive forms integration test**:
         - Create `FormControl` and bind to component
         - Set value via form control, verify component updates
         - Change value in component, verify form control updates
         - Set form control to disabled, verify component disables
       - **Validation tests** (if validators specified):
         - Test error messages display correctly
         - Test required validation
         - Test specific validators (email, minLength, etc.)
       - **Material harness tests**:
         - Use `MatFormFieldHarness` to verify label, hint, error display
         - Use input harness to interact with input programmatically
     - Example test structure:
       ```typescript
       import { ComponentFixture, TestBed } from '@angular/core/testing';
       import { ReactiveFormsModule, FormControl, Validators } from '@angular/forms';
       import { HarnessLoader } from '@angular/cdk/testing';
       import { TestbedHarnessEnvironment } from '@angular/cdk/testing/testbed';
       import { MatFormFieldHarness } from '@angular/material/form-field/testing';
       import { MatInputHarness } from '@angular/material/input/testing';
       import { EmailInputComponent } from './email-input.component';
       import { NoopAnimationsModule } from '@angular/platform-browser/animations';

       describe('EmailInputComponent', () => {
         let component: EmailInputComponent;
         let fixture: ComponentFixture<EmailInputComponent>;
         let loader: HarnessLoader;

         beforeEach(async () => {
           await TestBed.configureTestingModule({
             imports: [
               EmailInputComponent,
               ReactiveFormsModule,
               NoopAnimationsModule
             ]
           }).compileComponents();

           fixture = TestBed.createComponent(EmailInputComponent);
           component = fixture.componentInstance;
           loader = TestbedHarnessEnvironment.loader(fixture);
           fixture.detectChanges();
         });

         it('should create', () => {
           expect(component).toBeTruthy();
         });

         it('should implement ControlValueAccessor writeValue', () => {
           component.writeValue('test@example.com');
           expect(component.value).toBe('test@example.com');
         });

         it('should call onChange when value changes', () => {
           const onChangeSpy = jasmine.createSpy('onChange');
           component.registerOnChange(onChangeSpy);

           component.onValueChange('new@example.com');

           expect(onChangeSpy).toHaveBeenCalledWith('new@example.com');
         });

         it('should integrate with reactive forms', async () => {
           const formControl = new FormControl('initial@example.com');

           // Bind component to form control
           component.writeValue(formControl.value);
           component.registerOnChange((value) => formControl.setValue(value, { emitEvent: false }));

           // Test form -> component
           formControl.setValue('updated@example.com');
           component.writeValue(formControl.value);
           expect(component.value).toBe('updated@example.com');

           // Test component -> form
           component.onValueChange('changed@example.com');
           expect(formControl.value).toBe('changed@example.com');
         });

         it('should display error messages using harness', async () => {
           const formControl = new FormControl('', Validators.required);
           component.formControl = () => formControl;
           formControl.markAsTouched();
           fixture.detectChanges();

           const formField = await loader.getHarness(MatFormFieldHarness);
           const errors = await formField.getTextErrors();

           expect(errors).toContain('This field is required');
         });

         it('should disable input when setDisabledState is called', async () => {
           component.setDisabledState(true);
           fixture.detectChanges();

           const input = await loader.getHarness(MatInputHarness);
           expect(await input.isDisabled()).toBe(true);
         });
       });
       ```

7. **Update barrel export** (if placement is `shared` or feature has barrel file):
   - Append to `shared/form-fields/index.ts` or `features/<feature-name>/form-fields/index.ts`:
     ```typescript
     export * from './<componentName>/<componentName>.component';
     ```

8. **Compile check**:
   ```bash
   cd <workspacePath>
   ng build <appName> --configuration=development
   ```
   - Verify build succeeds with no errors

9. **Run specs**:
   ```bash
   ng test <appName> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Verify all tests pass

**Output**:
- Component files created: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`
- Component implements `ControlValueAccessor` interface
- Component integrated with reactive forms via `NG_VALUE_ACCESSOR`
- Validation and error handling configured
- Material form field wrapper with label, hint, error messages
- Test harness tests passing
- Barrel export updated
- Compilation successful

#### Modify

Update an existing form field component to change input type, add/remove validators, update error messages, or modify configuration.

**Input Requirements**:
- `componentName` (string, required): Name of the form field component to modify
- `workspacePath` (string, required): Absolute path to the Angular workspace root directory
- `appName` (string, required): Name of the application within the workspace
- `placement` (string, required): Where the component is located (`shared` or `feature/<feature-name>`)
- `modifications` (object, required): Specifies what to modify:
  - `changeFieldType` (enum, optional): Change to different field type (`input` | `textarea` | `select` | `datepicker` | `autocomplete`)
  - `changeInputType` (string, optional): Change HTML input type (for `fieldType: 'input'`)
  - `changeValueType` (string, optional): Change TypeScript value type (requires updating generics throughout)
  - `addValidators` (array, optional): Add validators and corresponding error messages
  - `removeValidators` (array, optional): Remove validators and error message blocks
  - `updateErrorMessages` (object, optional): Map of validator names to new error message templates
  - `addInputSignals` (array, optional): Add new input signals (e.g., `[{ name: 'maxLength', type: 'number', default: '100' }]`)
  - `updateStyles` (string, optional): Additional SCSS to append

**Process**:

1. **Validate prerequisites**:
   - Verify component exists at target path
   - Read existing component files to understand current structure
   - Verify requested modifications are compatible with current implementation

2. **Apply modifications based on modification type**:

   **If `changeFieldType` specified**:
   - This is a significant change requiring updates to TypeScript, HTML, and imports
   - Read current component TypeScript file
   - Update imports:
     - Remove old Material module imports (e.g., `MatInputModule` if changing from `input`)
     - Add new Material module imports based on new `fieldType`
   - Update template file completely:
     - Replace input element markup with new field type markup
     - Preserve existing `@if` error blocks
     - Update bindings to match new field type requirements
   - Update spec file:
     - Change harness imports to match new field type
     - Update test interactions to use correct harness methods

   **If `addValidators` specified**:
   - For each validator in list:
     - Add corresponding `<mat-error>` block to HTML template
     - Use modern `@if` syntax with `formControl?.hasError('validatorName')`
     - Use appropriate error message template:
       - `required`: "This field is required"
       - `email`: "Please enter a valid email"
       - `minlength`: "Minimum length is {{requiredLength}}"
       - `maxlength`: "Maximum length is {{requiredLength}}"
       - `min`: "Minimum value is {{min}}"
       - `max`: "Maximum value is {{max}}"
       - `pattern`: "Invalid format"
   - Update spec file to add tests for new validators

   **If `removeValidators` specified**:
   - For each validator in list:
     - Remove corresponding `<mat-error>` block from HTML template
     - Remove validator tests from spec file

   **If `updateErrorMessages` specified**:
   - For each validator in map:
     - Find and replace the error message text in the `<mat-error>` block
     - Preserve the `@if` condition structure

   **If `addInputSignals` specified**:
   - For each signal to add:
     - Add signal declaration to TypeScript: `<name> = input<<type>>(<default>)`
     - Add binding to HTML template where appropriate
     - Update spec tests to verify new input signal

   **If `updateStyles` specified**:
   - Append provided SCSS to `.component.scss` file
   - Ensure no duplicate selectors

3. **Update spec file**:
   - Add tests for any new functionality
   - Update existing tests if behavior changed
   - Ensure all ControlValueAccessor tests still pass

4. **Compile check**:
   ```bash
   cd <workspacePath>
   ng build <appName> --configuration=development
   ```

5. **Run specs**:
   ```bash
   ng test <appName> --watch=false --include='**/<componentName>.component.spec.ts'
   ```

**Output**:
- Component files updated with requested modifications
- All tests passing
- Compilation successful
- Changes documented in commit message

#### Delete

Remove a form field component completely from the codebase, including all related files and imports.

**Input Requirements**:
- `componentName` (string, required): Name of the form field component to delete
- `workspacePath` (string, required): Absolute path to the Angular workspace root directory
- `appName` (string, required): Name of the application within the workspace
- `placement` (string, required): Where the component is located (`shared` or `feature/<feature-name>`)
- `confirmDelete` (boolean, required): Explicit confirmation flag to prevent accidental deletion
- `force` (boolean, optional): Force deletion even if component is still imported elsewhere (default: `false`)

**Process**:

1. **Validate prerequisites**:
   - Verify component exists at target path
   - Confirm `confirmDelete` is `true`

2. **Check for component usage**:
   - Search for imports of the component across codebase:
     ```bash
     grep -r "from.*<componentName>.component" projects/<appName>/src/
     ```
   - If imports found and `force` is `false`:
     - Return error listing files that import the component
     - Require user to remove imports first or use `force: true`

3. **Remove from barrel exports**:
   - If `placement` is `shared`:
     - Remove export line from `shared/form-fields/index.ts`
   - If `placement` is `feature/<feature-name>`:
     - Remove export line from `features/<feature-name>/form-fields/index.ts` (if exists)

4. **Delete component directory**:
   - Determine target directory based on `placement`
   - Delete entire directory:
     ```bash
     rm -rf <targetDirectory>/<componentName>/
     ```

5. **Remove from any imports arrays** (if `force: true` and usages found):
   - Search for component usage in component `imports` arrays
   - Remove from component imports
   - This is a potentially breaking change, so log all modified files

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
- All component imports removed from codebase (if `force: true`)
- Compilation successful
- Confirmation message with deletion summary

### Context Files

{{context:../../shared/angular-conventions.md}}

{{context:../../shared/angular-material-patterns.md}}

### Templates

- `form-field.ts.tpl` — ControlValueAccessor TypeScript scaffold with `writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`, `NG_VALUE_ACCESSOR` provider, and typed signals
- `form-field.html.tpl` — Material form field template with `<mat-form-field>`, appropriate input element based on field type, label, hint, and error message blocks
- `component.scss.tpl` — Component styles using Material theme tokens and `:host` selector pattern

### Validation

Steps to validate successful execution of the skill:

**Post-Create Validation**:
1. **Verify directory structure**:
   ```bash
   ls -la <targetDirectory>/<componentName>/
   ```
   - Should contain: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`

2. **Verify ControlValueAccessor implementation**:
   ```bash
   grep "implements ControlValueAccessor" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should return match

3. **Verify NG_VALUE_ACCESSOR provider**:
   ```bash
   grep "NG_VALUE_ACCESSOR" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find provider configuration with `forwardRef`

4. **Verify required CVA methods**:
   ```bash
   grep -E "writeValue|registerOnChange|registerOnTouched|setDisabledState" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find all four interface methods

5. **Verify Material form field wrapper**:
   ```bash
   grep "<mat-form-field" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should find `<mat-form-field>` wrapper

6. **Verify error message blocks**:
   ```bash
   grep -E "@if.*hasError.*mat-error" <targetDirectory>/<componentName>/<componentName>.component.html
   ```
   - Should find error handling with modern `@if` syntax

7. **Verify signal usage**:
   ```bash
   grep -E "input<|output<" <targetDirectory>/<componentName>/<componentName>.component.ts
   ```
   - Should find typed input signals for label, placeholder, hint, etc.

8. **Compile check**:
   ```bash
   ng build <appName> --configuration=development
   ```
   - Should complete without errors

9. **Run specs**:
   ```bash
   ng test <appName> --watch=false --include='**/<componentName>.component.spec.ts'
   ```
   - Should pass all tests including CVA tests

10. **Check Material test harness usage**:
    ```bash
    grep "FormFieldHarness" <targetDirectory>/<componentName>/<componentName>.component.spec.ts
    ```
    - Should find Material form field test harness imports and usage

**Post-Modify Validation**:
1. **Verify requested changes applied**:
   - Check TypeScript file for updated field type, validators, or signals
   - Check template for new error message blocks
   - Check styles for new SCSS rules

2. **Compile and test** (same as create mode steps 8-9)

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
- **Resolution**: Convert name to kebab-case (e.g., `EmailInput` → `email-input`)

**Error**: `Material module <ModuleName> not found`
- **Cause**: Specified Material module doesn't exist or isn't installed
- **Resolution**: Verify Material is installed (`@angular/material` in `package.json`) and module name is correct

**Error**: `NG_VALUE_ACCESSOR provider not found`
- **Cause**: Component missing `NG_VALUE_ACCESSOR` provider configuration
- **Resolution**: Add provider object with `provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => Component), multi: true`

**Error**: `ControlValueAccessor interface not fully implemented`
- **Cause**: Missing one or more required interface methods
- **Resolution**: Ensure all four methods are implemented: `writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`

**Error**: `Cannot read formControl in template`
- **Cause**: `formControl` input signal not declared or not passed from parent
- **Resolution**: Add `formControl = input<FormControl | null>(null)` to component and pass from parent template

**Error**: `Compilation failed: Type mismatch in writeValue`
- **Cause**: Value type doesn't match declared `valueType`
- **Resolution**: Ensure all CVA methods use consistent generic type parameter

**Error**: `Tests failing: onChange not called`
- **Cause**: Value change handler not calling registered `onChange` callback
- **Resolution**: Ensure `onValueChange` method calls `this.onChange(value)` and `this.onTouched()`

**Error**: `Component is still imported in X files`
- **Cause**: Attempting to delete component that's still in use
- **Resolution**: Remove imports from listed files first, or use `force: true` flag to auto-remove

**Error**: `Validator error messages not displaying`
- **Cause**: Parent form control not passed to component or not marked as touched
- **Resolution**: Pass form control via input and ensure `markAsTouched()` is called on blur

### Dependencies

Required prerequisites before executing this skill:

1. **Angular Material workspace boilerplate** (Skill 1) — Workspace must exist with Angular Material installed
2. **Angular Material app boilerplate** (Skill 2) — Application must exist in workspace with proper directory structure

Optional dependencies:

- None — This skill is independent and can be executed once workspace and app exist

Dependent skills (use this skill before):

- **Angular Material reactive form generation** (Skill 9) — Forms use form field components as custom controls
- **Angular Material page generation** (Skill 10) — Pages may include forms with custom form fields
- **Angular component generation** (Skill 7) — Complex components may compose form fields

### Examples

**Example 1: Create an email input form field in shared**

```json
{
  "mode": "create",
  "componentName": "email-input",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "shared",
  "fieldType": "input",
  "inputType": "email",
  "valueType": "string",
  "validators": ["required", "email"]
}
```

**Execution**:
1. Validate workspace and app exist
2. Create directory: `projects/admin-dashboard/src/app/shared/form-fields/email-input/`
3. Generate TypeScript component with:
   - Implements `ControlValueAccessor`
   - Provides `NG_VALUE_ACCESSOR`
   - Imports: `MatFormFieldModule`, `MatInputModule`, `ReactiveFormsModule`, `CommonModule`
   - Input signals: `label`, `placeholder`, `hint`, `required`, `formControl`
   - CVA methods: `writeValue`, `registerOnChange`, `registerOnTouched`, `setDisabledState`
   - Value type: `string`
4. Generate HTML template:
   ```html
   <mat-form-field appearance="outline">
     <mat-label>{{ label() }}</mat-label>
     <input matInput
            type="email"
            [(ngModel)]="value"
            (ngModelChange)="onValueChange($event)"
            (blur)="onTouched()"
            [disabled]="disabled"
            [placeholder]="placeholder()"
            [attr.aria-required]="required()"
            [attr.aria-invalid]="formControl()?.invalid && formControl()?.touched">
     @if (hint()) {
       <mat-hint>{{ hint() }}</mat-hint>
     }
     @if (formControl()?.hasError('required')) {
       <mat-error>This field is required</mat-error>
     }
     @if (formControl()?.hasError('email')) {
       <mat-error>Please enter a valid email address</mat-error>
     }
   </mat-form-field>
   ```
5. Generate SCSS with `:host` and theme tokens
6. Generate spec with CVA tests and Material harness tests
7. Update `shared/form-fields/index.ts`: `export * from './email-input/email-input.component';`
8. Compile and test

**Output**: Email input form field component created at `projects/admin-dashboard/src/app/shared/form-fields/email-input/`

**Example 2: Create a country select form field in a feature**

```json
{
  "mode": "create",
  "componentName": "country-select",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "feature/users",
  "fieldType": "select",
  "valueType": "string",
  "validators": ["required"]
}
```

**Execution**:
1. Create directory: `projects/admin-dashboard/src/app/features/users/form-fields/country-select/`
2. Generate component with:
   - Field type: `select`
   - Input signal: `options = input<Array<{value: string, label: string}>>([])`
   - CVA implementation for `string` value type
   - Imports: `MatFormFieldModule`, `MatSelectModule`, `ReactiveFormsModule`, `CommonModule`
3. Generate template with:
   ```html
   <mat-form-field appearance="outline">
     <mat-label>{{ label() }}</mat-label>
     <mat-select [(ngModel)]="value"
                 (ngModelChange)="onValueChange($event)"
                 (blur)="onTouched()"
                 [disabled]="disabled"
                 [placeholder]="placeholder()">
       @for (option of options(); track option.value) {
         <mat-option [value]="option.value">{{ option.label }}</mat-option>
       }
     </mat-select>
     @if (formControl()?.hasError('required')) {
       <mat-error>Please select a country</mat-error>
     }
   </mat-form-field>
   ```
4. Compile and test

**Output**: Country select form field component created in users feature

**Example 3: Create a date picker form field with min/max date**

```json
{
  "mode": "create",
  "componentName": "birth-date-picker",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "feature/users",
  "fieldType": "datepicker",
  "valueType": "Date",
  "validators": ["required"]
}
```

**Execution**:
1. Create directory: `projects/admin-dashboard/src/app/features/users/form-fields/birth-date-picker/`
2. Generate component with:
   - Field type: `datepicker`
   - Input signals: `minDate = input<Date | null>(null)`, `maxDate = input<Date | null>(null)`
   - CVA implementation for `Date` value type
   - Imports: `MatFormFieldModule`, `MatInputModule`, `MatDatepickerModule`, `MatNativeDateModule`, `ReactiveFormsModule`, `CommonModule`
3. Generate template with:
   ```html
   <mat-form-field appearance="outline">
     <mat-label>{{ label() }}</mat-label>
     <input matInput
            [matDatepicker]="picker"
            [(ngModel)]="value"
            (ngModelChange)="onValueChange($event)"
            (blur)="onTouched()"
            [disabled]="disabled"
            [placeholder]="placeholder()"
            [min]="minDate()"
            [max]="maxDate()">
     <mat-datepicker-toggle matSuffix [for]="picker"></mat-datepicker-toggle>
     <mat-datepicker #picker></mat-datepicker>
     @if (formControl()?.hasError('required')) {
       <mat-error>Birth date is required</mat-error>
     }
   </mat-form-field>
   ```
4. Compile and test

**Output**: Birth date picker form field component created in users feature

**Example 4: Modify existing form field to add validator**

```json
{
  "mode": "modify",
  "componentName": "email-input",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "shared",
  "modifications": {
    "addValidators": ["maxlength"],
    "addInputSignals": [
      { "name": "maxLength", "type": "number", "default": "100" }
    ]
  }
}
```

**Execution**:
1. Read existing `email-input.component.ts`
2. Add input signal: `maxLength = input<number>(100)`
3. Read existing `email-input.component.html`
4. Add error block after existing error blocks:
   ```html
   @if (formControl()?.hasError('maxlength')) {
     <mat-error>Maximum length is {{ formControl()?.errors?.['maxlength'].requiredLength }}</mat-error>
   }
   ```
5. Update spec file to add test for maxlength validator
6. Compile and test

**Output**: Email input form field updated with maxlength validation

**Example 5: Change field type from input to textarea**

```json
{
  "mode": "modify",
  "componentName": "description-input",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "shared",
  "modifications": {
    "changeFieldType": "textarea"
  }
}
```

**Execution**:
1. Read existing `description-input.component.ts`
2. Verify imports already include `MatInputModule` (works for both input and textarea)
3. Read existing `description-input.component.html`
4. Replace `<input matInput>` with `<textarea matInput rows="5"></textarea>`
5. Preserve all existing attributes, bindings, and error blocks
6. Update spec file harness tests (MatInputHarness works for both)
7. Compile and test

**Output**: Description input changed from single-line input to multi-line textarea

**Example 6: Delete form field component**

```json
{
  "mode": "delete",
  "componentName": "old-phone-input",
  "workspacePath": "/workspace/my-project",
  "appName": "admin-dashboard",
  "placement": "shared",
  "confirmDelete": true
}
```

**Execution**:
1. Check for usage (find no imports)
2. Remove from `shared/form-fields/index.ts`
3. Delete directory: `projects/admin-dashboard/src/app/shared/form-fields/old-phone-input/`
4. Verify compilation succeeds

**Output**: Form field component deleted successfully
