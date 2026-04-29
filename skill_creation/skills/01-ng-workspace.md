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

