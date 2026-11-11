# session — changelog

Versions of the `session@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.2 — unreleased

- Session start injects the state line only (plus the missing-`python3` warning). The handoff
  age, `.todo` count and instructions-audit age moved to a Stop note for the user — not model
  context, never blocking, each fact once per session, worded as facts.
- The Stop notes are silent in a linked git worktree; `NUDGES_IN_WORKTREE=1` shows them there.

## 0.1.1 — 2026-11-02

- handoff: the "Active milestones / plans" section is a record list (one dash per item), never a
  table — matching the `no-tables` convention a project's own `.agent/` lint enforces.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `session` topic). Enable it per project with `claude plugin install session@optimiziramsi --scope project`.
