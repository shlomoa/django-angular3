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

Manage an Angular workspace area
- Create: Create an Angular Material workspace from scratch
- Modify: Changes might be: NPM packages, configuration parameters, new workspace methodologies and tools like build or test, new BKMs arising from an Angular version change.
- Delete: When entering an old area, and required to start from scratch it's better to Delete and Create than modify.

## Angular Material app boiler plate

Manage an Angular Material app 
- Create: Create an Angular Material workspace from scratch
- Modify: Changes might be: NPM packages, configuration parameters, new workspace methodologies and tools like build or test, new BKMs arising from an Angular version change.
- Delete: When entering an old area, and required to start from scratch it's better to Delete and Create than modify.

## Angular API generation

Manage Angular data model API, using ng-openapi-gen
- Create: Generate data model from scratch
- Modify: Make changes to an existing data model
- Delete: When it is too complex to modify successfully it's better to delete and generate from scratch.

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
Manage Angular component generation
- Create: Generate a component from scratch
- Modify: Modify an existing component
- Delete: When it's too complex to modify we delete and create.

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

