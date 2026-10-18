---
name: feedback
description: >-
  Process the user's `.todo` inbox into an agent-owned `.agent/FEEDBACK.md` ledger and work the
  items now. Use when the user says "process feedback", "feedback round", "work through my
  comments/notes", or mentions new items in `.todo` they want handled this session. Differs from
  `triage-todo` (which routes items into plans/milestones for later): feedback WORKS items
  immediately, tracking each through Open → In Progress → Done/Wont Do.
---

# Feedback round

`.todo` is the **user's** inbox — read-only for agents (this plugin ships the `todo-readonly-guard`
hook enforcing it; the user may be editing the file live). `.agent/FEEDBACK.md` is the agent-owned
ledger tracking what was done about each item. Ledger, not inbox — never write items *for* the user.

Sibling flow: `triage-todo` **routes** items into planning artifacts for later; this skill **works**
items now. If an item is too big to work this session, propose triaging it instead.

## The round

1. **Read `.todo` and `.agent/FEEDBACK.md`** (create the ledger from the template below if absent).
   **Diff them**: an item is new only if no Open / In Progress / Done / Wont Do line already covers
   it — stale lines and near-dupes happen; when unsure, ask rather than double-process.
2. **Copy genuinely new items** into FEEDBACK.md **Open** (verbatim enough to recognize the source
   line), then number the round (check Done for the last round number).
3. **Work items one at a time**: move the line to **In Progress**, implement, verify per the
   project's done-gate (real runs, not code-reading; screenshots for UI work), then move to **Done**
   with date + a short note of what was done. Items you won't do go to **Wont Do** with the reason —
   never silently drop one.
4. **Commit as you go** — one commit per item or coherent group.
5. **Retention**: Done keeps only the **last 2 rounds** — when adding a new round, delete the oldest
   (git history is the archive). Keeps the ledger small enough to diff against `.todo` at a glance.
6. **End the round**: lean summary (done / questions / next); refresh the handoff if significant.

## `.agent/FEEDBACK.md` template

```markdown
# Feedback ledger

Agent-owned mirror of `.todo` processing — the user writes `.todo`, this file tracks outcomes.

## Open

## In Progress

## Done

### Round 1 — YYYY-MM-DD

## Wont Do
```

## What NOT to do

- **Never edit `.todo`** — not even to mark items done; the user prunes their own inbox using the
  ledger. (If the project armed `.todo` writes, still prefer the ledger — arming is for triage.)
- **Deferrals you park in a `.todo-inbox`** follow the record entry shape the `triage-todo` skill
  documents (`topic` / `type` / `origin` / `why` / `context`) — parked ≠ unstructured.
- **Don't re-copy items** already tracked — the diff in step 1 is the dedup gate.
- **Don't batch everything into one commit** at the end.
