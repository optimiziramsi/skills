# Bump the plugin's `plugin.json` version in the SAME commit as any `plugins/<name>/` change

Any edit under `plugins/<name>/` (hook, skill, command, agent, config) MUST bump that plugin's
`plugins/<name>/.claude-plugin/plugin.json` `version` in the **same commit**. A code change with no
version bump does **not** reach installed consumers: CCD binds a plugin by its *installed* version
and only re-materializes its install cache when the version *changes*. Same version in → the old
code stays bound, no matter how many restarts, and re-fetching the marketplace clone doesn't help.

## What bit us (2026-07)

`47f58c1` added the `reset` strict token to `plugins/git/hooks/git-guard.py` (+ grew its self-test
to 82 cases) but left `plugins/git/.claude-plugin/plugin.json` at `0.1.0`. A consumer repo (homelab)
had set `GIT_GUARD_STRICT=rebase,amend,reset` — but the `reset` block was **silently dead across
three CCD restarts**: the consumer was pinned to installed `0.1.0`, and nothing re-materialized the
`0.1.0` cache because the version never moved. Fix: `8d1aef1` bumped `0.1.0 → 0.1.1`; only then did
the new hook code bind. The discipline the `instructions` plugin already follows — `711ccf1` bumps
`0.3.0 → 0.3.1` in the same commit as its code change — is the model.

## The rule

- Touch anything under `plugins/<name>/` → bump `plugins/<name>/.claude-plugin/plugin.json`
  `version` in the same commit. No exceptions for "it's just a hook tweak" — that is exactly the
  case that bit us.
- Bumping is necessary but not sufficient on the consumer side: a marketplace update is **not** a
  plugin-install update. The consumer must also update the install record and restart. See
  `ADOPTION.md` § "Updating an opsi plugin".
- Mechanization was proposed (a `tests.sh` gate that fails when a commit touches `plugins/<name>/**`
  without moving that plugin's `version`). Until it lands this is honored by hand — which is the
  whole reason this lesson is routed into CLAUDE.md § Authoring conventions.

**Origin:** 2026-07-21 — field adoption of `git@opsi` into a consumer repo surfaced a dead
`GIT_GUARD_STRICT=reset` across three restarts; root-caused to the missing version bump in `47f58c1`,
fixed in `8d1aef1`. Recorded so no future `plugins/<name>/` edit ships without a bump.
