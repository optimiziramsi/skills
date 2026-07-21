# Adopting `opsi` into an existing repo

How to enable the opsi plugins in a project, plus the non-obvious gotchas — distilled from a real
adoption (2026-07, CCD 2.1.215). Goal: the plugins own the generic system, the repo keeps only what
is repo-specific, zero overlap.

## Enable — project-only

- Enablement lives in the project's committed `.claude/settings.json`: set BOTH
  `extraKnownMarketplaces.opsi` AND `enabledPlugins` (`"<plugin>@opsi": true`). Never enable opsi in
  global `~/.claude/settings.json` — keep it per-repo so it travels with the code.
- Floor: CCD/CC >= 2.1.195. On older builds a project-only external plugin silently does NOT load
  (an install-gate, not a settings error).
- Plugins bind at session start — restart CCD after any enable/marketplace change; a running or
  resumed session won't pick them up.
- First load may need approving the repo trust / plugin-install prompt — enablement alone is not
  enough if the plugin is not installed yet.
- Verify, don't trust the settings file: confirm opsi `bin/` dirs on `$PATH`, opsi hooks fire, and
  `/plugin` lists them enabled.
- The `/plugin` UI writes enablement at GLOBAL scope even when you pick a project — that contaminates
  `~/.claude`. Edit `.claude/settings.json` as a FILE; if `@opsi` reappears in global, strip it.

## Updating an opsi plugin (a marketplace update ≠ an install update)

Getting a new plugin *version* to actually bind in a consumer repo takes more than re-fetching the
marketplace — two independent things must move, then a restart:

- **The author must bump the version.** CCD binds a plugin by its *installed* version and only
  re-materializes its install cache when that version *changes*. A same-version code change never
  reaches you, however many times you restart — re-fetching the marketplace clone updates the clone,
  not your installed cache. (Field case: a `git-guard` `reset` block sat dead across three restarts
  because the fix shipped without a version bump. opsi now treats "touch `plugins/<name>/` → bump its
  `plugin.json`" as an authoring rule, so this should not recur — but verify the version moved.)
- **You must update the install, not just the marketplace.** Even once the marketplace advances
  (e.g. `0.1.0 → 0.1.1`) and that version is materialized, `~/.claude/plugins/installed_plugins.json`
  can still pin the old version, and CCD keeps binding the old code. Update the plugin (`/plugin` →
  update, or re-point the install record) so the pin advances, **then restart** — plugins bind at
  session start.
- **Verify the bind, don't trust the fetch.** Confirm the new behavior actually fires (the new guard
  rule, the changed skill), not merely that `/plugin` shows a newer version available.

## Editing settings.json during adoption

- The desktop/app (auto-mode) runtime blocks an agent from editing `.claude/settings.json`. A
  terminal `claude` in the repo does not — it surfaces the file-guard ask for you to approve. Run
  enablement + settings/hook edits from a terminal worker (or hand the exact file to the owner).
  Deletions and doc edits are fine from either.

## git@opsi — two defaults that surprise

- amend/rebase PASS by default. The git-guard is a remote/discard safety net (push/pull/fetch,
  bulk-add, non-FF merge, protected-branch move, reset --hard, discards); it deliberately allows
  amend/rebase for FF-landing flows. If your repo enforces append-only history on protected branches
  ONLY (amend/rebase fine in worktrees), a branch-aware project tripwire in `.agent/guards.d/*.sh`
  (via instructions@opsi tripwire-guard) is the precise fit — `GIT_GUARD_STRICT` re-blocks globally,
  not per-branch.
- `git fetch` is BLOCKED by default. If your repo treats read-only fetch as fine, set
  `GIT_GUARD_ALLOW=fetch` in `.claude/settings.json` `env`. (`GIT_GUARD_ALLOW` takes comma-separated
  relax tokens: fetch, bulk-add, merge, protected-branch, soft-reset. Discards / `--no-verify` have
  no token — use `GIT_GUARD_OFF`.)

## What a repo keeps local (the zero-overlap line)

- Rules (`.claude/rules/`) and product / stack / deploy knowledge — never generic.
- Domain skills with no generic equivalent (e.g. a deploy-contract sync).
- Enforcement the plugins do not cover: project tripwires (`.agent/guards.d/`); a commit-guard for
  repo-specific post-commit checks (version bump, deploy-contract); the cap NUMBERS in
  `.agent/meta-lint.json` (the engine is instructions@opsi — only the policy is yours).

## A sequence that worked

- Prove load — enable, restart, verify `@opsi` resolves + hooks fire. No deletions yet.
- Port caps — write `.agent/meta-lint.json` with the repo's numbers; it supersedes the `caps.sh` hook.
- Remove dupes — delete the local skills/agents/hooks the plugins now ship; rewire `settings.json`;
  keep the repo-specific pieces; add tripwires for any enforcement the plugins do not replicate.
- Docs — rewrite the instruction docs to name the real (plugin-backed) guards; get meta-lint green.
- Finalize — env fixes (e.g. `GIT_GUARD_ALLOW=fetch`), capture a load-protocol lesson, restart.
