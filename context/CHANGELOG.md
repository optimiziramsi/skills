# context — changelog

Versions of the `context@optimiziramsi` plugin.

## 0.2.0 — 2026-11-12

- Three tiers by position in `CONTEXT_NUDGE_AT`: a hint that is shown to the user only (the model
  is no longer asked to mention it), the action level (the former handoff text), and a new red
  alert at the last level — finish the step, start nothing new, hand off now.
- Default thresholds are `20,30,55` (were `30,50,60`).
- An answer to a nudge ("remind me later", "keep going", "topic done") is only read from a short
  prompt (≤ 200 characters). A long prompt that quotes one of those phrases — a subagent's report,
  a pasted document — no longer silences the nudges for the session.

## 0.1.0 — 2026-10-18

- New: context-window nudges read from the transcript's usage — 30% / 50% / 60% of a 1M window by
  default, the last one saying plainly that a handoff is needed; "remind me later" / "keep going"
  / "topic done" answers are honored for the session. `/repack` writes the handoff for a
  `/clear` → `/continue` refresh.
