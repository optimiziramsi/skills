# Handoff

_Last updated:_ 2026-10-18 — session 13: split into 21 plugins, 0.1.0 released + pushed, installed per repo.

## Where we left off

`develop` = `main` = 0.1.0 for all 21 plugins; `main`, `develop` and the 21 `<plugin>--v0.1.0`
tags are on GitHub. The machine-wide install is gone: every repo now installs its own set at
project scope from `optimiziramsi` (GitHub); this repo dogfoods all 21 from `optimiziramsi-dev`
(this checkout). The user is about to review the work and come back with comments.

## This session's arc

- Split the single plugin into the user's 18 groups + new `code-first`, `context`, `upkeep`
  ([plan](plan/261018_135850_plugin-split.md), decisions log there).
- Shared code vendored from root `lib/` by `./vendor.sh`; branch detection + `hookio.setting`
  (env-only knobs) + override-file chain live in `hookio`.
- `reporting` contract and pulse text overridable per repo; `grind --status` no longer runs `done-check`.
- Bundle dropped; working-tree marketplace is `optimiziramsi-dev`, `release.sh` publishes `optimiziramsi`.
- Repo-local `skills-maintenance` skill added.
- Machine cleanup: old global installs, caches, data dirs and failed clones removed.

## Per-repo installs (uncommitted in each repo — the user's to commit)

`.claude/settings.json` gained `enabledPlugins` in: kupimkuham, app-example, games, hub,
homelab, ai-shopping-list-app (rabbit-run-single-instance committed).
`commit-commands@claude-plugins-official` was removed from games (project scope);
ai-shopping-list-app already had it disabled. Plugin sets per repo: see `claude plugin list`.

## Build state

`./tests.sh` ALL GREEN at 381317f. Every plugin is at 0.1.0 — the next edit to any plugin must
bump it to `0.1.1-dev.1` (tests.sh § 8 enforces).

## Outstanding

- The user's review comments on the split and the three new plugins.
- Live behavior unverified in real sessions: `context` thresholds (it did fire at 50% and 60%
  here), `upkeep` notice after a version bump, `code-first` Stop guard on inline code.
- `hub-session.sh` checked: additive only (handoff focus text, ../gitops state), no overlap with
  `session-start`; its header comment still says `session@opsi` (hub's file, user's to fix).
- Looper/grinder live test (USER, plain terminal; `.todo`).

## Suggested next topic

Work through the user's review comments. Alternatives: live-test `upkeep` by bumping one plugin
in a dev install.
