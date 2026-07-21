# Handoff

_Last updated:_ 2026-07-18 — session 5: flow@opsi install fix, runner live-test attempt, **squash landed on `main`**. Boot with `/continue`, then `_review/REVIEW.md`.

## SQUASH ON MAIN (2026-07-18, user request) — field-testing phase begins

- User decision: land everything as **one squash commit on `main`** (`67be9bd`) so they can start
  consuming the marketplace from other projects. `git merge --squash init-marketplace` → tree
  byte-identical to the branch (verified empty diff); `./tests.sh` ALL GREEN on main; **checked out:
  `main`**, exactly 1 ahead of `origin/main` → user's push is a fast-forward. USER pushes.
- `init-marketplace` (24+1 commits) retained as build history — do not delete or rewrite.
- CLAUDE.md hard rule updated first (commit `5bf1db3` on the branch, included in the squash):
  branch-only rule retired; "user owns pushes / append-only" unchanged.
- **User will field-test on other projects and come back with reports** — expect next sessions to be
  triaging that feedback into plugin fixes. Work now happens on `main` (or short-lived branches).

## Session 5 (2026-07-18, evening) — boot verification found flow@opsi NOT loaded; fixed

- Boot check per session-4 notes: no flow skills in-session; guard canary (bash `>> .todo` redirect)
  passed through un-denied → plugin never loaded. Settings path was correct; root cause:
  `extraKnownMarketplaces`+`enabledPlugins` registered the marketplace but don't *install* the plugin.
- **Fix: `claude plugin install --scope local flow@opsi`** — now enabled (scope local) in
  `claude plugin list`. Loads at session start → **verify on next boot** (flow skills visible /
  `.todo` canary denied). This session ran unguarded; `.todo` untouched regardless.
- **Runner live-test: attempted, blocked, USER-only.** In-session run (`FLOW_ALLOW_NESTED=1`) was
  denied by the permission classifier (unattended nested `claude -p` + bypassPermissions — correctly
  refused; matches the runner's own plain-terminal design). `--dry-run`/`--status`/queue-ordering DO
  work live. Scratch repo + smoke job prepared — path & run recipe in MEMORY.md
  (`flow-runner-not-yet-live-tested`). No repo changes → nothing to commit; `./tests.sh` ALL GREEN.

## Where we left off

The `opsi` marketplace is **11 plugins · 25 skills · 9 agents · 15 hooks · 1 runner**, all committed on
branch **`init-marketplace`**, **NOT pushed** (user owns the push; they'll review first). `main`
untouched. `_review/` + `.agent/` + `.todo` gitignored. Full record: `_review/REVIEW.md`;
local-dupe removal: `_review/MIGRATION.md`. **Done-gate is now `./tests.sh`** (ALL GREEN).

## Session 4 (2026-07-18) — second sweep of source repos for generic system tools

User asked for another round: anything generic still in the sources ships here. All deferred `.todo`
builds landed; REVIEW.md's deliberate skips honored (wakeup, hub-sync, games, release, coding-style,
verify-app stay domain-locked; drift-check/auto-commit were already merged):

- **review** +`isolation-reviewer` (adversarial multi-tenant isolation) +`doc-auditor` (docs-vs-code drift).
- **flow** +`feedback` skill (`.agent/FEEDBACK.md` ledger) +`todo-readonly-guard` hook ("ALLOW TODO" arms).
- **git** +`hotfix` (git-extras kernel: test-first, cherry-pick both ways). `release` skipped (deploy machinery).
- **instructions** +`file-guard` hook (T3 surface writes → ask).
- **NEW `reporting` plugin** — lean-reporting contract enforced (reminder + pulse + Stop report-guard).
- **Root `tests.sh`** — done-gate mechanized; CLAUDE.md cites it. (Session 3, same arc: re-grounding
  fix `.agent/MEMORY.md`, `setup/scaffold-claude-md`, this repo's CLAUDE.md.)

## This session's arc (highlights)

- **flow** plugin COMPLETE (+ a from-scratch Python-3 `bin/loop`/`bin/grind` runner). Pre-publish **safety sweep** PASS.
- **worktree** skill · **patterns** plugin (registry system) · root README refreshed.
- **Cross-project discovery sweep** → built the **`caps`** hook (instructions). isolation-reviewer DEFERRED.
- **`.agent/` consolidation** (`1c90be6`): all plugin working dirs under `.agent/`; `.todo`/`.docs` stay.
- **`commit` split** (`374a583`): `git` = safety net; new `commit` plugin = format/cadence (guards split + tested).
- **`setup` plugin** (`216fd5b`): `scaffold` skill — one-time `.agent/README.md` index + entrypoint pointer.
- **Memories live in `.agent/MEMORY.md`** (in-repo, singular — matches the source layer map) — NOT
  account-level memory (the projects' principle is "project knowledge in-repo, never account memory").
  Facts there: `.todo`/no-checkbox rule, flow-runner-not-yet-live-tested, and the re-grounding result.

## Build state

11 plugins · 25 skills · 9 agents · 15 hooks · 1 runner. Committed, not pushed → not yet installable.
Content-safety: push-ready. Tree clean.

## Outstanding (see `.todo`)

- **Push `main`** (fast-forward, 1 ahead of origin) to go installable — then `_review/MIGRATION.md`;
  drop the 3 worktree guards from `~/.claude/settings.json` if enabling `worktree@opsi`. USER action.
- **Field-test reports incoming** — user is trying the marketplace on other projects; triage their
  reports into fixes when they land.
- **Live-test the flow runner** — USER action from a plain terminal (agent-side attempt blocked by the
  permission classifier, session 5). Scratch repo prepared; recipe in MEMORY.md.
- **Verify flow@opsi loaded on next boot** (installed `--scope local` in session 5; loads at session start).

## Fresh-session boot notes (session 4 closed 2026-07-18)

**`flow@opsi` is now ENABLED in this repo** (user decision) via `.claude/settings.local.json`
(gitignored, directory-marketplace pointing at this checkout) **+ a real install** (session 5:
`claude plugin install --scope local flow@opsi` — settings alone didn't load it). On boot, verify it
loaded (flow skills visible / the guard fires). Consequence once live: **`.todo` writes need the user
to arm with "ALLOW TODO"** — deferrals go to `.todo-inbox` (memory: flow-opsi-dogfooded).

User is reviewing; will push when ready. All deferred builds + both source sweeps are done — **don't
re-sweep or re-migrate** (deliberate skips: REVIEW.md + `.todo`). Likely next = review notes, push, or
live-test the runner. Run `./tests.sh` before calling anything done; `.todo` format: plain bullets,
`(done)` prefix, no checkboxes.