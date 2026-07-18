---
name: instructions-audit
description: De-rot the agent instruction system — after many sessions of accretion, keep it SMALL, TRUE, and NON-DUPLICATED. Sweeps for broken pointers, dead/duplicate rules, truth-vs-reality drift, cap breaches, and enforcement drift; applies safe fixes (T2) directly and batches risky ones (T3) into one proposal. Use when a size cap trips, when instructions contradict reality, after heavy rule churn, roughly monthly, or when the user says "instructions audit" / "audit the setup" / "what's stale".
---

# Instructions audit — keep the system small, true, and non-duplicated

After many sessions of accretion the instruction set drifts: pointers rot, rules outlive what they
governed, the same fact ends up in three files, caps creep. This audit repairs that.

Assumes the `.agent/` house layout. Governance: **safe fixes apply directly (T2); risky changes are
proposed (T3)** — see § Apply.

## 1. Mechanical pass first (if available)

If the project has a mechanical linter / cap-checker (a `meta-lint`, `audit.sh`, or `caps` script),
run it FIRST and fold its output into the findings verbatim — it owns the cheap, exhaustive checks
(cross-ref existence, index sync, caps, filename conventions, frontmatter shape, wrapper parity)
far more reliably than greps. Don't re-derive what it already covers. If there's no such script, do
the inline checks below.

## 2. Delegate the sweep

Launch the `instructions-auditor` agent for the read-only discovery pass — it reads the whole
instruction surface and returns a severity-ranked findings list without polluting the main context.
You orchestrate and decide what to fix; the agent only finds.

## 3. Checklist (verify each; the agent does the reading)

1. **Reference integrity** — every path, command, link, and ID (`R##`, `lesson <slug>`, skill/agent
   name) referenced in `CLAUDE.md`, `.claude/**`, `.agent/**` exists. Check markdown links AND
   inline backtick paths. Missing → find the rename (`git log --diff-filter=R`) and fix, or remove.
2. **Rule liveness** — a rule is dead ONLY if the thing it governs is GONE. Verify against actual
   code/config, never memory. Dead → retire; merely unexercised ≠ dead. Never weaken a
   hook-enforced invariant on your own judgment — that's always T3.
3. **Truth vs reality** (the highest-value check — everything else verifies *form*, this verifies
   *truth*). For each instruction doc: date its last change (`git log -1 --format=%as -- <doc>`),
   then read what changed since in the code it describes
   (`git log --oneline --since=<date> -- <governed paths>`). Claims the code has outgrown are
   findings — fix at the source.
4. **Duplication & contradictions** — the same fact in two homes (allowed only: a one-line pointer +
   detail in the canonical home). Instruction files disagreeing with each other or with reality.
   Consolidate to the single owner; reduce the rest to pointers. Flag duplicates even when they
   currently agree — duplication is future drift.
5. **Enforcement health** — run the hook self-tests (they must all pass). For every `[ENFORCED]` /
   `[WARNED]` tag, confirm the named guard still exists and still matches the behavior; a tag with
   no guard gets downgraded to `[HONOR]`, or the guard gets fixed — never leave a lying tag. A rule
   change needs its matching hook + fixture in the same commit.
6. **Caps & compaction** — check every doc/skill/agent against its cap (flag files within ~10% too).
   Any breach → compact by precedence **merge → route → tighten → retire**. Meaning moves, it
   doesn't vanish; live files hold zero "(kept for history)" content — git is the archive. **Never
   raise a cap to fit** (that's T3).
7. **Wrapper parity** — commands ↔ skills are 1:1, and command wrappers carry no logic:

   ```bash
   for c in .claude/commands/*.md; do n=$(basename "$c" .md); \
     [ -f ".claude/skills/$n/SKILL.md" ] || echo "ORPHAN wrapper: $c"; done
   for s in .claude/skills/*/; do n=$(basename "$s"); \
     [ -f ".claude/commands/$n.md" ] || echo "MISSING wrapper: $n"; done
   ```
8. **Skill description vs content** — sample a few skills: does the frontmatter `description` still
   match what the body does? (Drifts when a skill evolves but its description doesn't.)
9. **Housekeeping** (whatever the project keeps) — process a drift log if present and clear the
   handled lines; scan a denials/telemetry log for repeated same-shape denials (a miscalibrated rule
   or a missing legit path) and truncate after fixing; archive plans whose changes are committed;
   re-stamp a doc's `reviewed:` date ONLY after actually re-verifying it.

## 4. Verify before cutting

For every "stale/dead" finding, verify against code/config YOURSELF before acting. When a rule is
doubtful-but-possibly-alive, flag it in the report — don't delete on suspicion.

## 5. Apply by tier

- **Safe (T2)** — merge a duplicate into its canonical home, fix a broken pointer, tighten wording,
  compact over-cap content by moving narrative into git history, retire a verifiably-dead rule:
  apply directly, one line each in `.agent/instructions-changelog.md`.
- **Risky (T3)** — add/remove a rule, change a cap, change any hook/skill/agent/settings behavior:
  do NOT apply. Batch ALL into ONE proposal (target file, exact diff, why, trigger). Apply only what
  is approved; a hook/rule change also re-runs the guard tests.

## 6. Close

- Re-run the mechanical pass (must be clean) and the hook self-tests (must pass).
- Update the `Last audit: YYYY-MM-DD` stamp at the bottom of the changelog.
- Commit single-line per the `commit` skill. Update the handoff only if the audit changed the repo's
  actual status.
- Report a compact table: check | status | fixed / needs-user, then list any decisions awaited.
