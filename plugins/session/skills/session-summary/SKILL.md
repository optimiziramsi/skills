---
name: session-summary
description: >-
  Generate a shareable changelog of what happened in this session — different from `handoff` (which
  is private continuity context for the next chat). Use when the user says: "session summary", "what
  did we do", "summarize today", "today's changes", "weekly summary", "wrap-up report", or wants
  something they can paste into Slack / a release note / a journal. Reads commits + decisions;
  produces a clean Markdown summary.
---

# Session-Summary

`handoff` is private — it captures working-style observations and where to resume. `session-summary`
is shareable — it captures what shipped and why, in a form the user can post somewhere.

## When invoked

The user wants a clean, factual summary of the session's outcomes. Often before context-switching to
another tool (Slack, a journal, a release note draft).

## Generate sequence

1. **Read commits** since session start (or a user-specified range): `git log --oneline
   --since="this morning"` or `--since="N days ago"` if explicitly broader.
2. **Group commits by theme** — don't list 30 commits flat. Cluster: "Docs review (8 commits)",
   "Filename format change (1 commit)", "Skills cleanup (10 commits)".
3. **Identify decisions made** — scope changes, architectural calls, deletions. These often live in
   commit messages or `.todo` deltas.
4. **Note pending follow-ups** — items parked during the session (e.g. new `.todo` entries).
5. **Format as a Markdown summary** with these sections:

```markdown
# Session summary — YYYY-MM-DD

## Themes shipped

- **{Theme}** — {one-line description}. {N} commits.
- ...

## Key decisions

- {Decision} — {why}.
- ...

## Pending

- {Items parked or that came up}.
```

6. **Save to `.agent/reviews/YYMMDD_session.md`** if the user wants it persisted, otherwise just
   output to chat.

## Heuristics

- **Don't list every commit.** A summary that's longer than the diff defeats the purpose.
- **Don't include what didn't ship.** "We considered X but decided not to" only goes in if the user
  asks for a decision log.
- **Don't include your own narration.** Just the outcomes. The user is the audience, not future-you.
- **Spotlight the surprising bits.** "Filename format changed" is more useful than "fixed several
  typos" even if the typo commit count was higher.

## Difference from related skills

- `handoff` — audience: Next-session agent (private). Lifecycle: per session. Content: working
  style + where we left off.
- `session-summary` — audience: Human (shareable). Lifecycle: per session. Content: what shipped
  + decisions made.
- `review` — audience: Human (shareable). Lifecycle: point-in-time. Content: code/architecture
  findings, P0/HIGH/MED/LOW.

## When NOT to use

- For a single-commit session: just describe the commit in chat. A skill invocation is overkill.
- For weekly digests across many sessions: this is meant for one session. Use it per session and
  aggregate manually.
- For internal handoff continuity: use `handoff` — that's its job.
