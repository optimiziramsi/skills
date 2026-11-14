# worktree-guards — changelog

Versions of the `worktree-guards@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.3 — 2026-11-14

- The SessionStart nudge points at `/parallel-work:worktree` (the `worktree` plugin is now `parallel-work`, and its `topic` skill is `worktree` again).

## 0.1.2 — 2026-11-13

- `worktree-detect`: the nudge names the renamed `/worktree:topic` skill (was `/worktree`).

## 0.1.1 — 2026-11-12

- `worktree-bash-guard`: the deny reason no longer tells the model to name the worktree path in the
  command or to unset `WORKTREE_BASH_GUARD_ENABLE`; it gives the allowed form (a path under the
  worktree) and otherwise says to stop and ask the user. Both remain documented in the README.
- `worktree-leak-detector`: the report no longer prints a command that discards the file in the main
  checkout (it can be the user's own edit). It lists the paths and says: do not change anything in
  the main checkout, stop and tell the user. What the guards block is unchanged.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the four guards of its `worktree` topic). Enable it per project with `claude plugin install worktree-guards@optimiziramsi --scope project`.
