---
name: calibrate
description: >-
  Tune the reporting output contract against real messages — grill-me or A/B compare. Use on
  /calibrate, when the session's rc-stamped contract nudges "run /calibrate", or when the user says
  the reports read wrong ("too fancy", "too terse", "this grated", "dial in the tone", "confirm the
  contract", "flip it to stable"). Repo-side only: it edits the project's own contract, never the
  shipped plugin text.
---

# calibrate — tune the output contract on real reports

The contract that governs reports is a file the project owns (`.agent/output-contract.md`, else the
shipped text). This skill confirms or edits it against what the session actually produced. Advisory:
it never blocks, and it edits only the contract the user tells you to.

The `calibrate` CLI (on PATH while `reporting` is enabled) reads two things, and only reads:
`calibrate contracts` (which text is in force, its `· rc:`/`· stable:` stamp, the active text, and —
when an override is in force — the shipped text to compare against) and `calibrate messages [N]`
(the last N turns' final reports, framed `--- report K ---`).

**Pick a mode first** (default `compare`): `compare` grades the current contract against the other
one on real reports; `grill` re-sets the knobs by asking.

## compare — A/B the last 5 reports

1. Run `calibrate contracts`. If `active-source: shipped` (no project override), there is nothing to
   compare against — say so and offer `grill`, or to write an override at `.agent/output-contract.md`
   first (seed it from the shipped block). Stop here in that case.
2. Run `calibrate messages 5`. For each report, produce **B**: that same report rewritten under the
   *other* contract (the `--- shipped ---` block). The active text's own rendering is **A** (the
   original).
3. Show the pairs and nothing else — numbered, A then B, no commentary, no scores:
   ```
   1A: <original>
   1B: <rewrite under the other contract>
   ```
4. The user answers `A` or `B` per pair, plus one free line — *what grated*. Don't argue; collect.
5. Tally (A = the contract in force). **A wins ≥ 4/5** → offer to flip its first-line stamp
   `· rc: <date> v<n>` → `· stable: <today>` (one Edit to the override). **Otherwise** → list the
   active contract's bullets that the losing reports trace to, as edit candidates, and stop. Don't
   edit the contract in compare mode beyond the stamp flip.
6. Append the record (below).

## grill — re-set the knobs

Ask these six, each with the current default in `[ ]`, each itself plain, one line and a real
fork. One message, numbered:

1. length — `[1 line / 3 bullets / 5 bullets]`
2. casualness — `[dry / buddy]`
3. numbers — `[always / only when they change what I do]`
4. questions — `[numbered list / one spoken line]`
5. context — `[never / one line when it's load-bearing]`
6. code in chat — `[never / paste-ready only]`

Turn the answers into a diff of the active contract file — the override if there is one, else
propose `.agent/output-contract.md` seeded from the shipped text and apply the answers to that.
When the project works code-first (idea branches), commit the edit as an `IDEA:` commit on an
`idea/` branch for the user to review as a diff; otherwise show the file. Append the record.

## The record (both modes)

Append one line to `.agent/output-contract.calibration.md` (create it with a `# output-contract
calibration` header if absent), so the trend is visible across sessions:

```
- <YYYY-MM-DD> · <compare|grill> · <result> · grated: <the user's free line>
```

`<result>` is short: `4/5 A → flipped to stable`, `2/5 A → edit candidates: bullets 3,5`,
`grill → 3 knobs changed`.

## Rules

- Reads come from the `calibrate` CLI; never hand-roll transcript paths or re-parse the stamp.
- Edit only the contract the user asked you to, and only `.agent/…` (never the shipped plugin file).
- The rc nudge is the one automatic trigger; the user runs `/calibrate` when they feel like it.
- `/calibrate` with no mode → ask which, defaulting to `compare`.
