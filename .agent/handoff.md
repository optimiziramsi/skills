# Handoff

_Last updated:_ 2026-07-29 — session 11: **0.0.6 landed on `main` (`4e979d4`) and pushed**;
`./tests.sh` ALL GREEN (7 checks, 438 tests); local install updated to 0.0.6 and verified from the
cache. `main` == `origin/main` == `slim`.

Repo is now two branches (`main`, `slim`) and two worktrees (checkout on `slim`, `_integration`
pinning `main`) — every earlier feature branch and its worktree was deleted this session; their
build history is fully contained in `main`.

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

`optimiziramsi-skills@optimiziramsi` **0.0.6** installed; smoke-tested from the cache (16 python
hooks execute, `lib/` + all 8 `tests/` dirs shipped, gate green, bare wrapper resolves 0.0.6 past
the legacy 0.0.1 entry under the old marketplace name). Stale caches 0.0.1 / 0.0.4 / 0.0.5 still on disk, harmless.
`main` pinned in `.claude/worktrees/_integration`; `receive.denyCurrentBranch=updateInstead`.
Tracked `.claude/settings.json` sets `GIT_GUARD_{PROTECTED,INTEGRATION}_BRANCH` = `main`.
The main checkout deliberately sits on `slim`, not `main` — git-guard blocks checking out the
protected branch, so a non-`main` working branch is the normal resting state here.

## Next up

1. Still open from earlier sessions — **the live leak-probe test** (USER, plain terminal): run
   `loop` from a worktree and read the verdict. `confined` = PreToolUse hooks DO fire under
   `--dangerously-skip-permissions`; `leak` = they don't, and the fallback is the OS sandbox
   (`sandbox.filesystem.allowWrite` **plus a git-dir carve-out** — a worktree commit writes into
   the shared main `/.git`). Doubles as the runners' never-done live smoke test.
2. Not yet slimmed: `instructions/bin/meta-lint` is still 1332 lines / 19 checks (user confirmed
   they use it). `flow/bin/_flowlib.py` (908) and the runners are justified by what they do.

## Standing context

`init-marketplace`, `single-plugin`, `topic-first`, `publish-readiness` = retained build history.
Done-gate `./tests.sh` (7 checks). `.todo`: plain bullets, `(done)` prefix, no checkboxes. Commits
single-line (guard live). History append-only. Deliberate source-sweep skips still honored.
Worktree board is `.agent/worktrees.md`.
