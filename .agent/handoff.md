# Handoff

_Last updated:_ 2026-07-28 — session 10: **0.0.5 (flow runner launch UX) is committed on
`feature/looper-grinder-worktree-7f4a4f` but NOT landed** — the land push was refused by the harness
permission classifier, not by the guard. `./tests.sh` ALL GREEN (now 8 checks).

Sessions 7–8's `update-ref` / `commit-tree` landing recipe is **obsolete — do not reuse it.** The
guard permits the land push now, and `update-ref` desyncs the index of whichever worktree holds the
target branch.

## Session 10 (2026-07-28) — how loop/grind get STARTED (0.0.5), unlanded

Release notes: [CHANGELOG.md](../CHANGELOG.md) § 0.0.5; plan + progress:
[.agent/plan/loop-grind-launch.md](plan/loop-grind-launch.md). What a cold session can't re-derive:

- **The runners were always cwd-relative** — "worktree-aware" needed no new addressing model, only a
  way to pick the cwd (`--worktree`) and a stable name for the binary (a **committed** wrapper).
  Symlinks were rejected: they encode a machine path, so they can't be tracked and never reach a
  fresh worktree.
- **The wrapper is version-locked** (user's call): it refuses to run against a plugin of a different
  version, and `tests.sh` check 8 keeps `flow/examples/runner-wrapper.sh`'s `WRAPPER_VERSION` equal
  to `plugin.json` — **bump both together or every consumer's wrapper hard-stops.**
- **Confinement reuses `worktree/hooks/*.sh`** instead of a second copy, so `flow/bin/_flowlib.py`
  now needs the `worktree` topic present (it dies loudly otherwise) — accepted, not overlooked.
- **`git push . HEAD:main` and `git reset --soft` were classifier-refused** this session (the same
  push succeeded once, for the claim row) — hence unlanded commits still carrying `<slug> ┃`.

## Session 9 (2026-07-28) — worktree lands into a pinned integration branch (0.0.4)

Release notes: [CHANGELOG.md](../CHANGELOG.md) § 0.0.4. Non-re-derivable: `GIT_GUARD_INTEGRATION_BRANCH`
only matters where the integration branch is ALSO protected (here `main` is both); `<integration>` is
pinned in a `_integration` worktree nobody edits, because (git 2.50.1) a push is refused whenever the
target is checked out in ANY worktree, `receive.denyCurrentBranch=updateInstead` lifts that only for a
clean tree and only at **repo level**, `branch -f` refuses, and `update-ref` silently desyncs.
`624b77a`+`8c10e3c` are a user-approved probe pair; net content == `2fb285b`.

## Machine-local (not repo)

`optimiziramsi-skills@optimiziramsi` **0.0.4** installed and live (so the shipped 0.0.5 wrapper
would refuse against it until the install is updated). Wiring live here: checkout parked on `work`;
`main` pinned in `.claude/worktrees/_integration`; `receive.denyCurrentBranch=updateInstead`. The
repo ships a tracked `.claude/settings.json` (`GIT_GUARD_PROTECTED_BRANCH` +
`GIT_GUARD_INTEGRATION_BRANCH`, both `main`); `.claude/worktrees/` is gitignored in-repo.

## Next up

1. **Land 0.0.5** — from the `looper-grinder-worktree-7f4a4f` worktree: `git push . HEAD:main`
   (fast-forward; `main` sits at the claim row `c5a0120`). Then **USER: push `main`** to origin.
2. **Teardown** from the main checkout: `git worktree remove` for
   `worktree-skill-merge-c479b2` **and** `looper-grinder-worktree-7f4a4f`; delete
   `feature/worktree-land-wiring`, `feature/worktree-skill-merge-c479b2` (`ed82d7b`),
   `feature/looper-grinder-worktree-7f4a4f`, and the now-superseded
   `feature/worktree-looper-grinder` (`11411cb`).
3. **The one live test that matters** (USER, plain terminal — the classifier blocks it in-session):
   run `loop`/`grind` from a worktree and read the leak-probe verdict. `confined` = PreToolUse hooks
   DO fire under `--dangerously-skip-permissions`; `leak` = they don't, and the OS-sandbox route
   (`sandbox.filesystem.allowWrite` + a git-dir carve-out, since a worktree commit writes into the
   shared main `/.git`) is the fallback. This also doubles as the runner's never-done live smoke
   test (recipe in MEMORY.md).
4. Unverified from 0.0.3: that skills (not commands) now carry the trigger descriptions.

## Standing context

`init-marketplace`, `single-plugin`, `topic-first`, `publish-readiness` = retained build history.
Done-gate `./tests.sh` (8 checks). `.todo`: plain bullets, `(done)` prefix, no checkboxes. Commits
single-line (guard live). History append-only. Deliberate source-sweep skips still honored.
Worktree work lands normally now; board is `.agent/worktrees.md`.
