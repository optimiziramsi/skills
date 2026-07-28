# Handoff

_Last updated:_ 2026-07-29 — session 11: **branch `slim`** (cut from `main`@`829c090`), 10 commits,
`./tests.sh` ALL GREEN (7 checks, 438 tests). Version 0.0.6, **not landed, not pushed**.

Session 10's 0.0.5 is on `main` and still unpushed. **Branch `work` is stale** (0.0.4) — ignore it.

## Session 11 (2026-07-29) — the slimming pass (0.0.6)

Release notes: [CHANGELOG.md](../CHANGELOG.md) § 0.0.6. What a cold session can't re-derive:

- **The diagnosis the user was right about.** The scripts felt like accretion, but the edge cases
  were each legitimate — the bloat was *scaffolding repeated per file*. Four worktree guards were
  220 lines carrying ~35 lines of actual decision; the rest was one git preamble ×4, a jq-DISARM
  block ×3, an inline self-test ×4, a header comment ×4. Fix duplication, not edge cases.
- **Every hook is python3 over [`lib/hookio.py`](../lib/hookio.py); `jq` is gone.** User's call
  (asked whether to port bash→python or the reverse). `lib/` at the repo root is a deliberate
  exception to topic-first co-location — the user approved it explicitly.
- **Tests live in `<topic>/tests/*.py`, never inside a shipped file.** `tests.sh` check 7a runs
  them; 7b still runs anything with an inline `--test` (`_flowlib`, `meta-lint`, guards.d examples).
- **The wrapper version lock is deleted** (user reversed the 0.0.5 decision): whatever plugin
  version is active supplies both the instructions and the runner, so wrapper/runner drift is not a
  reachable state. `WRAPPER_VERSION`, `FLOW_WRAPPER_ALLOW_DRIFT` and `tests.sh` check 8 are gone —
  **do not reintroduce them.** Consumers refresh `bin/loop`/`bin/grind` once.
- **Honest number:** shipped code lines are roughly flat (python is wordier per line than dense
  bash). The wins are one language, no external dep, no self-disarming guard, and 78 → 438 tests.

## Machine-local (not repo)

`optimiziramsi-skills@optimiziramsi` **0.0.4** installed and live — so the hooks binding this
session are the OLD `.sh` paths from the 0.0.1/0.0.4 cache, not this branch. Checkout on `slim`;
`main` pinned in `.claude/worktrees/_integration`; `receive.denyCurrentBranch=updateInstead`.
Tracked `.claude/settings.json` sets `GIT_GUARD_{PROTECTED,INTEGRATION}_BRANCH` = `main`.

## Next up

1. **Land `slim` → `main`** (`git push . HEAD:main` works; the 0.0.5 `update-ref` recipe is
   obsolete), then **USER: push `main`**.
2. Re-dogfood: update the local install to 0.0.6 and restart, so the python hooks actually bind.
3. Still open from earlier sessions — **the live leak-probe test** (USER, plain terminal): run
   `loop` from a worktree and read the verdict. `confined` = PreToolUse hooks DO fire under
   `--dangerously-skip-permissions`; `leak` = they don't, and the fallback is the OS sandbox
   (`sandbox.filesystem.allowWrite` **plus a git-dir carve-out** — a worktree commit writes into
   the shared main `/.git`). Doubles as the runners' never-done live smoke test.
4. Teardown (main checkout): `git worktree remove` `worktree-skill-merge-c479b2` +
   `looper-grinder-worktree-7f4a4f`; delete `feature/worktree-land-wiring`,
   `feature/worktree-skill-merge-c479b2`, `feature/looper-grinder-worktree-7f4a4f`,
   `feature/worktree-looper-grinder`, and the stale `work`.
5. Not yet slimmed: `instructions/bin/meta-lint` is still 1332 lines / 19 checks (user confirmed
   they use it). `flow/bin/_flowlib.py` (908) and the runners are justified by what they do.

## Standing context

`init-marketplace`, `single-plugin`, `topic-first`, `publish-readiness` = retained build history.
Done-gate `./tests.sh` (7 checks). `.todo`: plain bullets, `(done)` prefix, no checkboxes. Commits
single-line (guard live). History append-only. Deliberate source-sweep skips still honored.
Worktree board is `.agent/worktrees.md`.
