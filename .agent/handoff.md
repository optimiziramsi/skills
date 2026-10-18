# Handoff

_Last updated:_ 2026-10-18 — session 13: **split into one plugin per topic (phase 1 of
[plugin-split](plan/261018_135850_plugin-split.md)) — committed on `develop`, unreleased.**

`develop`: 18 per-concern plugins (the user's grouping, see the plan's decisions log) + the
deprecated `optimiziramsi-skills` bundle, all `0.1.0-dev.N`.
`main` still ships the single plugin 0.0.13. `./tests.sh` ALL GREEN (14 suites, 5 self-tests, `validate --strict`
on every plugin, vendored copies in sync).

## Machine state the user must act on

The directory registration has `autoUpdate: true`, so the split reached this machine's user-scope
install within minutes: `optimiziramsi-skills@optimiziramsi` is now the 0.1.0-dev.1 bundle with
`dependency-unsatisfied` errors — **from the next session on, no optimiziramsi component loads in
any project here** until the per-topic plugins are installed. Per project:
`claude plugin install <plugin>@optimiziramsi --scope project`, then uninstall the bundle
(ADOPTION.md § Migrating). This repo's own dogfood set is the user's to pick too.

## What a cold session can't re-derive

- Shared code is **vendored** (`./vendor.sh`; root `lib/` is the source): local-path marketplaces
  drop symlinks that leave a plugin. `runners/vendor/worktree-guards/` mirrors those guards + suite
  for the runners' confinement, so runners needs no dependency on worktree-guards.
- No inter-plugin `dependencies` on purpose — a dependency can't be disabled while its dependent
  is enabled. The bundle is migration-only for that reason.
- `release.sh` now ships every plugin whose tree differs from `main`, tags `<plugin>--v<version>`,
  and opens no dev series (tests.sh § 8 forces a plugin's next edit onto `X.Y.(Z+1)-dev.1`).
- Runner pointer moved to `<claude-config>/plugins/data/optimiziramsi-runners/current` → the runners
  plugin root; `runner-link` re-aims existing `.agent/bin/{loop,grind}` links.

## Next up

1. Phase 2 of the plan — config convention: one `hookio` resolver (env > `CLAUDE_PLUGIN_OPTION_*`
   > default); `userConfig` only for machine-wide personal defaults (it can't live in a project).
2. Phase 3 — `upkeep` plugin (update-available + new-plugin nudges, `/upkeep` runs the updates).
3. Phase 4 — `context` plugin; the user's spec (30/50/60% of 1M, overrides) is in the plan.
4. Open: a separate `optimiziramsi-dev` marketplace name vs this checkout's branch being what
   every project loads; drop the bundle before the first release?
5. Still open from before: the looper/grinder live test (USER, plain terminal; `.todo`).

## Standing context

Done-gate `./tests.sh`. `.todo`: plain bullets, `(done)` prefix, no checkboxes; edits need
"ALLOW TODO" while the todo plugin's guard is live, unarmed deferrals go to `.todo-inbox`. Commits
single-line (commit-format guard). History append-only. Tests live in `<plugin>/tests/*.py`.
