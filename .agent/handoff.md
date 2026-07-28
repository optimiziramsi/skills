# Handoff

_Last updated:_ 2026-07-28 — session 9: **0.0.4 landed on `main` (`8c10e3c`) from a worktree, via
the normal `git push . HEAD:main` land — no manual squash recipe needed any more.** `main` is 2
commits ahead of `origin/main`; **the push is the user's**. `./tests.sh` ALL GREEN.

Sessions 7–8's `update-ref`/`commit-tree` landing recipe is **obsolete** — don't reuse it. The
guard now permits the land push directly (below), and `update-ref` was always unsafe when the
target branch is checked out (it desyncs that worktree's index).

## Session 9 (2026-07-28) — worktree lands into a pinned integration branch (0.0.4)

Full release notes: [CHANGELOG.md](../CHANGELOG.md) § 0.0.4. The load-bearing bits:

- **`GIT_GUARD_INTEGRATION_BRANCH`** names the one branch work lands into. Only load-bearing where
  that branch is ALSO protected (this repo: `main` is both) — there the protected-branch rule was
  blocking the `worktree` protocol's own `git push . HEAD:<integration>`, so no slice could land.
  Permits exactly that FF land; force (`+HEAD:main`), delete (`:main`, `--delete`), and
  `checkout`/`switch` onto the branch stay blocked, as does a land into any *other* protected
  branch. Two-tier repos (`develop` + protected `main`) leave it unset.
- **Landing wiring reversed.** The skill used to say "keep the main repo on `<integration>`", which
  makes the human's own checkout the thing that must stay clean. It now pins `<integration>` in a
  dedicated `.claude/worktrees/_integration` worktree nobody edits — clean by construction, locks
  the branch against accidental checkout, keeps the landed state materialized. Verified empirically
  (git 2.50.1): a push is refused whenever the target is checked out in ANY worktree;
  `receive.denyCurrentBranch=updateInstead` lifts it only while that tree is clean and only at
  **repo level** (a `--worktree`-scoped value is ignored); `git branch -f` refuses; `update-ref`
  silently desyncs. Fallback: keep `<integration>` checked out nowhere → FF push, zero config.
- **~29 ms off every Bash tool call.** 0.0.3's default-branch detection shells out to git, and
  `check()` resolved it before knowing the command was even git — `ls -la` paid for up to five
  subprocesses. Now lazy at the two use-sites + memoized per cwd.
- Skill also reads `<integration>`/`<protected>` from settings `env` instead of guessing, skips the
  HARD GATE fork-point compare when the two are the same branch, and prechecks the landing wiring
  up front instead of discovering it at push time.
- Two throwaway commits (`624b77a` probe + `8c10e3c` removal) sit on `main` — deliberate,
  user-approved proof the wiring works end to end. Net content == `2fb285b`.

## Machine-local install state (not repo)

- `optimiziramsi-skills@optimiziramsi` **0.0.4** installed and live. This repo now ships a tracked
  `.claude/settings.json` declaring `GIT_GUARD_PROTECTED_BRANCH=main` +
  `GIT_GUARD_INTEGRATION_BRANCH=main` — both bound and verified working this session.
- Landing wiring is **live here**: main checkout parked on `work`; `main` pinned in
  `.claude/worktrees/_integration`; `receive.denyCurrentBranch=updateInstead`. `.claude/worktrees/`
  is now gitignored in-repo (was only in machine-local `.git/info/exclude`).

## Next up

1. **USER: push `main`** (2 ahead of origin, fast-forward).
2. **Teardown** (from the main checkout): `git worktree remove` for
   `.claude/worktrees/worktree-skill-merge-c479b2`, then delete `feature/worktree-land-wiring` and
   the superseded `feature/worktree-skill-merge-c479b2` (`ed82d7b`). The sibling
   `looper-grinder-worktree-7f4a4f` sits at `5794e29` with no commits — remove or reuse.
   `feature/worktree-looper-grinder` (`11411cb`) still holds unlanded loop/grind worktree-awareness
   work on the PRE-topic-first layout (`plugins/flow/**`) — needs re-homing to `flow/**` to land.
3. Still unverified from 0.0.3: that skills (not commands) now carry the trigger descriptions.
4. Older open items: live-test the flow runner from a plain terminal (recipe in MEMORY.md);
   worktree-aware loop/grind sit in `.todo`.

## Standing context

- `init-marketplace`, `single-plugin`, `topic-first`, `publish-readiness` = retained build history.
  Done-gate: `./tests.sh` (7 checks, incl. `claude plugin validate . --strict`). `.todo` format:
  plain bullets, `(done)` prefix, no checkboxes. Commit style is single-line (guard live). History
  is append-only. Deliberate source-sweep skips still honored — don't re-sweep.
- **Worktree work now lands normally** — reserve → slice → review → `git push . HEAD:main`. The
  board is `.agent/worktrees.md` (created this session; currently empty + one pending-cleanup row).
