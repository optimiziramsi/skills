# Handoff

_Last updated:_ 2026-10-29 — session 16: relay skill — applied 7 live-run rules (two-track branch, hard-gate close, narrowed teardown); worktree 0.1.7 released.

## Where we left off

Released locally: `main` @ 5737074 = worktree 0.1.7 + earlier worktree 0.1.1–0.1.6 and guards 0.1.1;
tags `worktree--v0.1.1…0.1.7`, `guards--v0.1.1`. `develop` @ 2021483 (+ this handoff commit),
`./tests.sh` ALL GREEN. **Remote sync pending (user):**
`git push origin main worktree--v0.1.7 && git push origin develop` (earlier tags pushed in
sessions 14–15; 0.1.5/0.1.6/0.1.7 may be outstanding). 0.1.7 applied 7 rules from a long live relay
run: the shared branch is now two-track — the primary's own state files (`relay.md`/`handoff.md`)
live in ONE squashed never-landed commit while the human's edits stay UNSTAGED (the rebase trick
ends `git restore --staged .`); a close is a HARD GATE on the primary reading the landed diff vs the
**original comment's** intent (not the brief's `Done =`, not the child's word); teardown shrinks to
archive + relay.md (worktree/branch/board cleanup is the human's `clean`, file-guard blocks the
board anyway); topics may also be an approved audit finding or a relayed question (no comment to
strip); a sub-chat land no longer re-arms the watcher (sub-chat-driven quiet → pause). `--amend` is
git-guard-safe by default; the earlier 0.1.6 doc-scan NOTE was already shipped — no action.
(relay-watch self-test caveat: this machine's `grep` is ugrep and accepts `\t`, so run
`PATH=/usr/bin:/bin bash worktree/bin/relay-watch --test` for BSD parity. Full 0.1.1–0.1.6 history
is in worktree/CHANGELOG.md.)

## This session's arc

- Relay = pair-programming by worktree: human + primary share one worktree (human edits unstaged,
  never landed; primary's state files in one never-landed commit); primary spawns one
  `worktree`-skill sub chat per topic, rebases, strips, reviews, archives. Spec came from the user's
  rabbit-run POC (2026-10-22→25).
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
- Model id `claude-opus-4-8` in the `RELAY_SUB_MODELS` / `RELAY_PRIMARY_MODELS` defaults is
  confirmed (the app's `/model claude-opus-4-8` accepts it; this session ran on it) — no change due.
- Decide whether `file-guard` should also guard the override files (`.agent/model-guard.md`,
  `.agent/output-contract.md`, `.agent/code-first.md`) — skipped for consistency.
- Stale Pending-cleanup lines from older sessions still on the board (looper-grinder, land-wiring).
- Consider the `_integration` worktree wiring for this repo (the worktree skill's one-time setup).

## Suggested next topic

Work through the user's comments on relay 0.1.1; then a second live relay in a real project with an
Opus 4.8 MAX primary (the log-check-every-turn and effort-lift text has not run live yet).
