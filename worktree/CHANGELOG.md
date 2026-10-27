# worktree — changelog

Versions of the `worktree@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.6 — 2026-10-27

- relay-watch now scans docs too: the blanket `*.md` / `.agent/` file-type skip is replaced by a narrow denylist of the relay's own free-prose state files (`.agent/relay.md`, `.agent/handoff.md`, `.agent/relay-watch/`, `.todo*`). A user handover left in a doc (a README, a milestone doc) now fires instead of depending on the primary sweeping it up by hand; the primary's own `relay:`-prefixed notes are still skipped everywhere, docs included (`<!-- relay: … -->`). Trade-off (chosen deliberately): because markdown `#` headings and `*` bullets read as comment markers, a newly added heading/bullet that contains a handover word (Ready, Scheduled, …) can fire. Self-test covers doc handovers firing, the state-file denylist, and the `relay:` prefix still winning in docs.

## 0.1.5 — 2026-10-27

- relay-watch: a human comment written directly under a `relay:` line (no blank or code line between) was swallowed — 0.1.4's multi-line-block rule read every comment line after a `relay:` line as the primary's continuation, so a handover glued under an audit note never fired TRIGGER or QUIET. The watcher now judges comment lines independently: a line is the primary's only if it itself carries the `relay:` prefix, so multi-line `relay:` notes must carry the prefix on every line (SKILL.md updated to require it). Self-test covers a glued human comment (fires TRIGGER and QUIET) and a fully-prefixed multi-line note (silent).

## 0.1.4 — 2026-10-26

- relay-watch: a multi-line `relay:` note (prefix on its first line only) is dropped as a whole — its continuation comment lines no longer count as new human comments (they made a file with an audit note show up as QUIET). A block ends at the first code line, removed line or hunk boundary; a human comment right after code still fires. Self-test covers it.

## 0.1.3 — 2026-10-26

- relay-watch fix: the `relay:` exclude never matched under a POSIX `grep -E` (no `\t` escape — the regex is now built with a real tab), so the primary's own `relay:` notes containing a handover word fired TRIGGER; self-test now covers a `// relay: audit — RELAY …` line (no TRIGGER, no QUIET) and runs clean under BSD tools. Digest falls back md5 → md5sum → shasum.

## 0.1.2 — 2026-10-26

- relay, from the first real run (8 topics): every line the primary writes carries a `relay:` prefix and `relay-watch` skips it (it used to ask the primary about its own audit notes); `relay-watch --seed` marks pre-existing comments as seen so the first arm does not flood, and existing comments are presented as one backlog list; the watcher's state dir goes into `info/exclude`; the rebase trick uses `git add -u` (git-guard blocks the bulk form) and settles modify/delete conflicts toward the integration branch (`-X ours` does not); the board strike may be committed from the main checkout when it holds the integration branch and is clean, with the project's archive log appended in the same commit; a refused model id falls through to the next list entry.

## 0.1.1 — 2026-10-26

- New `relay` skill + `/relay` command — pair-programming by worktree: the human comments in one shared worktree (any branch name, cut off the integration branch) (staged, never committed, never landed); the primary chat turns comments into topics, spawns one `worktree`-skill sub chat per topic off the integration branch, rebases the shared branch after each land, strips landed comments, reviews each land against the brief's `Done =`, and tears the sub chat down. Handover via phrases (`RELAY`, `READY`, …) → session card, or a quiet file → a Yes / Not yet question.
- New `bin/relay-watch` — the relay comment watcher for the Monitor tool (macOS + Linux, `--test`). `--help` also prints the full handover-phrase list generated from the trigger regex itself, so it can't drift from what fires.
- Knobs: `RELAY_SUB_MODELS`, `RELAY_PRIMARY_MODELS`, `RELAY_QUIET_SECS`.
- Shaped by a live run: the primary accepts the app-named shared branch, lifts a sub chat's model/effort after every spawn (the app clamps silently), checks the integration log every turn because land notes can be queued, and prunes a sub chat's worktree after archiving it.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the `worktree` skill of its `worktree` topic). Enable it per project with `claude plugin install worktree@optimiziramsi --scope project`.
