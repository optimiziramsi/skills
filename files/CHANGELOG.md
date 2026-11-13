# rename — changelog

Versions of the `files@optimiziramsi` plugin (named `rename` up to 0.1.0). History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.1 — unreleased

- Plugin renamed `rename` → `files`, so its name no longer overlaps its own command in the `/` menu. The command stays `/rename` (now `/files:rename`). Install `files@optimiziramsi` and uninstall `rename@optimiziramsi` (ADOPTION.md § Renamed plugins).

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the `rename` skill of its `repo` topic). Enable it per project with `claude plugin install rename@optimiziramsi --scope project`.
