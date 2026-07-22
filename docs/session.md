# session — Claude Code session continuity

Part of the [`optimiziramsi-skills`](../README.md) plugin (the opsi toolkit).

Write the handoff at session close; boot the next session from it.

## Contents

- name: `handoff`
  kind: skill + command
  purpose:
    Rewrite `.agent/handoff.md` — ephemeral **≤4k** next-session notes, rich 7-section shape,
    route durable knowledge out to lessons/docs.

- name: `continue`
  kind: skill + command
  purpose:
    Resume from `.agent/handoff.md` — sanity-check git state, surface pending todos, state a
    one-line plan, start.

- name: `session-summary`
  kind: skill + command
  purpose: Shareable changelog of what a session shipped — themes, decisions, pending.

- name: `session-start`
  kind: hook
  purpose:
    SessionStart — injects a state snapshot (branch · uncommitted · last commit), handoff
    freshness, todo count, an enforcement-health warning (loud if `python3` is missing → guards
    disarmed), and an audit-staleness nudge. Fully conditional; safe in any repo.

Assumes the **`.agent/` house layout** (`.agent/handoff.md`, `.agent/lessons/`, `.agent/reviews/`,
`.docs/`).

_Planned:_ `collab`, a stop-nudge hook.

## Enable

```json
{ "enabledPlugins": { "optimiziramsi-skills@optimiziramsi": true } }
```
