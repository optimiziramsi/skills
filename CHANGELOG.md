# Changelog

`optimiziramsi-skills` — one plugin, versioned in
[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json). Any consumer-visible change bumps that
version in the same commit; Claude Code only re-materializes an installed plugin on a version
*change*, so a same-version edit never reaches consumers. `1.0.0` is reserved for go-live —
everything below `0.1.0` is field-testing.

To pick up a new version: `claude plugin marketplace update optimiziramsi` → `claude plugin update
optimiziramsi-skills@optimiziramsi` → **restart**. See [ADOPTION.md](ADOPTION.md).

## 0.0.13-dev.6 — 2026-08-19

The worktree leak-probe was scoring the wrong thing. Reported from a consumer repo, where
`loop --worktree` refused to start on one worktree while an identically-provisioned sibling ran.

- **The verdict now reads the guards' own deny output, not filesystem side-effects.** The probe
  asked a throwaway session to write a positive control inside the worktree and to escape into the
  main checkout twice, then judged by `os.path.exists()`. Two ways that lied. A tidy model deleted
  its own control file and the run died `INCONCLUSIVE` (model-dependent — hence two trees
  disagreeing on identical input). Worse, a model that simply *declined* to attempt the escape —
  the correct reading of a prompt that looks like a sandbox break, and increasingly the likely one
  — left no leak file behind and was scored `confined`, printing "confinement proven" in green on
  a transcript in which no PreToolUse hook fired at all. That inverts the probe's purpose: whether
  hooks fire under `--dangerously-skip-permissions` is precisely the open question. `confined` now
  requires each guard's deny to be **observed in the transcript**, on both channels.
- **A declining probe gets its own verdict.** `declined` ("the probe model refused to attempt the
  escape, so the guards were never exercised", naming which channel was denied and which was never
  tried) instead of the old message that sent the user off to check their CLI. `inconclusive` now
  means only what it says: the session never ran (its control was never read, or it died).
- **The positive control is written by the runner and only read by the probe**, carrying a nonce
  that is not in the prompt — so a cleanup-happy model can't delete the evidence, and finding the
  nonce in the transcript proves the session really ran inside the worktree.
- **Every refusal keeps its transcript and prints the path** (log + raw stream). Previously only a
  `leak` did, so the two verdicts you actually hit were a dead end.
- **The runners now arm the opt-in bash guard (`WORKTREE_BASH_GUARD_ENABLE=1`) for their headless
  children.** It was off, so a worktree run was guarded on the file tools while `printf x >
  ../../<main>/f` walked straight out — and the probe's own Bash step would have landed a real file
  in the main checkout. Interactive sessions are unaffected; the guard stays opt-in there.
- **The leak-probe no longer depends on a model agreeing to attempt a sandbox break.** Asking a
  session to write into the main checkout is a request a correctly-aligned model refuses — and the
  lines added to preempt that refusal were quoted back as the evidence for it ("framing designed to
  preempt refusal … that's a social-engineering pattern"). Observed compliance was 1 in 4. Worse,
  each refusal was recorded by a session-memory plugin and replayed into the *next* probe, so
  refusal got likelier the more the probe ran. The probe now asks for two ordinary writes **inside
  the worktree** and injects a witness hook that denies them: a witness deny in the transcript plus
  neither file existing proves what actually mattered — that a PreToolUse `deny` fires **and is
  honored** in a `--dangerously-skip-permissions` child. Nothing in the prompt reads as an escape,
  and the probe no longer writes into the main checkout even when it fails.
- **The guards themselves are now checked directly, against the real worktree.** Before the probe,
  both guards are fired at this checkout's actual worktree/main pair with synthetic payloads — no
  model, no tool call, deterministic — and must deny. That covers layout-specific surprises (a
  worktree nested under its own main checkout, symlinked paths) the fixture suite can't.
- **The verdicts are named for what they establish, and both non-green ones refuse.**
  `unenforced` — a denied call took effect anyway — is the dangerous answer. `unconfirmed` — the
  session made no guarded tool call — proves nothing either way, which is not proof that nothing
  is wrong, so it refuses as well; `FLOW_PROBE_LENIENT=1` downgrades it to a warning for anyone
  who accepts running unproven.
- **The probe child runs with no settings sources** (`--setting-sources ""`), so no project or
  plugin `SessionStart` hook injects third-party context into it — the mechanism behind the
  self-poisoning loop above. Real jobs keep the project's settings; only the probe is isolated.
- **A `loop` run no longer blocks every later `grind` in the same tree.** grind's dirty-tree gate
  exempted runner-owned files only inside the *mission's* directory, so the structurally identical
  files loop writes into `.agent/loop/` — `runner_*.log`, per-job `.log` — counted as work in
  progress: grind refused to start, and (via the same predicate) scored every iteration
  unproductive. The exemption is now a property of the file's own directory, so each runner reads
  the other's bookkeeping as bookkeeping. A wholly-untracked job dir, which git reports as one
  collapsed entry, counts too.
- **Each runner commits the session logs it wrote, at the end of its run.** They were designed to
  be kept (only `*.jsonl` and grind's transient state are gitignored) but nothing ever committed
  them, so every run ended by handing the tree to the user dirty — leaving "commit runner logs as
  if they were work" or "gitignore them and lose the evidence" as the only outs. The commit is
  path-limited to that runner's own job dir, never touches a child's work or anything else staged,
  and is best-effort (a git failure is reported, never fatal). `FLOW_NO_LOG_COMMIT=1` opts out.
- **`worktree-bash-guard` no longer reads a trailing redirect as a destination.** For the verbs
  whose last positional argument is what gets written (`cp`, `mv`, `tee`, `install`, `rsync`,
  `sed -i`), `shlex` keeps a glued `2>/dev/null` as a single token, so it took that slot — and once
  a `cd` had moved the shell into the main checkout it resolved there, denying
  `cp x.log /tmp/dest/ 2>/dev/null` on a destination of `<main>/2>/dev/null` while the real one was
  never examined. Redirect tokens (and the target of a bare `>`) are now dropped before the last
  positional is taken. Suite: 48 → 52 cases.

## 0.0.12 — 2026-08-19

Two fixes to things that fail silently: a guard that blocked commands it should not have, and an
authoring rule that nothing enforced.

- **`todo-readonly-guard` no longer reads prose as a write.** Its verb rules (`mv`/`cp`/`rm`/
  `truncate`/`install`, `sed -i`/`perl -i`) matched anywhere in a Bash command, and the gap
  between verb and target could span newlines — so a heredoc whose *text* said "install for
  project" and, twelve lines later, "stale `.todo` item" was denied as a write to `.todo`. Verbs
  now count only at the start of a command segment (past any `VAR=x` prefix), and no rule pairs a
  verb on one line with a target on another. The same pass closed the opposite hole: the trailing
  boundary `(["'\s]|$)` missed every target followed by punctuation, so `(rm .todo)` and
  `rm .todo; echo x` were silently *allowed*. Now a `(?![\w.-])` lookahead, which still refuses
  `.todos`, `.todo.bak`, and `.todo-inbox`. Suite: 26 → 33 cases.
- **`ADOPTION.md` refreshed for the two-branch split**, re-verified against CCD/CC 2.1.235. New:
  what `main` actually contains and that your marketplace clone is shallow and main-only, so
  `develop` is never fetched; how to point the one registration at a local checkout instead of
  GitHub (and that the two are mutually exclusive, since marketplaces are keyed by name); that
  `claude plugin marketplace remove` drops the install records of every plugin from that
  marketplace, in every scope and repo, and re-adding restores none of them; and that a directory
  source has no clone to refresh — its install cache is still a version-keyed copy, so a bump plus
  `claude plugin update` plus a restart is the only path from an edit to a bind.

## 0.0.11 — 2026-08-19

The published tree is now the plugin and nothing else. `main` carries `.claude-plugin/`, the topic
folders, `lib/`, `other/`, and the public docs; the working repo — `.agent/`, `.todo`,
`.todo-inbox`, `CLAUDE.md`, `.claude/`, `tests.sh` — lives on `develop` and stops here.

- **Why it mattered.** You do not just browse this repo, you get a copy of it: installing the
  marketplace clones it to `~/.claude/plugins/marketplaces/optimiziramsi`, and installing the
  plugin copies the tree again to `~/.claude/plugins/cache/.../<version>/`. Both used to carry this
  repo's own workbench, so a file could plausibly be read as plugin payload, as the maintainer's
  live config, or as an example of what your repo should look like — three shapes, one directory.
  Now there is one shape.
- **Nothing moved inside the plugin.** Every skill, command, agent, hook, and `bin/` script is
  byte-identical to 0.0.10 and lives at the same path; `instructions/examples/` is still shipped
  payload the meta-lint and tripwire engines reference. Update as usual — nothing to re-wire.
- **How it's produced.** A filtered tree-copy, not a merge: each release builds one commit whose
  tree is `develop` minus the development-only paths, then fast-forwards `main` onto it. History is
  preserved on both branches, and a release can never conflict with the working tree.

## 0.0.10 — 2026-07-29

Doc-only. The `worktree` skill listed a guard bug that no longer exists, and told the agent to get
around it by switching channels — advice 0.0.9 turned into a bypass of the guard it had just
hardened.

- **Dropped the fourth "Known failure mode".** It claimed the write-guard false-positives on the
  worktree's *own* nested `.claude/**`. It doesn't, and hasn't since 0.0.6 rewrote the guard to
  test "inside the worktree" **before** "inside the main checkout" — re-verified here across both
  layouts (sibling and the nested `.claude/worktrees/<name>` one) down to
  `<wt>/.claude/worktrees/inner/x.md`; every in-worktree path is allowed and every main-rooted one
  still denied. The other three failure modes were correct and are untouched.
- **Its workaround was the real damage.** "Work around it with an in-worktree relative Bash/Python
  write, not an absolute-path tool write" was written when the shell channel was unguarded. After
  0.0.9 it read as *route around `worktree-bash-guard`* — directly against § Path discipline three
  lines above it. Replaced with the opposite instruction: **verify, never route around** — a guard
  denial is a real escape, so re-issue the path instead of switching channels.
- **What replaces it is attributed to the host, not the guard:** a nested `.claude/**` target
  occasionally mis-canonicalized by Claude Code's own path resolver (reported from a consumer repo
  2026-07-29; not reproducible against these guards). The remedy is a `git -C <worktree> status`
  check that the write landed, not a different write channel.

## 0.0.9 — 2026-07-29

`worktree-bash-guard` resolves paths instead of grepping for them — it was blind to every
relative escape.

- **The guard could be walked around with `cd`.** It asked whether the main checkout's absolute
  path appeared as a substring of the command text, so anything that never *spelled* that path was
  invisible: `cd ../../.. && echo x > ./LEAK.md` wrote into the main checkout and the guard said
  nothing. Found by a live worktree session on a consumer repo (2026-07-29), then reproduced four
  ways — chained `cd` hops, a bare `../../../LEAK.md`, a subshell, `tee`/`dd of=` through a
  relative path — all previously allowed, while only the absolute-path form was blocked.
  It now walks the command's segments, tracks the cwd across `cd`, resolves each write target
  against it, and compares resolved paths. An interpreter write it cannot resolve (`python3 -c`)
  is judged by where the shell is standing, so `cd <out> && python3 -c "open('x','w')"` is caught
  too. Subshell scoping is deliberately not modelled — over-blocking is recoverable (name the
  worktree path, or use the kill-switch); a missed escape is not.
  **Still not containment.** It is a best-effort resolver, not a shell: `eval`, a variable holding
  the path, or a command substitution all defeat it. The Write-tool guard remains the real
  boundary, and this stays opt-in.
- **The resolver starts from the session's cwd, not the worktree root.** Relative hops are counted
  from wherever the shell is standing, and the Bash tool's cwd persists across calls — so a session
  sitting in a subdirectory made the old start point off by one hop per level: it let a real escape
  through (`<wt>/src` + `> ../../../../LEAK.md`) and denied writes that never left the worktree
  (`<wt>/src` + `> ../f.ts`, in the nested layout). The payload's `cwd` is now the origin.
- 20 tests for the escapes, computed from the fixture rather than hardcoded so they hold for a
  sibling worktree AND the nested `.claude/worktrees/<name>` layout the skill actually uses, with
  the worktree root and a subdirectory each exercised as the session cwd.
- **`worktree` skill § Path discipline was stale** — it said "Bash redirects aren't probed", true
  only before this guard shipped. It now states what each guard actually covers and keeps the
  standing instruction: write as if neither existed.

## 0.0.8 — 2026-07-29

**Project tripwires are no longer bash-only.** `tripwire-guard` discovered `.agent/guards.d/*.sh`
and ran each under `bash` — so a repo that speaks python (or node, or ruby) still had to write its
guards in shell. This plugin's own hooks being python3 is *its* implementation choice; it was
never meant to reach into consumer repos, and neither is bash.

- **Discovery + launch are now language-agnostic.** `*.sh` → `bash`, `*.py` → `python3` (neither
  needs the executable bit, so existing guards are unaffected), and any other file with `+x` runs
  directly via its own shebang. Files that are neither — a README, a config, a guard you disabled
  by dropping its `+x` — are ignored instead of being fed to `bash`.
- **A guard that cannot be launched now warns** (bad shebang, lost `+x`) instead of failing
  silently, matching how a crashing guard already behaved: loud, non-blocking, never a session
  brick.
- The three shipped `examples/guards.d/*.sh` stay bash — they are mostly `git` plumbing, which is
  what bash is good at. They are examples, not the contract.

## 0.0.7 — 2026-07-29

The launcher stops being a file in your repo. It is now your own symlink, and the old short brand
name is retired in favour of `optimiziramsi`.

- **`bin/loop` + `bin/grind` (committed wrappers) → `.agent/bin/loop` + `.agent/bin/grind`
  (gitignored symlinks).** The committed wrapper put a launcher for *your* machine into *everyone's*
  repo and made every consumer carry a 29-line script whose only job was to find the plugin. The
  links are machine-local, made on request by `scaffold` / `looper` / `grind`, and live under
  `.agent/` with everything else the toolkit creates. **Migration:** delete `bin/loop` +
  `bin/grind`, add `.agent/bin/` to `.gitignore`, and let a skill (or the recipe in
  [`flow/README.md`](flow/README.md)) make the links.
- **New hook `runner-link` (SessionStart) answers "which version do the links run?"** They point
  through one stable per-machine path — `<claude-config>/plugins/data/optimiziramsi-skills/current`
  — that the hook re-stamps at every session start to the plugin version *actually loaded* (it reads
  its own location, the one answer that cannot be stale). It deliberately does **not** use
  `${CLAUDE_PLUGIN_DATA}`: that dir's name carries the install identity
  (`optimiziramsi-skills-<marketplace>`), and a pointer every repo hardcodes must be one address for
  all install shapes. So a plugin update moves every repo's links at
  once, nothing on disk encodes a version, and there is no launcher copy left to go stale. The hook
  **creates nothing** and refuses to touch a real file; it only re-aims existing symlinks. Off:
  `FLOW_LINK_OFF=1`.
- **`flow/examples/runner-wrapper.sh` is deleted**, its test replaced by
  `flow/tests/test_runner_link.py` — which executes a runner through the full two-hop link, pinning
  the assumption the design rests on (CPython resolves `sys.path[0]` through symlinks, so the
  sibling `_flowlib` import survives).
- **The old four-letter brand name is gone from the repo.** It collides with an unrelated GitHub
  account, so the only names used anywhere are `optimiziramsi-skills` (plugin) and `optimiziramsi`
  (marketplace, after the domain optimiziram.si) — in prose, paths, identifiers, the scaffold
  trigger phrase, the topic-README bylines, and the temp-marker prefix in `lib/hookio.py`.

## 0.0.6 — 2026-07-28

A slimming pass over the shipped scripts. No behavior removed except one guard-of-a-guard that
could not fire; everything else is the same rules with less scaffolding and far more tests.

- **Every hook is python3 now, over a shared [`lib/hookio.py`](lib/hookio.py) — and `jq` is gone.**
  Ten hooks were bash+`jq`, and five of them shipped a `"⚠️ DISARMED — jq not found"` path: on any
  host without `jq` those guards silently switched themselves **off**. `python3` is the one
  interpreter a Claude Code host already needs, so the guards can no longer disarm. The duplicated
  plumbing each of them re-derived — read the payload, find the tool's file paths, resolve the
  worktree roots, emit a deny/ask/notice verdict, nag once per state, skip read-only sessions —
  now lives once in `hookio`. Worst offender retired: `todo-readonly-guard`'s write-detector was a
  single line of nested shell quoting; it is five named regex alternatives you can edit.
- **Tests moved out of the shipped files into `<topic>/tests/`, and the gate actually runs them.**
  A guard should read as its decision, not as its test suite (`git-guard.py` was 237 lines of test
  against 258 of logic). `tests.sh` gained check 7a for `*/tests/*.py`; its old glob never reached
  `instructions/examples/guards.d/*.sh`, so **17 tests had never once executed**.
- **First tests for `bin/loop`, `bin/grind`, the wrapper template, and `contract-pulse`** — the
  three largest shipped programs and the file every consumer copies had none. 55 cases drive the
  runners' real control flow (dependency ordering, crash-resume, the productivity gate, the retry
  ladder, the dirty-tree guard, transient backoff) against a stubbed CLI. Suite: 78 → 438 tests.
- **The wrapper's version lock is removed; `flow/examples/runner-wrapper.sh` is 95 → 29 lines.**
  It guarded a scenario the design cannot produce: the wrapper contributes no flags of its own, it
  `exec`s with `"$@"` verbatim, so a "stale wrapper passing a renamed flag" cannot happen — the
  lock only ever fired as a false alarm after a plugin update. Gone with it: `WRAPPER_VERSION`,
  `FLOW_WRAPPER_ALLOW_DRIFT`, `tests.sh` check 8, and the rule that a plugin bump means re-copying
  the wrapper. **Consumers should refresh `bin/loop` + `bin/grind` once**, then never again.
- **One real bug:** `commit-nudge`'s `COMMIT_NUDGE_EXTRA_DIRS` resolved relative sibling paths
  against the process cwd rather than the project dir, so `../gitops` pointed somewhere else
  depending on where the hook ran. Also: docstrings in `git-guard` and `meta-lint` that restated
  their READMEs are now pointers, and `meta-lint`'s stale `caps.sh` references are corrected.

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
(`optimiziramsi-skills`), and the marketplace was renamed to `optimiziramsi` — so the install
identity is `optimiziramsi-skills@optimiziramsi`.

Because the *marketplace* name changed, consumers of the old 11-plugin layout could not simply
update — they had to re-register the marketplace under its new name, drop the old per-topic
installs, and install the single plugin. (The step-by-step `MIGRATION.md` was removed in 0.0.3,
once every repo had migrated.) Per-project tailoring moved from plugin selection to env
kill-switches.
