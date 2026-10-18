# Adopting the `optimiziramsi` plugins into an existing repo

How to enable the plugins in a project, plus the non-obvious gotchas — distilled from a real
adoption (2026-07, CCD 2.1.215). History: an 11-plugin marketplace, consolidated in 2026-07
(0.0.1) into the single `optimiziramsi-skills@optimiziramsi` plugin, split again in 2026-10
(0.1.0) into one plugin per concern so each project enables only what suits it. Goal: the plugins
own the generic system, the repo keeps only what is repo-specific, zero overlap.

## Migrating from the single `optimiziramsi-skills` plugin

`optimiziramsi-skills@optimiziramsi` survives as a **deprecated bundle**: no components of its
own, `dependencies` on all eleven plugins. **An update to it does not install those
dependencies** (observed 2026-10-18: the auto-updated install reported `dependency-unsatisfied` for
each and loaded nothing) — it only turns "plugin gone" into an error naming what to install. And
while it is enabled, none of the eleven can be disabled. So migrate rather than keep it, per
project:

1. `claude plugin marketplace update optimiziramsi`
2. `claude plugin install <plugin>@optimiziramsi --scope project` for each plugin the project
   wants (the README's table lists them).
3. `claude plugin uninstall optimiziramsi-skills@optimiziramsi` at the scope it was installed in,
   and drop its key from `enabledPlugins`.
4. Restart, then confirm with `claude plugin list` that only the chosen plugins are enabled.

Two things move with the split: env switches keep their names (they now belong to the plugin that
reads them), and the flow runner pointer moved to
`<claude-config>/plugins/data/optimiziramsi-flow/current` — the `flow` plugin's SessionStart hook
re-aims existing `.agent/bin/{loop,grind}` symlinks on its first run.

Re-verified 2026-08-19 against CCD/CC 2.1.235 and the `develop`/`main` split (0.0.11): the install
and update mechanics below still hold, and the CLI equivalents of every UI step are named inline.

## What you receive: `main`, and only `main`

- **Two branches, one of them yours.** `main` is the published marketplace — `.claude-plugin/`,
  the plugin folders, `other/`, and the public docs (this file, `README.md`, `CHANGELOG.md`).
  The working repo — `.agent/`, `.todo*`, `CLAUDE.md`, `.claude/`, `tests.sh`, `release.sh`,
  `vendor.sh`, the root `lib/` the plugins' copies are vendored from —
  lives on `develop` and stops there. `main` is written only by the release script, as a filtered
  tree-copy rather than a merge, so each release is one commit and `main`'s history is the release
  list.
- **Your clone is shallow and main-only.** The marketplace clone under
  `~/.claude/plugins/marketplaces/<name>` fetches `+refs/heads/main:refs/remotes/origin/main`, so
  `develop` is not merely hidden — it is never fetched. What you have is the published tree, not
  the authors' working tree.
- **Version shapes tell you the source.** A plain `X.Y.Z` came from `main`. Any pre-release
  (`X.Y.Z-dev.N`, `X.Y.Z-<branch-slug>.N`) can only come from a local directory-source
  registration — the release script refuses to publish one.

## Enable — marketplace global, plugins per-project

- Two layers, two homes. The **marketplace registration** lives in global `~/.claude/settings.json`:
  `extraKnownMarketplaces.optimiziramsi = {"source": {"source": "github", "repo": "optimiziramsi/skills"}}`
  — the `github` form takes `repo:`, not `url:`; a `git` form (`{"source": "git", "url":
  "https://github.com/optimiziramsi/skills.git"}`) also works. **Plugin enablement** lives in the
  project's committed `.claude/settings.json` `enabledPlugins` — one key per plugin the project
  wants (`"git@optimiziramsi": true`, …). Never enable them in global settings — enables travel
  with the repo. A personal opt-out goes in `.claude/settings.local.json`
  (`"<plugin>@optimiziramsi": false`), which wins over the shared file.
- **Two sources, one name.** The registration above points at GitHub. Point it at a local
  checkout instead — `claude plugin marketplace add /path/to/skills`, or `"source": {"source":
  "directory", "path": "/path/to/skills"}` — and every project on that machine loads whatever
  branch is checked out there. That is how you try an unreleased fix, and the only way to see a
  `-dev` series. Marketplaces are keyed by NAME globally, so the two forms are mutually exclusive:
  swapping means `claude plugin marketplace remove optimiziramsi` and then adding the other source.
- **`marketplace remove` is not a local operation.** It drops the install records of every plugin
  from that marketplace, in every scope, for every repo on the machine — and re-adding the
  marketplace restores none of them. A registered marketplace whose plugins were never re-installed
  renders as a marketplace with nothing in it. After any remove/re-add: re-install, then confirm
  with `claude plugin list`.
- Why the marketplace is NOT declared per-project: the name registers once in the global registry
  (`~/.claude/plugins/known_marketplaces.json`); startup syncs the settings declaration into the
  registry, and a second project-level declaration of the same name is just a competing identity
  with no benefit. One global declaration; restart after changing it.
- Enablement ≠ installation. `enabledPlugins` in the project's `.claude/settings.json` only flags
  intent — it installs NOTHING by itself. Every plugin also needs an install record
  (`~/.claude/plugins/installed_plugins.json`), and the record's scope decides everything below.
- **The correct CCD install path for per-project use**: select the right project (new-session
  picker / folder in the plugins list), Browse → open the PLUGIN PAGE → the install DROPDOWN →
  **"Install for project (shared)"**. That writes a `project` row AND the repo-settings enable —
  the same records CC's `/plugin` install creates. From then on, Manage Plugins shows scope
  PROJECT and the plugin-page enable switch works correctly both ways at project scope. Repeat per
  plugin, per repo. CLI equivalent: `claude plugin install <plugin>@optimiziramsi --scope project`.
  - The `+` beside a plugin in Browse and the plain Install button are "install for me": a global
    `user` row + a global-settings enable.
  - "Install for project (local)" installs into the project itself rather than the shared
    per-project record — not what adoption wants.
- Pick ONE scope per plugin, never both:
  - **Per-project (the recommended default):** install-for-project-shared in each repo; toggle via the UI
    switch or the repo settings file. Zero global traces; enables travel with the code.
  - **Global:** install-for-me once (`user` row + global enable), then hand-add
    `"<plugin>@optimiziramsi": false` in each repo that must NOT run it — settings
    merge, so the global enable wins wherever you don't override.
  Mixing scopes for one plugin is the failure mode: settings merge and enable BOTH records, the
  list shows DOUBLE entries (one per row — a truthful render of a real dual install), the toggle
  flickers (the repo `true` shadows the global `false` it writes), and the two rows pin versions
  independently, so they drift apart.
- How mixes happen: the CCD UI refuses to offer install once a record already covers the selected
  context — but CC's `/plugin` install in a terminal, or installing globally from one project and
  per-project from another, still adds the second scope. (The 2026-07 doubles traced to exactly
  that: CLI installs made during update tests.)
- Cleanup of a mixed plugin is FILE surgery (the desktop runtime blocks agents from editing these):
  in `~/.claude/plugins/installed_plugins.json` delete the row of the scope you are abandoning, and
  strip the matching enable (global `~/.claude/settings.json` for `user`, the repo's
  `.claude/settings.json` for `project`). Then restart + fresh session.
- The list's CONTEXT is the new-session project pre-selection, not the chat you opened it from —
  switching that picker swaps the whole `+` → Plugins view (enables, doubles, versions) for every
  open chat. Check the selected project before reading anything off the list. Tag semantics are
  asymmetric: an enable key REMOVED from settings shows DISABLED; an explicit
  `"<plugin>@optimiziramsi": false` DELISTS the plugin entirely.
- Floor: CCD/CC >= 2.1.195. On older builds a project-only external plugin silently does NOT load
  (an install-gate, not a settings error).
- Plugins bind at session start — restart CCD after any enable/install/marketplace change; a
  running or resumed session won't pick them up.
- Verify, don't trust the settings file: confirm the plugin's `bin/` dirs on `$PATH`, its hooks fire, and
  `/plugin` lists them enabled.

## Updating the plugin (a marketplace update ≠ an install update)

Getting a new plugin *version* to actually bind in a consumer repo takes more than re-fetching the
marketplace — two independent things must move, then a restart:

- **The author must bump the version.** CCD binds a plugin by its *installed* version and only
  re-materializes its install cache when that version *changes*. A same-version code change never
  reaches you, however many times you restart — re-fetching the marketplace clone updates the clone,
  not your installed cache. (Field case: a `git-guard` `reset` block sat dead across three restarts
  because the fix shipped without a version bump. Every plugin now treats "any consumer-visible
  change → bump its `<plugin>/.claude-plugin/plugin.json`" as an authoring rule, so this should not
  recur — but verify the version moved.)
- **You must update the install, not just the marketplace.** Even once the marketplace advances
  (e.g. `0.1.0 → 0.1.1`) and that version is materialized, `~/.claude/plugins/installed_plugins.json`
  can still pin the old version, and CCD keeps binding the old code. Update the plugin (`/plugin` →
  update, or re-point the install record) so the pin advances, **then restart** — plugins bind at
  session start.
- **Verify the bind, don't trust the fetch.** Confirm the new behavior actually fires (the new guard
  rule, the changed skill), not merely that `/plugin` shows a newer version available.

The mechanics (observed 2026-07-22): `~/.claude/plugins/installed_plugins.json` is the pin — one row
per install scope (`project` rows per repo; a `user` row if globally installed). A repo binds
through its own `project` row when it has one, else through the `user` row. Rows update
independently — with per-project installs, the update is per repo (update with that project
selected), and any other repos' rows stay pinned where they were.

- What writes what: **marketplace update** — CCD: session `+` → Plugins → Manage plugins →
  Marketplaces → optimiziramsi → `⋯` → Update; CLI: `claude plugin marketplace update optimiziramsi` — refreshes the
  clone under `~/.claude/plugins/marketplaces/optimiziramsi` only, pins untouched. **Plugin update** — CCD:
  Manage plugins → plugin page → Update (offers "update to X"); CLI: `claude plugin update
  <plugin>@optimiziramsi` — rewrites the pin and materializes `~/.claude/plugins/cache/optimiziramsi/<plugin>/<ver>/`.
  **Restart alone** writes nothing (no auto-refresh of marketplaces); **session start** re-resolves
  bindings in memory from settings + registry + pins.
- Full author→consumer chain, no skippable step: bump the plugin's `plugin.json` + push → marketplace update
  (clone) → plugin update (pin) → new session / restart (bind).
- **With a directory source there is no clone to refresh** — the marketplace reads the checkout
  live, so `marketplace update` only re-validates it and rewrites a timestamp. The install cache is
  still a version-keyed COPY of that tree, never a link to it: an edit in the checkout reaches you
  only after a version bump, `claude plugin update`, and a restart. Verified 2026-08-19 across
  three `-dev` bumps.

## Editing settings.json during adoption

- The desktop/app (auto-mode) runtime blocks an agent from editing `.claude/settings.json`. A
  terminal `claude` in the repo does not — it surfaces the file-guard ask for you to approve. Run
  enablement + settings/hook edits from a terminal worker (or hand the exact file to the owner).
  Deletions and doc edits are fine from either.

## The git safety net — two defaults that surprise

- amend/rebase PASS by default. The git-guard is a remote/discard safety net (push/pull/fetch,
  bulk-add, non-FF merge, protected-branch move, reset --hard, discards); it deliberately allows
  amend/rebase for FF-landing flows. If your repo enforces append-only history on protected branches
  ONLY (amend/rebase fine in worktrees), a branch-aware project tripwire in `.agent/guards.d/`
  (via the tripwire-guard) is the precise fit — `GIT_GUARD_STRICT` re-blocks globally,
  not per-branch.
- `git fetch` is BLOCKED by default. If your repo treats read-only fetch as fine, set
  `GIT_GUARD_ALLOW=fetch` in `.claude/settings.json` `env`. (`GIT_GUARD_ALLOW` takes comma-separated
  relax tokens: fetch, bulk-add, merge, protected-branch, soft-reset. Discards / `--no-verify` have
  no token — use `GIT_GUARD_OFF`.) `GIT_GUARD_ALLOW=fetch` is all-or-nothing; for finer control,
  `GIT_GUARD_ALLOW_FETCH=origin,upstream` permits `git fetch <remote>` for **named remotes only**
  (bare `git fetch`, `--all`, `--multiple` stay blocked) — the precise fit when one remote is fine
  but others aren't.

## What a repo keeps local (the zero-overlap line)

- Rules (`.claude/rules/`) and product / stack / deploy knowledge — never generic.
- Domain skills with no generic equivalent (e.g. a deploy-contract sync).
- Enforcement the plugins do not cover: project tripwires (`.agent/guards.d/`); a commit-guard for
  repo-specific post-commit checks (version bump, deploy-contract); the cap NUMBERS in
  `.agent/meta-lint.json` (the engine is the plugin's meta-lint — only the policy is yours).
- Project-specific session / commit signals. The shipped `session-start` and `commit-nudge` hooks
  are deliberately **current-repo-scoped**. For a dirty *sibling* worktree, set
  `COMMIT_NUDGE_EXTRA_DIRS=../gitops`; for anything else they don't cover (e.g. extra start-up
  context), CCD composes multiple hooks per event — layer your own SessionStart / Stop hook.

## A sequence that worked

- Prove load — enable, restart, verify `@optimiziramsi` resolves + hooks fire. No deletions yet.
- Port caps — write `.agent/meta-lint.json` with the repo's numbers; it supersedes the `caps` hook.
- Remove dupes — delete the local skills/agents/hooks the plugins now ship; rewire `settings.json`;
  keep the repo-specific pieces; add tripwires for any enforcement the plugins do not replicate.
- Docs — rewrite the instruction docs to name the real (plugin-backed) guards; get meta-lint green.
- Finalize — env fixes (e.g. `GIT_GUARD_ALLOW=fetch`), capture a load-protocol lesson, restart.
