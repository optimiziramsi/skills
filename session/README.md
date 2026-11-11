# session — Claude Code session continuity

The `session@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

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
    SessionStart — injects one state line as context (branch · uncommitted · last commit), plus
    an enforcement-health warning when `python3` is missing (guards disarmed). Nothing else: a
    chat starts on the work it was opened for.

- name: `session-end`
  kind: hook
  purpose:
    Stop — a note for the **user** (a `systemMessage`: not model context, never blocks the stop)
    with the handoff age, the `.todo` item count, and the instructions-audit age when it is over
    30 days. Each fact is shown once per session and again only when it changes; every line is
    conditional on its file existing, so it is safe in any repo. Silent in a linked git worktree
    (see Settings).

Assumes the **`.agent/` house layout** (`.agent/handoff.md`, `.agent/lessons/`, `.agent/reviews/`,
`.docs/`).

_Planned:_ `collab`, a stop-nudge hook.

## Settings

In a settings.json `env` block (any scope):

- `SESSION_START_OFF=1` — both hooks off.
- `NUDGES_IN_WORKTREE=1` — show the Stop notes in a linked git worktree too. Off by default: a
  worktree is for one topic, and cleanup belongs to the main checkout's chat. The same switch is
  read by every plugin that ships such notes.

Tests: `python3 tests/test_session_start.py`, `python3 tests/test_session_end.py`.

## Enable

```json
{ "enabledPlugins": { "session@optimiziramsi": true } }
```
