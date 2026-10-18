# Handoff

_Last updated:_ 2026-10-18 — session 13: **split into one plugin per topic (phase 1 of
[plugin-split](plan/261018_135850_plugin-split.md)) — committed on `develop`, unreleased.**

`develop`: 11 per-topic plugins + the deprecated `optimiziramsi-skills` bundle, all `0.1.0-dev.N`.
`main` still ships the single plugin 0.0.13. `./tests.sh` ALL GREEN (14 suites, 5 self-tests, 13
`validate --strict` targets, 21 vendored copies). `./release.sh --dry-run` lists all 12 as shipping
and blocks only on their `-dev` versions — correct.

## Machine state the user must act on

The directory registration has `autoUpdate: true`, so the split reached this machine's user-scope
install within minutes: `optimiziramsi-skills@optimiziramsi` is now the 0.1.0-dev.1 bundle with
`dependency-unsatisfied` errors — **from the next session on, no optimiziramsi component loads in
any project here** until the per-topic plugins are installed. Per project:
`claude plugin install <plugin>@optimiziramsi --scope project`, then uninstall the bundle
(ADOPTION.md § Migrating). This repo's own dogfood set is the user's to pick too.

## What a cold session can't re-derive

- Shared code is **vendored** (`./vendor.sh`; root `lib/` is the source): local-path marketplaces
  drop symlinks that leave a plugin. `flow/vendor/worktree/` mirrors worktree's guards + suite for
  the runners' confinement, so flow needs no dependency on worktree.
- No inter-plugin `dependencies` on purpose — a dependency can't be disabled while its dependent
  is enabled. The bundle is migration-only for that reason.
- `release.sh` now ships every plugin whose tree differs from `main`, tags `<plugin>--v<version>`,
  and opens no dev series (tests.sh § 8 forces a plugin's next edit onto `X.Y.(Z+1)-dev.1`).
- Runner pointer moved to `<claude-config>/plugins/data/optimiziramsi-flow/current` → the flow
  plugin root; `runner-link` re-aims existing `.agent/bin/{loop,grind}` links.

## Next up

1. Phase 2 of the plan — config convention: one `hookio` resolver (env > `CLAUDE_PLUGIN_OPTION_*`
   > default); `userConfig` only for machine-wide personal defaults (it can't live in a project).
2. Phase 3 — `upkeep` plugin (update-available + new-plugin nudges, `/upkeep` runs the updates).
3. Phase 4 — `context` plugin (transcript-usage threshold nudge + `/repack`).
4. Open questions in the plan: skills-maintenance scope; a separate `optimiziramsi-dev`
   marketplace name vs this checkout's branch being what every project loads.
5. Still open from before: the looper/grinder live test (USER, plain terminal; `.todo`).

## Standing context

Done-gate `./tests.sh`. `.todo`: plain bullets, `(done)` prefix, no checkboxes; edits need
"ALLOW TODO" while the flow plugin's guard is live, unarmed deferrals go to `.todo-inbox`. Commits
single-line (commit-format guard). History append-only. Tests live in `<plugin>/tests/*.py`.
