# instructions — changelog

Versions of the `instructions@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.3.1 — unreleased

- The caps note and the meta-lint note are now silent in a desktop-app worktree chat too (its project dir is the main checkout, only the cwd is the worktree), and the meta-lint cap gate checks that worktree's files instead of the main checkout's.
- `meta-lint --changed <branch>` — the land-time check: only the findings that name a file changed since `<branch>` (committed, uncommitted, untracked, deleted), on the checkout it is run in. A worktree chat sees its own findings before landing instead of the whole repo backlog.
- `/instructions:audit` closes by suggesting — once, never creating — a roughly monthly scheduled run of itself when the user has none, since repo-wide findings are no longer pushed into worktree chats.

## 0.3.0 — 2026-11-13

- `/instructions-audit` renamed to `/instructions:audit` and `/instructions-maintenance` to `/instructions:maintenance`, so typing the plugin name in the `/` menu no longer also matches a skill with the same start.
- References to the renamed `lessons:capture` and `planning:new` skills updated.

## 0.2.0 — 2026-11-12

- Nothing runs at session start any more. `caps` is a Stop note for the user (a `systemMessage`:
  not model context, never blocking, once per session per distinct breach-set, whether or not
  the session wrote files) instead of start context plus a blocking Stop nudge.
- `meta-lint --end-note` (new) shows the findings count the same way at Stop; it replaces the
  `--fast` pulse at session start (`--fast` stays for manual runs). The `--stop` gate is
  unchanged. Both notes are silent in a linked git worktree unless `NUDGES_IN_WORKTREE=1`.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `instructions` topic, minus what moved to `lessons` and `guards`). Enable it per project with `claude plugin install instructions@optimiziramsi --scope project`.
