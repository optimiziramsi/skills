# upkeep — changelog

Versions of the `upkeep@optimiziramsi` plugin.

## 0.2.1 — unreleased

- `/upkeep` renamed to `/upkeep:apply`, so the plugin name no longer overlaps its own command in the `/` menu. The end-of-turn note now says `/upkeep:apply to apply`. Plugin id, hook, CLI and env switches are unchanged.

## 0.2.0 — 2026-11-12

- The notice moved from session start to Stop and is for the user only (a `systemMessage`; the
  model-context copy is gone). One check per session, never blocking; the once-a-day repeat
  throttle and the background refresh are unchanged.
- Silent in a linked git worktree; `NUDGES_IN_WORKTREE=1` runs the check there too.

## 0.1.0 — 2026-10-18

- New: a session-start notice for outdated plugins and plugins new to the marketplaces a project
  uses, a throttled background marketplace refresh, `/upkeep` to apply, and the `upkeep` CLI.
