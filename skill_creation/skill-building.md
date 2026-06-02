# Skill building

To create a skill from scratch with the skill-creator, I need roughly four things from you. Only the first two are required upfront; the rest can be built together.

**1. Intent — required, conversational**

Three short answers:
- What should the skill enable Claude to do? (the capability)
- When should it trigger? (user phrases, file types, contexts — this becomes the `description` field, which is what actually decides whether the skill fires)
- What's the expected output? (a file, a code change, a report, etc.)

Free-form prose is fine; I'll ask follow-ups to fill the gaps.

**2. Domain detail — required, format flexible**

Whatever a competent practitioner would need to do the task by hand. Concretely: the input shape (file paths, schemas, structured data, free text), the output shape (exact format, extensions, naming, directory layout), conventions or style rules the output must follow, edge cases (missing input, conflicts, partial state), and dependencies on other skills or artifacts.

The highest-bandwidth form here is a sample: an example input, a hand-written "good" output, or an existing spec doc. Much better than describing in prose. `doc/GENERATE_AI_AUTOMATIONS.md` is exactly this kind of input — a structured spec.

**3. Bundled resources — optional**

Anything that should live inside the skill folder so the skill doesn't reinvent it on every run: scripts in `scripts/` for deterministic steps, long reference docs in `references/` loaded on demand, and assets in `assets/` (templates, fixtures, icons). If you don't have these, I draft them as part of skill creation.

**4. Evaluation setup — optional but recommended when outputs are verifiable**

Two or three realistic test prompts (what a real user would actually type), any input files those prompts need, and a rough sense of what "right" looks like — I turn that into assertions. For subjective outputs (writing style, design feel) we skip assertions and rely on your review of the rendered results.

---
