# Plan — `loop-grind-launch`: fix how the flow runners are started

**Topic:** the flow runners (`loop`, `grind`) work, but *launching* them is the sore spot — the chat
has to `echo "$CLAUDE_PLUGIN_ROOT"`, the human has to `cd` into the right worktree and paste an
absolute versioned path, and a `bin/loop` symlink can't be committed (it encodes a machine path) so
it never travels to a fresh worktree.

**Branch:** `feature/looper-grinder-worktree-7f4a4f` · **worktree:** `.claude/worktrees/looper-grinder-worktree-7f4a4f`

## Decisions (user, this session)

1. **Committed wrapper**, not a symlink. A tracked `bin/loop` / `bin/grind` in the *consumer* repo
   that discovers the installed plugin at runtime. Tracked ⇒ it exists in every worktree by
   construction, contains no local paths, and survives plugin version bumps.
2. **`--worktree <name>`** selection: run from the checkout root, name a worktree, the runner
   `chdir`s there and everything downstream (job discovery, `.agent/loop/`, confinement detection)
   keeps working because it is all cwd-relative already.
3. **A skill scaffolds the wrapper** into a consumer repo (not a docs-only paste recipe).
4. **Port the confinement** work from `feature/worktree-looper-grinder` *if it survives review* —
   it is written against the pre-topic-first `plugins/flow/**` layout and duplicates guards the
   `worktree` topic already ships.

## Why this shape

The runners are already **cwd-relative** — verified: `loop --status` run through a symlink from an
unrelated repo found that repo's job dir, and the sibling `_flowlib` import resolves because CPython
realpaths `sys.path[0]`. So "make it worktree-aware" needs **no new addressing model**; it needs a
way to *pick the cwd* (`--worktree`) and a stable way to *name the executable* (the wrapper).

Rejected: `--root <path>` (session 2026-07-21 rejected it — two sources of truth for "where am I");
a gitignored symlink (doesn't travel to a fresh worktree — the exact complaint on record).

## Slices

- **1 — worktree resolution + `--worktree` in `loop`** (the example slice). `_flowlib`:
  `list_worktrees()` / `resolve_worktree(name)` + a `--test` self-test (tests.sh check 7 picks it up
  automatically). `loop` gains `--worktree NAME`, chdir + a one-line banner.
- **2 — same flag in `grind`, plus `--worktree all` / `--all`** — iterate every worktree that has a
  non-empty queue, run each in its own cwd, sequentially.
- **3 — the committed wrapper + its scaffolder.** `flow/examples/bin-loop.sh` (the template, POSIX
  sh) + a skill that writes `bin/loop` + `bin/grind` into the consumer repo. Resolution order:
  `$FLOW_RUNNER_ROOT` → `$CLAUDE_PLUGIN_ROOT` → newest `~/.claude/plugins/cache/*/optimiziramsi-skills/*/`.
- **4 — docs.** `looper` / `grind` / `collab` SKILL.md launch sections rewritten around the wrapper
  + `--worktree`; `flow/README.md`; CHANGELOG; version bump.
- **5 — confinement port (conditional).** Re-home `worktree_preflight()` + the leak-probe onto
  `flow/**`, and decide whether to inject `worktree/hooks/worktree-{write,bash}-guard.sh` instead of
  shipping a second `worktree-confine.sh`. Requires the live probe the old branch never ran.

## Progress / next slice

- Slice 1 — **in progress**.
- Open question for the human, does not block slice 1: does the wrapper scaffolder get its own skill
  or fold into `setup/skills/scaffold`?

## Notes

- The runner still refuses to run inside a Claude session (`_flowlib.nested_guard`), and the harness
  permission classifier independently refuses an unattended nested `claude -p
  --dangerously-skip-permissions`. Terminal handoff stays; only its ergonomics are in scope.
- Stable install path (verified): `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` — the
  version segment is why the wrapper must glob + version-sort rather than hardcode.
