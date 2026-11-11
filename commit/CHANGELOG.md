# commit — changelog

Versions of the `commit@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.1 — unreleased

- The commit nudge no longer adds "also refresh the handoff (/handoff)" when the project has an
  `.agent/handoff.md` — it asks for one thing, the commit.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `commit` topic). Enable it per project with `claude plugin install commit@optimiziramsi --scope project`.
