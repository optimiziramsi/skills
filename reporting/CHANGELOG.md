# reporting — changelog

Versions of the `reporting@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.0 — unreleased

- Split out of the single `optimiziramsi-skills` plugin (its `reporting` topic). Enable it per project with `claude plugin install reporting@optimiziramsi --scope project`.
- The injected contract can be replaced per repo: `REPORT_CONTRACT_FILE` → `.agent/output-contract.md`
  → `.claude/output-contract.md` → the shipped text; a broken override prints a visible DISARMED line.
- `REPORT_PULSE_TEXT` replaces the mid-turn pulse one-liner.
