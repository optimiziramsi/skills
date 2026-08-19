# Agent memory — optimiziramsi-skills marketplace

Durable facts, decisions, and gotchas for this repo. **This repo's own working memory**, not the
account/plugin memory store. One dated section per fact; delete what turns out wrong; keep volatile
"now/next" in [handoff.md](./handoff.md).

Convention note: the source projects name this file `.agent/MEMORY.md` (singular) and **commit** it
(portable memory). This repo does the same — `.agent/` is tracked like an ordinary project (only
runner scratch, machine-local settings, and OS junk stay gitignored), so this durable memory travels
with the repo.

Precedence on conflict (source `rules/sessions.md`): the user's live word > repo docs > this file /
handoff > auto-injected session memory (claude-mem observations). Injected memory records the PAST and
may predate a pivot — when it contradicts a repo file, the repo file wins.

---

## Conventions re-grounded against source — verified 2026-07-13

Re-read the source projects (`gitlab.com/{optimiziramsi,opsi-infra}/*`) after the maintainer flagged
that a prior session reconstructed conventions from memory instead of re-reading them. Result:

- **Shipped plugins are faithful.** Every `MEMOR` reference in `plugins/` points at `.agent/MEMORY.md`
  or the "in-repo, never account memory" principle. `triage-todo` correctly treats `.todo` as
  user-owned / LLM-readonly with a gated allow-phrase. No propagated drift found.
- **Canonical durable-memory file = `.agent/MEMORY.md` (singular)** — confirmed in kupimkuham's file,
  its `.claude/README.md` layer map, and `rules/sessions.md`. The prior session's `.agent/MEMORIES.md`
  (plural) was an unverified guess; renamed to match.
- **Two valid source memory models:** kupimkuham = single dated `.agent/MEMORY.md` merged via `/retro`;
  rabbit-run = `.agent/lessons/` (one file per lesson, indexed). This repo's *shipped* `instructions`
  plugin ships the `lessons/` model; this repo's *own* memory uses the single-file model (2 facts).
- **`.todo` is user-owned in source** (kupimkuham: never edit → `FEEDBACK.md`; rabbit-run: gated
  "ALLOW TODO"). This repo's agent-maintained `.todo` with `(done)` markers is a deliberate local
  choice the user established (below), not drift.

## `.todo` format — no checkboxes, `(done)` prefix (2026-07-13, user)

Never use `[ ]`/`[x]`/`[~]` checkbox syntax for status, anywhere — empty brackets make noisy/ambiguous
git diffs and LLMs mangle them.

- **`.todo` (this repo):** plain `- ...` bullets only — no checkboxes, no group headings, no status
  tags. Done → prepend `(done)` (`- (done) ...`); leave in place and remove done items only once the
  user confirms cleanup. (This repo opts into an agent-maintained `.todo`; consumer projects keep
  `.todo` user-owned per the shipped skills.)
- **Other status** (plans, milestones, job files): prose ("Step 1 — done (commit abc)") or a `status:`
  field — never brackets. This toolkit already complies.

## Single-plugin restructure — repo root IS the plugin (2026-07-22, user)

Naming (user, same session): plugin **`optimiziramsi-skills`**, marketplace renamed to
**`optimiziramsi`** → install identity `optimiziramsi-skills@optimiziramsi` (the
mattpocock-skills@mattpocock pattern).

**The old four-letter brand name is retired everywhere (2026-07-29, user)** — reversing the
earlier "keep it as the informal brand" call. Reason: an unrelated GitHub account holds that name,
so it reads as someone else's. Prose, paths, identifiers and history all say `optimiziramsi-skills`
/ `optimiziramsi` (after the domain optimiziram.si). The only surviving spellings are external
facts we don't own: the `opsi-infra` GitLab group and stale on-disk cache dirs.

Because the MARKETPLACE name changed, consumers can't just update: remove the old registration,
re-add (manifest resolves the new name), rename the `extraKnownMarketplaces` settings key —
MIGRATION.md step 1.

11 plugins consolidated into ONE plugin at **0.0.1** (user: not live / not production-ready —
1.0.0 is reserved for go-live), repo root = plugin root (user asked explicitly — update pain
across 11 versions/installs in field-testing). Version rule: any shipped-content change bumps the
single root `.claude-plugin/plugin.json` (repo-meta exempt). Per-project tailoring = env
kill-switches (README table), not plugin selection. Built on branch `single-plugin` (2026-07-22).
Consumer migration is DONE — root `MIGRATION.md` deleted 2026-07-28 (0.0.3); the gist survives in
CHANGELOG.md's 0.0.1 entry.

## Topic-first layout (2026-07-28, user, → 0.0.2)

Reorganized the single plugin **topic-first**: one `<topic>/` folder per concern (git, commit,
flow, …), each owning its own `skills/ commands/ agents/ hooks/` (+ `bin/ examples/ README.md`).
Motive: legibility — see/update/replace a whole topic in one place. `plugin.json` declares
component paths (arrays REPLACE the default top-level dirs), so the type dirs need not sit at the
repo root. **Gotchas proven via `claude plugin validate .` (it works — use it as a second gate):**
`skills`/`commands` accept per-topic DIRECTORIES; **`agents` needs explicit `.md` FILE paths (dirs
are rejected)**; `hooks` takes an array of per-topic `hooks.json` that merge. Skill/command/agent
invocation names come from frontmatter/filename, NOT the folder → grouping is organizational only,
no `<topic>:` prefix, no consumer-visible rename. Adding/removing a topic = touch its folder AND
its plugin.json path entries (tests.sh checks both). `bin` scripts that import a sibling (loop/grind
→ `_flowlib`, pattern-guards → generate-pattern-routes) rely on `__file__`-relative paths, so keep
importers and their helpers in the SAME topic dir.

## Dogfood state — settings.local.json REMOVED by user (observed 2026-07-22)

The 2026-07-18 directory-marketplace dogfood (`.claude/settings.local.json` + `claude plugin
install --scope local flow@<old-marketplace>`) is **gone**: the file no longer exists; the marketplace is
now registered **globally from GitHub** (`known_marketplaces.json`: github optimiziramsi/skills,
autoUpdate). `claude plugin list` shows the old per-plugin installs as project-scoped rows across
consumer repos, all disabled for this checkout → **todo-readonly-guard is NOT live here right
now**; `.todo` stays user-owned by convention regardless (deferrals → `.todo-inbox`). Re-dogfood
after the merge: install `optimiziramsi-skills@optimiziramsi` at project scope here. (Still true: settings alone
install nothing — an install record + restart binds; plugins load at session start.)

## Flow runner not yet live-tested (2026-07-13; USER-only, confirmed 2026-07-18)

`bin/{loop,grind}` (pre-consolidation: `plugins/flow/bin/`) were built + tested with a FAKE `CLAUDE_BIN`, never against a real
`claude -p`. Session 5 attempt from inside a session (`FLOW_ALLOW_NESTED=1`) was **blocked by the
permission classifier** — spawning an unattended nested `claude -p` is not something the agent can
(or should) do. It must be run by the USER from a plain terminal; `--dry-run`/`--status`/queue
detection verified live and work. A scratch repo + smoke job can be prepared under the session
scratchpad (any empty git repo works; the smoke-job recipe is in the looper skill's "First run"
section).
Run: `cd <scratch> && python3 <repo>/flow/bin/loop --model sonnet` → type `yes`. Confirm:
SMOKE.txt says "ok", job-status flipped to done, ## Report filled, new commit in `git log`.
Remove this note once the live test passes.

## Public `main` / working `develop` — filtered tree-copy release (2026-08-19, user)

`main` is the **published plugin only**; `develop` is the working repo. Reason is legibility, not
secrecy: a visitor (and every consumer's plugin cache) could not tell plugin content from this
repo's own workbench, and some files existed in three near-identical forms (shipped payload,
this repo's live copy, an example for a consumer repo).

Load-bearing facts behind the design:

- **A consumer's marketplace clone is SHALLOW and main-only** — `~/.claude/plugins/marketplaces/<name>/.git`
  carries a `shallow` file and the refspec `+refs/heads/main:refs/remotes/origin/main`.
  `develop` never reaches anyone. This is why a private repo was rejected as unnecessary.
- **Consumers get the tree twice**: that clone *plus* a per-version copy at
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Before the split both carried
  `.agent/`, `.todo`, `.todo-inbox`, `CLAUDE.md`, `.claude/settings.json`.
- **Directory-sourced marketplaces are not special**: the plugin still materializes into the same
  version-keyed cache dir as a github source (verified byte-identical for `opsi-infra/platform`
  0.1.0 — a copy, not a symlink). So "a local path is always fresh" is **unproven**; iterate on a
  `0.0.N-dev.M` series, which `release.sh` refuses to release.
- **Marketplaces are keyed by NAME globally** (`known_marketplaces.json`) — there is exactly one
  `optimiziramsi`. It is registered from **this checkout's path** (2026-08-19, user), so the
  branch checked out here is what every project on this machine loads: `main` = production,
  `develop`/feature = field-testing, for as long as it stays checked out. Consequence: `develop`'s
  version must never equal `main`'s or the switch is invisible — hence the `-dev` series, which
  `release.sh` opens after every release and refuses to publish.

Decisions: `main` stays GitHub's default branch (the `github` source resolves the default branch).
History is kept on both sides — no orphan restart. Hotfixes are ordinary releases; no cherry-pick
path back from `main`. No separate examples repo — `scaffold-claude-md` / `scaffold` already
generate the example, and a checked-in copy would become the third drifting version of it.
`instructions/examples/` stays on `main`: it is shipped payload the meta-lint and tripwire engines
reference, not a showcase. `other/` stays public by user call.

Machinery: [`release.sh`](../release.sh) (filtered tree-copy → FF land → tag, no remote),
[`.claude/skills/release/`](../.claude/skills/release/SKILL.md) (the protocol),
[`dev-marketplace.md`](./dev-marketplace.md) (test unreleased code in other repos).
