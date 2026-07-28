---
name: continue
description: >-
  Resume work in this repo. Use when the user says "lets continue", "continue", "nadaljuj", "pick up
  where we left off", or opens a session without a specific ask.
---

# Resume a session

If the project defines a session boot order (e.g. a start-here doc), follow that first — the
handoff supplements it, it does not replace it. Otherwise the session boots from the handoff.
Pairs with the `handoff` skill.

1. Read `.agent/handoff.md` — the **Outstanding** and **Suggested next topic** sections are your
   work queue. Load project memory (`.agent/MEMORY.md` or the project's memory store) if not
   already loaded.
2. Sanity-check state: `git status` + `git log --oneline -5`. If the tree is dirty with changes
   you didn't make, ask before touching them.
3. Check `.todo` / `.todo-inbox` for items not yet handled — surface them briefly.
4. State a one-line plan, then start. No long preambles — the owner wants lean reporting.
