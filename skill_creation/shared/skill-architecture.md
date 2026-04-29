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

