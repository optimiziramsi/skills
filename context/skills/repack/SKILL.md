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
3. **Write the handoff.** Use the `handoff` skill when it is enabled (the `session` plugin) — it
   owns the format and the 4k cap. Otherwise write `.agent/handoff.md` yourself: current state
   (branch, last commit, what is done), decisions a cold session can't re-derive, the exact next
   step, and open questions. Facts, not narrative; no secrets or personal data.
4. **Hand over.** Tell the user, in two lines: the handoff is written (path), then run `/clear`
   and say `continue` (or `/continue` where the `session` plugin is enabled) in the fresh
   session. Offer `/compact` instead only if they'd rather keep this thread.

## Rules

- Don't start new work after the handoff is written — the next step belongs to the fresh session.
- The handoff is for the next session, not a report: no recap of this conversation's process.
