Create a solution based on claude code and claude skills to build and maintain Angular applications

* Create skills to build and modify angular objects
* Generate build commands from an Open API schema

# Glossary

For authoritative definitions see `doc/ARCHITECTURE.md` §2 and §19.

| Term | Definition | See |
|---|---|---|
| **`djng`** | The `django-angular3` solution — this repository, the Django package, and the tool. Contains the agent, SKILLS, `build_app`, and all configuration files. | `doc/ARCHITECTURE.md` §2.5 |
| **`ngdj`** | The `angular-django2` companion Angular package. Provides the Angular-side schematics and templates invoked by the agent during construction. | `doc/ARCHITECTURE.md` §2.6 |
| **`build_app`** | The `djng` Django management command. Entry point that drives the agent through the procedure graph. | `doc/APP_BUILDER_REQUIREMENTS.md` |
| **the agent** | The agentic orchestrator bundled in `djng`. At implementation level, driven by the Claude Agent SDK. | `doc/ARCHITECTURE.md` §2.16 |
| **SKILLS** | Bounded AI skills (`SKILL.md` files) bundled in `djng` that guide the agent within each guided agent session. The subject of this document. | `doc/ARCHITECTURE.md` §2.14 |
| **guided agent session** | A single agent session in which the agent carries out one procedure, guided by the specified SKILL(s). | `doc/ARCHITECTURE.md` §2.13 |

---

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

## Invocation Model

SKILLS are used by the agent within guided agent sessions, not invoked by users
directly:

1. **Procedure graph construction**: `build_app` derives a procedure graph from
   schema and config changes. Each node specifies which SKILL(s) apply and what
   inputs to provide.
2. **Guided agent session**: For each procedure node, `build_app` makes a Claude
   Agent SDK `query()` call with the relevant SKILL(s) enabled and the procedure
   inputs as the prompt. The agent carries out the construction work, using the
   SKILL's knowledge to guide its actions — invoking ngdj schematics, reading
   and writing files, and verifying results.
3. **Next procedure**: `build_app` proceeds to the next procedure node in
   dependency order until all procedures are complete.

**Key Principle**: SKILLS are composable knowledge units. Multiple SKILLS may be
enabled for a single guided agent session when a procedure composes capabilities
from several skills.

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

- **oasdiff — schema diff and change detection**: Run `oasdiff` against the previous and current OpenAPI schema before any generation step. Breaking changes reported by `oasdiff` must be acknowledged or resolved before generation proceeds.
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

**File**: `service.ts.tpl` (intended resource path for the `ng-data-service` skill template)

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

The mode to apply to each object is determined by running `oasdiff` against the previous and current OpenAPI schema. `oasdiff` output identifies which API resources, operations, and models were added (→ Create), changed (→ Modify), or removed (→ Delete), driving the correct skill mode for each affected object.

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
- **`packageManager`** (enum, optional): Package manager to use (`npm` | `yarn` | `pnpm`). Defaults to `pnpm` unless project configuration says otherwise
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
  "packageManager": "pnpm",
  "style": "scss",
  "routing": true,
  "workspaceName": "my-shop"
}
```

**Execution**:
1. Run `npx @angular/cli new my-shop --directory=/home/user/projects/my-shop --package-manager=pnpm --style=scss --routing=true --standalone=true`
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
1. **Preflight validation**:
   - Verify OpenAPI source file exists at `openapi_source_path`
   - Validate OpenAPI spec is well-formed JSON or YAML
   - Check `oasdiff` is installed (`oasdiff --version`)
   - Check ng-openapi-gen is installed in workspace (`npm list ng-openapi-gen`)
   - If config file path provided, verify it exists; otherwise check for default `ng-openapi-gen.json`
2. **Schema diff with oasdiff** (if a previous schema version exists):
   - Run: `oasdiff breaking <previous_schema> <openapi_source_path>`
   - If breaking changes are reported, halt and surface the `oasdiff` output to the caller
   - For non-breaking changes, log the summary and continue
   - If no previous schema exists, skip this step and proceed
3. **Configuration setup** (if config doesn't exist):
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
2. **Schema diff with oasdiff**:
   - Run: `oasdiff breaking <previous_schema> <openapi_source_path>`
   - If breaking changes are reported, halt and surface the `oasdiff` output to the caller before regenerating
   - Run: `oasdiff summary <previous_schema> <openapi_source_path>` and include in the change report
3. **Clean previous generation** (optional, based on ng-openapi-gen behavior):
   - ng-openapi-gen handles incremental updates, but note that removed endpoints/models may leave orphaned files
4. **Re-run generation**:
   - Execute: `npx ng-openapi-gen --config <ng_openapi_gen_config_path>`
4. **Diff analysis**:
   - Identify new services (new OpenAPI tags)
   - Identify modified services (changed endpoints)
   - Identify new models
   - Identify modified models (schema changes)
5. **Report changes**:
   - Include the `oasdiff summary` output in the change report
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
- `oasdiff` CLI installed (download the prebuilt binary from https://github.com/oasdiff/oasdiff/releases)
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

```yaml
---
name: ng-data-service
description: Create, modify, or delete Angular data services that wrap generated `<Resource>ApiService` clients with typed `Observable` methods, snack-bar feedback, and focused unit tests.
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

The `ng-data-service` skill manages handwritten Angular data services that sit on top of generated `*ApiService` clients from the `ng-api` skill. It creates or updates a resource-specific service that centralises API calls, wraps errors with `catchError`, reports failures through `MatSnackBar`, preserves typed `Observable<>` return values, and maintains a matching unit spec.

### Inputs

- `resource_name` (string): Resource name used to resolve the generated `<Resource>ApiService` and related model types

**Resource Mapping**:
- `resource_name` maps to `<Resource>ApiService` generated by the `ng-api` skill
- Service file names follow Angular conventions such as `features/<resource>/services/<resource>.service.ts`
- Shared services that are reused across features may instead live in `core/services/<resource>.service.ts`

### Modes

#### Create

Generate a new Angular data service and unit spec when a resource already has generated OpenAPI client code.

**Input Requirements**:
- `resource_name` (string): Name of the resource to wrap
- Optional placement hint indicating feature-local service (`features/<resource>/services/`) or shared service (`core/services/`)

**Process**:
1. **Pre-flight validation**:
   - Verify the Angular workspace exists
   - Verify the generated `<Resource>ApiService` exists and is importable
   - Identify the generated model and request/response types needed for method signatures
2. **Choose placement**:
   - Use `features/<resource>/services/` when the service belongs to one feature area
   - Use `core/services/` when the same wrapper is shared by multiple features
3. **Scaffold the service**:
   - Create `<resource>.service.ts` from `templates/service.ts.tpl`
   - Inject the generated `<Resource>ApiService` and `MatSnackBar`
   - Add one wrapper method per generated API method
   - Preserve typed `Observable<>` return values for every wrapper
   - Wrap each API call with `catchError(...)` and route user-facing failures through `MatSnackBar`
   - Add success notifications for state-changing wrappers such as create, update, patch, and delete operations; do not add them for read-only list, get, or search methods
4. **Add focused tests**:
   - Create `<resource>.service.spec.ts` beside the service
   - Configure `TestBed` with `HttpClientTestingModule`
   - Mock or spy on `<Resource>ApiService` and `MatSnackBar`
   - Verify wrapped methods delegate correctly, preserve return types, and surface error handling behavior
5. **Report generated artifacts**:
   - List the created `.service.ts` and `.spec.ts` files
   - Summarise wrapped API methods

**Output**:
- New Angular data service at `features/<resource>/services/<resource>.service.ts` or `core/services/<resource>.service.ts`
- Matching unit spec at the same location with `.spec.ts` suffix
- Wrapped methods for each generated `<Resource>ApiService` endpoint

#### Modify

Update an existing Angular data service when generated API methods or service behavior changes.

**Input Requirements**:
- `resource_name` (string): Name of the resource whose service should be updated
- Description of the required change, such as added/removed endpoints, caching changes, or updated error-handling rules

**Process**:
1. Locate the existing `<resource>.service.ts` and `.spec.ts`
2. Reconcile the wrapper surface with the current `<Resource>ApiService`
   - Add wrapper methods for new generated API methods
   - Remove wrapper methods that no longer have generated counterparts
3. Apply requested behavioral updates
   - Change caching strategy where required
   - Update `catchError` logic and snack-bar messaging
   - Adjust mapping logic while keeping typed `Observable<>` returns intact
4. Update the spec to match the service changes
   - Add or remove tests for wrapped methods
   - Update caching and error-handling assertions
5. Report the modified methods and any removed wrappers

**Output**:
- Updated `<resource>.service.ts`
- Updated `<resource>.service.spec.ts`
- Change summary covering wrapped methods, caching, and error handling

#### Delete

Remove a handwritten Angular data service and its associated unit spec.

**Input Requirements**:
- `resource_name` (string): Name of the resource whose service should be removed

**Process**:
1. Locate the target `<resource>.service.ts` in `features/<resource>/services/` or `core/services/`
2. Verify the paired `<resource>.service.spec.ts` file exists if tests were generated
3. Remove both files
4. Check for any now-stale barrel exports (`index.ts` re-export files) or imports; remove them automatically when the deleted service is the only matching export or when a grep check confirms there are no remaining imports, otherwise report the required manual follow-up

**Output**:
- Removed `<resource>.service.ts`
- Removed `<resource>.service.spec.ts`
- Confirmation of deleted artifacts and any follow-up cleanup notes

### Context Files

{{context:../../shared/openapi-integration.md}}

### Supporting Files

- `templates/service.ts.tpl` — Service scaffold that wraps generated `<Resource>ApiService` methods with typed `Observable<>` returns and shared error handling
- `context/openapi-integration.md` — Guidance for locating generated OpenAPI services, models, and import paths

### Validation

**Post-Create/Modify Validation**:
1. **Compile check**:
   ```bash
   npx tsc --noEmit --project tsconfig.json
   ```
   - Confirm the service and spec compile with the generated API imports
2. **Spec run**:
   ```bash
   npm test -- --watch=false --include='**/<resource>.service.spec.ts'
   ```
   - Confirm the targeted service spec passes
3. **Manual review**:
   - Verify every generated `<Resource>ApiService` method that should be exposed has a matching wrapper
   - Verify `catchError` and `MatSnackBar` behavior are present on error paths

### Error Handling

**Common Errors**:

1. **Generated API service missing**:
   - Error: `<Resource>ApiService` cannot be resolved
   - Resolution: Run the `ng-api` skill first, then retry this skill

2. **Wrong service placement**:
   - Error: Service created in a feature folder but needed across the application
   - Resolution: Move the wrapper to `core/services/` and update imports

3. **Untyped wrapper methods**:
   - Error: Service methods return `Observable<any>` or lose generated model typing
   - Resolution: Reuse the generated request/response types from the OpenAPI client and restore explicit `Observable<>` signatures

4. **Spec not aligned with wrapper behavior**:
   - Error: Tests no longer cover all wrapped methods or error paths
   - Resolution: Update `<resource>.service.spec.ts` whenever methods, caching, or snack-bar behavior changes

### Dependencies

**Required Skills**:
- `ng-workspace` for the Angular workspace structure
- `ng-api` for the generated `<Resource>ApiService` dependency

**Required Tools/Libraries**:
- Angular workspace with TypeScript configuration
- Angular HTTP client testing support via `HttpClientTestingModule`
- Angular Material `MatSnackBar`

### Examples

**Example 1: Create a feature-local data service**
```markdown
Input:
- resource_name: "orders"

Process:
1. Verify OrdersApiService exists from ng-api generation
2. Create features/orders/services/orders.service.ts
3. Wrap each OrdersApiService method with typed Observable returns and catchError
4. Create features/orders/services/orders.service.spec.ts using HttpClientTestingModule

Output:
- features/orders/services/orders.service.ts
- features/orders/services/orders.service.spec.ts
```

**Example 2: Modify wrapper behavior after API regeneration**
```markdown
Input:
- resource_name: "users"
- change: "Add wrapper for new deactivate endpoint and update cache invalidation"

Process:
1. Compare UsersApiService methods with users.service.ts
2. Add deactivate wrapper and cache updates
3. Update error handling and spec coverage

Output:
- Updated users.service.ts
- Updated users.service.spec.ts
```

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

## Angular Material form field generation

```yaml
---
name: ng-form-field
description: Create, modify, or delete Angular Material form field components implementing ControlValueAccessor for seamless reactive forms integration with validation and error handling
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

**Skill Name**: `ng-complex-component`

### YAML Frontmatter

```yaml
---
name: ng-complex-component
description: Create, modify, or delete Angular Material complex components with theme mixins, nested child components, content projection, and CDK overlay integration
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

The `ng-complex-component` skill manages Angular Material components that go beyond a single standalone component scaffold. It is used when a component needs one or more advanced composition features: a dedicated theme mixin, nested child components, typed content projection slots, or CDK overlay behavior. The skill keeps the component aligned with the simpler `ng-component` conventions while expanding the generated structure to cover public API documentation, theming integration, and multi-file component composition.

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

## ng-reactive-form

```yaml
---
name: ng-reactive-form
description: Create, modify, or delete Angular Material reactive forms with typed FormGroup, FormBuilder scaffolding, Material form fields, server-side validation error handling, and comprehensive specs
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

The `ng-reactive-form` skill manages Angular reactive form components that use typed `FormGroup<>` interfaces, `FormBuilder` for control creation, Angular Material form fields (`MatFormField`), and integrate with data services for submission. These forms implement loading states with `MatProgressBar`, handle server-side validation errors by calling `setErrors()` on individual controls, wire submit actions to data service methods, and provide cancel handlers for navigation or output events. Forms can operate in create mode (empty initial values), edit mode (pre-populated from resource), or both modes (dynamic based on route parameters).

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
  - Inspect generated API models from `ng-api` output to derive field types
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
     - Verify generated API models exist from `ng-api` skill output
     - Verify corresponding data service exists from `ng-data-service` skill
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
   - Resolution: Run `ng-api` skill first to generate OpenAPI models, then retry

2. **Data service missing**:
   - Error: Cannot inject data service for submit integration
   - Resolution: Run `ng-data-service` skill to create service wrapper, then retry

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

## Angular Material page generation

**Skill Name**: `ng-page`

### YAML Frontmatter

```yaml
---
name: ng-page
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

The `ng-page` skill manages top-level Angular Material pages inside an existing feature area. It covers page scaffolding, route registration, optional sidenav navigation, and page-specific layout patterns for common application screens. Use this skill after the Angular workspace and app exist, and after supporting skills such as data services, shared components, and reactive forms are available when the requested page depends on them.

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
   - Resolution: run the `ng-reactive-form` skill first for the required step forms (see Dependencies below), then retry page generation

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
   - Confirm the planned build step is valid without executing a full deployment build

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

# Skill building

To create a skill from scratch with the skill-creator, I need roughly four things from you. Only the first two are required upfront; the rest can be built together.

**1. Intent — required, conversational**

Three short answers:
- What should the skill enable Claude to do? (the capability)
- When should it trigger? (user phrases, file types, contexts — this becomes the `description` field, which is what actually decides whether the skill fires)
- What's the expected output? (a file, a code change, a report, etc.)

Free-form prose is fine; I'll ask follow-ups to fill the gaps.

**2. Domain detail — required, format flexible**

Whatever a competent practitioner would need to do the task by hand. Concretely: the input shape (file paths, schemas, structured data, free text), the output shape (exact format, extensions, naming, directory layout), conventions or style rules the output must follow, edge cases (missing input, conflicts, partial state), and dependencies on other skills or artifacts.

The highest-bandwidth form here is a sample: an example input, a hand-written "good" output, or an existing spec doc. Much better than describing in prose. `GENERATE_SKILLS.md` is exactly this kind of input — a structured spec.

**3. Bundled resources — optional**

Anything that should live inside the skill folder so the skill doesn't reinvent it on every run: scripts in `scripts/` for deterministic steps, long reference docs in `references/` loaded on demand, and assets in `assets/` (templates, fixtures, icons). If you don't have these, I draft them as part of skill creation.

**4. Evaluation setup — optional but recommended when outputs are verifiable**

Two or three realistic test prompts (what a real user would actually type), any input files those prompts need, and a rough sense of what "right" looks like — I turn that into assertions. For subjective outputs (writing style, design feel) we skip assertions and rely on your review of the rendered results.

---
