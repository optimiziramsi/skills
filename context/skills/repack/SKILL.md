---
name: repack
description: >-
  Refresh a long chat — write the next-session handoff, then hand the user /clear → /continue so
  the work resumes in a fresh context window. Use when the context nudge reaches the handoff
  level, or the user says "repack", "refresh the chat", "context is getting full", "fresh
  session", "start clean". If the topic is already done, skip the handoff and just offer /clear.
---

# repack — fresh context, same work

A long session degrades: early context gets compressed or lost, and every turn costs more. Repack
moves what matters into a handoff file, so a fresh session picks the work up with none of the
weight. The agent cannot clear or compact a session — that is always the user's `/clear` (or
`/compact`).

## Steps

1. **Topic already done?** If the user says so (or the work is landed and nothing is pending),
   skip the handoff: say in one line that the topic is closed and `/clear` is safe. Stop.
2. **Close what's open.** Uncommitted work: commit it per the project's commit rules (the `commit`
   skill where enabled), or name it in the handoff as uncommitted — never leave it unmentioned.
3. **Write the handoff.** Work under a skill that keeps its own handoff goes there, not to
   `.agent/handoff.md` — a worktree topic's is the Handoff section of its `.agent/plan/<slug>.md`.
   Otherwise use the `handoff` skill when it is enabled (the `session` plugin) — it owns the format
   and the 4k cap — or write `.agent/handoff.md` yourself: current state
   (branch, last commit, what is done), decisions a cold session can't re-derive, the exact next
   step, and open questions. Facts, not narrative; no secrets or personal data.
4. **Hand over.** Two things, nothing else: one line naming the handoff path (run `/clear`, then
   paste), and the resume prompt below as a fenced code block — the exact text to paste, never
   described in prose. No recap of the handoff's content. Offer `/compact` instead only if they'd
   rather keep this thread.

## The resume prompt

```
/continue <topic> — read the handoff in <path>
```

A worktree topic, for example:

```
/parallel-work:worktree continue login-form — read the Handoff section in .agent/plan/261114_075116_login-form.md
```

- The command is `/continue` where the `session` plugin is enabled, else `continue` — or the
  skill the work runs under, by its full `/plugin:skill` name.
- The path is the handoff file actually written in step 3 (and its section, when it is one).
- One line: command + pointer, no prose. Next step, constraints and decisions live in the file —
  never repeat them in the prompt.
- Only when there is no file to point to does the prompt carry the work itself: the next step and
  any constraint the user set, in full words (the fresh session knows nothing of this chat).
- Put the same block in the handoff, so the next repack reuses it.

## Rules

- Don't start new work after the handoff is written — the next step belongs to the fresh session.
- The handoff is for the next session, not a report: no recap of this conversation's process.
