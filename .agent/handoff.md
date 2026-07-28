# Handoff

_Last updated:_ 2026-07-28 — session 8: **`publish-readiness` (0.0.3) is staged to SQUASH-LAND on
`main`** — 17 commits, `main` is an ancestor, tree clean, `./tests.sh` ALL GREEN + `claude plugin
validate . --strict` passes. NOT landed and NOT pushed (both are the user's).

Landing (same recipe as session 7 — git-guard blocks agent `checkout`/`merge` of `main`, and the
harness classifier blocks the agent from moving a branch ref at all, so the USER runs this):

```bash
git update-ref refs/heads/main "$(git commit-tree publish-readiness^{tree} -p main \
  -m 'publish readiness — manifest metadata, hook kill-switches, branch detection, extended done-gate (0.0.3)')"
```

HEAD stays on `publish-readiness`; keep the branch as build history (like `topic-first`). After
this, `main` diverges from `publish-readiness` — expected for a squash land.

## Session 8 (2026-07-28) — publish readiness + de-hardcoding `main` (0.0.3)

Full release notes: [CHANGELOG.md](../CHANGELOG.md) § 0.0.3. The load-bearing bits:

- **No branch name is hardcoded any more.** `git-guard` DETECTS the repo's default branch
  (origin/HEAD → first existing of main/master/develop/trunk → repo-LOCAL `init.defaultBranch`;
  never the machine-global one, which made every repo look like `main`). The 19 pre-existing
  protected tests now pin the branch so the suite can't drift with the host repo.
  `scaffold-claude-md` no longer bakes `main`/`develop` into consumer CLAUDE.md files.
- **Every hook now has a switch** and three gained self-tests — `worktree-bash-guard` also had a
  real hole: its write-verb regex required leading whitespace, so a command *starting* with
  `sed -i` / `tee` / `dd` slipped through. Done-gate 4 → 7 checks.
- **Commands stay thin aliases, now `disable-model-invocation: true`.** A plugin command SHADOWS
  its same-named skill in the model's listing, so the terse wrapper line — not the SKILL.md's
  trigger phrases — drove auto-invocation. A first attempt copied all 25 descriptions into the
  commands; user rejected it as bloat (rightly — breaks "linked, not restated"), reverted for the
  one-line flag. **Not verified live.**
- Naming settled: **keep `optimiziramsi-skills`** — the `<plugin>:<name>` prefix is a menu label
  only; bare `/<name>` works on CC ≥ 2.1.216. Renaming = a third forced consumer migration for
  nothing. `MIGRATION.md` deleted (user: all repos migrated).

## Machine-local install state (not repo)

- Marketplace registered globally from GitHub. `optimiziramsi-skills@optimiziramsi` **0.0.1** is
  what's installed and live here — hooks bind from the 0.0.1 cache (old
  `${CLAUDE_PLUGIN_ROOT}/hooks/…` paths). Nothing from 0.0.2/0.0.3 is bound yet.

## Next up

1. **USER: run the squash-land above**, then **push `main`** (fast-forwards origin, which sits at
   0.0.1 `366b19c`; the 0.0.2 squash and this 0.0.3 squash ride along).
2. Re-dogfood here at project scope, restart, and **verify the two unverified 0.0.3 claims**:
   skills (not commands) now carry the trigger descriptions, and git-guard's branch detection.
3. Older open items: live-test the flow runner from a plain terminal (recipe in MEMORY.md);
   worktree-aware loop/grind sit in `.todo`.

## Standing context

- `init-marketplace`, `single-plugin`, `topic-first` = retained build history. Done-gate:
  `./tests.sh` (now includes `claude plugin validate . --strict`). `.todo` format: plain bullets,
  `(done)` prefix, no checkboxes. Commit style is single-line (guard live). History is append-only
  — the one revert this session was a `revert -n` + fresh commit, never an amend/rebase.
  Deliberate source-sweep skips still honored — don't re-sweep.
