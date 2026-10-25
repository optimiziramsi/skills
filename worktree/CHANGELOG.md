# worktree — changelog

Versions of the `worktree@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.2 — unreleased

- relay, from the first real run (8 topics): every line the primary writes carries a `relay:` prefix and `relay-watch` skips it (it used to ask the primary about its own audit notes); `relay-watch --seed` marks pre-existing comments as seen so the first arm does not flood, and existing comments are presented as one backlog list; the watcher's state dir goes into `info/exclude`; the rebase trick uses `git add -u` (git-guard blocks the bulk form) and settles modify/delete conflicts toward the integration branch (`-X ours` does not); the board strike may be committed from the main checkout when it holds the integration branch and is clean, with the project's archive log appended in the same commit; a refused model id falls through to the next list entry.

## 0.1.1 — 2026-10-26

- New `relay` skill + `/relay` command — pair-programming by worktree: the human comments in one shared worktree (any branch name, cut off the integration branch) (staged, never committed, never landed); the primary chat turns comments into topics, spawns one `worktree`-skill sub chat per topic off the integration branch, rebases the shared branch after each land, strips landed comments, reviews each land against the brief's `Done =`, and tears the sub chat down. Handover via phrases (`RELAY`, `READY`, …) → session card, or a quiet file → a Yes / Not yet question.
- New `bin/relay-watch` — the relay comment watcher for the Monitor tool (macOS + Linux, `--test`). `--help` also prints the full handover-phrase list generated from the trigger regex itself, so it can't drift from what fires.
- Knobs: `RELAY_SUB_MODELS`, `RELAY_PRIMARY_MODELS`, `RELAY_QUIET_SECS`.
- Shaped by a live run: the primary accepts the app-named shared branch, lifts a sub chat's model/effort after every spawn (the app clamps silently), checks the integration log every turn because land notes can be queued, and prunes a sub chat's worktree after archiving it.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the `worktree` skill of its `worktree` topic). Enable it per project with `claude plugin install worktree@optimiziramsi --scope project`.
