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

