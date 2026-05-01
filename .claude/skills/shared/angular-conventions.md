# Angular Conventions (shared)

The following conventions apply to all Angular artifacts produced by ngdj
schematics and djng skills for generated apps.

## Standalone components

All components use `standalone: true`. NgModules are not generated. Imports
are declared directly in the component decorator.

## Signals

State management uses Angular signals (`signal()`, `computed()`, `effect()`).
Avoid `BehaviorSubject` and `Observable`-based state where signals suffice.

## SCSS and Material theming

Component stylesheets use `.scss`. Global theme tokens (palette, typography,
density) are defined once in the workspace theme file and consumed via
`mat.get-theme-color()` / `mat.get-theme-typography()` mixins. Do not hard-code
colour values in component SCSS files.

## Naming conventions

- Files: `<name>.<type>.ts` — e.g., `user-list.component.ts`
- Classes: PascalCase — e.g., `UserListComponent`
- Selectors: `app-<name>` — e.g., `app-user-list`

## Dependency injection

Use Angular's `inject()` function. Do not use constructor injection for new
code. Barrel files (`index.ts`) are generated for each feature directory.

## Testing patterns

Unit tests use Jest with Angular Testing Library. Each component test file
follows `<name>.component.spec.ts`. Services use `TestBed` with
`provideHttpClientTesting()` for HTTP dependencies.
