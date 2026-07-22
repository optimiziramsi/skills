# Migrating: 11 plugins → the single `optimiziramsi-skills` plugin (0.0.1)

The old 11-plugin marketplace (then named `opsi`) shipped 11 separate plugins (`git@opsi`,
`commit@opsi`, …). From 0.0.1 the repo root is ONE plugin, `optimiziramsi-skills@optimiziramsi`
— same skills, commands, agents, and hooks, one version, and the **marketplace itself is renamed
`opsi` → `optimiziramsi`**. The old plugin names no longer exist in the marketplace, so old
installs go stale (they keep their materialized cache but never update again).

Once, machine-wide:

1. **Re-register the marketplace under its new name** — the registry knows this repo as `opsi`;
   the manifest now says `optimiziramsi`, so update-in-place can't be trusted across the rename:
   `claude plugin marketplace remove opsi`, then `claude plugin marketplace add
   optimiziramsi/skills` (name resolves from the manifest → `optimiziramsi`). If the old
   registration came from an `extraKnownMarketplaces.opsi` settings block, rename that key to
   `optimiziramsi` (README snippet) — a leftover `opsi` key just re-registers the old name.

Then per consumer repo:

2. **Remove the old installs** — for each enabled `<name>@opsi`: uninstall via `/plugin` (or CCD
   plugin page), with the right project selected for `project`-scoped rows.
3. **Rewrite the repo's `.claude/settings.json`** — replace the whole `enabledPlugins` block with
   `"optimiziramsi-skills@optimiziramsi": true`.
4. **Install** `optimiziramsi-skills@optimiziramsi` — "Install for project (shared)" in CCD, or
   `/plugin` in a terminal `claude`.
5. **Restart, then verify the bind** — the toolkit's hooks fire (e.g. git-guard blocks
   `git push`), skills resolve, `/plugin` lists `optimiziramsi-skills@optimiziramsi` enabled.

What changes and what doesn't:

- **Nothing behavioral** — hooks, commands, timeouts, and skills are byte-identical at 0.0.1; only
  packaging moved. `${CLAUDE_PLUGIN_ROOT}` now resolves to the repo root copy
  (`~/.claude/plugins/cache/optimiziramsi/optimiziramsi-skills/<ver>/`).
- **Selective enablement → env switches.** Projects that enabled a subset of plugins now enable
  `optimiziramsi-skills@optimiziramsi` and switch concerns off in `.claude/settings.json` `env` — see the kill-switch
  table in [README.md](README.md). All existing `GIT_GUARD_*`, `COMMIT_NUDGE_*`, `REPORT_*`,
  `TODO_GUARD_*`, `PATTERN_*` env config keeps working unchanged.
- **One version to chase.** Author bumps `.claude-plugin/plugin.json`; consumer chain stays
  bump → marketplace update → plugin update → restart ([ADOPTION.md](ADOPTION.md)).

Delete this file once every consumer repo has migrated.
