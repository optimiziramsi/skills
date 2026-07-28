# Changelog

`optimiziramsi-skills` — one plugin, versioned in
[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json). Any consumer-visible change bumps that
version in the same commit; Claude Code only re-materializes an installed plugin on a version
*change*, so a same-version edit never reaches consumers. `1.0.0` is reserved for go-live —
everything below `0.1.0` is field-testing.

To pick up a new version: `claude plugin marketplace update optimiziramsi` → `claude plugin update
optimiziramsi-skills@optimiziramsi` → **restart**. See [ADOPTION.md](ADOPTION.md).

## 0.0.5 — 2026-07-28

The flow runners can be pointed at a worktree instead of being `cd`-ed into one.

- **`loop --worktree NAME`** — resolve a worktree by branch, directory name, path, a unique
  substring of either, or `root` for the main checkout, then run there. The runners were always
  cwd-relative (job dir, the repo they commit into, worktree-confinement detection), so selecting a
  worktree is only ever picking the cwd: the flag chdirs before anything reads the filesystem and
  nothing downstream changes. An ambiguous name is an error listing the candidates, never a guess.
- **`grind --worktree NAME`** — the same flag, same resolver.
- **`loop --worktree all`** — surveys every worktree, lists the ones with pending jobs, arms once,
  then runs a child runner per tree (a child rather than a chdir loop: own cwd, own preflight, own
  crash blast radius). Composes with `--status` / `--dry-run`; refused with `--watch`, which would
  park on the first tree forever.
- **Committed `bin/loop` + `bin/grind` wrappers** — new template
  [`flow/examples/runner-wrapper.sh`](flow/examples/runner-wrapper.sh), installed by the `scaffold`
  skill. It resolves the runner at run time (`$FLOW_RUNNER_ROOT` → `$CLAUDE_PLUGIN_ROOT` → newest
  copy in the plugin cache), so it holds no machine path and can be **tracked** — which means it
  exists in every worktree by construction and survives plugin updates. The old advice (symlink
  into the versioned cache) does none of the three. One template, two identical copies: it
  dispatches on its own filename. **Version-locked:** the wrapper is stamped with the plugin
  version it came from and refuses to run against a different one, printing the refresh command —
  a stale wrapper passing flags a newer runner renamed is the drift the lock exists to catch
  (`FLOW_WRAPPER_ALLOW_DRIFT=1` overrides). `tests.sh` check 8 keeps the stamp honest.
- **Worktree runs are confined, and the confinement is proven before anything runs.** In a linked
  worktree both runners now inject the `worktree` topic's PreToolUse guards into every headless
  child (`--settings`), then spend one throwaway session on a **leak-probe** that tries to write
  into the main checkout by both the Write tool and a bash redirect — and **refuse to start**
  unless both are blocked. Main-checkout runs are byte-identical to before. `FLOW_WORKTREE_UNSAFE=1`
  skips it; `FLOW_PROBE_MODEL` picks the probe model (default sonnet). The guards are the
  `worktree` topic's own, not a second copy — one implementation, one self-test.
  *Still unverified against a real CLI:* whether PreToolUse hooks fire at all under
  `--dangerously-skip-permissions`. The probe is exactly that question asked at runtime — a `leak`
  verdict is the answer, and it aborts rather than risking the main checkout.
- `_flowlib.py --test` is new and runs in the repo done-gate (25 cases over a real throwaway repo
  with two worktrees, including all three probe verdicts against a stubbed CLI).

## 0.0.4 — 2026-07-28

Single-branch repos can land worktree work; the guard stops taxing every Bash call.

- **`GIT_GUARD_INTEGRATION_BRANCH`** — names the one branch day-to-day work lands into. Only
  load-bearing where that branch is *also* protected (a GitHub-flow repo whose `main` is both
  production and the base worktrees are cut from): there the protected-branch rule was blocking
  the `worktree` protocol's own `git push . HEAD:<integration>`, so no slice could ever land. The
  flag permits exactly that fast-forward land — force (`+HEAD:main`), delete (`:main`,
  `--delete main`), and `checkout`/`switch` onto the branch all stay blocked, as does a land into
  any *other* protected branch. Two-tier (`main` + `develop`) repos leave it unset.
- **~29 ms shaved off every Bash tool call.** Default-branch detection shells out to `git`, and
  `check()` was resolving it before it knew the command was even git-related — `ls -la` paid for
  up to five subprocesses. It is now reached lazily by the two rules that need it, and memoized
  per cwd.
- Fixed the detection order stated in `git-guard`'s module docstring (it listed
  `init.defaultBranch` before the first-existing-branch probe; the code does the reverse), and
  pinned `GIT_CEILING_DIRECTORIES` in the detection self-test so the "not a repo" case can't be
  fooled by a `$TMPDIR` that happens to sit inside a git repo.
- This repo now ships a tracked `.claude/settings.json` declaring its own
  `GIT_GUARD_PROTECTED_BRANCH` / `GIT_GUARD_INTEGRATION_BRANCH` (both `main`) — dogfooding the
  single-branch case.
- **The `worktree` protocol's landing wiring changed.** It used to say "keep the main repo on
  `<integration>`" — which makes the human's own checkout the thing that must stay clean, so their
  branch switches and uncommitted work break every worker's land. It now pins `<integration>` in a
  dedicated `.claude/worktrees/_integration` worktree that nobody edits: clean by construction, so
  lands are always accepted; it locks `<integration>` against accidental checkout elsewhere; and
  the human's checkout is free to sit on any branch in any state. `receive.denyCurrentBranch=
  updateInstead` must be **repo-level** — a `--worktree`-scoped value is ignored by `receive-pack`.
  The skill also now reads `<integration>` / `<protected>` from the settings `env` instead of
  guessing, skips the HARD GATE's fork-point compare when the two are the same branch, and checks
  the landing wiring up front rather than discovering it at push time.

## 0.0.3 — 2026-07-28

Publishing readiness, plus the end of the `main` assumption.

- **No branch name is hardcoded any more.** `git-guard` now *detects* the repo's default branch
  (origin's `HEAD` symref → first existing of `main`/`master`/`develop`/`trunk` → repo-local
  `init.defaultBranch`; never the machine-global one) instead of defaulting to `main`, so a
  `develop`- or `trunk`-based project protects the right branch with no config.
  `GIT_GUARD_PROTECTED_BRANCH` still overrides — set it when the protected branch is *not* the
  default (e.g. `main` protected while work lands on `develop`); an empty string protects nothing.
- **`scaffold-claude-md` reads the branch layout before writing a rule about it.** Its template
  used to hardcode "don't commit on `main` — work on `develop`"; it now carries `<protected>` /
  `<integration>` placeholders and a probe-then-confirm step, and points at
  `GIT_GUARD_PROTECTED_BRANCH` when the two differ.
- **Commands no longer suppress their skill's triggering.** Inside a plugin, a command shadows the
  same-named skill in the model's listing, so the terse `(runs the X skill)` wrapper line — not the
  skill's rich description — was what drove auto-invocation, throwing away every trigger phrase the
  SKILL.md defined. All 25 commands now carry `disable-model-invocation: true`, which keeps the
  command out of the model's context (it stays typeable as `/x`) and lets the skill's own
  description do the triggering. The commands stay thin aliases — nothing is duplicated.
- `MIGRATION.md` removed — every consumer repo has migrated off the 11-plugin layout.

Naming is unchanged: components appear as `optimiziramsi-skills:<name>` in menus and autocomplete,
and the bare `/<name>` invokes them too (CC ≥ 2.1.216) — the prefix is a display label, not a
required form.

- **Manifests** carry the metadata the `/plugin` browser shows: `displayName`, `homepage`,
  `repository`, plus author URL — in both `plugin.json` and the marketplace entry (which also
  gained `author`, `license`, `keywords`).
- **Every hook now has a switch.** `session-start` gained `SESSION_START_OFF=1` (its state line
  fired in *any* git repo with no way off); `worktree-detect` now honors `WORKTREE_GUARD_DISABLE=1`.
- **Three hooks gained self-tests** — `session-start`, `worktree-detect`, `worktree-bash-guard`
  (previously the only registered hooks with no `--test`).
- **`worktree-bash-guard` detection fix:** the write-verb pattern required leading whitespace, so a
  command *starting* with `sed -i` / `tee` / `dd` / `install` slipped through. Now anchored.
- **Done-gate extended** (`./tests.sh`): every `${CLAUDE_PLUGIN_ROOT}` hook target must exist, every
  `/command` must have its same-named skill and every skill's frontmatter `name` must match its
  directory, and `claude plugin validate . --strict` runs when the CLI is present.
- **Docs:** README leads with the `claude plugin marketplace add` / `install` path; the
  kill-switch table is complete and every entry verified against its implementation; fixed the
  `flow` runner symlink instructions and the `meta-lint` path (both stale since the topic-first
  move).

## 0.0.2 — 2026-07-28

**Topic-first layout.** One `<topic>/` folder per concern (`git/ commit/ flow/ …`), each owning its
own `skills/ commands/ agents/ hooks/` (+ `bin/ examples/ README.md`). `plugin.json` declares the
component paths, so the type dirs no longer sit at the repo root.

Invocation names come from frontmatter/filename, never the folder — **no consumer-visible rename**,
no `<topic>:` prefix, behavior byte-identical to 0.0.1. Per-topic `docs/<t>.md` became
`<topic>/README.md`.

## 0.0.1 — 2026-07-22

**Eleven plugins consolidated into one.** The repo root *is* the plugin
(`optimiziramsi-skills`), and the marketplace was renamed `opsi` → `optimiziramsi` — so the install
identity is `optimiziramsi-skills@optimiziramsi`.

Because the *marketplace* name changed, consumers of the old 11-plugin layout could not simply
update — they had to re-register the marketplace under its new name, drop the `<name>@opsi`
installs, and install the single plugin. (The step-by-step `MIGRATION.md` was removed in 0.0.3,
once every repo had migrated.) Per-project tailoring moved from plugin selection to env
kill-switches.
