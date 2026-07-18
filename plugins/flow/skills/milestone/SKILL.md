---
name: milestone
description: |
  Create, switch, and close milestones in `.agent/milestone/`. Milestones are strategic initiatives that span multiple topics and sessions (e.g. "cleanup and patterns", "ship v1 iOS app"). Each milestone is a folder with its own scope, steps, progress, and notes — giving agents a tight context window per initiative. Use when the user says: "let's start a milestone", "switch to the X milestone", "what milestones are active", "close this milestone", or opens a strategic initiative that will take multiple sessions. Do NOT use for single-topic plans (those go in `.agent/plan/` — use the `plan` skill).
---

# Milestone

Milestones live in `.agent/milestone/`. Each milestone is a folder containing its scope, steps, and progress. The folder is the working surface for one strategic initiative across many sessions.

## When to use milestones vs plans vs direct work

| Situation | Use |
| --- | --- |
| Single focused task finishable in one session | direct |
| One topic, one execution plan | `.agent/plan/` + `plan` skill |
| Strategic initiative spanning many topics and multiple sessions | `.agent/milestone/` (this) |
| Parallel initiatives where context-switching needs a clean workspace | multiple `.agent/milestone/*/` |

A milestone is the right abstraction when:

- The initiative has its own scope cut, its own progress log, its own notes.
- Agents dispatched for this initiative should read ONLY this folder + referenced docs (tighter context).
- Multiple plans may live under it.
- The user says things like "let's continue on X" where X is a multi-session effort.

Two guardrails: multi-step or structurally-different work gets its **own** milestone — don't bolt it onto an active one. And on close, no active file may keep referencing the archived milestone.

## Folder layout

```
.agent/milestone/
  YYMMDD_{slug}/                    # milestone folder — date-only prefix (milestones span days/weeks)
    README.md                       # status/progress at top, then scope/goals/success-criteria/notes
    steps.md                        # execution sequence (numbered steps) — separate so it can be referenced/edited independently
    {topic}.md                      # milestone-specific docs (scope-cut.md, etc.)
  archive/                          # closed milestones archived here
```

Milestones use a date-only prefix (`YYMMDD` from `date '+%y%m%d'`) because they're long-lived — second-level precision isn't useful and clutters the path. Inner files do NOT carry a prefix — they're structural to the milestone, not topical.

**Folder-README convention:** the milestone's primary file is `README.md`, with status/progress at the top so a returning user sees "where we are" before re-reading "why we exist."

## Active-milestones index

`.agent/milestones.md` is the single human-facing index of what's in flight. It lists ONLY live (non-archive) milestones and stays in lockstep with `.agent/milestone/`: **add** a row on create, **flip** its status on switch/pause, **remove** the row on close. When nothing is active the file reads `_None active._` Archived milestones are NEVER listed — their folder under `.agent/milestone/archive/` is the only acknowledgment a closed milestone gets. Every create/switch/close below carries the matching index step; do not skip it.

## Creating a milestone

When the user asks to start a new milestone:

1. Ask (briefly) for the slug name if not obvious. Kebab-case, short (`scope-cut-execution`, `ship-v1-ios`, `rbac-hardening`).
2. Get today's date: `date '+%y%m%d'` → e.g. `260420`.
3. Create `.agent/milestone/{date}_{slug}/`.
4. Write the core files:
   - **`README.md`** — status/progress at top; then context, goals, success criteria, out of scope, related files, notes for agents.
   - **`steps.md`** — numbered execution steps, each step one commit's worth of work (or several).
   - Any milestone-specific docs (scope-cut.md, etc.) as needed.
5. Add a row for it to the active-milestones index (status `active`) — see [§ Active-milestones index](#active-milestones-index).
6. Hand off to the user — do not start executing steps until the user says go.

## `README.md` structure

```markdown
# Milestone — {Human Title}

**Created:** YYYY-MM-DD
**Status:** active | paused | closed
**Closes when:** {success criteria in one sentence}

## Status / Progress

(at the top so returning users see "where we are" before "why we exist")

**Overall:** one-line state.

### Step tracker

Prose, no checkboxes. Each step gets one line:
- Step 1 — done. {what shipped, link to commit/file if helpful}.
- Step 2 — in progress. {what's underway}.
- Step 3 — not started. {what it'll do}.

### Log

Session-dated entries describing what landed and what changed. Newest at the top OR bottom — pick one and stick with it within the file. Reference commits, not file lists.

### Blocked

Anything blocking forward progress. "Nothing right now" is fine.

### Notes for future sessions

What a re-entering session needs to know to pick up cleanly.

---

## Context

Why this milestone exists. What problem it solves. The state of the world that made it necessary.

## Goals

Numbered list. Concrete, observable. "Cut scope", "ship X app".

## Success criteria

Observable conditions that indicate the milestone is done.

## Out of scope for this milestone

Explicit negative list — what this milestone does NOT attempt. Prevents scope creep.

## Related files (inside this milestone folder)

Pointers to `steps.md` and any milestone-specific docs.

## Notes for agents

How agents dispatched under this milestone should behave:
- Which files they may read
- Which files they must reference
- Task-section prefix (e.g. "milestone: scope-cut-execution")
```

## Switching milestones

When the user says "let's continue on {X} milestone":

1. Find the folder matching the slug (usually a unique suffix; if not, the latest timestamp match).
2. Read `README.md` (status/progress at top → context/scope/notes below).
3. Read the step file or topic file the user references.
4. If this changes the active set (e.g. the previously-active milestone is now paused), update the status column in the active-milestones index.
5. Proceed from there.

## Closing a milestone

When all success criteria are met:

1. Update `README.md` status to `closed`, add a closing date in the `**Status:**` line.
2. Write a closing note in the Status / Progress section summarizing what shipped, what carried over, any lessons.
3. **Archive OR delete** the folder:
   - **Archive** (default) — move to `.agent/milestone/archive/`. Use when the milestone files (steps, decisions, scope-cut tables) have historical value.
   - **Delete** (when files are stale/ad-hoc) — `git rm -r .agent/milestone/{folder}` and rely on git history. Use when work shipped outside the milestone workflow and the files don't reflect what actually happened. Mention the closure in the next active milestone's log so context isn't lost.
4. Remove the milestone's row from the active-milestones index. If that leaves nothing active, replace the table with `_None active._` — the index NEVER lists archived milestones. If a sibling milestone references the closed one, update its body too.
5. Commit: `close milestone: {slug}` (archive form) or `milestone: close+delete {slug}` (delete form, with a one-line reason in the message).

## Crediting ad-hoc work toward a milestone

It's common for work that fits a milestone's scope to land outside the milestone workflow — direct chat sessions, side discussions. When you (re-)activate or close such a milestone:

1. In the Log, add a session-dated entry listing the ad-hoc work that should count. Reference commits/files where helpful.
2. Update the relevant Step tracker rows in prose ("done", "in progress", "not started", "skipped/superseded") — no checkboxes.
3. In "Notes for future sessions", list what's still left so the milestone has a clean re-entry point.

This avoids the trap where the milestone reads "step 0 — not started" while the work is half-done in the codebase already.

## Parallel milestones

Multiple milestones can be active at once. The user switches between them via natural language ("let's continue on X"). Each session scopes itself to ONE milestone — don't cross-reference work between milestones mid-session unless the user explicitly asks.

## Agent dispatch under a milestone

If the project runs a background/autonomous job runner and a job is needed for work inside a milestone:

- The job's Task section MUST open with `milestone: {slug}` as the first line.
- The job MUST be told which files to read — typically the milestone folder + named docs. Nothing else.
- No architectural decisions in autonomous jobs. If a job hits an undecided pattern or an ambiguous shape, it STOPS and flags to the user rather than improvising.

## When NOT to use this skill

- Single-session task: just do it in chat.
- One-topic plan with clear scope: use the `plan` skill, write in `.agent/plan/`.
- Recurring mechanical / fire-and-forget batch work: that's a job-runner flow (deferred `grind`/`looper`), not a milestone.

Milestones are for strategic, multi-session, multi-topic initiatives. Don't over-use them.
