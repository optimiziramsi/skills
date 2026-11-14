# commit — changelog

Versions of the `git@optimiziramsi` plugin (named `commit` up to 0.1.1). History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.2.1 — unreleased

- A project can now set its own commit message convention in `.agent/commit.json` (`pattern`, `types`, `scopes` with what each `covers`, `scopes_open`, `examples`). The `commit` skill reads it in place of the bare-imperative shape; single line, no body, no trailers still apply. The `commit-format` hook blocks a model commit whose message doesn't match `pattern`, and, when `scopes_open` is false, one whose `type(scope):` scope isn't listed. A missing or invalid file changes nothing. Before this a project could override only the cadence, so a `type(scope): summary` repo needed its own skill delta and tripwire.

## 0.2.0 — 2026-11-13

- Plugin renamed `commit` → `git`, so its name no longer overlaps its own command in the `/` menu. The command stays `/commit` (now `/git:commit`). Install `git@optimiziramsi` and uninstall `commit@optimiziramsi` (ADOPTION.md § Renamed plugins). Env switches keep their names.

## 0.1.1 — 2026-11-12

- The commit nudge no longer adds "also refresh the handoff (/handoff)" when the project has an
  `.agent/handoff.md` — it asks for one thing, the commit.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `commit` topic). Enable it per project with `claude plugin install commit@optimiziramsi --scope project`.
