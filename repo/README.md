# repo — Claude Code repo-maintenance utilities

The `repo@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

## Contents

- name: `rename`
  kind: skill + command
  purpose:
    `git mv` a file + update every non-archive reference across the project (the
    "dozen-references-cascade" problem).

_Planned:_ `scope-cut` (sweep + remove a cut feature) and similar repo-hygiene utilities.

## Enable

```json
{ "enabledPlugins": { "repo@optimiziramsi": true } }
```
