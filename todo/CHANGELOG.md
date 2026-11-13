# todo — changelog

Versions of the `todo@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.2 — 2026-11-13

- `triage-todo`: points at the renamed `planning:new` skill.

## 0.1.1 — 2026-11-12

- `todo-readonly-guard`: the deny reason no longer names the `TODO_GUARD_SKIP=1` bash prefix. It says
  `.todo` is the user's, points at `.todo-inbox`, and that writing `.todo` needs the user to reply
  "ALLOW TODO". The prefix still works and stays documented in the README.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (`triage-todo`, `feedback`, `scope-cut` and the `.todo` guard from its `flow` topic). Enable it per project with `claude plugin install todo@optimiziramsi --scope project`.
