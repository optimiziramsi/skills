# planning — changelog

Versions of the `planning@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.2.0 — 2026-11-02

- milestone: umbrella milestones (many parallel chats under one orchestrator) now keep a
  machine-scannable `ledger.md` in place of `steps.md` — tagged records, parallel groups,
  cross-group requests, and a `verify:`-gated acceptance group; complete = `ledger open` empty +
  `ledger check` exit 0. Format / vocab / report shapes live in the new `milestone/ledger.md`; the
  `README.md` scaffold moved to `milestone/readme-template.md` (SKILL.md links both, back under the
  9000-char cap). The active-milestones index and the `plan` skill's "prose, no checkboxes" rule
  gain a carve-out for the ledger's closed-enum `[status:…]` tags.
- Ships `bin/ledger` — a pure bash+awk, read-only reader (`list` / `ready` / `open` / `blocked` /
  `active` / `id` / `next` / `check`, `--test`) on PATH while the plugin is enabled, so repos stop
  vendoring it.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (`plan` and `milestone` from its `flow` topic). Enable it per project with `claude plugin install planning@optimiziramsi --scope project`.
