---
name: milestone
description: >-
  Create, switch, and close milestones in `.agent/milestone/`. Milestones are strategic initiatives
  that span multiple topics and sessions (e.g. "cleanup and patterns", "ship v1 iOS app"). Each
  milestone is a folder with its own scope, steps, progress, and notes — giving agents a tight
  context window per initiative. Use when the user says: "let's start a milestone", "switch to the X
  milestone", "what milestones are active", "close this milestone", or opens a strategic initiative
  that will take multiple sessions. Do NOT use for single-topic plans (those go in `.agent/plan/` —
  use the `planning:new` skill).
---

# Milestone

Milestones live in `.agent/milestone/`. Each milestone is a folder containing its scope, steps, and
progress. The folder is the working surface for one strategic initiative across many sessions.

## When to use milestones vs plans vs direct work

- Single focused task finishable in one session: direct
- One topic, one execution plan: `.agent/plan/` + `planning:new` skill
- Strategic initiative spanning many topics and multiple sessions: `.agent/milestone/` (this)
- Parallel initiatives where context-switching needs a clean workspace: multiple
  `.agent/milestone/*/`

A milestone is the right abstraction when the initiative has its own scope cut, progress log and
notes; when agents dispatched for it should read ONLY this folder + referenced docs; when multiple
plans may live under it; or when the user says "let's continue on X" for a multi-session effort.

Two guardrails: multi-step or structurally-different work gets its **own** milestone — don't bolt it
onto an active one. And on close, no active file may keep referencing the archived milestone.

## Folder layout

```
.agent/milestone/
  YYMMDD_{slug}/                    # milestone folder — date-only prefix (milestones span days/weeks)
    README.md                       # status/progress at top, then scope/goals/success-criteria/notes
    steps.md                        # execution sequence (numbered steps) — single-chat milestone
    ledger.md                       # umbrella milestone only — records/groups/requests, replaces steps.md (§ Umbrella milestones)
    {topic}.md                      # milestone-specific docs (scope-cut.md, etc.)
  archive/                          # closed milestones archived here
```

Milestones use a date-only prefix (`YYMMDD` from `date '+%y%m%d'`) — long-lived, so second-level
precision just clutters the path. Inner files carry no prefix (they're structural, not topical).

## Active-milestones index

`.agent/milestones.md` is the single human-facing index of what's in flight. It lists ONLY live
(non-archive) milestones as a **record list — one dash per milestone, fields as 2-space-indented
`field: value` lines, never a table** (so it diffs cleanly and passes a `no-tables` lint). It stays
in lockstep with `.agent/milestone/`: **add** a record on create, **flip** its `status:` on
switch/pause, **remove** it on close. When nothing is active the file reads `_None active._`
Archived milestones are NEVER listed. Every create/switch/close below carries the matching index
step; do not skip it.

## Umbrella milestones (parallel chats) — the ledger

An **umbrella** milestone fans one initiative across **many parallel chats under one orchestrator**
(the chat holding this skill). It keeps `<milestone>/ledger.md` **in place of `steps.md`** — one
tagged record per task (`[id:]` `[group:]` `[status:]` `[needs:]`), groups for what runs in
parallel, a cross-group `## Requests` section, and a gate that is itself a group of
`verify:`-carrying records. **Complete = `ledger open` empty + `ledger check` exits 0** (the
`ledger` reader is on PATH). Only the orchestrator writes the ledger — workers report and it folds
them in; the `README.md` stays the prose narrative.

Full format, vocab, group/request rules, report shapes and the reader: **[`ledger.md`](ledger.md)**;
the orchestrator's own playbook: **[`orchestrator.md`](orchestrator.md)** — both in this skill
folder. The ledger's `[status:…]` tags are the one sanctioned exception to **prose, no checkboxes**
(§ `README.md` structure) — a closed enum a tool parses. A single-chat milestone keeps `steps.md`
and ignores all of this.

## Creating a milestone

When the user asks to start a new milestone:

1. Ask (briefly) for the slug name if not obvious. Kebab-case, short (`scope-cut-execution`,
   `ship-v1-ios`, `rbac-hardening`).
2. Get today's date: `date '+%y%m%d'` → e.g. `260420`.
3. Create `.agent/milestone/{date}_{slug}/`.
4. Write the core files:
   - **`README.md`** — status/progress at top; then context, goals, success criteria, out of scope,
     related files, notes for agents.
   - **`steps.md`** — numbered execution steps, each step one commit's worth of work (or several).
   - Any milestone-specific docs (scope-cut.md, etc.) as needed.
5. Add a row for it to the active-milestones index (status `active`) — see [§ Active-milestones
   index](#active-milestones-index).
6. Hand off to the user — do not start executing steps until the user says go.

## `README.md` structure

Copy the scaffold in **[`readme-template.md`](readme-template.md)** (this skill folder) and fill it:
status/progress at the top, then context, goals, success criteria, out of scope, related files,
notes for agents. The Step tracker and Log stay **prose, no checkboxes**.

## Switching milestones

When the user says "let's continue on {X} milestone":

1. Find the folder matching the slug (usually a unique suffix; if not, the latest timestamp match).
2. Read `README.md` (status/progress at top → context/scope/notes below).
3. Read the `steps.md` / `ledger.md` or topic file the user references.
4. If this changes the active set (e.g. the previously-active milestone is now paused), update the
   `status:` in the active-milestones index record.
5. Proceed from there.

## Closing a milestone

When all success criteria are met:

1. Update `README.md` status to `closed`, add a closing date in the `**Status:**` line.
2. Write a closing note in the Status / Progress section summarizing what shipped, what carried
   over, any lessons.
3. **Archive OR delete** the folder:
   - **Archive** (default) — move to `.agent/milestone/archive/`. Use when the milestone files
     (steps, decisions, scope-cut tables) have historical value.
   - **Delete** (when files are stale/ad-hoc) — `git rm -r .agent/milestone/{folder}` and rely on
     git history. Use when work shipped outside the milestone workflow and the files don't reflect
     what actually happened. Mention the closure in the next active milestone's log so context isn't
     lost.
4. Remove the milestone's record from the active-milestones index. If that leaves nothing active,
   clear it to `_None active._` — the index NEVER lists archived milestones. If a sibling milestone
   references the closed one, update its body too.
5. Commit: `close milestone: {slug}` (archive form) or `milestone: close+delete {slug}` (delete
   form, with a one-line reason in the message).

## Crediting ad-hoc work toward a milestone

Work that fits a milestone's scope often lands outside the workflow (direct chats, side
discussions). When you (re-)activate or close such a milestone: add a session-dated Log entry
listing the ad-hoc work (reference commits); update the Step tracker rows in prose; and list what's
still left under "Notes for future sessions" — so the milestone never reads "step 0 — not started"
while the work is already half-done in the codebase.

## Parallel milestones

Multiple milestones can be active at once; the user switches via natural language ("let's continue
on X"). Each session scopes itself to ONE milestone — don't cross-reference work between milestones
mid-session unless the user asks.

## Agent dispatch under a milestone

If the project runs a background/autonomous job runner and a job is needed for work inside a
milestone:

- The job's Task section MUST open with `milestone: {slug}` as the first line.
- The job MUST be told which files to read — typically the milestone folder + named docs. Nothing
  else.
- No architectural decisions in autonomous jobs. If a job hits an undecided pattern or an ambiguous
  shape, it STOPS and flags to the user rather than improvising.
- **Under an umbrella milestone with a `ledger.md`**: the dispatched chat works ONE group, reports
  in the ledger's shapes (`REVIEW`/`BLOCKED`/`REQUEST`/`PAUSE` + the land-report lines) and NEVER
  edits the ledger — the orchestrator folds reports in ([`ledger.md`](ledger.md) § Reports).

## When NOT to use this skill

- Single-session task: just do it in chat.
- One-topic plan with clear scope: use the `planning:new` skill (`.agent/plan/`).
- Recurring mechanical / batch work: a job-runner flow (`grind`/`looper`), not a milestone.

Milestones are for strategic, multi-session, multi-topic initiatives. Don't over-use them.
