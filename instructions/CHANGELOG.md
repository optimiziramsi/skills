# instructions — changelog

Versions of the `instructions@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.2.0 — 2026-11-12

- Nothing runs at session start any more. `caps` is a Stop note for the user (a `systemMessage`:
  not model context, never blocking, once per session per distinct breach-set, whether or not
  the session wrote files) instead of start context plus a blocking Stop nudge.
- `meta-lint --end-note` (new) shows the findings count the same way at Stop; it replaces the
  `--fast` pulse at session start (`--fast` stays for manual runs). The `--stop` gate is
  unchanged. Both notes are silent in a linked git worktree unless `NUDGES_IN_WORKTREE=1`.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `instructions` topic, minus what moved to `lessons` and `guards`). Enable it per project with `claude plugin install instructions@optimiziramsi --scope project`.
