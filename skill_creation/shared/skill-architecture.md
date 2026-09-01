# Skill Architecture

> **Rendering note:** This historical authoring guide describes the planned
> Claude Agent Skills rendering. The canonical Skill contract is defined in
> `doc/contracts/AI_AUTOMATION_CONTRACTS.md`; provider adapters render that contract into
> native formats. The `.claude/` layout and YAML fields below are not canonical
> requirements for OpenAI, Gemini, or Copilot renderings.

The Claude rendering uses the **Agent Skills** format — reusable capabilities
designed to be auto-invoked by the Claude adapter.

This file describes the architecture of the SKILLS primitive only. It does not
define TOOLS, HOOKS, or PLUGINS as automation primitives; those belong to the
broader AI automation model defined in `doc/ARCHITECTURE.md` §3.6. Their
canonical contracts remain in `doc/contracts/AI_AUTOMATION_CONTRACTS.md`.

## Directory Structure

Each skill lives in its own directory under `.claude/skills/`:

```
.claude/skills/<skill-name>/
  SKILL.md          # Main skill specification with YAML frontmatter
  references/       # Optional reference files read on demand
  templates/        # Optional template files read and adapted on demand
  examples/         # Optional example files read on demand
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
- **`allowed-tools`**: List of Claude Code tools the skill is permitted to use during execution. This field governs what a SKILL may call; it is not itself the definition of the broader TOOLS primitive.

## Three Loading Levels

Skills are loaded incrementally to manage token costs:

### 1. Metadata Level (lowest cost)
- Loads only the YAML frontmatter
- Used by outer agent for skill discovery and matching
- Minimal token consumption (~50-100 tokens per skill)

### 2. Instructions Level (medium cost)
- Loads the full `SKILL.md` content including all markdown sections
- Used when the outer agent has selected the skill and needs execution instructions
- Moderate token consumption (~500-2000 tokens depending on skill complexity)

### 3. Resources Level (highest cost)
- Supporting files are read with the Read tool only when the instructions link
  to them and the skill needs them
- High token consumption (~2000-10000+ tokens for complex skills)

**Token Cost Strategy**: The outer agent loads metadata for all skills and
instructions for candidate skills. Supporting files are read on demand only by
the executing skill, minimizing overall token usage.

## Supporting File References

Skills reference supporting files with standard Markdown links. Read linked
files on demand; do not inject their contents when the skill instructions load.

### Shared Reference Files

Within `SKILL.md`, point to shared reference files with a one-level-up relative
link:

```markdown
See [filename.md](../shared/filename.md) — read this on demand before following these conventions.
```

### Template References

Within skill instructions, link to templates and read and adapt them when
generating the output:

```markdown
Use [template-name.ts](templates/template-name.ts) — read and adapt it for the output file.
```

## Auto-Invocation Model

Skills are invoked by an **outer agent**, not by users:

1. **User Request**: User provides high-level task to outer agent (e.g., "Create an Angular Material workspace")
2. **Skill Selection**: Outer agent loads metadata for all skills and matches user request to appropriate skill(s) based on descriptions
3. **Skill Execution**: Outer agent forks a new context, loads the selected skill at instructions level, and executes it
4. **Result Handoff**: Skill completes and returns results to outer agent
5. **Continuation**: Outer agent may invoke additional skills or return final results to user

**Key Principle**: Skills are designed as composable units that can be chained together by the outer agent to accomplish complex tasks. In the broader automation model, they are one execution primitive alongside deterministic TOOLS, enforced HOOKS, and packaging-oriented PLUGINS.

## Claude `SKILL.md` Template Structure

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

## Supporting Files

See [additional-guidance.md](references/additional-guidance.md) — read this on demand before applying its guidance.

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

This Claude rendering structure provides consistent guidance for Claude adapter
invocation and rendering. It must preserve the canonical Skill contract rather
than become a second source of truth.
