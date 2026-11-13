# planning — changelog

Versions of the `planning@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.2.2 — unreleased

- `/plan` renamed to `/planning:new`, so typing the plugin name in the `/` menu no longer also matches a skill with the same start.
- References to the renamed `worktree:topic` skill updated.

## 0.2.1 — 2026-11-02

- milestone/`ledger`: `ledger why <ID>` prints the transitive chain of unlanded `needs:` for one
  record as an indented tree — group refs shown as `group:X (n/m landed)`, `group:PREFIX*` globs
  supported, depth-capped. The critical path for a record, derived from the tags instead of restated
  in prose.
- milestone/`ledger`: `ledger check` now lints `verify:` for runnability — a `verify:` carrying no
  backticked command/path, `review:`, `user:`, or `README § Log` token (or under 25 chars) is an
  ERROR, not a missing-field pass, so a vague `verify: works` no longer counts as land-ready.
- milestone/`ledger.md`: documents the `verify:` runnability rule and the `by:` project-decision-id
  form (e.g. `OD-n`) beside `<id>` / `walk:<pattern>`, and notes a project may add its own
  land-report lines on top of the ledger minimum.
- milestone: new `milestone/orchestrator.md` lifts the parent chat's own playbook (opening a group,
  the worker brief, the per-land loop, requests/blockers, phase boundaries, context refresh);
  SKILL.md § Umbrella milestones points at it.
- `bin/ledger` header notes it is on PATH only inside a Claude Code session
  (`…/cache/<plugin>/<version>/bin`); a headless runner started outside the session must call it by
  path. Any change under a published version number requires a version bump — the cache is
  version-keyed, so an unmoved version reaches nobody.

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
