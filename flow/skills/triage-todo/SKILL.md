---
name: triage-todo
description: >-
  Process items in `.todo` + `.todo-inbox` and convert each into a milestone, plan, scheduled task,
  scope-cut, or deletion. Use when the user says: "triage todo", "process todo", "clear todo",
  "address todo items", "go through .todo", "what's in todo", or signals they want the parking lot
  cleared. Pulls items off the list — opposite of the default flow which only adds.
---

# Triage-Todo

`.todo` accumulates side topics, ideas, and parked decisions; `.todo-inbox` (if the project keeps
one) accumulates agent deferrals awaiting user triage. This skill walks each item, decides where it
belongs, and clears it from the list.

Recommended inbox entry shape (record list, newest on top): `- topic:` (short imperative title),
`type:` (decision | bug | feature | refactor | meta | chore — the triage routing hint), `origin:`
(date + which session parked it), `why:` (out-of-scope-of-X / blocked-on-Y / needs-user-decision),
`context:` (act-cold content — long values as a bare key + 4-space-indented lines). Scan `type:` +
`why:` to route without reading bodies.

## When invoked

The user wants to clear the parking lot. The flow is collaborative — you propose, they confirm.

**`.todo` is guarded** (this plugin ships the `todo-readonly-guard` hook making it LLM-read-only): a
triage session edits it constantly, so if a write is blocked, FIRST ask the user to arm the session
by replying **"ALLOW TODO"**. `.todo-inbox` is always writable. (To *work* items now instead of
routing them, see the sibling `feedback` skill.)

## Process per item

For each item in `.todo-inbox` (all entries) and the `.todo` top section (above any `# TMP NOTES`
divider):

1. **Read the item** — understand its scope.
2. **Propose a destination**:
   - **Milestone** (`.agent/milestone/{date}_{slug}/`) — strategic, multi-session, multi-topic. Use
     the `milestone` skill.
   - **Plan** (`.agent/plan/YYMMDD_HHMMSS_{topic}.md`) — single topic, multi-step. Use the `plan`
     skill.
   - **Scheduled task** — recurring or one-time future action.
   - **Scope-cut** — if the item is "remove X". Use the `scope-cut` skill.
   - **Background job** — a well-scoped task or incremental backlog the project would run through
     its job runner (deferred `looper`/`grind` flows). Only if the project has such a runner.
   - **Already done** — verify, then delete from `.todo`.
   - **Defer in place** — leave with a clarifying note (e.g. "blocked on Y", "after milestone Z
     closes"). Don't move it, but enrich it.
   - **Trash** — no longer relevant, just delete.

3. **Show the user**: "Item N: '{text}' → propose **{destination}** because {one-sentence reason}.
   OK?"
4. **On confirmation**, take the action and delete the item from its source file. Inbox items the
   user wants parked long-term move INTO `.todo`. Don't ask for each item one at a time — show 3-5
   proposals at once and let the user batch-confirm or override individual ones.
5. **Repeat** until the section is empty or the user wants to stop.

## Batching

Use the `AskUserQuestion` tool to batch decisions when items are similar:

```
Q: Items 3, 5, 7 are all "small UI polish" tasks. Convert to a single plan?
   - Yes — one plan "ui-polish-sweep"
   - No — keep as individual items
   - Defer — leave as-is for now
```

Saves round-trips.

## What gets PRESERVED in .todo

- Everything below a `# TMP NOTES` (or similar) divider — reference notes, parking-lot ideas, source
  material for future work, scoped working areas. Section names evolve; the rule is "don't touch
  below the divider."

Don't touch the lower reference sections unless the user explicitly asks.

## What gets DELETED from .todo

- Top-level `- ` items that have been actioned (moved to milestone/plan/scheduled/scope-cut, marked
  done, or trashed).
- Items the user explicitly says "drop" or "no longer relevant."

## Final commit

One commit at the end: `triage .todo: process N items (M to milestones, K to plans, P deleted)`.

## What NOT to do

- Don't auto-create milestones/plans/jobs without confirmation. The proposal step matters.
- Don't drop items just because they're old. Some are intentionally parked.
- Don't touch the lower reference sections unless asked.
- Don't combine into mega-milestones. If 5 items become 1 milestone, fine; if 20 items become 1,
  you're hiding work.
