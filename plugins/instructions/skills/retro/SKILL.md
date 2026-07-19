---
name: retro
description: Harvest durable learnings from this session into the instruction system — with provenance, dedup, and pruning. Use at the end of a significant session, after a user correction worth keeping, when a convention drifted or a footgun was hit, or when the user says "retro", "wrap up", "save learnings", "what did we learn", "lets stop here", "remember this". The single door for instruction updates.
---

# Retro — route learnings, close the unit

This is how the instruction system self-updates without rotting. Harvest what this session taught,
route each learning to the store that owns it, and keep the system lean.

Assumes the `.agent/` house layout: `.agent/lessons/`, `.claude/rules/`, `.docs/`,
`.agent/handoff.md`, `.agent/instructions-changelog.md`.

## 1. Harvest

Scan the session for durable learnings:

- user corrections ("no, do it this way"), confirmed conventions, owner decisions;
- bugs whose root cause implies a rule; gotchas that cost real time;
- a procedure that was wrong or missing.

**Skip:** session narration, one-off trivia, anything already recorded, secrets/personal data. A
learning qualifies only if it would change how a *future* session acts — git history already holds
the narrative.

## 2. Route each learning to its store

| Learning | Store | Via |
|---|---|---|
| Durable fact, gotcha, working agreement, engineering lesson | `.agent/lessons/` | the `lessons` skill |
| Binding rule (must / never) | the project's binding-rule home — `.claude/rules/*.md` only if the project uses that layer, else its canonical rule book / CLAUDE.md (never create a new instruction layer) | add the enforcement tag; if you write `[ENFORCED]`, the guard must exist — extend a hook in the same change, else tag it `[HONOR]` |
| Repeatable procedure that was wrong or missing | the matching skill's steps | edit the skill |
| Architecture / code-shape / recipe | `.docs/` | edit the doc |
| Volatile "where we left off" state | `.agent/handoff.md` | the `handoff` skill — NOT here |
| Enforcement gap (a checkable violation slipped through) | a hook | add / extend the guard |
| One-off, not worth encoding | — | say so, drop it |

## 3. Merge, don't append

For each learning, search the target file for an existing entry **first** — update it in place and
refresh its date rather than adding a near-duplicate. Delete any entry this learning contradicts;
git is the archive. Prefer sharpening an existing rule to adding a new one.

## 4. Retention — compact as you go

Respect each file's size cap. At or near a cap, **compact before adding** (one-in-one-out) — route
the displaced content to a cheaper home (always-loaded rules are the most expensive real estate;
prefer a skill / doc / lesson). A retro that only *adds* is suspect: state what you demoted or
deleted, or why nothing qualified.

## 5. Apply by governance tier

- **Safe changes — apply directly (T2):** clarify the wording of an existing rule, fix a broken
  pointer, fold a duplicate into its canonical home, compact over-cap content. Apply, then add one
  line to `.agent/instructions-changelog.md` (newest first, tier-tagged).
- **Risky changes — propose only (T3):** add or remove a rule, change a cap, or change any
  hook / skill / agent / settings behavior. **Do NOT apply.** Batch ALL of them into ONE proposal —
  for each: target file, the exact diff, why, and what triggered it. On approval: apply + changelog
  line, and re-run the guard's tests if a hook or rule changed.

## 6. Verify (optional mechanical layer)

If the project provides a mechanical linter / cap-checker (e.g. a `meta-lint` or `caps` script), run
it and ensure it's clean — it covers cross-ref existence, index sync, caps, and filename conventions
faster and more reliably than eyeballing. If not, spot-check inline: touched pointers resolve,
edited indexes match their directories, no file is over cap.

## 7. Commit

Commit the applied changes single-line and imperative, per the `commit` skill. If retro touched
several stores, commit each logical change on its own or summarize the dominant one. Record rule
provenance (who decided, when, quoted) in the rule file itself — not the commit message. Never
push; the user owns remote sync.
