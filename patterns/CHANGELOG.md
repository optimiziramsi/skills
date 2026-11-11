# patterns — changelog

Versions of the `patterns@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.1 — unreleased

- `pattern-guards`: the edit gate's block reason no longer ends with "Set PATTERN_GUARDS_OFF=1 to
  disable" or offers "an explicit human go" as a way through. It names the path and the non-blessed
  pattern, says the pattern is walked and blessed with the user first, and ends with "Stop and tell
  the user what you wanted to do." The switch stays documented in the README; gating is unchanged.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `patterns` topic). Enable it per project with `claude plugin install patterns@optimiziramsi --scope project`.
