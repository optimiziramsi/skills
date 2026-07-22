# repo — Claude Code repo-maintenance utilities

Part of the [`optimiziramsi-skills`](../README.md) plugin (the opsi toolkit).

## Contents

- name: `rename`
  kind: skill + command
  purpose:
    `git mv` a file + update every non-archive reference across the project (the
    "dozen-references-cascade" problem).

_Planned:_ `scope-cut` (sweep + remove a cut feature) and similar repo-hygiene utilities.

## Enable

```json
{ "enabledPlugins": { "optimiziramsi-skills@optimiziramsi": true } }
```
