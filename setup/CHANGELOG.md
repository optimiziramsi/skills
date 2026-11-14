# setup — changelog

Versions of the `setup@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.2.1 — 2026-11-14

- The scaffold table names the worktree skill as `parallel-work:worktree` (the `worktree` plugin is now `parallel-work`).

## 0.2.0 — 2026-11-13

- `/scaffold-claude-md` renamed to `/setup:claude-md`, so typing the plugin name in the `/` menu no longer also matches a skill with the same start.
- `scaffold`: the layout table names the renamed `lessons:capture`, `planning:new` and `worktree:topic` skills.
- `claude-md`: the message-format pointer names the renamed `git` plugin (was `commit`).

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `setup` topic). Enable it per project with `claude plugin install setup@optimiziramsi --scope project`.
