# review — Claude Code review & quality gates

Part of the [`opsi`](../../README.md) marketplace.

## Contents

| Kind | Name | Purpose |
|---|---|---|
| skill + command | `review` | Structured review/audit → `.agent/reviews/YYMMDD_*.md` with P0/HIGH/MED/LOW findings, scope-first method, verify-before-reporting, optional delegation to review subagents. |
| skill + command | `qa-gate` | The done-gate — typecheck → unit → e2e → **visual (read the screenshots)** before claiming done. Commands stay per-project; the loop and "a red gate reported green is the one unforgivable sin" don't. |
| agent | `semantic-reviewer` | 7-item semantic-bug checklist (lifecycle, error handling, unbounded growth, idempotent cleanup, empty input, shutdown, unvalidated casts) — the bugs grep misses. Read-only. |
| agent | `spec-cross-checker` | One feature/topic: diff `.docs/` spec vs code → MATCH/PARTIAL/MISSING/EXTRA. Read-only. |
| agent | `wireframe-vs-code` | Diff a wireframe's functional spec vs the implementation → gap report. Read-only. |
| agent | `doc-auditor` | Full drift audit of the repo's **binding docs vs code reality** — checkable claims (paths, commands, env vars both directions, asserted values, cross-doc duplication, enforcement tags) → severity-ranked drift table. Broader than `spec-cross-checker` (one feature); read-only. |
| agent | `isolation-reviewer` | Adversarial **multi-tenant isolation** review — establishes the project's tenancy model, then tries to REFUTE "this change is isolation-safe" across 7 bug classes (tenant scoping, boundary validation, lifecycle races, connection revocation, token atomicity, abuse caps, leaks). Read-only. |

Assumes the **`.agent/` house layout** (`.agent/reviews/` for assessments, `.docs/` for specs). The
`review` skill delegates to these agents. (A `pattern-verifier` agent lives in the `patterns` plugin.)

## Enable

```json
{ "enabledPlugins": { "review@opsi": true } }
```
