# runners — changelog

Versions of the `runners@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (`looper`, `grind`, `collab`, the runners and `runner-link` from its `flow` topic). Enable it per project with `claude plugin install runners@optimiziramsi --scope project`.
- Worktree confinement injects a vendored copy of the `worktree-guards` plugin's guards
  (`vendor/worktree-guards/`), so it works whether or not a project enables that plugin.
- The runner pointer moved to `<claude-config>/plugins/data/optimiziramsi-runners/current` and
  targets this plugin itself; links are `…/current/bin/{loop,grind}`. `runner-link` re-aims existing
  `.agent/bin/{loop,grind}` symlinks on the next session start.
- `grind --status` no longer executes the mission's `done-check` — it shows the command instead.
  The arm prompt now shows the `done-check` too, so the shell it will run is approved with the run.
