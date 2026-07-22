---
name: scaffold
description: >-
  One-time bootstrap of a project for the opsi toolkit: create the `.agent/` workspace layout with
  an index (`.agent/README.md`), and add a single pointer to it from the entrypoint (CLAUDE.md /
  AGENTS.md). Use when setting up a new or existing repo to use these plugins — "set up opsi here",
  "scaffold the agent workspace", "wire up the .agent layout", "initialize the toolkit in this
  project". Idempotent; confirms before editing the entrypoint. Does NOT register individual skills
  (they auto-trigger) and does NOT generate anything on an ongoing basis.
---

# Scaffold — bootstrap the `.agent/` workspace

A **one-time** setup. The opsi plugins keep everything they create under `.agent/` (so they don't
clutter the repo root). This skill makes that layout legible: it writes a static `.agent/README.md`
index and adds **one** pointer to it from the project's entrypoint. That's all — skills discover
themselves via their descriptions, and the `session-start` hook keeps live state fresh, so there's
nothing to generate or re-sync afterward.

## Why it's shaped this way

- **Skills don't need to be listed in CLAUDE.md to work** — Claude Code auto-triggers them on their
  descriptions when the plugin is enabled. So this skill does NOT enumerate skills into the
  entrypoint (that would duplicate the plugin manifests and drift).
- **The index is static**, not generated from enabled plugins. It describes the standard layout; a
  dir simply won't exist until you use the matching skill. Nothing to keep in sync.
- **It's the only step that touches your entrypoint**, and it asks first.

## Steps

1. **Find the entrypoint.** Prefer `CLAUDE.md`, else `AGENTS.md`, at the repo root. If neither
   exists, tell the user and offer the **`scaffold-claude-md`** skill — it writes a house-style
   CLAUDE.md (a slim router of the hard rules), then this skill adds the pointer. (Claude Code's
   built-in `/init` writes a full codebase-doc CLAUDE.md instead, if they'd rather.) Never silently
   create one.

2. **Write `.agent/README.md`** (if absent — never overwrite an existing one without asking). Use
   the template below. Create the `.agent/` dir if needed; do NOT pre-create the working sub-dirs
   (`plan/`, `loop/`, …) — each skill makes its own on first use.

3. **Add one pointer to the entrypoint** (idempotent — skip if a link to `.agent/README.md` is
   already there). Insert near the top or in a "Conventions"/"Layout" section:

   ```markdown
   **Agent workspace:** this project uses the opsi toolkit's `.agent/` layout — see
   [`.agent/README.md`](.agent/README.md) for what lives where.
   ```

   **Show the user the exact edit and confirm before writing it.**

4. **Mention the commit choice** (don't decide it): `.agent/` can be **committed** (team-shared
   continuity — handoff, lessons, plans travel with the repo) or **gitignored** (private working
   notes). Ask which they prefer; if gitignore, add `.agent/` to `.gitignore` (but consider keeping
   durable knowledge like `lessons/` and `patterns/` committed even then).

5. **Stop.** Do not register individual skills, do not create a cron/generator, do not add more than
   the one pointer. Setup is done.

## `.agent/README.md` template

```markdown
# `.agent/` — the agent workspace

Everything the [opsi](https://github.com/optimiziramsi/skills) toolkit's plugins create lives here, so
it stays out of your repo root. Files/dirs appear as you use the matching skill — not all will exist.

| Path | What it holds | Owned by (skill/plugin) |
|---|---|---|
| `handoff.md` | next-session continuity notes (≤4k) | `handoff` / session |
| `FEEDBACK.md` | agent-owned ledger of processed `.todo` items | `feedback` / flow |
| `lessons/` | durable, hard-won lessons + a README index | `lessons` / instructions |
| `instructions-changelog.md` | tier-tagged log of instruction changes | `retro` / instructions |
| `milestones.md` | active-milestones index (what's in flight) | `milestone` / flow |
| `milestone/{date}_{slug}/` | strategic multi-session initiatives | `milestone` / flow |
| `plan/` | single-topic implementation plans | `plan` / flow |
| `loop/` | background job queue + logs | `looper` / flow |
| `grind/` | grind missions + cross-iteration memory logs | `grind` / flow |
| `reviews/` | point-in-time review/audit outputs | `review` / review |
| `patterns/` | the per-topic pattern registry (blessed code shapes) | `manage-patterns` / patterns |
| `worktrees.md` | the parallel-work board | `worktree` / worktree |

**Not here (on purpose):** `.docs/` is your own architecture/specs (skills *link* to it, never write
it); `.todo` / `.todo-inbox` are your parking lot at the repo root; `.claude/rules/` is Claude config.

Closed plans/milestones move to an `archive/` subdir — kept as a frozen record, never edited again.
```

## What NOT to do

- **Don't enumerate skills into the entrypoint** — they auto-trigger; listing them duplicates the
  manifests and drifts.
- **Don't overwrite** an existing `.agent/README.md` or re-add a pointer that's already there.
- **Don't create the working sub-dirs** — the skills make them on demand.
- **Don't set up any ongoing generation** — this is a one-time bootstrap.
