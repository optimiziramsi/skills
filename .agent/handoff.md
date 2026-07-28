# Handoff

_Last updated:_ 2026-07-28 — session 9: **0.0.4 landed on `main` from a worktree via the ordinary
`git push . HEAD:main`.** Check `git rev-list --count origin/main..main` before assuming it's
pushed; **the push is always the user's**. `./tests.sh` ALL GREEN.

Sessions 7–8's `update-ref` / `commit-tree` landing recipe is **obsolete — do not reuse it.** The
guard permits the land push now, and `update-ref` desyncs the index of whichever worktree holds the
target branch.

## Session 9 (2026-07-28) — worktree lands into a pinned integration branch (0.0.4)

Release notes: [CHANGELOG.md](../CHANGELOG.md) § 0.0.4. What a cold session can't re-derive:

- **`GIT_GUARD_INTEGRATION_BRANCH`** only matters where the integration branch is ALSO protected
  (here `main` is both) — the protected-branch rule was blocking the `worktree` skill's own land.
  Two-tier repos (`develop` + protected `main`) leave it unset.
- **Landing wiring reversed** — `<integration>` is pinned in a `_integration` worktree nobody
  edits, instead of living in the human's checkout. Verified on git 2.50.1: a push is refused
  whenever the target is checked out in ANY worktree; `receive.denyCurrentBranch=updateInstead`
  lifts that only while that tree is clean and only at **repo level** (`--worktree` scope is
  ignored); `branch -f` refuses; `update-ref` silently desyncs. Fallback: check `<integration>` out
  nowhere → FF push, zero config.
- `624b77a` + `8c10e3c` on `main` are a deliberate, user-approved probe pair proving the wiring;
  net content == `2fb285b`.

## Machine-local (not repo)

`optimiziramsi-skills@optimiziramsi` **0.0.4** installed and live. Wiring live here: checkout parked
on `work`; `main` pinned in `.claude/worktrees/_integration`;
`receive.denyCurrentBranch=updateInstead`. The repo now ships a tracked `.claude/settings.json`
(`GIT_GUARD_PROTECTED_BRANCH` + `GIT_GUARD_INTEGRATION_BRANCH`, both `main`), and
`.claude/worktrees/` is gitignored in-repo.

## Next up

1. **USER: push `main`.**
2. **Teardown** from the main checkout: `git worktree remove .claude/worktrees/worktree-skill-merge-c479b2`,
   then delete `feature/worktree-land-wiring` + the superseded `feature/worktree-skill-merge-c479b2`
   (`ed82d7b`). `looper-grinder-worktree-7f4a4f` sits at `5794e29` with no commits — remove or reuse.
3. `feature/worktree-looper-grinder` (`11411cb`) holds unlanded loop/grind worktree-awareness on the
   PRE-topic-first layout (`plugins/flow/**`) — needs re-homing to `flow/**` before it can land.
4. Unverified from 0.0.3: that skills (not commands) now carry the trigger descriptions. Older: live-test
   the flow runner from a plain terminal (recipe in MEMORY.md); worktree-aware loop/grind in `.todo`.

## Standing context

`init-marketplace`, `single-plugin`, `topic-first`, `publish-readiness` = retained build history.
Done-gate `./tests.sh` (7 checks). `.todo`: plain bullets, `(done)` prefix, no checkboxes. Commits
single-line (guard live). History append-only. Deliberate source-sweep skips still honored.
Worktree work lands normally now; board is `.agent/worktrees.md`.
