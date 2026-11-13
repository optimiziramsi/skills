# playbooks — changelog

Versions of the `playbooks@optimiziramsi` plugin (named `hotfix` up to 0.1.0). History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.1 — unreleased

- Plugin renamed `hotfix` → `playbooks`, so its name no longer overlaps its own command in the `/` menu. The command stays `/hotfix` (now `/playbooks:hotfix`). Install `playbooks@optimiziramsi` and uninstall `hotfix@optimiziramsi` (ADOPTION.md § Renamed plugins).

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the `hotfix` skill of its `git` topic). Enable it per project with `claude plugin install hotfix@optimiziramsi --scope project`.
