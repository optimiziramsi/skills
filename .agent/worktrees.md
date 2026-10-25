# Worktrees — the parallel-work board

The `worktree` skill is the protocol; this file is only the board.

## Active

| # | Status | Branch | Worktree | Brief |
|---|---|---|---|---|
| relay-watch-help-phrases | active | `feature/relay-watch-help-phrases-416fb8` | `.claude/worktrees/relay-watch-help-phrases-416fb8` | `relay-watch --help` prints the handover phrase list generated from the `TRIGGER` regex (human-readable, every alternative shown); selftest case + docs. Touches `worktree/` only. |

## Open

_none_

## Pending cleanup

- `feature/looper-grinder-worktree-7f4a4f` (`.claude/worktrees/looper-grinder-worktree-7f4a4f`) —
  loop-grind-launch. Also retire `feature/worktree-looper-grinder` (`11411cb`) — its confinement
  work was re-homed onto the topic-first layout and landed here, so the branch is superseded.
- `feature/worktree-land-wiring` (`.claude/worktrees/worktree-skill-merge-c479b2`) —
  worktree-land-without-checkout. Also retire the superseded `feature/worktree-skill-merge-c479b2`
  branch (`ed82d7b`; its content was cherry-picked onto this one).
