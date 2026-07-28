# Worktrees — the parallel-work board

The `worktree` skill is the protocol; this file is only the board.

## Active

| # | Status | Branch | Worktree | Brief |
|---|---|---|---|---|
| `loop-grind-launch` | active | `feature/looper-grinder-worktree-7f4a4f` | `.claude/worktrees/looper-grinder-worktree-7f4a4f` | Fix how the flow runners are *started*: a committed `bin/loop`/`bin/grind` wrapper (scaffolded by a skill) that discovers the plugin at runtime, plus `--worktree <name>` selection so one command run from the checkout root targets any worktree. Then port the unlanded worktree-confinement from `feature/worktree-looper-grinder` (pre-topic-first layout) if it survives review. Touches: `flow/**`, `setup/**`, `worktree/**`. |

## Open

_none_

## Pending cleanup

- `feature/worktree-land-wiring` (`.claude/worktrees/worktree-skill-merge-c479b2`) —
  worktree-land-without-checkout. Also retire the superseded `feature/worktree-skill-merge-c479b2`
  branch (`ed82d7b`; its content was cherry-picked onto this one).
