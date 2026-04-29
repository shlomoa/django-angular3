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

