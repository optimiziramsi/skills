# worktree — changelog

Versions of the `worktree@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.1 — unreleased

- New `relay` skill + `/relay` command — pair-programming by worktree: the human comments in one shared worktree (any branch name, cut off the integration branch) (staged, never committed, never landed); the primary chat turns comments into topics, spawns one `worktree`-skill sub chat per topic off the integration branch, rebases the shared branch after each land, strips landed comments, reviews each land against the brief's `Done =`, and tears the sub chat down. Handover via phrases (`RELAY`, `READY`, …) → session card, or a quiet file → a Yes / Not yet question.
- New `bin/relay-watch` — the relay comment watcher for the Monitor tool (macOS + Linux, `--test`).
- Knobs: `RELAY_SUB_MODELS`, `RELAY_PRIMARY_MODELS`, `RELAY_QUIET_SECS`.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the `worktree` skill of its `worktree` topic). Enable it per project with `claude plugin install worktree@optimiziramsi --scope project`.
