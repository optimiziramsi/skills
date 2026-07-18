---
name: handoff
description: |
  Update `.agent/handoff.md` — ephemeral next-session continuity notes for the next chat. Use when the user signals end of session: "handoff", "prepare for next session", "wrap up", "ready to close", "end session", "we're done for today", "see you tomorrow", or similar. The file is ephemeral session-context ONLY and is HARD-CAPPED at 4k chars; durable knowledge (working style, operational gotchas, engineering lessons) lives in `.agent/lessons/`, not here.
---

# Handoff

Maintains `.agent/handoff.md` so the next session starts with the right context — and nothing more.
Pairs with the `continue` skill, which boots the next session from this file.

Assumes the `.agent/` house layout: `.agent/handoff.md`, `.agent/lessons/`, `.docs/`.

## The model

- **`.agent/handoff.md` = ephemeral next-session continuity ONLY.** Where we left off, what's queued,
  recent project-state changes. Rewritten (overwritten) each handoff. **HARD CAP: 4k characters.**
- **Durable knowledge → `.agent/lessons/`** (working style, operational gotchas, engineering
  lessons), via the `lessons` skill. It is NEVER in handoff.
- **Architecture / code-shape → `.docs/`** (and a patterns registry if the project keeps one).
- **Pending work → `.todo` / `.todo-inbox`** (the user triages), or the relevant plan/milestone steps.

If you're about to write something a *future* session (beyond the next one) would want, it's not
handoff content — route it to the list above.

## Update sequence

1. **Read `.agent/handoff.md`.** You OVERWRITE the session-context, not append to it.
2. **Identify what changed this session:** `git log --oneline -20` (or `--since=`); file
   renames/deletions; new decisions; `.todo` changes.
3. **Rewrite the session-context** (sections below).
4. **Update the `_Last updated:_` line.**
5. **If you observed a new durable lesson** (a repeatable preference/gotcha the user established),
   capture it via the `lessons` skill — NOT in handoff.
6. **Check the 4k cap** (below) before committing.
7. **Commit** single-line: `update handoff for next session`.

## 4k hard cap

After editing, verify: `wc -c < .agent/handoff.md` must be ≤ 4000. If over, the content is in the
wrong place — move it out, don't shrink by deleting what the next session needs:

- Durable preference/gotcha → a lesson (`.agent/lessons/`).
- Architecture/code-shape → `.docs/`.
- Pending work that isn't a plan/milestone step → `.todo` / `.todo-inbox`.

Only after routing content elsewhere, tighten wording. The cap is the forcing function that keeps
handoff ephemeral.

## Session-context sections + caps

Total ≤ 4k chars. Per-section:

| Section | Shape | Cap |
| --- | --- | --- |
| `_Last updated:_` | One terse line | 1 line |
| Where we left off | 1 short paragraph (3-5 sentences); name branch + last-shipped + what's queued | ~5 lines |
| This session's arc | Bullets grouped BY TOPIC, not per-commit | 3-7 bullets, 1 line each |
| Active milestones / plans | Table, no editorial | ~5 lines |
| Build state | One paragraph (bullets only if it changed) | ~3 lines |
| Outstanding | Bullets that POINT at `.todo`/plan files, not re-list | 3-5 bullets |
| Suggested next topic | 1 paragraph + a few alternatives | ~8 lines |

## Rules

- **Time window = ONLY this session** (since the last handoff). A tiny session → a tiny handoff.
  No padding.
- **Group by topic.** 25 commits on one topic = ONE arc bullet. SHAs live in git, not handoff.
- **One line per bullet.** If a bullet needs a paragraph, the content belongs in a lesson / doc /
  plan file, not handoff.
- **Link to commits**, don't list every file.
- **No implementation detail, no architecture, no pattern bodies, no duplication of
  CLAUDE.md/skills.**
