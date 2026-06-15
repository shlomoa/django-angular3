## Angular Material workspace boiler plate

**Skill Name**: `angular-workspace-foundation`

### YAML Frontmatter

```yaml
---
name: angular-workspace-foundation
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

The `angular-workspace-foundation` skill manages the creation, modification, and deletion of Angular workspaces configured with Angular Material, following modern Angular conventions (standalone components, signals, SCSS theming). This is the foundation skill that must be executed before any app-level or component-level skills can be invoked.

### Inputs

All inputs are read from `django-angular3.json` passed as the procedure input.

| Key | Required | Type | Default | Description |
|---|---|---|---|---|
| `angular.output` | yes | string | — | Absolute path where the workspace will be created |
| `project.name` | yes | string | — | Name of the workspace |
| `angular.workspace.packageManager` | no | `npm` \| `yarn` \| `pnpm` | `pnpm` | Package manager to use |
| `angular.workspace.style` | no | `css` \| `scss` \| `sass` \| `less` | `scss` | Stylesheet format |
| `angular.workspace.routing` | no | boolean | `true` | Whether to include routing |

### Mode: Create

Generate an Angular Material workspace from scratch when it doesn't exist.

#### Input Requirements

- **`angular.output`**: Must not already exist or must be an empty directory
- **`project.name`**: Valid workspace name (lowercase, hyphenated)
- **`angular.workspace.packageManager`**: Valid package manager executable must be available in PATH
- **`angular.workspace.style`**: Must be a valid Angular CLI stylesheet option
- **`angular.workspace.routing`**: Boolean flag

#### Pre-flight Checks

Before creating the workspace, verify:

1. `angular.output` directory does not exist or is empty
2. Node.js version meets Angular's requirements (currently Node 18.19+ or 20.11+ or 22.0+)
3. Sufficient disk space is available (minimum 500MB recommended)

Package manager availability and Angular CLI access are validated by the `ng_new` djng wrapper.

#### Process (Create Mode)

1. **Create workspace via djng wrapper**:
   ```bash
   django-admin ng_new django-angular3.json --dry-run
   ```
   Review the dry-run output (the previewed command invocation). When `ng_new` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_new django-angular3.json
   ```

2. **Install Angular Material via djng wrapper**:
   ```bash
   django-admin ng_add django-angular3.json --dry-run
   ```
   When `ng_add` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_add django-angular3.json
   ```

   > **Note**: `ng_new` and `ng_add` are not in `command_allowlist` by default — they plan dry-runs unless the allowlist is explicitly broadened. See `django_angular3/settings.py`.

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
   pnpm install --save-dev @angular-eslint/builder @angular-eslint/eslint-plugin @angular-eslint/eslint-plugin-template @angular-eslint/schematics @angular-eslint/template-parser
   ```

9. **Initialize ESLint configuration** (uses locally installed Angular CLI — no download):
   ```bash
   pnpm exec ng add @angular-eslint/schematics --skip-confirmation
   ```

10. **Create initial Git commit** (if not skipped):
    ```bash
    git add .
    git commit -m "chore: initialize Angular Material workspace with modern conventions"
    ```

#### Expected Output

After successful execution, the workspace directory contains:

```
<angular.output>/
├── .angular/                    # Angular cache directory
├── .editorconfig               # Editor configuration
├── .gitignore                  # Git ignore rules
├── .prettierrc.json            # Prettier configuration
├── angular.json                # Angular workspace configuration
├── node_modules/               # Installed dependencies
├── package.json                # NPM package manifest
├── pnpm-lock.yaml              # pnpm lock file (default package manager)
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

> **Note**: `build_app` does not trigger `angular-workspace-foundation` Modify mode during normal operation — `django-angular3.json` is always read as current and its changes are not tracked. Modify mode is available for manual invocation via `--force`.

#### Input Requirements

- **`angular.output`**: Must exist and contain a valid Angular workspace (check for `angular.json`)
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
1. Verify `angular.output` exists and contains `angular.json`
2. Update all packages: `pnpm update`
3. Run build: `django-admin ng_build django-angular3.json`
4. Run tests: `pnpm exec ng test --watch=false`
5. Fix any breaking changes
6. Commit changes: `git add . && git commit -m "chore: update dependencies"`

**For `update-angular` modifications**:
1. Verify `angular.output` exists and contains `angular.json`
2. Run Angular update: `pnpm exec ng update @angular/core @angular/cli @angular/material`
3. Review migration messages
4. Run build and tests: `django-admin ng_build django-angular3.json` and `pnpm exec ng test --watch=false`
5. Fix any breaking changes or deprecated API usage
6. Commit changes: `git add . && git commit -m "chore: update Angular to v<version>"`

**For `change-build-config` modifications**:
1. Verify `angular.output` exists and contains `angular.json`
2. Read `angular.json` using Read tool
3. Apply requested configuration changes using Edit tool
4. Validate JSON syntax
5. Test build: `django-admin ng_build django-angular3.json`
6. Commit changes: `git add angular.json && git commit -m "chore: update build configuration"`

**For `reconfigure-material` modifications**:
1. Verify `angular.output` exists and contains `angular.json`
2. Update `src/styles.scss` with new theme configuration using Edit tool
3. Test build: `django-admin ng_build django-angular3.json`
4. Verify Material components render correctly
5. Commit changes: `git add . && git commit -m "style: update Material theme"`

**For `add-eslint-rule` modifications**:
1. Verify `angular.output` exists and ESLint is configured
2. Read `.eslintrc.json` using Read tool
3. Add or modify rules using Edit tool
4. Run linter: `pnpm exec ng lint`
5. Fix any new violations
6. Commit changes: `git add . && git commit -m "chore: update ESLint rules"`

#### Output

- Modified workspace with requested changes applied
- All builds and tests passing
- Git commit created documenting the modification

### Mode: Delete

Remove the workspace directory completely, typically when starting fresh is simpler than extensive modification.

#### Input Requirements

- **`angular.output`**: Must exist and contain a valid Angular workspace (check for `angular.json`)

#### Process (Delete Mode)

1. **Remove workspace via djng wrapper**:
   ```bash
   django-admin ng_workspace_delete django-angular3.json --dry-run
   ```
   Review the dry-run output (the previewed command invocation). When `ng_workspace_delete` is in `command_allowlist`, execute:
   ```bash
   django-admin ng_workspace_delete django-angular3.json
   ```
   The wrapper removes the directory cross-platform via `shutil.rmtree`.

   > **Note**: `ng_workspace_delete` is not in `command_allowlist` by default. See `django_angular3/settings.py`.

2. **Verify deletion**: Confirm `angular.output` directory no longer exists.

#### Output

- Workspace directory removed
- Deletion confirmed

### Supporting Files

#### Context Files

This skill references the following shared context files:

- **`{{context:../../shared/angular-conventions.md}}`** — Loaded at instructions level, provides conventions for standalone components, signals, SCSS theming, naming, imports, and testing patterns

#### Template Files

This skill does not use template files directly, as it relies on Angular CLI schematics for code generation. However, it configures the workspace to use the templates defined in the Templates section when subsequent skills (like `angular-component-composition` or `angular-page-composition`) are invoked.

### Validation

#### Post-Creation Validation

After creating a workspace, verify:

1. **Directory structure exists**:
   ```bash
   [ -f <angular.output>/angular.json ] && echo "✓ Workspace created"
   ```

2. **Dependencies installed**:
   ```bash
   [ -d <angular.output>/node_modules ] && echo "✓ Dependencies installed"
   ```

3. **Build succeeds**:
   ```bash
   django-admin ng_build django-angular3.json
   ```
   Expected: Build completes without errors

4. **Tests pass**:
   ```bash
   pnpm exec ng test --watch=false
   ```
   Expected: All tests pass

5. **Dev server starts**:
   ```bash
   pnpm exec ng serve --port 4200
   ```
   Expected: Server starts and application loads at `http://localhost:4200`

6. **Material is configured**:
   - Check `package.json` contains `@angular/material`
   - Check `src/styles.scss` contains Material theme imports
   - Verify Material components can be imported in app component

#### Post-Modification Validation

After modifying a workspace, verify:

1. **Build still succeeds**: `django-admin ng_build django-angular3.json`
2. **Tests still pass**: `pnpm exec ng test --watch=false`
3. **Linter passes**: `pnpm exec ng lint` (if ESLint configured)
4. **No TypeScript errors**: `django-admin ng_build django-angular3.json` (production configuration)

### Error Handling

#### Common Errors and Resolutions

**Error**: `ng: command not found`
- **Cause**: Angular CLI not installed in workspace `node_modules`
- **Resolution**: Re-run `django-admin ng_new django-angular3.json` to recreate the workspace with all dependencies

**Error**: `EACCES: permission denied`
- **Cause**: Insufficient permissions to create directory or install packages
- **Resolution**: Check directory permissions

**Error**: Dependency conflict during `pnpm install`
- **Cause**: Conflicting package versions
- **Resolution**: Resolve dependency versions manually or use `--force` flag

**Error**: `Schematic "ng-add" not found in collection "@angular/material"`
- **Cause**: Material package issue or version mismatch
- **Resolution**: Install Material manually and configure theme manually

**Error**: `The serve command requires to be run in an Angular project`
- **Cause**: Not in workspace root directory
- **Resolution**: Verify `angular.output` in `django-angular3.json` is correct and points to a directory containing `angular.json`

**Error**: Workspace directory already exists and is not empty
- **Cause**: Target directory contains files
- **Resolution**: Use Delete mode first, or choose a different directory

### Dependencies

**Prerequisites**:
- Node.js (v18.19+ or v20.11+ or v22.0+)
- pnpm package manager
- Git (for version control)
- Sufficient disk space (500MB+)
- djng installed with `ng_new`, `ng_add`, `ng_build`, `ng_workspace_delete` wrappers available

**No skill dependencies**: This is the foundational skill. All other Angular skills depend on this skill being executed first to create the workspace.

**Dependent skills** (must have workspace before using):
- `angular-app-composition` — Angular Material app boiler plate
- `ng-api-gen` — Angular API generation
- All component, form, page, and site generation skills

### Examples

#### Example 1: Create New Workspace

**Input** (from `django-angular3.json`):
- `project.name`: `"my-shop"`
- `angular.output`: `"/home/user/projects/my-shop"`
- `angular.workspace.packageManager`: `"pnpm"`
- `angular.workspace.style`: `"scss"`
- `angular.workspace.routing`: `true`

**Execution**:
1. Run `django-admin ng_new django-angular3.json`
2. Run `django-admin ng_add django-angular3.json`
3. Configure custom SCSS theme
4. Install ESLint with `pnpm exec ng add @angular-eslint/schematics`
5. Create initial commit

**Output**: Workspace created at `/home/user/projects/my-shop` with Material configured

#### Example 2: Update Angular Version

**Input** (from `django-angular3.json`):
- `project.name`: `"my-shop"`
- `angular.output`: `"/home/user/projects/my-shop"`

**Execution**:
1. Run `pnpm exec ng update @angular/core @angular/cli @angular/material`
2. Review and apply migrations
3. Run `django-admin ng_build django-angular3.json` and `pnpm exec ng test --watch=false`
4. Commit changes

**Output**: Angular updated to latest version with all migrations applied

#### Example 3: Delete Workspace

**Input** (from `django-angular3.json`):
- `project.name`: `"my-shop"`
- `angular.output`: `"/home/user/projects/my-shop"`

Procedure-level input: `confirmDelete: true`

**Execution**:
1. Check for uncommitted changes (warn if present)
2. Create backup tarball
3. Remove workspace directory
4. Confirm deletion

**Output**: Workspace deleted, backup saved to `/home/user/projects/my-shop-backup-20260425-153000.tar.gz`
