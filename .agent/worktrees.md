# Worktrees — the parallel-work board

The `worktree` skill is the protocol; this file is only the board.

## Active

| # | Status | Branch | Worktree | Brief |
|---|---|---|---|---|
| relay-model-guard-tail-knob | active | `feature/mystifying-meninsky-53e3d5` | `.claude/worktrees/mystifying-meninsky-53e3d5` | Make model-guard's transcript tail size a knob: `MODEL_GUARD_TAIL_KB` (via `hookio.setting_int`, default 512) controls the seek in `transcript_model`. Cover default/custom/malformed in tests; name the knob in guards README, root switches row, guards CHANGELOG; bump guards to 0.1.1-dev.3. touches: `guards/` only + root `README.md` switches row. |

## Open

_none_

## Pending cleanup

- `feature/looper-grinder-worktree-7f4a4f` (`.claude/worktrees/looper-grinder-worktree-7f4a4f`) —
  loop-grind-launch. Also retire `feature/worktree-looper-grinder` (`11411cb`) — its confinement
  work was re-homed onto the topic-first layout and landed here, so the branch is superseded.
- `feature/worktree-land-wiring` (`.claude/worktrees/worktree-skill-merge-c479b2`) —
  worktree-land-without-checkout. Also retire the superseded `feature/worktree-skill-merge-c479b2`
  branch (`ed82d7b`; its content was cherry-picked onto this one).
