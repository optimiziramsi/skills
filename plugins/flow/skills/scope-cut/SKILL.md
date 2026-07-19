---
name: scope-cut
description: |
  When a feature is being removed from the release or deferred, sweep the codebase + docs + cron + todo for every reference and propose delete-or-defer for each. Use when the user says: "cut X", "remove X from V1", "X is out of scope", "scope-cut X", "we're not building X", "drop X", or signals a feature is being deprioritized. Prevents half-removed features (UI shells without backend, cron jobs for dead features, doc references to non-existent code).
---

# Scope-Cut

Removing a feature is more than deleting code. Docs, cron jobs, todo items, milestone references, tests, migrations — everything has to follow.

## When invoked

The user is removing/deferring a feature. Don't start deleting until the sweep is done and confirmed.

## Sweep sequence

1. **Confirm what's being cut** with one short question: feature name + delete-vs-defer (deferred → recorded in a scope-cut note / todo, not removed). Skip if obvious from context.

2. **Grep for references** across every place a feature leaves a trace. Adapt the list to the project's layout:
   - **Docs / specs** — `.docs/**/*.md`, root `README.md`, `CLAUDE.md`.
   - **Design artifacts** — wireframes, mockups, design notes that mention the feature.
   - **Code** — source dirs (`src/`, `packages/*/src/`, `apps/*/src/`, …).
   - **Scheduled work** — cron/scheduler definitions.
   - **Tests** — `*.test.*`, `*.spec.*`.
   - **Migrations / schema** — DB migration files, schema definitions.
   - **Flow files** — `.agent/milestone/*/` (scope-cut.md + progress), `.agent/plan/`, `.todo` + `.todo-inbox`.

3. **Categorize each reference**:
   - **Delete** — code, tests, cron entries, migrations that only exist for this feature.
   - **Update** — doc mentions where the rest of the topic stays valid.
   - **Mark as cut** — append to `.agent/milestone/{current}/scope-cut.md` if a milestone is active, else to a `## Cut` section in the todo INBOX file (`.todo-inbox`); `.todo` itself may be guard-protected (§ If `.todo` is guarded) — route there only via the armed flow.
   - **Leave** — archive folders (`*/archive/`) — historical record, never touch.

4. **Show the user the categorized list** before applying. They may flag items subtler than they look (cross-feature dependencies, billing implications).

5. **Apply changes** — one commit at the end, single-line message: `cut {feature}: {brief summary}`. Don't commit per file.

6. **Verify** — re-grep for the feature name; only archive matches should remain.

## If `.todo` is guarded

Some projects make `.todo` LLM-read-only (a hook blocks agent writes). If a write is blocked, ask the user to arm the session (e.g. reply with the project's allow phrase) before editing it. `.todo-inbox`, if the project keeps one, is normally writable.

## What NOT to do

- Don't delete migrations that have already shipped — write a new migration that reverses, or mark as no-op.
- Don't touch archive folders.
- Don't commit per-file; one cohesive commit.
- Don't skip the doc/cron sweep — those are the most common drift sources after a cut.

## Cut patterns

- **Feature was never in scope**: full delete (code + cron + doc mentions + todo references).
- **Feature deferred to a later release**: keep the mention in the scope-cut note / todo, delete the code, keep design artifacts (still useful later).
- **Sub-feature of a larger one**: edit the parent doc to clarify what stays vs what goes; don't carve out a separate cut entry.

## After the cut

Before calling the cut complete, audit for the gaps a plain grep misses: repurposed names (the string survives but now means something else), references that use a synonym or abbreviation, and orphan schema columns / config flags the feature left behind.

If the cut affects user-facing copy (landing page, marketing), flag it in the final report — the user may need to update copy separately. If it leaves orphan files (a config flag with no consumers, a DB column with no readers), flag those too — not strictly "in scope" for the cut, but they should follow.
