# openui-spec integration plan

## What openui-spec provides

The `openui-spec` defines three layered artifacts:

- **`openui.schema.json`** — grammar: validates the shape of any OpenUI JSON document
- **`openui.json`** — catalog: machine-readable vocabulary of all scope objects (Application, Controls, Behaviors, Pages, Views, Containers, Widgets, …)
- **concrete UI document** (`input.json`) — a schema-valid document using vocabulary from the catalog; this is the user-authored UI description

The concrete document format directly resolves the `<project>.project.json` "schema TBD" blocker in APP_BUILDER_REQUIREMENTS.md and TODO §1.

---

## Task 1: Document update cadence — proposed sequence

### Step 1.1. — Anchor the format in ARCHITECTURE.md (foundational)
**Target:** `doc/ARCHITECTURE.md §8.5`  
Add a reference to `shlomoa/openui-spec` as the format authority for the non-CRM input source. Name the concrete document as an OpenUI concrete UI document conforming to `openui.schema.json` with vocabulary from `openui.json`. Settle the file name (e.g. `app.ui.json` or keep `input.json`).  
**Why first:** all other documents derive from this anchor.

### Step 1.2. — Formalize the stage in REQUIREMENTS.md (gap named in TODO §1)
**Target:** `doc/REQUIREMENTS.md §4.2.2`  
Add the missing sentence naming the non-CRM content stage as a discrete governed construction stage, referencing `ARCHITECTURE.md §7.1 stage 4`.  
**Why second:** depends on the format name established in Step 1.

### Step 1.3. — Resolve TBDs in APP_BUILDER_REQUIREMENTS.md
**Target:** APP_BUILDER_REQUIREMENTS.md  
Replace the three ⚠️/TBD markers (schema definition, diff function, `<project>.project.json` name) with concrete references: the file name settled in Step 1, `openui.schema.json` as the validation schema, and a note that diff behavior operates on the OpenUI document tree.

### Step 1.4. — Update the spec/ui example
**Target:** example.ui.json  
Rewrite the example to use the openui-spec concrete document format (`id`, `version`, `type`, `attrs`, `children` per `openui.schema.json`) instead of the current custom `pages`/`forms` shape. Reference the per-scope examples at `openui-spec.readthedocs.io/en/latest/examples/` as the vocabulary source.

### Step 1.5. — Update README.md
**Target:** `README.md` (line 231 area)  
Replace the YAML `pages`/`forms` snippet (the old custom format) with an equivalent openui-spec concrete document JSON example. The copilot-instructions require `README.md` to be updated for user-facing workflow or command changes; switching the UI input format is user-facing.  
**Why here:** depends on the format and file name settled in Steps 1 and 4.

### Step 1.6. — Close / update TODO §1
**Target:** `TODO.md §1`  
Change status from **Blocked** to **In progress** or **Resolved — pending implementation**. Record openui-spec as the format definition. List the remaining open items: validation implementation in `validation.py`, final file name if still to be confirmed, and `REQUIREMENTS.md §4.2.2` gap if not yet closed.

**Dependency chain:** Step 1 → Steps 2, 3 (parallel) → Step 4 → Step 5 → Step 6.  
Steps 2 and 3 can be done in the same pass once the file name is anchored. Step 4 requires the name and format to be settled. Step 5 (README.md) follows Step 4. Step 6 should be the final close-out pass.

---
