# qa-gate — changelog

Versions of the `testing@optimiziramsi` plugin (named `qa-gate` up to 0.1.0). History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.2.0 — 2026-11-13

- Plugin renamed `qa-gate` → `testing`, so its name no longer overlaps its own command in the `/` menu. The command stays `/qa-gate` (now `/testing:qa-gate`). Install `testing@optimiziramsi` and uninstall `qa-gate@optimiziramsi` (ADOPTION.md § Renamed plugins).

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the `qa-gate` skill of its `review` topic). Enable it per project with `claude plugin install qa-gate@optimiziramsi --scope project`.
