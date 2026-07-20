# review — Claude Code review & quality gates

Part of the [`opsi`](../../README.md) marketplace.

## Contents

- name: `review`
  kind: skill + command
  purpose:
    Structured review/audit → `.agent/reviews/YYMMDD_*.md` with P0/HIGH/MED/LOW findings,
    scope-first method, verify-before-reporting, optional delegation to review subagents.

- name: `qa-gate`
  kind: skill + command
  purpose:
    The done-gate — typecheck → unit → e2e → **visual (read the screenshots)** before claiming
    done. Commands stay per-project; the loop and "a red gate reported green is the one
    unforgivable sin" don't.

- name: `semantic-reviewer`
  kind: agent
  purpose:
    7-item semantic-bug checklist (lifecycle, error handling, unbounded growth, idempotent
    cleanup, empty input, shutdown, unvalidated casts) — the bugs grep misses. Read-only.

- name: `spec-cross-checker`
  kind: agent
  purpose:
    One feature/topic: diff `.docs/` spec vs code → MATCH/PARTIAL/MISSING/EXTRA. Read-only.

- name: `wireframe-vs-code`
  kind: agent
  purpose: Diff a wireframe's functional spec vs the implementation → gap report. Read-only.

- name: `doc-auditor`
  kind: agent
  purpose:
    Full drift audit of the repo's **binding docs vs code reality** — checkable claims (paths,
    commands, env vars both directions, asserted values, cross-doc duplication, enforcement
    tags) → severity-ranked drift table. Broader than `spec-cross-checker` (one feature);
    read-only.

- name: `isolation-reviewer`
  kind: agent
  purpose:
    Adversarial **multi-tenant isolation** review — establishes the project's tenancy model,
    then tries to REFUTE "this change is isolation-safe" across 7 bug classes (tenant scoping,
    boundary validation, lifecycle races, connection revocation, token atomicity, abuse caps,
    leaks). Read-only.

Assumes the **`.agent/` house layout** (`.agent/reviews/` for assessments, `.docs/` for specs). The
`review` skill delegates to these agents. (A `pattern-verifier` agent lives in the `patterns`
plugin.)

## Enable

```json
{ "enabledPlugins": { "review@opsi": true } }
```
