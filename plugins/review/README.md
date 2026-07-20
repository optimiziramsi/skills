# review — Claude Code review & quality gates

Part of the [`opsi`](../../README.md) marketplace.

## Contents

- `review` (skill + command): Structured review/audit → `.agent/reviews/YYMMDD_*.md` with
  P0/HIGH/MED/LOW findings, scope-first method, verify-before-reporting, optional delegation to
  review subagents.
- `qa-gate` (skill + command): The done-gate — typecheck → unit → e2e → **visual (read the
  screenshots)** before claiming done. Commands stay per-project; the loop and "a red gate
  reported green is the one unforgivable sin" don't.
- `semantic-reviewer` (agent): 7-item semantic-bug checklist (lifecycle, error handling,
  unbounded growth, idempotent cleanup, empty input, shutdown, unvalidated casts) — the bugs
  grep misses. Read-only.
- `spec-cross-checker` (agent): One feature/topic: diff `.docs/` spec vs code →
  MATCH/PARTIAL/MISSING/EXTRA. Read-only.
- `wireframe-vs-code` (agent): Diff a wireframe's functional spec vs the implementation → gap
  report. Read-only.
- `doc-auditor` (agent): Full drift audit of the repo's **binding docs vs code reality** —
  checkable claims (paths, commands, env vars both directions, asserted values, cross-doc
  duplication, enforcement tags) → severity-ranked drift table. Broader than
  `spec-cross-checker` (one feature); read-only.
- `isolation-reviewer` (agent): Adversarial **multi-tenant isolation** review — establishes the
  project's tenancy model, then tries to REFUTE "this change is isolation-safe" across 7 bug
  classes (tenant scoping, boundary validation, lifecycle races, connection revocation, token
  atomicity, abuse caps, leaks). Read-only.

Assumes the **`.agent/` house layout** (`.agent/reviews/` for assessments, `.docs/` for specs). The
`review` skill delegates to these agents. (A `pattern-verifier` agent lives in the `patterns`
plugin.)

## Enable

```json
{ "enabledPlugins": { "review@opsi": true } }
```
