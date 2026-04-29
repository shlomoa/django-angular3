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

