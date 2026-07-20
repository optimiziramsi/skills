# patterns — a pattern registry for Claude

Part of the [`opsi`](../../README.md) marketplace.

A **per-topic pattern registry**: capture each blessed code shape once, as a full body with GOOD /
BAD / anti-patterns / edge cases, and make the agent *consult it at the moment of editing* — so new
code follows the decided shape and drift gets caught. The registry lives at `.agent/patterns/`; one
markdown file per topic, plus a `README.md` index.

This ships the **system**, not any project's conventions. You fill `.agent/patterns/` with your own
project's patterns; the skill, agents, and hooks are the machinery for authoring, verifying, and
enforcing them. (It does **not** include a coding-style guide — that's project content.)

## Contents

- name: `manage-patterns`
  kind: skill + command
  purpose:
    Author + curate the registry — the file-first, human-reviewed **5-phase workflow**
    (brainstorm → plan → build code → human review → write pattern), topic-file structure,
    `blessed`/`decided`/`TODO` status + gating, filename/frontmatter conventions, split/merge.

- name: `pattern-compliance`
  kind: agent
  purpose:
    Read-only audit of changed code against the formal `.agent/patterns/<topic>.md` bodies —
    shape match, anti-patterns, edge cases, and status (refuses code following a
    `decided`/`TODO` pattern).

- name: `pattern-verifier`
  kind: agent
  purpose:
    Read-only check of changed code against the **project's own** coding-style / convention
    rules (read fresh each run). The lighter, code-shape pass that pairs with
    `pattern-compliance`.

- name: `pattern-guards`
  kind: hook
  purpose:
    PreToolUse — **hard-blocks** an edit whose path is governed only by non-blessed patterns
    (the gating rule, mechanized). PostToolUse — reminds once/session which pattern checklists
    govern the edited file, and **auto-regenerates** the routes table when you change a pattern.
    Fails open; escape hatch `PATTERN_GUARDS_OFF=1`.

- name: `generate-pattern-routes`
  kind: hook
  purpose:
    Compiles every pattern's `paths:`/`route:`/`status:` frontmatter into
    `.agent/patterns/pattern-routes.tsv` (the table the guard reads). Runs automatically via the
    guard; also runnable by hand.

## How the gate works

Each pattern's frontmatter declares the **globs it governs** (`paths:`) and a **route** (`edit` =
remind at edit-time; `land` = codebase-wide, review at land-time). `generate-pattern-routes.py`
compiles those into `.agent/patterns/pattern-routes.tsv`; the `pattern-guards` hook reads it on
every Write/Edit:

- Editing a path governed **only** by `decided`/`TODO` patterns → **blocked** (walk the pattern
  first).
- Editing a path a `blessed` pattern also governs → allowed, with a one-time reminder to read its
  `#### Rules — write-time checklist` (any non-blessed overlap is surfaced as a STOP-warning).

Config: `PATTERN_REGISTRY_DIR` (default `.agent/patterns`), `PATTERN_GUARDS_OFF=1` to disable.

> **Note:** enabling this plugin activates `pattern-guards` in every project that enables it. In a
> project with **no** `.agent/patterns/` registry the hook is a silent no-op (nothing to gate). It
> only starts gating once you author patterns with `paths:` frontmatter.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "opsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "patterns@opsi": true }
}
```

Then `/manage-patterns` to walk your first topic.
