# flow — changelog

Versions of the `flow@optimiziramsi` plugin. History before the split into one plugin per topic
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.0 — unreleased

- Split out of the single `optimiziramsi-skills` plugin as its own plugin; enable it per project with `claude plugin install flow@optimiziramsi --scope project`.
- The worktree confinement now injects a vendored copy of the `worktree` plugin's guards
  (`vendor/worktree/`), so it works whether or not a project enables `worktree`.
- The runner pointer moved to `<claude-config>/plugins/data/optimiziramsi-flow/current` and now
  targets the flow plugin itself; links are `…/current/bin/{loop,grind}`. `runner-link` re-aims
  existing `.agent/bin/{loop,grind}` symlinks on the next session start.
