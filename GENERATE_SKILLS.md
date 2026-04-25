Create a solution based on claude code and claude skills to build and maintain Angular applications

* Create skills to build and modify angular objects
* Generate build commands from an Open API schema

# Skill Architecture

All skills in this document follow the **Agent Skills** format — reusable capabilities designed to be auto-invoked by an outer Claude API agent pipeline.

## Directory Structure

Each skill lives in its own directory under `.claude/skills/`:

```
.claude/skills/<skill-name>/
  SKILL.md          # Main skill specification with YAML frontmatter
  context/          # Optional context files loaded at instruction level
  templates/        # Optional template files for code generation
  examples/         # Optional example files demonstrating usage
```

## YAML Frontmatter

Every `SKILL.md` file begins with YAML frontmatter that defines skill metadata:

```yaml
---
name: <skill-name>
description: <brief description of skill purpose>
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

### Field Definitions

- **`name`**: Unique identifier for the skill (matches directory name)
- **`description`**: Brief description used by outer agent for skill matching and invocation
- **`user-invocable`**: Always `false` for these skills — invoked by outer agent, not by users directly
- **`context`**: Always `fork` — each skill execution runs in an isolated context
- **`allowed-tools`**: List of Claude Code tools the skill is permitted to use during execution

## Three Loading Levels

Skills are loaded incrementally to manage token costs:

### 1. Metadata Level (lowest cost)
- Loads only the YAML frontmatter
- Used by outer agent for skill discovery and matching
- Minimal token consumption (~50-100 tokens per skill)

### 2. Instructions Level (medium cost)
- Loads the full `SKILL.md` content including all markdown sections
- Loads any files referenced in the `context/` directory
- Used when the outer agent has selected the skill and needs execution instructions
- Moderate token consumption (~500-2000 tokens depending on skill complexity)

### 3. Resources Level (highest cost)
- Loads all referenced templates, examples, and supporting files
- Only loaded when skill execution requires access to these resources
- High token consumption (~2000-10000+ tokens for complex skills with many templates)

**Token Cost Strategy**: The outer agent loads metadata for all skills, instructions for candidate skills, and resources only for the executing skill, minimizing overall token usage.

## Dynamic Context Injection

Skills can reference external context that gets injected at load time:

### Context File References

Within `SKILL.md`, reference context files using:

```markdown
{{context:filename.md}}
```

When the skill loads at the instructions level, these references are replaced with the actual file contents from `.claude/skills/<skill-name>/context/filename.md`.

### Template References

Within skill instructions, reference templates using:

```markdown
{{template:template-name.ts}}
```

Templates are loaded at the resources level when the skill needs them for code generation.

## Auto-Invocation Model

Skills are invoked by an **outer agent**, not by users:

1. **User Request**: User provides high-level task to outer agent (e.g., "Create an Angular Material workspace")
2. **Skill Selection**: Outer agent loads metadata for all skills and matches user request to appropriate skill(s) based on descriptions
3. **Skill Execution**: Outer agent forks a new context, loads the selected skill at instructions level, and executes it
4. **Result Handoff**: Skill completes and returns results to outer agent
5. **Continuation**: Outer agent may invoke additional skills or return final results to user

**Key Principle**: Skills are designed as composable units that can be chained together by the outer agent to accomplish complex tasks.

## Canonical SKILL.md Template Structure

Every `SKILL.md` file follows this structure:

```markdown
---
name: <skill-name>
description: <brief description>
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

# <Skill Display Name>

## Purpose

Brief statement of what this skill does and when to use it.

## Modes

All skills support three operational modes:

### Create
Generate the artifact from scratch when it doesn't exist.

**Input Requirements**:
- List required inputs for creation

**Process**:
1. Step-by-step creation process
2. Including validation
3. And error handling

**Output**:
- Description of created artifacts

### Modify
Update an existing artifact with changes.

**Input Requirements**:
- List required inputs for modification

**Process**:
1. Step-by-step modification process
2. Including validation
3. And error handling

**Output**:
- Description of modified artifacts

### Delete
Remove the artifact completely.

**Input Requirements**:
- List required inputs for deletion

**Process**:
1. Step-by-step deletion process
2. Including cleanup
3. And verification

**Output**:
- Confirmation of deletion

## Context Files

{{context:additional-guidance.md}}

## Templates

- `template-name.ts` — description of template purpose
- `another-template.html` — description of template purpose

## Validation

Steps to validate successful execution of the skill.

## Error Handling

Common errors and their resolution strategies.

## Dependencies

List any skills that must be executed before this skill (e.g., workspace must exist before creating an app).

## Examples

Brief examples demonstrating typical usage patterns.
```

This canonical structure ensures consistency across all 11 skills and provides clear guidance for both outer agent invocation and skill implementation.

# Shared Context Files

Shared context files are reference documents stored in `.claude/skills/shared/` that multiple skills load on-demand at the instructions level. They eliminate duplication by centralising conventions, patterns, and integration rules that apply across many skills.

Each file is injected into a skill using the standard context reference syntax:

```markdown
{{context:../../shared/<filename>}}
```

## `angular-conventions.md`

**Path**: `.claude/skills/shared/angular-conventions.md`

**Contents**:

- **Standalone components**: All components use `standalone: true`; no NgModules are generated. Imports are declared directly in the component decorator.
- **Signals**: State management uses Angular signals (`signal()`, `computed()`, `effect()`). Avoid `BehaviorSubject` and `Observable`-based state where signals suffice.
- **SCSS & Material theming**: Component stylesheets use `.scss`. Global theme tokens (palette, typography, density) are defined once in the workspace theme file and consumed via `mat.get-theme-color()` / `mat.get-theme-typography()` mixins.
- **Naming conventions**: Files follow `<name>.<type>.ts` (e.g., `user-list.component.ts`). Classes follow PascalCase (e.g., `UserListComponent`). Selectors follow `app-<name>` (e.g., `app-user-list`).
- **Imports**: Use Angular's `inject()` function for dependency injection. Barrel files (`index.ts`) are generated for each feature directory.
- **Testing patterns**: Unit tests use Jest with Angular Testing Library. Each component test file follows `<name>.component.spec.ts`. Services use `TestBed` with `HttpClientTestingModule` for HTTP dependencies.

**Referenced by**:
- Angular Material app boiler plate
- Angular Material small field level component generation
- Angular Material form field generation
- Angular component generation
- Angular Material complex component generation
- Angular Material reactive form generation
- Angular Material page generation
- Angular Material site generation

## `angular-material-patterns.md`

**Path**: `.claude/skills/shared/angular-material-patterns.md`

**Contents**:

- **MatTable page**: Standard data-table layout using `<mat-table>`, `MatPaginatorModule`, `MatSortModule`, and a `MatProgressSpinnerModule` loading overlay. Data source is a `MatTableDataSource` bound to a signal-based service.
- **MatCard form**: Form contained within a `<mat-card>` with `<mat-card-header>`, `<mat-card-content>`, and `<mat-card-actions>`. Uses `ReactiveFormsModule` with `FormBuilder`.
- **MatSidenav shell**: Application shell with `<mat-sidenav-container>`, a collapsible `<mat-sidenav>` for navigation, and `<mat-sidenav-content>` for the router outlet.
- **Dialog pattern**: Dialogs are opened via `MatDialog.open()`, receive data through `MAT_DIALOG_DATA`, and return results via `MatDialogRef.close()`.
- **Snackbar pattern**: User feedback is delivered through `MatSnackBar.open()` with a duration of 3000 ms and a dismiss action.

**Referenced by**:
- Angular Material app boiler plate
- Angular Material small field level component generation
- Angular Material form field generation
- Angular Material complex component generation
- Angular Material reactive form generation
- Angular Material page generation
- Angular Material site generation

## `openapi-integration.md`

**Path**: `.claude/skills/shared/openapi-integration.md`

**Contents**:

- **ng-openapi-gen output paths**: Generated files are placed in `src/app/api/` by default. The output directory is configured in `ng-openapi-gen.json` at the workspace root.
- **Service naming**: Each OpenAPI tag produces one Angular service named `<Tag>ApiService` (e.g., tag `Users` → `UsersApiService`). Import from `src/app/api/services/<tag>-api.service.ts`.
- **Import patterns**: Models are imported from `src/app/api/models/<model-name>.ts`. The barrel export at `src/app/api/models.ts` re-exports all models.
- **Do-not-edit rule**: All files inside `src/app/api/` are auto-generated and **must not be edited manually**. Re-run `ng-openapi-gen` to regenerate after schema changes.

**Referenced by**:
- Angular API generation
- Angular data model Service
- Angular Material complex component generation
- Angular Material page generation
- Angular Material site generation

# Templates

Template files are reusable Angular code scaffolds stored in `.claude/skills/<skill-name>/templates/` that skills reference during code generation. Each template provides a complete, working example following the conventions defined in the Shared Context Files section.

Skills inject these templates using the standard template reference syntax:

```markdown
{{template:template-name.ts}}
```

## Template 1: Standalone Component (`.ts` + `.html` + `.scss`)

**Files**: `component.ts.tpl`, `component.html.tpl`, `component.scss.tpl`

**Used by**:
- Angular Material small field level component generation (skill 5)
- Angular Material form field generation (skill 6)
- Angular component generation (skill 7)
- Angular Material complex component generation (skill 8)

### `component.ts.tpl`

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
  data = input<any>(null);

  // Output signals
  itemClicked = output<void>();

  handleClick(): void {
    this.itemClicked.emit();
  }
}
```

### `component.html.tpl`

```html
<mat-card>
  <mat-card-header>
    <mat-card-title>{{ title() }}</mat-card-title>
  </mat-card-header>

  <mat-card-content>
    @if (data()) {
      <p>{{ data() }}</p>
    } @else {
      <p>No data available</p>
    }
  </mat-card-content>

  <mat-card-actions>
    <button mat-raised-button color="primary" (click)="handleClick()">
      Action
    </button>
  </mat-card-actions>
</mat-card>
```

### `component.scss.tpl`

```scss
@use '@angular/material' as mat;

:host {
  display: block;

  mat-card {
    margin: 1rem 0;

    mat-card-header {
      background-color: mat.get-theme-color(primary, 50);
      padding: 1rem;
      margin: -1rem -1rem 1rem -1rem;
    }

    mat-card-title {
      color: mat.get-theme-color(primary, 700);
      font-weight: mat.get-theme-typography(headline-6, font-weight);
    }

    mat-card-actions {
      padding: 0 1rem 1rem;
    }
  }
}
```

## Template 2: ControlValueAccessor Boilerplate

**File**: `form-field.ts.tpl`

**Used by**:
- Angular Material form field generation (skill 6)

```typescript
import { Component, input, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-{{FIELD_NAME_KEBAB}}',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './{{FIELD_NAME_KEBAB}}.component.html',
  styleUrl: './{{FIELD_NAME_KEBAB}}.component.scss',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => {{FIELD_NAME_PASCAL}}Component),
      multi: true
    }
  ]
})
export class {{FIELD_NAME_PASCAL}}Component implements ControlValueAccessor {
  // Input properties
  label = input<string>('');
  placeholder = input<string>('');

  // Internal state
  value: string = '';
  disabled: boolean = false;

  // Callbacks
  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  // ControlValueAccessor implementation
  writeValue(value: string): void {
    this.value = value || '';
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  // Value change handler
  onValueChange(value: string): void {
    this.value = value;
    this.onChange(value);
    this.onTouched();
  }
}
```

## Template 3: Typed Reactive `FormGroup<>`

**File**: `reactive-form.ts.tpl`

**Used by**:
- Angular Material reactive form generation (skill 9)

```typescript
import { Component, inject, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';

// Typed form interface
interface {{FORM_NAME_PASCAL}}Form {
  name: FormControl<string>;
  email: FormControl<string>;
  description: FormControl<string>;
}

@Component({
  selector: 'app-{{FORM_NAME_KEBAB}}-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatProgressBarModule,
  ],
  templateUrl: './{{FORM_NAME_KEBAB}}-form.component.html',
  styleUrl: './{{FORM_NAME_KEBAB}}-form.component.scss'
})
export class {{FORM_NAME_PASCAL}}FormComponent {
  private fb = inject(FormBuilder);

  // Signals
  loading = signal(false);

  // Outputs
  formSubmit = output<any>();
  formCancel = output<void>();

  // Typed FormGroup
  form: FormGroup<{{FORM_NAME_PASCAL}}Form> = this.fb.group({
    name: this.fb.control('', { nonNullable: true, validators: [Validators.required, Validators.minLength(2)] }),
    email: this.fb.control('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
    description: this.fb.control('', { nonNullable: true, validators: [Validators.maxLength(500)] }),
  });

  onSubmit(): void {
    if (this.form.valid && !this.loading()) {
      this.loading.set(true);
      this.formSubmit.emit(this.form.getRawValue());
    }
  }

  onCancel(): void {
    this.form.reset();
    this.formCancel.emit();
  }

  // Server-side validation error handler
  setServerErrors(errors: Record<string, string[]>): void {
    Object.entries(errors).forEach(([field, messages]) => {
      const control = this.form.get(field);
      if (control) {
        control.setErrors({ server: messages.join(', ') });
      }
    });
  }
}
```

## Template 4: `MatTable` + Paginator + Sort Page

**Files**: `list-page.ts.tpl`, `list-page.html.tpl`

**Used by**:
- Angular Material page generation (skill 10)

### `list-page.ts.tpl`

```typescript
import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { {{RESOURCE_NAME_PASCAL}} } from '../../api/models/{{RESOURCE_NAME_KEBAB}}';
import { {{RESOURCE_NAME_PASCAL}}Service } from '../../services/{{RESOURCE_NAME_KEBAB}}.service';

@Component({
  selector: 'app-{{RESOURCE_NAME_KEBAB}}-list',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatProgressBarModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './{{RESOURCE_NAME_KEBAB}}-list.component.html',
  styleUrl: './{{RESOURCE_NAME_KEBAB}}-list.component.scss'
})
export class {{RESOURCE_NAME_PASCAL}}ListComponent implements OnInit {
  private router = inject(Router);
  private {{RESOURCE_NAME_CAMEL}}Service = inject({{RESOURCE_NAME_PASCAL}}Service);

  // Signals
  items = signal<{{RESOURCE_NAME_PASCAL}}[]>([]);
  loading = signal(false);
  totalCount = signal(0);
  pageSize = signal(10);
  pageIndex = signal(0);

  // Data source
  dataSource = computed(() => {
    const ds = new MatTableDataSource(this.items());
    return ds;
  });

  // Table configuration
  displayedColumns: string[] = ['id', 'name', 'status', 'createdAt', 'actions'];

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading.set(true);
    this{{RESOURCE_NAME_CAMEL}}Service
      .list(this.pageIndex(), this.pageSize())
      .subscribe({
        next: (response) => {
          this.items.set(response.results);
          this.totalCount.set(response.count);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
        }
      });
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.loadData();
  }

  onSortChange(sort: Sort): void {
    // Implement sorting logic
    this.loadData();
  }

  onRowClick(item: {{RESOURCE_NAME_PASCAL}}): void {
    this.router.navigate(['/{{RESOURCE_NAME_KEBAB}}', item.id]);
  }

  onCreate(): void {
    this.router.navigate(['/{{RESOURCE_NAME_KEBAB}}/new']);
  }

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource().filter = filterValue.trim().toLowerCase();
  }
}
```

### `list-page.html.tpl`

```html
<div class="list-container">
  <div class="list-header">
    <h1>{{RESOURCE_NAME_TITLE}}s</h1>
    <button mat-raised-button color="primary" (click)="onCreate()">
      <mat-icon>add</mat-icon>
      New {{RESOURCE_NAME_TITLE}}
    </button>
  </div>

  @if (loading()) {
    <mat-progress-bar mode="indeterminate"></mat-progress-bar>
  }

  <mat-form-field appearance="outline" class="filter-field">
    <mat-label>Filter</mat-label>
    <input matInput (keyup)="applyFilter($event)" placeholder="Search...">
    <mat-icon matSuffix>search</mat-icon>
  </mat-form-field>

  <div class="table-container">
    <table mat-table [dataSource]="dataSource()" matSort (matSortChange)="onSortChange($event)">

      <ng-container matColumnDef="id">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>ID</th>
        <td mat-cell *matCellDef="let item">{{ item.id }}</td>
      </ng-container>

      <ng-container matColumnDef="name">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Name</th>
        <td mat-cell *matCellDef="let item">{{ item.name }}</td>
      </ng-container>

      <ng-container matColumnDef="status">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Status</th>
        <td mat-cell *matCellDef="let item">{{ item.status }}</td>
      </ng-container>

      <ng-container matColumnDef="createdAt">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Created</th>
        <td mat-cell *matCellDef="let item">{{ item.createdAt | date:'short' }}</td>
      </ng-container>

      <ng-container matColumnDef="actions">
        <th mat-header-cell *matHeaderCellDef>Actions</th>
        <td mat-cell *matCellDef="let item">
          <button mat-icon-button (click)="onRowClick(item)">
            <mat-icon>visibility</mat-icon>
          </button>
        </td>
      </ng-container>

      <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
      <tr mat-row *matRowDef="let row; columns: displayedColumns;"
          (click)="onRowClick(row)"
          class="clickable-row"></tr>
    </table>
  </div>

  <mat-paginator
    [length]="totalCount()"
    [pageSize]="pageSize()"
    [pageIndex]="pageIndex()"
    [pageSizeOptions]="[5, 10, 25, 50]"
    (page)="onPageChange($event)"
    showFirstLastButtons>
  </mat-paginator>
</div>
```

## Template 5: `MatSidenav` App Shell

**Files**: `app-shell.ts.tpl`, `app-shell.html.tpl`

**Used by**:
- Angular Material site generation (skill 11)

### `app-shell.ts.tpl`

```typescript
import { Component, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { toSignal } from '@angular/core/rxjs-interop';

interface NavItem {
  label: string;
  route: string;
  icon: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  private breakpointObserver = inject(BreakpointObserver);
  private router = inject(Router);

  // Responsive layout
  isHandset = toSignal(
    this.breakpointObserver.observe([Breakpoints.Handset]),
    { initialValue: { matches: false } }
  );

  isMobile = computed(() => this.isHandset().matches);
  sidenavMode = computed(() => this.isMobile() ? 'over' : 'side');
  sidenavOpened = signal(true);

  // Navigation items
  navItems: NavItem[] = [
    { label: 'Dashboard', route: '/dashboard', icon: 'dashboard' },
    { label: 'Users', route: '/users', icon: 'people' },
    { label: 'Settings', route: '/settings', icon: 'settings' },
  ];

  toggleSidenav(): void {
    this.sidenavOpened.set(!this.sidenavOpened());
  }

  navigate(route: string): void {
    this.router.navigate([route]);
    if (this.isMobile()) {
      this.sidenavOpened.set(false);
    }
  }
}
```

### `app-shell.html.tpl`

```html
<mat-sidenav-container class="app-container">
  <mat-sidenav
    [mode]="sidenavMode()"
    [opened]="sidenavOpened()"
    class="app-sidenav">

    <div class="sidenav-header">
      <h2>{{APP_NAME}}</h2>
    </div>

    <mat-nav-list>
      @for (item of navItems; track item.route) {
        <a mat-list-item (click)="navigate(item.route)">
          <mat-icon matListItemIcon>{{ item.icon }}</mat-icon>
          <span matListItemTitle>{{ item.label }}</span>
        </a>
      }
    </mat-nav-list>
  </mat-sidenav>

  <mat-sidenav-content>
    <mat-toolbar color="primary" class="app-toolbar">
      <button mat-icon-button (click)="toggleSidenav()">
        <mat-icon>menu</mat-icon>
      </button>
      <span class="toolbar-spacer"></span>
      <button mat-icon-button>
        <mat-icon>account_circle</mat-icon>
      </button>
    </mat-toolbar>

    <div class="content-container">
      <router-outlet></router-outlet>
    </div>
  </mat-sidenav-content>
</mat-sidenav-container>
```

## Template 6: Service + `catchError` + `MatSnackBar`

**File**: `data-service.ts.tpl`

**Used by**:
- Angular data model Service (skill 4)

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { MatSnackBar } from '@angular/material/snack-bar';
import { {{RESOURCE_NAME_PASCAL}} } from '../api/models/{{RESOURCE_NAME_KEBAB}}';
import { {{RESOURCE_NAME_PASCAL}}ApiService } from '../api/services/{{RESOURCE_NAME_KEBAB}}-api.service';

@Injectable({
  providedIn: 'root'
})
export class {{RESOURCE_NAME_PASCAL}}Service {
  private http = inject(HttpClient);
  private snackBar = inject(MatSnackBar);
  private apiService = inject({{RESOURCE_NAME_PASCAL}}ApiService);

  /**
   * List all resources with pagination
   */
  list(page: number = 0, pageSize: number = 10): Observable<{ results: {{RESOURCE_NAME_PASCAL}}[]; count: number }> {
    return this.apiService
      .list{{RESOURCE_NAME_PASCAL}}s({ page: page + 1, pageSize })
      .pipe(
        map((response) => ({
          results: response.results || [],
          count: response.count || 0
        })),
        catchError((error) => this.handleError(error, 'Failed to load {{RESOURCE_NAME_KEBAB}}s'))
      );
  }

  /**
   * Get a single resource by ID
   */
  get(id: number): Observable<{{RESOURCE_NAME_PASCAL}}> {
    return this.apiService
      .get{{RESOURCE_NAME_PASCAL}}({ id })
      .pipe(
        catchError((error) => this.handleError(error, 'Failed to load {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Create a new resource
   */
  create(data: Partial<{{RESOURCE_NAME_PASCAL}}>): Observable<{{RESOURCE_NAME_PASCAL}}> {
    return this.apiService
      .create{{RESOURCE_NAME_PASCAL}}({ body: data })
      .pipe(
        map((response) => {
          this.showSuccess('{{RESOURCE_NAME_TITLE}} created successfully');
          return response;
        }),
        catchError((error) => this.handleError(error, 'Failed to create {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Update an existing resource
   */
  update(id: number, data: Partial<{{RESOURCE_NAME_PASCAL}}>): Observable<{{RESOURCE_NAME_PASCAL}}> {
    return this.apiService
      .update{{RESOURCE_NAME_PASCAL}}({ id, body: data })
      .pipe(
        map((response) => {
          this.showSuccess('{{RESOURCE_NAME_TITLE}} updated successfully');
          return response;
        }),
        catchError((error) => this.handleError(error, 'Failed to update {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Delete a resource
   */
  delete(id: number): Observable<void> {
    return this.apiService
      .delete{{RESOURCE_NAME_PASCAL}}({ id })
      .pipe(
        map(() => {
          this.showSuccess('{{RESOURCE_NAME_TITLE}} deleted successfully');
        }),
        catchError((error) => this.handleError(error, 'Failed to delete {{RESOURCE_NAME_KEBAB}}'))
      );
  }

  /**
   * Handle HTTP errors and display user-friendly messages
   */
  private handleError(error: HttpErrorResponse, fallbackMessage: string): Observable<never> {
    let errorMessage = fallbackMessage;

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else if (error.status === 0) {
      // Network error
      errorMessage = 'Network error. Please check your connection.';
    } else if (error.status >= 400 && error.status < 500) {
      // Client error (validation, authentication, etc.)
      errorMessage = error.error?.message || error.error?.detail || fallbackMessage;
    } else if (error.status >= 500) {
      // Server error
      errorMessage = 'Server error. Please try again later.';
    }

    this.showError(errorMessage);
    return throwError(() => error);
  }

  /**
   * Display success message
   */
  private showSuccess(message: string): void {
    this.snackBar.open(message, 'Dismiss', {
      duration: 3000,
      horizontalPosition: 'end',
      verticalPosition: 'top',
      panelClass: ['success-snackbar']
    });
  }

  /**
   * Display error message
   */
  private showError(message: string): void {
    this.snackBar.open(message, 'Dismiss', {
      duration: 5000,
      horizontalPosition: 'end',
      verticalPosition: 'top',
      panelClass: ['error-snackbar']
    });
  }
}
```

# Skills

Section will break down the "skills" requirement into the different skills.

Each skill will include:
- A building script(s).
- A description of the skill, including when to use it and how to use it.
  - Optionally additional details about the skill or sub section, in seperate md files.
- Template files.
Each script will have the following modes:
- Create: from zero, the object didn't exist before.
- Modify: Modify a given object
- Delete: Delete the object

## Angular Material workspace boiler plate

**Skill Name**: `ng-workspace`

### YAML Frontmatter

```yaml
---
name: ng-workspace
description: Create, modify, or delete an Angular Material workspace with modern conventions (standalone components, signals, SCSS theming)
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

The `ng-workspace` skill manages the creation, modification, and deletion of Angular workspaces configured with Angular Material, following modern Angular conventions (standalone components, signals, SCSS theming). This is the foundation skill that must be executed before any app-level or component-level skills can be invoked.

### Inputs

**From project configuration**:
- **`workspacePath`** (string, required): Absolute path where the workspace will be created (e.g., `/home/user/projects/my-angular-app`)
- **`packageManager`** (enum, optional): Package manager to use (`npm` | `yarn` | `pnpm`). Defaults to `npm`
- **`style`** (enum, optional): Stylesheet format (`css` | `scss` | `sass` | `less`). Defaults to `scss`
- **`routing`** (boolean, optional): Whether to include routing in the default application. Defaults to `true`
- **`workspaceName`** (string, optional): Name of the workspace. Defaults to directory name from `workspacePath`

### Mode: Create

Generate an Angular Material workspace from scratch when it doesn't exist.

#### Input Requirements

- **`workspacePath`**: Must not already exist or must be an empty directory
- **`packageManager`**: Valid package manager executable must be available in PATH
- **`style`**: Must be a valid Angular CLI stylesheet option
- **`routing`**: Boolean flag
- **`workspaceName`**: Valid workspace name (lowercase, hyphenated)

#### Pre-flight Checks

Before creating the workspace, verify:

1. Target directory doesn't exist or is empty
2. Package manager is installed and accessible (`npm --version`, `yarn --version`, or `pnpm --version`)
3. Angular CLI is installed globally or can be invoked via npx (`ng version` or `npx @angular/cli version`)
4. Node.js version meets Angular's requirements (currently Node 18.19+ or 20.11+ or 22.0+)
5. Sufficient disk space is available (minimum 500MB recommended)

#### Process (Create Mode)

1. **Create workspace with Angular CLI**:
   ```bash
   npx @angular/cli@latest new <workspaceName> \
     --directory=<workspacePath> \
     --package-manager=<packageManager> \
     --style=<style> \
     --routing=<routing> \
     --standalone=true \
     --skip-git=false \
     --skip-install=false
   ```

2. **Install Angular Material**:
   ```bash
   cd <workspacePath>
   npx ng add @angular/material --skip-confirmation --theme=custom --typography=true --animations=true
   ```

3. **Configure custom Material theme**:
   - Read the generated `src/styles.scss`
   - Replace default theme imports with custom theme configuration using Material 3 token-based theming
   - Define palette variables: `$primary`, `$accent`, `$warn`
   - Apply theme to core, typography, and density

4. **Update `angular.json` configuration**:
   - Set `inlineStyleLanguage` to `scss`
   - Enable source maps for development
   - Configure build optimization for production
   - Add Material prebuilt CSS path if needed

5. **Create `.editorconfig`** (if not present):
   - Standard Angular formatting rules
   - 2-space indentation for TS/HTML/SCSS
   - UTF-8 charset
   - Insert final newline

6. **Create `.prettierrc.json`** (optional but recommended):
   - Configure Prettier for consistent formatting
   - Single quotes, 2-space indent, trailing commas

7. **Update `tsconfig.json` with strict mode**:
   - Enable `strict: true`
   - Enable `strictNullChecks: true`
   - Enable `noImplicitAny: true`
   - Enable `skipLibCheck: true`

8. **Install additional development dependencies**:
   ```bash
   <packageManager> install --save-dev @angular-eslint/builder @angular-eslint/eslint-plugin @angular-eslint/eslint-plugin-template @angular-eslint/schematics @angular-eslint/template-parser
   ```

9. **Initialize ESLint configuration**:
   ```bash
   npx ng add @angular-eslint/schematics --skip-confirmation
   ```

10. **Create initial Git commit** (if not skipped):
    ```bash
    git add .
    git commit -m "chore: initialize Angular Material workspace with modern conventions"
    ```

#### Expected Output

After successful execution, the workspace directory contains:

```
<workspacePath>/
├── .angular/                    # Angular cache directory
├── .editorconfig               # Editor configuration
├── .gitignore                  # Git ignore rules
├── .prettierrc.json            # Prettier configuration
├── angular.json                # Angular workspace configuration
├── node_modules/               # Installed dependencies
├── package.json                # NPM package manifest
├── package-lock.json           # (or yarn.lock / pnpm-lock.yaml)
├── README.md                   # Project readme
├── tsconfig.json               # TypeScript configuration
├── tsconfig.app.json           # App-specific TS config
├── tsconfig.spec.json          # Test-specific TS config
├── .eslintrc.json              # ESLint configuration
└── src/
    ├── index.html              # Main HTML file
    ├── main.ts                 # Application entry point
    ├── styles.scss             # Global styles with Material theme
    ├── app/
    │   ├── app.component.ts    # Root component (standalone)
    │   ├── app.component.html  # Root template
    │   ├── app.component.scss  # Root styles
    │   ├── app.component.spec.ts # Root tests
    │   ├── app.config.ts       # Application configuration
    │   └── app.routes.ts       # Application routes (if routing enabled)
    └── assets/                 # Static assets
```

**Key characteristics**:
- All components are standalone (no NgModules)
- Material theming configured with custom SCSS theme
- ESLint configured for Angular projects
- TypeScript strict mode enabled
- Routing configured if requested

### Mode: Modify

Update an existing workspace with configuration changes, package updates, or new tooling.

#### Input Requirements

- **`workspacePath`**: Must exist and contain a valid Angular workspace (check for `angular.json`)
- **`modificationTarget`** (enum): Type of modification to perform:
  - `add-package`: Add NPM package(s)
  - `update-packages`: Update existing packages to latest versions
  - `update-angular`: Update Angular framework to latest version
  - `change-build-config`: Modify `angular.json` build configuration
  - `upgrade-typescript`: Upgrade TypeScript version
  - `reconfigure-material`: Change Material theme or configuration
  - `add-eslint-rule`: Add or modify ESLint rules
- **`modificationDetails`** (object): Details specific to the modification type

#### Process (Modify Mode)

**For `add-package` modifications**:
1. Verify workspace exists
2. Install package(s) using package manager: `<packageManager> install <packageName>`
3. Update imports in relevant files if needed
4. Run tests to verify compatibility
5. Commit changes: `git add . && git commit -m "chore: add <packageName>"`

**For `update-packages` modifications**:
1. Verify workspace exists
2. Update all packages: `<packageManager> update` (or `npm-check-updates -u && npm install`)
3. Run build: `ng build`
4. Run tests: `ng test`
5. Fix any breaking changes
6. Commit changes: `git add . && git commit -m "chore: update dependencies"`

**For `update-angular` modifications**:
1. Verify workspace exists
2. Run Angular update: `ng update @angular/core @angular/cli @angular/material`
3. Review migration messages
4. Run build and tests
5. Fix any breaking changes or deprecated API usage
6. Commit changes: `git add . && git commit -m "chore: update Angular to v<version>"`

**For `change-build-config` modifications**:
1. Verify workspace exists
2. Read `angular.json`
3. Apply requested configuration changes using Edit tool
4. Validate JSON syntax
5. Test build with new configuration
6. Commit changes: `git add angular.json && git commit -m "chore: update build configuration"`

**For `reconfigure-material` modifications**:
1. Verify workspace exists
2. Update `src/styles.scss` with new theme configuration
3. Test theme by running dev server: `ng serve`
4. Verify Material components render correctly
5. Commit changes: `git add . && git commit -m "style: update Material theme"`

**For `add-eslint-rule` modifications**:
1. Verify workspace exists and ESLint is configured
2. Read `.eslintrc.json`
3. Add or modify rules using Edit tool
4. Run linter: `ng lint`
5. Fix any new violations
6. Commit changes: `git add . && git commit -m "chore: update ESLint rules"`

#### Output

- Modified workspace with requested changes applied
- All builds and tests passing
- Git commit created documenting the modification

### Mode: Delete

Remove the workspace directory completely, typically when starting fresh is simpler than extensive modification.

#### Input Requirements

- **`workspacePath`**: Must exist and contain an Angular workspace
- **`confirmDelete`** (boolean, required): Safety confirmation flag (must be `true`)
- **`backupBeforeDelete`** (boolean, optional): Create backup before deletion. Defaults to `false`

#### Pre-flight Checks

1. Verify `workspacePath` exists
2. Verify it contains `angular.json` (confirm it's an Angular workspace)
3. Require explicit `confirmDelete: true` flag
4. Warn if workspace has uncommitted Git changes

#### Process (Delete Mode)

1. **Check for uncommitted changes**:
   ```bash
   cd <workspacePath>
   git status --porcelain
   ```
   If output is not empty, warn: "Workspace has uncommitted changes. Commit or stash before deletion."

2. **Create backup** (if `backupBeforeDelete: true`):
   ```bash
   tar -czf <workspacePath>-backup-$(date +%Y%m%d-%H%M%S).tar.gz <workspacePath>
   mv <workspacePath>-backup-*.tar.gz <backupLocation>
   ```

3. **Remove workspace directory**:
   ```bash
   rm -rf <workspacePath>
   ```

4. **Verify deletion**:
   ```bash
   [ ! -d <workspacePath> ] && echo "Workspace deleted successfully"
   ```

#### Output

- Workspace directory removed
- Backup created if requested
- Confirmation message with deletion status

### Supporting Files

#### Context Files

This skill references the following shared context files:

- **`{{context:../../shared/angular-conventions.md}}`** — Loaded at instructions level, provides conventions for standalone components, signals, SCSS theming, naming, imports, and testing patterns

#### Template Files

This skill does not use template files directly, as it relies on Angular CLI schematics for code generation. However, it configures the workspace to use the templates defined in the Templates section when subsequent skills (like `ng-component` or `ng-page`) are invoked.

### Validation

#### Post-Creation Validation

After creating a workspace, verify:

1. **Directory structure exists**:
   ```bash
   [ -f <workspacePath>/angular.json ] && echo "✓ Workspace created"
   ```

2. **Dependencies installed**:
   ```bash
   [ -d <workspacePath>/node_modules ] && echo "✓ Dependencies installed"
   ```

3. **Build succeeds**:
   ```bash
   cd <workspacePath> && ng build
   ```
   Expected: Build completes without errors

4. **Tests pass**:
   ```bash
   cd <workspacePath> && ng test --watch=false
   ```
   Expected: All tests pass

5. **Dev server starts**:
   ```bash
   cd <workspacePath> && ng serve --port 4200
   ```
   Expected: Server starts and application loads at `http://localhost:4200`

6. **Material is configured**:
   - Check `package.json` contains `@angular/material`
   - Check `src/styles.scss` contains Material theme imports
   - Verify Material components can be imported in app component

#### Post-Modification Validation

After modifying a workspace, verify:

1. **Build still succeeds**: `ng build`
2. **Tests still pass**: `ng test --watch=false`
3. **Linter passes**: `ng lint` (if ESLint configured)
4. **No TypeScript errors**: `ng build --configuration production`

### Error Handling

#### Common Errors and Resolutions

**Error**: `ng: command not found`
- **Cause**: Angular CLI not installed
- **Resolution**: Install globally (`npm install -g @angular/cli`) or use npx

**Error**: `EACCES: permission denied`
- **Cause**: Insufficient permissions to create directory or install packages
- **Resolution**: Check directory permissions, avoid using sudo with npm (configure npm prefix instead)

**Error**: `npm ERR! code ERESOLVE` (dependency conflicts)
- **Cause**: Conflicting package versions
- **Resolution**: Use `--legacy-peer-deps` or `--force` flag, or resolve dependency versions manually

**Error**: `Schematic "ng-add" not found in collection "@angular/material"`
- **Cause**: Material package issue or version mismatch
- **Resolution**: Install Material manually and configure theme manually

**Error**: `The serve command requires to be run in an Angular project`
- **Cause**: Not in workspace root directory
- **Resolution**: Verify `workspacePath` is correct and contains `angular.json`

**Error**: Workspace directory already exists and is not empty
- **Cause**: Target directory contains files
- **Resolution**: Use Delete mode first, or choose a different directory

### Dependencies

**Prerequisites**:
- Node.js (v18.19+ or v20.11+ or v22.0+)
- NPM/Yarn/PNPM package manager
- Git (for version control)
- Sufficient disk space (500MB+)

**No skill dependencies**: This is the foundational skill. All other Angular skills depend on this skill being executed first to create the workspace.

**Dependent skills** (must have workspace before using):
- `ng-app` — Angular Material app boiler plate
- `ng-api-gen` — Angular API generation
- All component, form, page, and site generation skills

### Examples

#### Example 1: Create New Workspace

**Input**:
```json
{
  "mode": "create",
  "workspacePath": "/home/user/projects/my-shop",
  "packageManager": "npm",
  "style": "scss",
  "routing": true,
  "workspaceName": "my-shop"
}
```

**Execution**:
1. Run `npx @angular/cli new my-shop --directory=/home/user/projects/my-shop --package-manager=npm --style=scss --routing=true --standalone=true`
2. Install Material with `ng add @angular/material`
3. Configure custom SCSS theme
4. Install ESLint
5. Create initial commit

**Output**: Workspace created at `/home/user/projects/my-shop` with Material configured

#### Example 2: Update Angular Version

**Input**:
```json
{
  "mode": "modify",
  "workspacePath": "/home/user/projects/my-shop",
  "modificationTarget": "update-angular",
  "modificationDetails": {
    "targetVersion": "latest"
  }
}
```

**Execution**:
1. Run `ng update @angular/core @angular/cli @angular/material`
2. Review and apply migrations
3. Run tests
4. Commit changes

**Output**: Angular updated to latest version with all migrations applied

#### Example 3: Delete Workspace

**Input**:
```json
{
  "mode": "delete",
  "workspacePath": "/home/user/projects/my-shop",
  "confirmDelete": true,
  "backupBeforeDelete": true
}
```

**Execution**:
1. Check for uncommitted changes (warn if present)
2. Create backup tarball
3. Remove workspace directory
4. Confirm deletion

**Output**: Workspace deleted, backup saved to `/home/user/projects/my-shop-backup-20260425-153000.tar.gz`

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

2. **Generate application scaffold**
   ```bash
   cd <workspacePath>
   ng generate application <appName> --routing=<routing> --standalone=<standalone> --style=scss --prefix=<prefix>
   ```

3. **Create standard directory structure**
   - Create `projects/<appName>/src/app/core/` - Core services and guards
   - Create `projects/<appName>/src/app/shared/components/` - Shared components
   - Create `projects/<appName>/src/app/shared/pipes/` - Shared pipes
   - Create `projects/<appName>/src/app/features/` - Feature modules/routes
   - Create barrel exports (`index.ts`) in each directory

4. **Wire Angular Material theme**
   - Install Angular Material if not already present:
     ```bash
     ng add @angular/material --project=<appName> --theme=indigo-pink --typography=true --animations=true
     ```
   - Update `projects/<appName>/src/styles.scss` with custom theme configuration:
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
   - Create/update `projects/<appName>/src/app/app.config.ts`:
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

   - Update `projects/<appName>/src/main.ts` to use standalone bootstrap:
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

7. **Verify compilation**
   ```bash
   ng build <appName> --configuration=development
   ```

**Output**:
- Complete Angular Material application created in `projects/<appName>/`
- Directory structure with `core/`, `shared/`, `features/` folders
- Material theme configured in `styles.scss`
- Standalone bootstrap with `app.config.ts`
- Application shell with responsive navigation
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

// Executes:
// 1. ng generate application admin-dashboard --routing --standalone --style=scss --prefix=admin
// 2. Creates core/, shared/, features/ directories
// 3. Installs Material: ng add @angular/material --project=admin-dashboard
// 4. Configures theme in projects/admin-dashboard/src/styles.scss
// 5. Sets up app.config.ts with providers
// 6. Generates responsive nav shell from app-shell templates
// 7. Runs: ng build admin-dashboard --configuration=development

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

## Angular API generation

```yaml
---
name: ng-api
description: Generate Angular API clients from OpenAPI specifications using ng-openapi-gen. Auto-invoked when the outer agent detects a need to generate or regenerate API service layer code from an OpenAPI schema.
user-invocable: false
context: fork
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
---
```

### Purpose

Generate TypeScript API client code (services and models) from OpenAPI specifications using the ng-openapi-gen tool. This skill creates strongly-typed Angular services that wrap HTTP endpoints defined in the OpenAPI schema, producing `*ApiService` files organized by OpenAPI tags and corresponding TypeScript model interfaces.

### Modes

#### Create

Generate API client code from an OpenAPI specification when it doesn't exist.

**Input Requirements**:
- `openapi_source_path` (string): Path to the OpenAPI specification file (JSON or YAML format)
- `ng_openapi_gen_config_path` (string, optional): Path to ng-openapi-gen configuration file. Defaults to `ng-openapi-gen.json` at workspace root
- `output_path` (string, optional): Target directory for generated files. Defaults to `src/app/api/` as configured in ng-openapi-gen config

**Process**:
1. **Pre-flight validation**:
   - Verify OpenAPI source file exists at `openapi_source_path`
   - Validate OpenAPI spec is well-formed JSON or YAML
   - Check ng-openapi-gen is installed in workspace (`npm list ng-openapi-gen`)
   - If config file path provided, verify it exists; otherwise check for default `ng-openapi-gen.json`
2. **Configuration setup** (if config doesn't exist):
   - Create `ng-openapi-gen.json` at workspace root with:
     ```json
     {
       "$schema": "node_modules/ng-openapi-gen/ng-openapi-gen-schema.json",
       "input": "<openapi_source_path>",
       "output": "src/app/api",
       "ignoreUnusedModels": false
     }
     ```
3. **Run generation**:
   - Execute: `npx ng-openapi-gen --config <ng_openapi_gen_config_path>`
   - Capture stdout/stderr for diagnostics
4. **Verify output**:
   - Confirm `services/` directory populated with `*-api.service.ts` files
   - Confirm `models/` directory populated with model TypeScript interfaces
   - Check for `models.ts` barrel export file
   - Check for `services.ts` barrel export file
5. **Report results**:
   - List all generated `*ApiService` files (one per OpenAPI tag)
   - Report count of generated models
   - Output any warnings from ng-openapi-gen

**Output**:
- Generated TypeScript services in `<output_path>/services/`
- Generated TypeScript model interfaces in `<output_path>/models/`
- Barrel exports at `<output_path>/models.ts` and `<output_path>/services.ts`
- Base API configuration file at `<output_path>/base-service.ts`

#### Modify

Regenerate API client code after OpenAPI specification changes.

**Input Requirements**:
- `openapi_source_path` (string): Path to the updated OpenAPI specification file
- `ng_openapi_gen_config_path` (string, optional): Path to ng-openapi-gen configuration file

**Process**:
1. **Verify existing generation**:
   - Confirm `ng-openapi-gen.json` config exists
   - Confirm output directory exists with previous generation
2. **Clean previous generation** (optional, based on ng-openapi-gen behavior):
   - ng-openapi-gen handles incremental updates, but note that removed endpoints/models may leave orphaned files
3. **Re-run generation**:
   - Execute: `npx ng-openapi-gen --config <ng_openapi_gen_config_path>`
4. **Diff analysis**:
   - Identify new services (new OpenAPI tags)
   - Identify modified services (changed endpoints)
   - Identify new models
   - Identify modified models (schema changes)
5. **Report changes**:
   - List added services and models
   - List modified services and models
   - Warn about any orphaned files if manual cleanup needed

**Output**:
- Updated TypeScript services reflecting spec changes
- Updated TypeScript models reflecting schema changes
- Change summary report

**Important**: Never hand-edit generated files in `<output_path>/`. Always regenerate via this skill.

#### Delete

Remove generated API client code directory; invoke Create mode to regenerate.

**Input Requirements**:
- `output_path` (string, optional): Directory to remove. Defaults to `src/app/api/`

**Process**:
1. **Verify target**:
   - Confirm output directory exists
   - Verify it contains ng-openapi-gen generated structure (`services/`, `models/`, barrel exports)
2. **Safety check**:
   - Warn if directory contains non-generated files
   - Confirm user intent if interactive, or proceed if auto-invoked with regeneration intent
3. **Remove directory**:
   - Execute: `rm -rf <output_path>`
4. **Optional: Remove configuration**:
   - Ask whether to remove `ng-openapi-gen.json` (typically keep for regeneration)
5. **Suggest regeneration**:
   - If deletion was to clean before regeneration, automatically invoke Create mode

**Output**:
- Removed output directory
- Confirmation message

### Context Files

{{context:../../shared/openapi-integration.md}}

### Supporting Files

- `ng-openapi-gen.json` — Configuration file for ng-openapi-gen tool (created if doesn't exist)
- OpenAPI specification file (external input, not part of skill)

### Validation

**Post-Create/Modify Validation**:
1. **Directory structure check**:
   ```bash
   ls -la <output_path>/services/
   ls -la <output_path>/models/
   ```
   - Verify `services/` directory contains at least one `*-api.service.ts` file per OpenAPI tag
   - Verify `models/` directory populated with `.ts` model files
2. **Barrel exports check**:
   ```bash
   cat <output_path>/models.ts
   cat <output_path>/services.ts
   ```
   - Confirm barrel files exist and contain re-exports
3. **TypeScript compilation check**:
   ```bash
   npx tsc --noEmit --project tsconfig.json
   ```
   - Confirm generated files compile without errors
4. **Service naming validation**:
   - Each OpenAPI tag should produce exactly one `<Tag>ApiService`
   - Service file names follow kebab-case: `<tag>-api.service.ts`
   - Service class names follow PascalCase: `<Tag>ApiService`

### Error Handling

**Common Errors**:

1. **OpenAPI spec not found**:
   - Error: `ENOENT: no such file or directory`
   - Resolution: Verify `openapi_source_path` is correct; check file exists

2. **Invalid OpenAPI spec**:
   - Error: `OpenAPI schema validation failed`
   - Resolution: Validate spec using online validator or `npx @apidevtools/swagger-cli validate <spec>`

3. **ng-openapi-gen not installed**:
   - Error: `command not found: ng-openapi-gen`
   - Resolution: Install via `npm install --save-dev ng-openapi-gen`

4. **Generation errors**:
   - Error: Various ng-openapi-gen errors during generation
   - Resolution: Check stderr output; common issues include:
     - Unsupported OpenAPI features
     - Circular references in schemas
     - Invalid TypeScript identifiers from spec

5. **TypeScript compilation errors after generation**:
   - Error: Compilation failures in generated code
   - Resolution: Usually indicates OpenAPI spec issue or ng-openapi-gen version incompatibility; check ng-openapi-gen documentation for supported OpenAPI versions

### Dependencies

**Required Skills**:
- Angular Material workspace boilerplate must exist (workspace with `package.json` and Angular CLI)

**Required Tools**:
- `ng-openapi-gen` npm package installed in workspace
- Angular workspace with TypeScript configuration

**Optional Dependencies**:
- OpenAPI specification linting tools for validation

### Examples

**Example 1: Initial API generation**
```markdown
Input:
- openapi_source_path: "spec/openapi.yaml"
- output_path: "src/app/api"

Process:
1. Verify spec/openapi.yaml exists
2. Create ng-openapi-gen.json config
3. Run npx ng-openapi-gen
4. Report generated files

Output:
Generated 3 API services:
- src/app/api/services/users-api.service.ts (UsersApiService)
- src/app/api/services/posts-api.service.ts (PostsApiService)
- src/app/api/services/comments-api.service.ts (CommentsApiService)

Generated 8 models in src/app/api/models/
Barrel exports created
```

**Example 2: Regeneration after spec update**
```markdown
Input:
- openapi_source_path: "spec/openapi.yaml" (updated)

Process:
1. Detect existing ng-openapi-gen.json
2. Re-run generation
3. Analyze changes

Output:
Changes detected:
- New service: AuthApiService
- Modified models: User (added 'role' field), Post (changed 'content' to optional)
- No removed services
```

**Example 3: Clean regeneration**
```markdown
Input:
- output_path: "src/app/api"

Process:
1. Delete mode: Remove src/app/api/
2. Auto-invoke Create mode with previous config

Output:
Cleaned and regenerated API client code
```

## Angular data model Service

Manage Angular data model API service
- Create: Generate the service
- Modify: Modify the service if changes made in Angular forced changes related to this service
- Delete: When it's too complex to modify we delete and create.

## Angular Material small field level component generation
Manage Angular Material small component generation
- Create: Generate a component from scratch
- Modify: Modify an existing component
- Delete: When it's too complex to modify we delete and create.

## Angular Material form field generation
Manage Angular Material form field generation
- Create: Generate a form field from scratch
- Modify: Modify an existing form field
- Delete: When it's too complex to modify we delete and create.

## Angular component generation

**Skill Name**: `ng-component`

### YAML Frontmatter

```yaml
---
name: ng-component
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

The `ng-component` skill manages the creation, modification, and deletion of Angular components within an existing Angular Material application. Components are generated following modern Angular conventions (standalone components, signals, Material Design patterns) and can be one of three types: **display** (presentational with Material layout), **container** (smart component with service injection and Observable data binding), or **dialog** (Material dialog with data injection and action buttons). This skill should be used after the workspace and application have been created.

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

## Angular Material complex component generation
Manage Angular Material complex component generation, including mixins, nested components, and complex cross component interactions
- Create: Generate a complex component from scratch
- Modify: Modify an existing complex component
- Delete: When it's too complex to modify we delete and create.

## Angular Material reactive form generation
Manage Angular Material reactive form generation
- Create: Generate a reactive form from scratch
- Modify: Modify an existing reactive form
- Delete: When it's too complex to modify we delete and create.

## Angular Material page generation
Manage Angular Material page (like "Landing Page", "Dashboard", "Profile Page", etc.) generation, including routing and navigation
- Create: Generate a page from scratch
- Modify: Modify an existing page
- Delete: When it's too complex to modify we delete and create.

## Angular Material site generation
Manage Angular Material site generation, including multiple pages, routing, navigation, and shared components
- Create: Generate a site from scratch
- Modify: Modify an existing site
- Delete: When it's too complex to modify we delete and create.

---

# Skill building

Each skill building will include the following steps:
1. Define the skill and its purpose.
2. Identify the necessary inputs and outputs for the skill.
3. Develop the building script(s) for the skill, ensuring they can handle the create, modify, and delete modes effectively.
4. Create reusable templates that can be used by the building scripts to generate the necessary code or configurations for the skill.
5. Test the skill to ensure it works as expected in all modes (create, modify, delete).

## 1. Define the skill and its purpose
## 2. Identify the necessary inputs and outputs for the skill
## 3. Develop the building script(s) for the skill
## 4. Create reusable templates that can be used by the building scripts to generate the necessary code or configurations for the skill
## 5. Test the skill to ensure it works as expected in all modes (create, modify, delete)

