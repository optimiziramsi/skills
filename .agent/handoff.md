# Handoff

_Last updated:_ 2026-07-29 — session 12: **0.0.9 reviewed + pushed; 0.0.10 committed, unpushed.**

`main` is the only branch and there are no worktrees left — the `slim` branch and both worktrees
(checkout + `_integration`) are gone, so the checkout now sits on `main` itself. The user squashed
this session's 0.0.9 review fixup into `f4fefc7` and pushed it. **`27ffcbf` (0.0.10, doc-only) is
one commit ahead of `origin/main` and is the user's to push.** `./tests.sh` ALL GREEN (7 checks,
466 tests).

## Session 12 (2026-07-29) — reviewing 0.0.9, then 0.0.10 on a consumer report

Release notes: [CHANGELOG.md](../CHANGELOG.md) § 0.0.9. What a cold session can't re-derive:

- **0.0.9 shipped with a bug that undercut its own fix.** The rewritten `worktree-bash-guard`
  resolves write paths instead of grepping for them, but it started resolving from `wt_root`
  rather than the hook payload's `cwd`. The Bash tool's cwd persists across calls, so a session
  standing in a worktree *subdirectory* was off by one hop per level — it let the exact escape
  class 0.0.9 exists to close straight through, and denied writes that never left the worktree.
  Fixed in `4512ac7`; 6 regression tests pin it (reverting the one-line fix fails 4 of them).
- **The fix folded into 0.0.9 rather than cutting 0.0.10** — 0.0.9 was unpushed and materialized
  in no cache (the local one tops out at 0.0.8), so no consumer could have seen it. Same reasoning
  applies to anything else caught before this push.
- **0.0.10 came from a consumer repo (rabbit-run) field-testing 0.0.9** — doc-only, `27ffcbf`. The
  `worktree` skill's fourth "Known failure mode" claimed a write-guard false-positive on the
  worktree's own nested `.claude/**`: fixed since 0.0.6, re-verified false here in both layouts.
  Its workaround had become an instruction to route around the guard 0.0.9 hardened. Generalized
  into a lesson: [doc-fixes-must-not-become-bypasses](lessons/doc-fixes-must-not-become-bypasses.md).
- **Verify a consumer's claims before landing them.** Both of rabbit-run's held up, but the fix
  they proposed (just drop the item) needed a replacement they hadn't scoped.

## Machine-local (not repo)

`optimiziramsi-skills@optimiziramsi` **0.0.8** is installed; caches 0.0.4–0.0.8 on disk plus a
legacy `opsi/…/0.0.1` under the old marketplace name, all harmless. After the push:
`claude plugin marketplace update optimiziramsi` → `plugin update` → **restart**.
Tracked `.claude/settings.json` sets `GIT_GUARD_{PROTECTED,INTEGRATION}_BRANCH` = `main`.
Committing on `main` is not blocked; git-guard blocks bulk staging (`git add -A`) — stage by name.

## Next up

1. Still open from earlier sessions — **the live leak-probe test** (USER, plain terminal): run
   `loop` from a worktree and read the verdict. `confined` = PreToolUse hooks DO fire under
   `--dangerously-skip-permissions`; `leak` = they don't, and the fallback is the OS sandbox
   (`sandbox.filesystem.allowWrite` **plus a git-dir carve-out** — a worktree commit writes into
   the shared main `/.git`). Doubles as the runners' never-done live smoke test.
2. Not yet slimmed: `instructions/bin/meta-lint` is still 1332 lines / 19 checks (user confirmed
   they use it). `flow/bin/_flowlib.py` (908) and the runners are justified by what they do.
3. `.todo` carries two open design questions the user raised: making `loop`/`grind` worktree-aware,
   and landing a worktree into a branch that isn't checked out.

## Standing context

`init-marketplace`, `single-plugin`, `topic-first`, `publish-readiness` = retained build history.
Done-gate `./tests.sh` (7 checks). `.todo`: plain bullets, `(done)` prefix, no checkboxes; the
`todo-readonly-guard` is live here, so `.todo` edits need "ALLOW TODO" and unarmed deferrals go to
`.todo-inbox`. Commits single-line (guard live). History append-only. Tests live in
`<topic>/tests/*.py`, never inside a shipped file. Worktree board is `.agent/worktrees.md`.
