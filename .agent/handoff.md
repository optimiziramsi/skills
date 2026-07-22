# Handoff

_Last updated:_ 2026-07-22 — session 6: **single-plugin restructure SQUASH-LANDED on `main`**
(one commit, main exactly 1 ahead of origin/main → user's push is a fast-forward). NOT pushed
(user owns pushes). Branch `single-plugin` retained as build history (like `init-marketplace`).

## Session 6 (2026-07-22) — 11 plugins → ONE root-sourced plugin (0.0.1), renamed

User decision (update pain in field-testing): consolidate to as few plugins as possible → single
plugin, **repo root = plugin root** (mattpocock/skills layout, user-requested explicitly).
Then renamed (user): **plugin `optimiziramsi-skills`, marketplace `opsi` → `optimiziramsi`** —
install identity `optimiziramsi-skills@optimiziramsi` (mattpocock-skills@mattpocock pattern).
Rename consequence: consumers must RE-REGISTER the marketplace (registry knows it as `opsi`;
remove + add, and rename any `extraKnownMarketplaces.opsi` settings key) — step 1 in MIGRATION.md.

- `.claude-plugin/{marketplace,plugin}.json` at root; content in root `skills/ commands/ agents/
  hooks/ bin/ docs/ examples/`. All moves are 100% `git mv` renames — history preserved.
- `hooks/hooks.json` = merge of the 8 old per-plugin hook manifests, same commands/timeouts;
  brevity-reminder inject newly gated behind `REPORT_GUARD_OFF` (was the only ungated opinionated
  hook — every concern now has a kill-switch or self-gates; inventory table in README).
- Old per-plugin READMEs → `docs/<concern>.md`. Root README reworked (install = `optimiziramsi-skills@optimiziramsi`,
  concern table, kill-switch table). New root `MIGRATION.md` = consumer steps 11 → 1 (delete
  after all repos migrate). ADOPTION.md (user's field doc): only mechanically-stale bits updated
  (single install, one version, cache path `cache/optimiziramsi/optimiziramsi-skills/<ver>/`), voice untouched.
- CLAUDE.md conventions rewritten: one plugin / one concern per module; version rule now = bump
  root `.claude-plugin/plugin.json` on any shipped-content change (repo-meta exempt); lesson file
  generalized. tests.sh reworked for the layout — ALL GREEN (12 self-testing tools).
- Version starts at **0.0.1** (user: not live / not production-ready — 1.0.0 reserved for
  go-live); the whole branch is the 0.0.1 artifact (no per-commit bumps pre-release).

## Live install state discovered (machine-local, not repo)

- `.claude/settings.local.json` is GONE — user re-registered the opsi marketplace **globally from
  GitHub** (known_marketplaces: `github optimiziramsi/skills`, autoUpdate, updated 2026-07-22).
  The old directory-marketplace dogfood note in CLAUDE.md was stale; fixed (conditional wording).
- `installed_plugins.json` still carries per-project rows for the OLD 11 plugins across consumer
  repos (games, kupimkuham, …), some pinned at versions ahead of origin/main (e.g. instructions
  0.3.8 vs 0.3.6 in git) — user's field-testing state; not touched.
- flow@opsi shows disabled everywhere → todo-readonly-guard NOT live this session; `.todo`
  untouched anyway (deferrals went to `.todo-inbox`).

## Next up

1. **USER: push `main`** (fast-forward, 1 ahead of origin).
2. **After push: migrate consumer repos** per MIGRATION.md — uninstall old `<name>@opsi` rows,
   rewrite each repo's `enabledPlugins` to `"optimiziramsi-skills@optimiziramsi": true`, install for project, restart.
   Then delete MIGRATION.md.
3. **Re-dogfood here**: install `optimiziramsi-skills@optimiziramsi` in this repo (project scope) if wanted — the
   todo-readonly-guard goes live again ("ALLOW TODO" to arm).
4. Still open from before: live-test the flow runner from a plain terminal (recipe in MEMORY.md);
   worktree-aware loop/grind items sit in `.todo`.

## Standing context

- `main` == `origin/main` (verified via fetch 2026-07-22). `init-marketplace` = retained build
  history. Done-gate: `./tests.sh`. `.todo` format: plain bullets, `(done)` prefix, no checkboxes.
- Deliberate skips from the source sweeps (wakeup, hub-sync, games, release, coding-style,
  verify-app stay domain-locked) remain honored — don't re-sweep.
