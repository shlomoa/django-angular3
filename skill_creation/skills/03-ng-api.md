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

