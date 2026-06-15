## Angular reactive form generation

```yaml
---
name: angular-reactive-form-composition
description: Create, modify, or delete Angular Material reactive forms with typed FormGroup, FormBuilder scaffolding, Material form fields, server-side validation error handling, and comprehensive specs
when_to_use: Use when build_app dispatches a reactive-form procedure node, or when a user runs /angular-reactive-form-composition to scaffold a typed Material reactive form with FormBuilder, validation, and server-error handling.
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

The `angular-reactive-form-composition` skill manages Angular reactive form components that use typed `FormGroup<>` interfaces, `FormBuilder` for control creation, Angular Material form fields (`MatFormField`), and integrate with data services for submission. These forms implement loading states with `MatProgressBar`, handle server-side validation errors by calling `setErrors()` on individual controls, wire submit actions to data service methods, and provide cancel handlers for navigation or output events. Forms can operate in create mode (empty initial values), edit mode (pre-populated from resource), or both modes (dynamic based on route parameters).

### Inputs

- `formName` (string, required): Name of the form component in kebab-case (e.g., `user-profile`, `order-create`, `product-edit`)
- `workspacePath` (string, required): Absolute path to the Angular workspace root directory
- `appName` (string, required): Name of the application within the workspace
- `targetPath` (string, required): Relative path from app source where form should be placed (e.g., `features/users/forms`, `shared/forms`)
- `mode` (enum, required): Form operational mode:
  - `create` — Form for creating new resources (empty initial values)
  - `edit` — Form for editing existing resources (pre-populated from resource)
  - `both` — Form supporting both create and edit based on route parameters or input
- `resourceName` (string, optional): Name of the resource this form operates on. If provided, the skill will:
  - Inspect generated API models from `angular-api-integration` output to derive field types
  - Create typed `FormGroup<>` interface matching the model structure
  - Wire submit to corresponding data service method (e.g., `createUser()`, `updateUser()`)
  - If not provided, form fields must be manually specified

### Modes

#### Create

Generate a new Angular reactive form component from scratch with typed `FormGroup<>`, Material form fields, validation, loading state, server error handling, and comprehensive spec tests.

**Input Requirements**:
- `formName` (string): Form component name in kebab-case
- `workspacePath` (string): Workspace root path
- `appName` (string): Application name
- `targetPath` (string): Target directory relative to app source
- `mode` (enum): `create`, `edit`, or `both`
- `resourceName` (string, optional): Resource name for API integration

**Process**:

1. **Pre-flight validation**:
   - Verify workspace exists at `workspacePath` and contains `angular.json`
   - Verify application `appName` exists in `projects/<appName>/`
   - Validate `formName` follows naming conventions (lowercase, hyphenated)
   - Check form component doesn't already exist at `targetPath/<formName>/`
   - If `resourceName` is provided:
     - Verify generated API models exist from `angular-api-integration` skill output
     - Verify corresponding data service exists from `angular-data-service-composition` skill
     - Extract field names and types from the resource model

2. **Determine target directory**:
   - Resolve full path: `projects/<appName>/src/app/<targetPath>/<formName>/`
   - Create directory if it doesn't exist:
     ```bash
     mkdir -p <targetDirectory>
     ```

3. **Inspect resource model** (if `resourceName` provided):
   - Locate generated model at `src/app/api/models/<resource-name>.ts`
   - Parse model interface to extract:
     - Field names (convert to camelCase for form controls)
     - Field types (string, number, boolean, Date, custom types)
     - Optional vs required fields (use `?` indicator)
     - Nested objects (flatten to form controls or create nested `FormGroup`)
   - Map TypeScript types to appropriate validators:
     - `string` fields → `Validators.required`, `Validators.minLength()`, `Validators.maxLength()`
     - `email` or `*Email` fields → `Validators.email`
     - `number` fields → `Validators.required`, `Validators.min()`, `Validators.max()`
     - `Date` fields → `Validators.required`
     - Optional fields → omit `Validators.required`

4. **Generate TypeScript file** using `{{template:reactive-form.ts.tpl}}`:
   - Create `<formName>.component.ts` with:
     - `@Component` decorator with `standalone: true`
     - Typed form interface:
       ```typescript
       interface {{FORM_NAME_PASCAL}}Form {
         fieldName: FormControl<string>;
         anotherField: FormControl<number>;
         optionalField: FormControl<string | null>;
       }
       ```
     - Component class with PascalCase: `{{FORM_NAME_PASCAL}}Component`
     - Selector: `app-{{FORM_NAME_KEBAB}}-form`
     - Import required Material modules:
       - `MatFormFieldModule`, `MatInputModule`, `MatButtonModule`
       - `MatCardModule` (for form container)
       - `MatProgressBarModule` (for loading state)
       - Additional modules based on field types (e.g., `MatSelectModule`, `MatDatepickerModule`)
     - Import `ReactiveFormsModule`, `CommonModule`
     - Inject `FormBuilder` using `inject()` function
     - If `resourceName` provided: Inject corresponding data service (e.g., `UsersService`)
     - Signals for state management:
       - `loading = signal(false)` — Loading state during form submission
       - `serverErrors = signal<Record<string, string[]> | null>(null)` — Server validation errors
     - Outputs:
       - `formSubmit = output<FormValue>()` — Emitted on successful submission (for parent component handling)
       - `formCancel = output<void>()` — Emitted when user cancels
     - Typed `FormGroup`:
       ```typescript
       form: FormGroup<{{FORM_NAME_PASCAL}}Form> = this.fb.group({
         fieldName: this.fb.control('', {
           nonNullable: true,
           validators: [Validators.required, Validators.minLength(2)]
         }),
         numberField: this.fb.control(0, {
           nonNullable: true,
           validators: [Validators.required, Validators.min(0)]
         }),
         optionalField: this.fb.control<string | null>(null)
       });
       ```
     - **Mode: Create** — Form starts with empty values
     - **Mode: Edit** — Add input signal:
       ```typescript
       initialValue = input<ResourceModel | null>(null);

       ngOnInit(): void {
         if (this.initialValue()) {
           this.form.patchValue(this.initialValue()!);
         }
       }
       ```
     - **Mode: Both** — Detect based on `initialValue` presence:
       ```typescript
       isEditMode = computed(() => this.initialValue() !== null);
       ```
     - `onSubmit()` method:
       - Check `form.valid` and `!loading()`
       - Set `loading(true)`
       - If data service integrated:
         - Call service method based on mode (e.g., `createUser()` or `updateUser()`)
         - Subscribe to result
         - On success: Reset loading, emit `formSubmit` output or navigate
         - On error: Set loading to false, call `setServerErrors()`
       - If no service: Emit `formSubmit.emit(this.form.getRawValue())`
     - `onCancel()` method:
       - Reset form: `this.form.reset()`
       - Emit `formCancel.emit()`
     - `setServerErrors(errors: Record<string, string[]>)` method:
       - Iterate over error object
       - For each field, call `control.setErrors({ server: messages.join(', ') })`
       - Update `serverErrors` signal for display
   - Placeholders to replace:
     - `{{FORM_NAME_KEBAB}}` → e.g., `user-profile`
     - `{{FORM_NAME_PASCAL}}` → e.g., `UserProfile`
     - `{{RESOURCE_NAME_PASCAL}}` → e.g., `User` (if resource provided)
     - `{{SERVICE_NAME_PASCAL}}` → e.g., `UsersService` (if resource provided)

5. **Generate HTML template** using `{{template:reactive-form.html.tpl}}`:
   - Create `<formName>.component.html` with:
     - Wrap form in `<mat-card>` with header and actions
     - `<mat-card-header>` with title (e.g., "Create User" or "Edit User")
     - `<mat-progress-bar>` with `@if (loading())` for loading state
     - `<form [formGroup]="form" (ngSubmit)="onSubmit()">` with `<mat-card-content>`
     - One `<mat-form-field>` per form control:
       ```html
       <mat-form-field appearance="outline">
         <mat-label>Field Label</mat-label>
         <input matInput formControlName="fieldName" placeholder="Enter value">
         @if (form.get('fieldName')?.hasError('required') && form.get('fieldName')?.touched) {
           <mat-error>This field is required</mat-error>
         }
         @if (form.get('fieldName')?.hasError('minlength')) {
           <mat-error>Minimum length is {{ form.get('fieldName')?.errors?.['minlength'].requiredLength }}</mat-error>
         }
         @if (form.get('fieldName')?.hasError('server')) {
           <mat-error>{{ form.get('fieldName')?.errors?.['server'] }}</mat-error>
         }
       </mat-form-field>
       ```
     - Use modern control flow (`@if`, `@for`) instead of `*ngIf`, `*ngFor`
     - `<mat-card-actions>` with two buttons:
       ```html
       <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || loading()">
         @if (isEditMode()) { Update } @else { Create }
       </button>
       <button mat-button type="button" (click)="onCancel()" [disabled]="loading()">
         Cancel
       </button>
       ```

6. **Generate SCSS file** using `{{template:component.scss.tpl}}`:
   - Create `<formName>.component.scss` with:
     - `:host` selector with `display: block;`
     - Material theme token usage
     - Form field spacing and layout
     - Example structure:
       ```scss
       @use '@angular/material' as mat;

       :host {
         display: block;

         mat-card {
           max-width: 600px;
           margin: 0 auto;
         }

         mat-form-field {
           width: 100%;
           margin-bottom: 16px;
         }

         mat-card-actions {
           display: flex;
           gap: 8px;
           justify-content: flex-end;
         }
       }
       ```

7. **Generate spec file**:
   - Create `<formName>.component.spec.ts` with:
     - Import `ReactiveFormsModule`, `NoopAnimationsModule`
     - Mock data service (if integrated) using Jest spy
     - Test suite structure:
       - **should create** — Component initialization test
       - **Form initialization tests**:
         - Form should be invalid when empty (if required fields exist)
         - Form should initialize with correct control names
         - Form controls should have correct initial validators
       - **Mode: Create tests**:
         - Initial form values should be empty/default
         - Submit should call create method on data service
       - **Mode: Edit tests**:
         - `patchValue()` should populate form with initial values
         - Submit should call update method on data service
       - **Validation state transition tests**:
         - Form should transition from invalid to valid when required fields filled
         - Individual control errors should appear/disappear correctly
         - `form.invalid` should disable submit button
       - **Submit flow with mocked service**:
         - Successful submit: loading true → service called → loading false → output emitted
         - Failed submit with server errors: `setServerErrors()` called → control errors set
       - **Loading state tests**:
         - Loading state should disable submit button
         - Progress bar should display when loading
       - **Cancel flow**:
         - Cancel should reset form
         - Cancel should emit `formCancel` output
       - **Server-side validation error tests**:
         - `setServerErrors()` should set errors on matching controls
         - Server errors should display in `<mat-error>` blocks
     - Example test:
       ```typescript
       it('should handle successful form submission', fakeAsync(() => {
         const mockService = TestBed.inject(UsersService);
         const createSpy = jest.spyOn(mockService, 'createUser').mockReturnValue(
           of({ id: 1, name: 'Test User', email: 'test@example.com' })
         );

         component.form.patchValue({
           name: 'Test User',
           email: 'test@example.com'
         });

         component.onSubmit();
         expect(component.loading()).toBe(true);

         tick();

         expect(createSpy).toHaveBeenCalledWith({ name: 'Test User', email: 'test@example.com' });
         expect(component.loading()).toBe(false);
       }));

       it('should handle server validation errors', () => {
         const serverErrors = {
           email: ['Email already exists'],
           name: ['Name is too short']
         };

         component.setServerErrors(serverErrors);

         expect(component.form.get('email')?.hasError('server')).toBe(true);
         expect(component.form.get('email')?.errors?.['server']).toBe('Email already exists');
         expect(component.form.get('name')?.hasError('server')).toBe(true);
       });
       ```

8. **Wire to data service** (if `resourceName` provided):
   - Add route parameter handling for edit mode:
     - Inject `ActivatedRoute` and `Router`
     - Load resource data based on route params
     - Example:
       ```typescript
       private route = inject(ActivatedRoute);
       private usersService = inject(UsersService);

       ngOnInit(): void {
         const id = this.route.snapshot.paramMap.get('id');
         if (id) {
           this.usersService.getUser(+id).subscribe(user => {
             this.form.patchValue(user);
           });
         }
       }
       ```

9. **Report generated artifacts**:
   - List created files:
     - `<formName>.component.ts`
     - `<formName>.component.html`
     - `<formName>.component.scss`
     - `<formName>.component.spec.ts`
   - Summarise form fields and validators
   - Note integration with data service (if applicable)

**Output**:
- New reactive form component at `projects/<appName>/src/app/<targetPath>/<formName>/`
- Four files: `.component.ts`, `.component.html`, `.component.scss`, `.component.spec.ts`
- Typed `FormGroup<>` interface matching resource model (if provided)
- Integration with data service for submit/cancel actions (if provided)
- Loading state with `MatProgressBar`
- Server-side validation error handling with `setErrors()`
- Comprehensive unit tests covering validation state transitions and submit flow

#### Modify

Update an existing reactive form component to add/remove fields, change validators, update submit target, or adjust behavior.

**Input Requirements**:
- `formName` (string): Name of the form to modify
- `workspacePath` (string): Workspace root path
- `appName` (string): Application name
- `targetPath` (string): Current location of form component
- Description of changes:
  - Fields to add/remove (with types and validators)
  - Validator changes for existing fields
  - Submit target changes (different service method or navigation)
  - Mode changes (create ↔ edit ↔ both)

**Process**:
1. Locate existing form component files:
   - Find `<formName>.component.ts`, `.html`, `.scss`, `.spec.ts`
   - Verify all files exist and are readable
2. **Add fields**:
   - Update typed form interface with new field types
   - Add new `FormControl` to `form` definition with appropriate validators
   - Add corresponding `<mat-form-field>` to template with error handling
   - Update spec tests to cover new fields
3. **Remove fields**:
   - Remove field from typed form interface
   - Remove `FormControl` from `form` definition
   - Remove `<mat-form-field>` from template
   - Remove field-specific tests from spec
4. **Change validators**:
   - Update validator array in `FormControl` definition
   - Update corresponding `<mat-error>` blocks in template
   - Update validation tests in spec
5. **Update submit target**:
   - Change injected service if switching resources
   - Update service method call in `onSubmit()` (e.g., `createUser()` → `createOrder()`)
   - Update mock service in spec tests
6. **Mode transitions**:
   - **Create → Edit**: Add `initialValue` input signal, add `ngOnInit()` with `patchValue()`
   - **Edit → Create**: Remove `initialValue` input, remove `ngOnInit()` patching logic
   - **Create/Edit → Both**: Add `isEditMode` computed signal, update button text with conditional
7. **Re-generate spec tests** for modified sections
8. Report modified files and changes

**Output**:
- Updated `<formName>.component.ts` with modified form definition
- Updated `<formName>.component.html` with added/removed fields
- Updated `<formName>.component.spec.ts` with matching test coverage
- Change summary documenting field additions/removals and validator updates

#### Delete

Remove a reactive form component and clean up references (route configurations, parent component imports).

**Input Requirements**:
- `formName` (string): Name of the form to delete
- `workspacePath` (string): Workspace root path
- `appName` (string): Application name
- `targetPath` (string): Location of form component

**Process**:
1. Locate form component directory: `projects/<appName>/src/app/<targetPath>/<formName>/`
2. Verify all component files exist:
   - `<formName>.component.ts`
   - `<formName>.component.html`
   - `<formName>.component.scss`
   - `<formName>.component.spec.ts`
3. Search for references:
   - Check for route definitions importing this component
   - Check for parent components using this form in their templates
   - Check for barrel exports (`index.ts`) re-exporting this component
4. Remove all four component files:
   ```bash
   rm -rf projects/<appName>/src/app/<targetPath>/<formName>/
   ```
5. Remove stale imports and references:
   - If component is used in routes: Remove route entry or comment with TODO for manual cleanup
   - If barrel export exists: Remove export line from `index.ts`
   - If parent component imports: Report manual cleanup required (cannot automatically determine replacement)
6. Report deleted files and any follow-up manual cleanup needed

**Output**:
- Removed form component directory and all files
- Confirmation of deletion
- List of references that require manual cleanup (routes, parent component usage)

### Context Files

{{context:../../shared/angular-conventions.md}}
{{context:../../shared/angular-material-patterns.md}}
{{context:../../shared/openapi-integration.md}}

### Supporting Files

- `templates/reactive-form.ts.tpl` — Typed reactive form scaffold with `FormGroup<>`, `FormBuilder`, loading state, and server error handling
- `templates/reactive-form.html.tpl` — Material form template with `MatCard`, `MatFormField` per control, progress bar, and submit/cancel buttons
- `context/angular-conventions.md` — Angular standalone component patterns, signals, dependency injection
- `context/openapi-integration.md` — Resource model location and import patterns for deriving form field types

### Validation

**Post-Create/Modify Validation**:

1. **Compile check**:
   ```bash
   npx tsc --noEmit --project tsconfig.json
   ```
   - Confirm form component compiles with typed `FormGroup<>` interface
   - Verify Material module imports are correct
   - Verify data service integration (if applicable) compiles

2. **Spec run**:
   ```bash
   npm test -- --watch=false --include='**/<formName>.component.spec.ts'
   ```
   - Confirm form spec passes
   - Verify validation state transition tests
   - Verify submit flow tests with mocked service

3. **Manual review**:
   - Verify form fields match resource model (if provided)
   - Verify `setServerErrors()` method handles server validation correctly
   - Verify loading state disables submit button
   - Verify `form.invalid` disables submit button
   - Test form interactively in running application

### Error Handling

**Common Errors**:

1. **Generated model not found**:
   - Error: Cannot resolve resource model for form field derivation
   - Resolution: Run `angular-api-integration` skill first to generate OpenAPI models, then retry

2. **Data service missing**:
   - Error: Cannot inject data service for submit integration
   - Resolution: Run `angular-data-service-composition` skill to create service wrapper, then retry

3. **Form control type mismatch**:
   - Error: TypeScript compilation fails due to form control type not matching model field type
   - Resolution: Verify model field types, adjust `FormControl<Type>` definitions to match

4. **Server error handling not working**:
   - Error: Server validation errors don't display in form
   - Resolution: Verify `setServerErrors()` is called in error handler, verify field names match form control names

5. **Spec tests fail after field changes**:
   - Error: Tests reference old field names or validators
   - Resolution: Regenerate spec tests to match current form definition

### Dependencies

**Required Skills** (must execute before this skill):

1. **ng-workspace** (Skill 1) — Workspace must exist with Angular Material installed
2. **ng-app** (Skill 2) — Application must exist in workspace with proper directory structure

**Optional Dependencies** (enhance functionality if present):

- **ng-api** (Skill 3) — If `resourceName` provided, generated models are used to derive typed `FormGroup<>` fields
- **ng-data-service** (Skill 4) — If `resourceName` provided, data service is injected for submit integration
- **ng-form-field** (Skill 6) — Custom form field components can be used in place of standard `MatFormField` inputs

**Dependent Skills** (use this skill before):

- **ng-page** (Skill 10) — Pages include forms with routing integration and navigation
- **ng-component** (Skill 7) — Container components may include reactive forms as child components

### Examples

**Example 1: Create a user profile form with API integration**

```json
{
  "formName": "user-profile",
  "workspacePath": "/workspace/my-app",
  "appName": "admin-dashboard",
  "targetPath": "features/users/forms",
  "mode": "both",
  "resourceName": "user"
}
```

**Process**:
1. Inspect `src/app/api/models/user.ts` for field types
2. Create typed form interface:
   ```typescript
   interface UserProfileForm {
     firstName: FormControl<string>;
     lastName: FormControl<string>;
     email: FormControl<string>;
     phoneNumber: FormControl<string | null>;
   }
   ```
3. Generate form with validators derived from model
4. Wire submit to `UsersService.createUser()` or `UsersService.updateUser()` based on mode
5. Add `isEditMode` computed signal for button text

**Output**:
- `features/users/forms/user-profile/user-profile.component.ts` (with typed form and service integration)
- `features/users/forms/user-profile/user-profile.component.html` (with Material fields and loading state)
- `features/users/forms/user-profile/user-profile.component.scss` (with form layout)
- `features/users/forms/user-profile/user-profile.component.spec.ts` (with validation and submit tests)

**Example 2: Create a simple contact form without API integration**

```json
{
  "formName": "contact",
  "workspacePath": "/workspace/my-app",
  "appName": "public-site",
  "targetPath": "shared/forms",
  "mode": "create"
}
```

**Process**:
1. No `resourceName` provided, manually define form fields
2. Create form with standard fields (name, email, message)
3. No data service integration, emit `formSubmit` output for parent handling
4. Parent component subscribes to `formSubmit` and handles submission

**Output**:
- `shared/forms/contact/contact.component.ts` (with typed form and output event)
- `shared/forms/contact/contact.component.html` (with Material fields)
- `shared/forms/contact/contact.component.scss` (with form layout)
- `shared/forms/contact/contact.component.spec.ts` (with validation tests)

**Example 3: Modify existing form to add a new field**

```markdown
Input:
- formName: "product-edit"
- workspacePath: "/workspace/my-app"
- appName: "admin-dashboard"
- targetPath: "features/products/forms"
- change: "Add 'category' select field with dropdown options"

Process:
1. Locate existing `product-edit.component.ts`
2. Add `category: FormControl<string>` to form interface
3. Add form control with required validator
4. Add `<mat-form-field>` with `<mat-select>` to template
5. Update spec tests to cover category field validation

Output:
- Updated `product-edit.component.ts`
- Updated `product-edit.component.html`
- Updated `product-edit.component.spec.ts`
```
