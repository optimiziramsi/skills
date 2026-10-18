---
name: skills-maintenance
description: Add, change, split, rename or retire a plugin, skill, command, agent or hook in this marketplace — the checklist that keeps manifests, docs, vendored code, versions and tests in step. Use when the user says "add a plugin", "new skill", "add a hook", "split/merge plugins", "rename a skill", "retire X", or before any edit under a `<plugin>/` folder that adds or removes a component. Repo-local — this is NOT shipped to consumers.
---

# Maintain this marketplace's plugins

The rules live in [CLAUDE.md](../../../CLAUDE.md) § Authoring conventions; this is the order to
apply them in. `./tests.sh` catches most misses — run it before every commit, not just at the end.

## Add a plugin

1. `<name>/` at the root (dir name = plugin name) with `.claude-plugin/plugin.json` — copy a
   sibling's shape: `name`, `displayName` (`optimiziramsi <name>`), `version` `0.1.0-dev.1`,
   `description`, `author`, `homepage` (`…/tree/main/<name>#readme`), `repository`, `license`,
   `keywords`. Default layout only (`skills/ commands/ agents/ hooks/hooks.json`, + `bin/ tests/`).
2. `.claude-plugin/marketplace.json` — an entry `{name, source: "./<name>", description, category}`.
3. `README.md` in the house shape: the per-concern header line, `## Contents` as `- name:` records,
   `## Settings`, `## Escape hatches`, `## Enable` (`claude plugin install <name>@optimiziramsi
   --scope project`). `CHANGELOG.md` with `## 0.1.0 — unreleased`.
4. Root README: a row in the plugin table (keep the count in its first line right) and a row in the
   switches table for every new kill-switch.
5. No `dependencies` on other plugins — a project must be able to drop any one. Mention a sibling
   softly ("when that plugin is enabled") instead.

## Add or change a component

- **Skill**: `skills/<name>/SKILL.md`, frontmatter `name` = dir name; the description carries the
  trigger phrases (it is what auto-triggers). Under the 9000-char cap.
- **Command**: `commands/<name>.md`, a thin shim to the same-named skill, with
  `disable-model-invocation: true` and no logic or duplicated description.
- **Agent**: `agents/<name>.md`, read-only unless it truly must write.
- **Hook**: python3 stdlib, over `lib/hookio.py`; resolves `lib/` as `parents[1] / "lib"`; entry
  point under `if __name__ == "__main__":` (tests import it); fails open via `hookio.guard`;
  ships a kill-switch or self-gates on project config; every knob is an env var read through
  `hookio.setting`. Wire it in `hooks/hooks.json` as `${CLAUDE_PLUGIN_ROOT}/hooks/<file>`.
- **CLI**: `bin/<name>` (executable, on PATH while the plugin is enabled) when a skill needs a
  deterministic answer the hooks also use.
- **Tests**: `tests/test_<name>.py` on `lib/selftest.py` (`Check`, `hook`, `invoke`, `run_cli`);
  strip the developer's own env knobs at the top so fixtures can't inherit them.

## Shared code

Edit root `lib/` only, then `./vendor.sh` — it copies each module into every plugin that imports
it (and `worktree-guards` into `runners/vendor/`). Commit the copies with the change; every
plugin whose copy moved needs its version bumped.

## Split, merge, rename, retire

`git mv` so history follows. Move the README records and CHANGELOG notes with the files; fix every
cross-plugin mention (`grep -rn '<old name>'`); update the marketplace entry, the root README
tables, ADOPTION.md, and CLAUDE.md where named. A retired plugin's id stops resolving for its
installs — say so in ADOPTION.md § Migrating.

## Before the commit

- Bump every touched plugin's `version` in the same commit (`-dev.N+1`; first edit after a release
  → `X.Y.(Z+1)-dev.1`) and add a CHANGELOG line.
- `./tests.sh` ALL GREEN, and no project-specific content leaked in.
- Optional for a skill whose triggering matters: `claude plugin eval <plugin dir>` with cases.
