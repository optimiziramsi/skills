# optimiziramsi-skills — changelog

Versions of the `optimiziramsi-skills@optimiziramsi` plugin. History before the split into one plugin per topic
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.0 — unreleased

- Now a deprecated bundle: no components of its own, `dependencies` on all eighteen per-concern plugins. Updating an existing install to it does **not** install those dependencies — it loads nothing and names each missing one. Install the plugins the project wants and uninstall this; while it is enabled none of them can be disabled.
