# Handoff

_Last updated:_ 2026-10-18 — session 13: **marketplace split into 21 per-concern plugins, all
released locally as 0.1.0** (`main` ebe981a, tags `<plugin>--v0.1.0`; push is the user's) ([plan](plan/261018_135850_plugin-split.md)).

`develop` = `main`: 21 plugins at `0.1.0` — the user's 18 + `code-first`, `context`, `upkeep`.
The old `optimiziramsi-skills` bundle is gone. The working tree's marketplace is
`optimiziramsi-dev`; `release.sh` publishes it as `optimiziramsi`.

## Machine state

See [dev-marketplace.md](dev-marketplace.md). This repo dogfoods `<plugin>@optimiziramsi-dev`
at project scope. Other projects on the machine: the old `optimiziramsi` registration (this
checkout) is removed; they need `claude plugin marketplace add optimiziramsi/skills` and
per-project installs once `main` is released + pushed (ADOPTION.md § Migrating).

## What a cold session can't re-derive

- Shared code is **vendored** (`./vendor.sh`; root `lib/` is the source) — local-path
  marketplaces drop symlinks leaving a plugin. `runners/vendor/worktree-guards/` mirrors those
  guards for the runners' confinement. Branch detection (default/protected/integration) lives in
  `hookio` so `git-guard` and `code-first` agree.
- No inter-plugin `dependencies` on purpose. Every knob is env via `hookio.setting`.
- `autoUpdate` installs the WORKING TREE of this checkout into dev installs, committed or not.
- `release.sh` ships every plugin whose tree differs from `main`, tags `<plugin>--v<version>`.

## Next up

1. The user pushes `main` + the 21 tags + `develop`, then comes back with review comments.
2. Live-test the new hooks in a real session: `context` (needs a long session), `upkeep`
   (after a bump), `code-first` Stop guard.
3. Still open from before: the looper/grinder live test (USER, plain terminal; `.todo`).

## Standing context

Done-gate `./tests.sh`. Adding/changing components: the repo-local `skills-maintenance` skill.
`.todo`: plain bullets, `(done)` prefix; edits need "ALLOW TODO" while the todo plugin's guard is
live. Commits single-line. History append-only. Tests live in `<plugin>/tests/*.py`.
