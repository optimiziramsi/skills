# upkeep — keep the plugins current

The `upkeep@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

Claude Code's own auto-update is off by default for third-party marketplaces, only updates what
is already installed, and never tells you either way. This plugin tells you at session start
when an installed plugin has a newer version, or when a marketplace you install from has gained
a plugin — and `/upkeep` applies it.

## Contents

- name: `upkeep-check`
  kind: hook
  purpose:
    SessionStart — compares this project's installs (user scope, plus its own project/local
    rows) with the local copies of the marketplaces they come from; one line when something is
    outdated or new. "New" means new since this project first looked — the first look records a
    baseline silently, so a big marketplace doesn't announce its whole catalogue. An identical
    report shows once a day. Then refreshes the watched marketplaces in the background
    (`claude plugin marketplace update`, at most once per `UPKEEP_REFRESH_HOURS`), so the next
    session sees what's new. The hook itself never touches the network.

- name: `upkeep`
  kind: skill + command
  purpose:
    Refresh the marketplaces, update every outdated plugin at its own scope, offer the new ones
    (installed only on your pick), then hand over `/reload-plugins`.

- name: `bin/upkeep`
  kind: cli
  purpose: "`upkeep status [--json]` / `upkeep marketplaces` — what the hook sees, on PATH while enabled."

## Settings

In a settings.json `env` block (any scope):

- `UPKEEP_MARKETPLACES` — comma-separated marketplaces to watch; default: every marketplace this
  project installs from.
- `UPKEEP_REFRESH_HOURS` — background refresh throttle, default `24`; `0` = never refresh.

## Escape hatches

`UPKEEP_OFF=1` — off entirely.

## Limits

Reads Claude Code's plugin records under `<claude-config>/plugins/` (`installed_plugins.json`,
`known_marketplaces.json`, each marketplace's manifests). They are documented but carry no
stability promise; if their shape changes the plugin goes quiet rather than wrong. A plugin
installed with no declared version (`unknown`) can't be compared and is skipped.

## Enable

```bash
claude plugin install upkeep@optimiziramsi --scope project
```
