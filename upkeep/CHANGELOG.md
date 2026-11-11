# upkeep — changelog

Versions of the `upkeep@optimiziramsi` plugin.

## 0.1.1 — unreleased

- The notice moved from session start to Stop and is for the user only (a `systemMessage`; the
  model-context copy is gone). One check per session, never blocking; the once-a-day repeat
  throttle and the background refresh are unchanged.
- Silent in a linked git worktree; `NUDGES_IN_WORKTREE=1` runs the check there too.

## 0.1.0 — 2026-10-18

- New: a session-start notice for outdated plugins and plugins new to the marketplaces a project
  uses, a throttled background marketplace refresh, `/upkeep` to apply, and the `upkeep` CLI.
