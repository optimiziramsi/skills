---
name: plan
description: |
  Create and manage implementation plans in .agent/plan/ files. Use this skill when: starting a new feature or refactor, the user says "plan this", "think about how to", "design the approach", "prepare a plan", or any time structured planning is needed before execution. Plans are the source of truth for a topic — they capture scope, approach, and decisions. Execution waits until the user says go.
---

# Plan

Plans live in `.agent/plan/` and are the source of truth for their topic. One plan = one topic. Planning and execution are separate steps — never execute during planning unless explicitly told to.

## File naming

```
.agent/plan/YYMMDD_HHMMSS_{topic}.md
```

6+6 datetime prefix from `date '+%y%m%d_%H%M%S'`. Topics use kebab-case (snake_case also fine). For bug fixes, prefix the topic with `fix_` (e.g. `fix_score_race_condition`). Examples:

- `.agent/plan/260420_220500_permission_system.md`
- `.agent/plan/260420_220510_sse_multi_instance.md`
- `.agent/plan/260420_220520_fix_score_race_condition.md`

If the project runs milestones (the `milestone` skill), a plan often belongs to one. When it does, reference the milestone in the plan's Context section and record the cross-link in the milestone's `README.md` (Status / Progress section).

## Structure

```markdown
# {Topic Title}

## Context

Why this work exists. What problem it solves. Link to relevant `.docs/` files.

## Scope

What's in and what's out. Be explicit about boundaries — prevents scope creep during execution.

## Approach

The technical plan. Concrete enough to execute from:

- Which files to create/modify
- Which patterns to follow (reference the project's style guide / existing code)
- Key decisions and why
- Dependencies on other work (if any)

## Tasks

Ordered list of implementation steps. Each step should be one commit's worth of work.

1. {step} — {what it produces}
2. {step} — {what it produces}
3. ...

## Open questions

Anything unresolved. If this section is non-empty, ask the user before executing.

## Decisions log

Capture decisions made during planning discussions:

- YYYY-MM-DD: {decision} — {reasoning}

## Execution status

Updated during execution. No checkboxes — write prose:

- Step 1: done (commit abc123)
- Step 2: in progress
- Step 3: not started
```

> Legacy plans may use `[ ]` / `[x]` checkboxes for execution status. New plans use prose. Don't retrofit unless you're already editing the file for other reasons.

## Rules

### Planning phase

1. Create the `.agent/plan/` file — this is the only file you change during planning.
2. Read relevant `.docs/` specs and existing code to inform the approach. For codebase-wide exploration (find all callers, map an entire flow, identify references), delegate to a read-only exploration agent (e.g. `Explore`) — keeps main context lean.
3. **If the project keeps a pattern/architecture registry** (e.g. `.agent/patterns/`), consult the matching topic before approving an Approach that touches it. If the pattern is unblessed/undecided, STOP, flag it, and settle the pattern first. Skip this step if the project has no such registry.
4. Present the plan to the user. Don't start executing.
5. If there are open questions, ask them before the plan is final.
6. Iterate on the plan based on user feedback.

### Execution phase

1. Wait for the user's go-ahead. An explicit "execute immediately" / "continue" / autonomous cue overrides this.
2. Follow the plan's task list in order.
3. Commit at plan close — one logical topic = one commit. Per-step commits are fine if the plan spans multiple sessions or has genuinely independent steps.
4. Update the execution status section as you go.
5. If you discover something that changes the plan, stop and discuss — don't silently deviate.

### After execution

1. Update affected `.docs/` files immediately — zero context loss for the next session.
2. Leave the `.agent/plan/` file as-is (it's the historical record of what was planned and done).
3. If the plan was cancelled, write a conclusion explaining why.

### Multi-session safety

- Each session owns its own `.agent/plan/` file — read others' plans but don't edit them.
- If a plan depends on another plan's output, note the dependency explicitly.

### Versioning

When a plan goes through major revisions:

- Never edit the current version in-place.
- Copy to v(N+1) in a scratch location.
- Add a changelog + `## V(N+1) HUMAN COMMENTS:` heading.

## Closing a plan

On close, write the final prose status + forward pointers, then `git mv` the file to `.agent/plan/archive/`. Archived plans are a frozen record — no live file should keep pointing at one.

## When NOT to use a plan

- Quick bug fixes you can diagnose and fix in minutes — just do it.
- Single-file changes with an obvious approach.
- Reviews and audits — use the review skill instead.
