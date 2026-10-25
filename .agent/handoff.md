# Handoff

_Last updated:_ 2026-10-26 — session 14: `relay` skill + `model-guard` hook added, live-tested end to end.

## Where we left off

`develop` ahead of `main` (0.1.0) with two plugins on a dev series: `worktree` 0.1.1-dev.6
(`relay` skill, `/relay`, `bin/relay-watch`) and `guards` 0.1.1-dev.3 (`model-guard` hook,
`MODEL_GUARD_TAIL_KB`). `./tests.sh` ALL GREEN at caa4527. Nothing pushed.

## This session's arc

- Relay = pair-programming by worktree: human + primary share one worktree (edits staged, never
  committed, never landed); primary spawns one `worktree`-skill sub chat per topic, rebases, strips,
  reviews against `Done =`, tears down. Spec came from the user's rabbit-run POC (2026-10-22→25).
- Live test ran inside this repo: two real topics landed on `develop` through the gate (`f0afa14`
  relay-watch `--help` phrases; `21cfee3` `MODEL_GUARD_TAIL_KB`), both sub chats archived, board
  struck. Seven skill fixes came out of it (see worktree CHANGELOG 0.1.1 — unreleased).
- Findings baked into the skill: app names worktree branches (`feature/<slug>-<hash>`); a card
  ignores `branch_name`/`source_branch`; `start_session` clamps model/effort silently → lift with
  `set_session_effort`/`set_session_model` after every spawn; land notes to the primary can be
  queued (happened twice) → primary checks `<integration>`'s log every turn, human's "X landed" is
  the fallback; a dirty `<integration>` checkout refuses every land (this repo has no
  `_integration` worktree — `develop` sits in the main checkout).
- Plugin cache only moves on `claude plugin update <p>@optimiziramsi-dev`; a running session's
  Skill tool keeps the text it first loaded.

## Outstanding

- User to archive the lab primary session (`Relay lab primary`, worktree `.claude/worktrees/relay-lab-fb223f`)
  and delete `feature/relay-lab-fb223f` (reference-only branch, nothing on it).
- Model id for Opus 4.8 in `RELAY_SUB_MODELS` / `RELAY_PRIMARY_MODELS` defaults is a guess
  (`claude-opus-4-8`) — confirm against the app's model picker.
- Decide whether `file-guard` should also guard the override files (`.agent/model-guard.md`,
  `.agent/output-contract.md`, `.agent/code-first.md`) — skipped for consistency.
- Stale Pending-cleanup lines from older sessions still on the board (looper-grinder, land-wiring).
- Consider the `_integration` worktree wiring for this repo (the worktree skill's one-time setup).

## Suggested next topic

Cut 0.1.1 for `worktree` + `guards` once the user has reviewed the relay skill text in their IDE.
