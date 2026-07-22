---
name: rules-change
description: >-
  The sanctioned way to make a T3 change to the instruction system — add/remove a rule, change a
  cap, or change any hook/skill/agent/settings behavior. Use ONLY on an explicit user request or
  approval (including approving a retro/audit proposal, or granting a one-time exception). Never
  invoke as a side effect of another task — if a rule is in your way mid-task, stop and present the
  conflict first.
---

# rules-change

The controlled door for T3 changes (tiers are defined in the `instructions-maintenance`
constitution). **Precondition: an explicit user request or approval.** If you arrived here mid-task
because a rule is in the way, STOP — present the conflict; the user picks "one-time exception" or
"change the rule". Execution resumes only after.

## A. One-time exception (the rule stays intact)

1. Log it (newest first) in your decisions store (`.agent/decisions.md` or the changelog): date, the
   rule bent, the exact scope of the exception, and that the user approved it in-session.
2. Continue the original task under the exception. Nothing else changes.

## B. Rule change

1. **Confirm the exact change** back to the user in one sentence (the rule text / skill step / hook
   behavior), plus what triggered it.
2. **Coherence + budget check.** Does any other rule, skill, hook, or checker contradict the new
   text? Change them in the SAME pass — the system must never disagree with itself. If the addition
   breaches a cap, compact or merge something in the same change; growth is never the default.
3. **Apply.**
   - Rules: edit **in place**. Rule IDs are stable — never renumber or reuse; retiring a rule leaves
     a `superseded by … (YYYY-MM-DD)` / `[retired YYYY-MM-DD: reason]` marker behind.
   - Skills / hooks / checkers: apply the diff. **Enforcement changes MUST be re-tested** — extend
     the guard's self-test with a case for the new behavior and run it, plus the project's checks.
4. **Reality check.** The project's checks are green after the change. If the new rule makes the
   current repo violate it, fix the repo in the same effort or shrink the rule until it's true — a
   rule that doesn't match reality rots the whole system.
5. **Log it.** One tier-tagged line in `.agent/instructions-changelog.md` (and/or a decisions
   entry): what changed, why, trigger.
6. **Commit** everything as one change, single-line message per the `commit` skill.

> If an approval-gate hook fires on these edits, that is by design — it's the mechanical signature
> of
> the user's consent.
