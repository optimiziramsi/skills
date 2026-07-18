# repo — Claude Code repo-maintenance utilities

Part of the [`opsi`](../../README.md) marketplace.

## Contents

| Kind | Name | Purpose |
|---|---|---|
| skill + command | `rename` | `git mv` a file + update every non-archive reference across the project (the "dozen-references-cascade" problem). |

_Planned:_ `scope-cut` (sweep + remove a cut feature) and similar repo-hygiene utilities.

## Enable

```json
{ "enabledPlugins": { "repo@opsi": true } }
```
