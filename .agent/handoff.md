# Handoff

_Last updated:_ 2026-10-26 — session 14: `relay` skill + `model-guard` hook added, live-tested, released as worktree 0.1.1 + guards 0.1.1.

## Where we left off

Released locally: `main` @ dbc9732 = worktree 0.1.3 (`relay` skill, `/relay`, `bin/relay-watch`) +
guards 0.1.1 (`model-guard`, `MODEL_GUARD_TAIL_KB`); tags `worktree--v0.1.1/2/3`, `guards--v0.1.1`.
`develop` @ c486ad0, `./tests.sh` ALL GREEN. **Remote sync pending (user):** publish `main`, the
four tags and `develop` to origin. 0.1.3 = relay-watch exclude built with a real tab (the RR run
saw `relay:` notes fire TRIGGER; this machine's `grep` is ugrep, which accepts `\t`, so the self-test
passed falsely — run `PATH=/usr/bin:/bin bash worktree/bin/relay-watch --test` for BSD parity).
0.1.2 applied the RR chat's first-run feedback (`relay:` prefix, `--seed`, modify/delete in the
rebase trick, board strike from a clean main checkout, model-id fallthrough); two points were
adjusted, not taken verbatim: `git add -u` instead of the guard-blocked bulk add, and the
worktrees-archive log made conditional (RR convention, not shipped).

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

Work through the user's comments on relay 0.1.1; then a second live relay in a real project with an
Opus 4.8 MAX primary (the log-check-every-turn and effort-lift text has not run live yet).
