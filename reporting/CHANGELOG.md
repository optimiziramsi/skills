# reporting — changelog

Versions of the `reporting@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.2.1-dev.1

- Stop guard no longer false-positives when the final message *quotes* a banned phrase, header or
  pipe (e.g. a report explaining the guard's own "Let me…" ban): inline `"…"`, `'…'` and `` `…` ``
  spans are now blanked before the narration / header / table checks run, the same way the triple-
  backtick fenced blocks already were. Single-quoted spans are boundary-guarded so an apostrophe
  (don't, I'll) can't pair up and swallow real narration, and the line-count check still runs on the
  un-blanked text — real narration is still caught.

## 0.2.0 — 2026-11-02

- Dev-to-dev PLAIN block in the shipped contract: plain names over ids, the decision itself over
  "confirm as written", order-and-dependency over calendar, a question as the thing + the two
  choices + your pick. Dropped "terse" (it produced id soup) — plain beats short.
- `/calibrate` (skill + command, backed by the read-only `bin/calibrate` CLI): `compare` A/Bs the
  session's last reports under the active vs. the shipped contract and, when the active text wins,
  offers to flip its stamp `· rc:` → `· stable:`; `grill` re-sets the knobs by asking six plain
  questions. Logs each run to `.agent/output-contract.calibration.md`.
- The contract's first line may carry a `· rc: <date> v<n>` / `· stable: <date>` stamp. A stale
  `rc:` contract appends a once-per-session "run /calibrate" nudge (`REPORT_RC_DAYS`, default 7);
  advisory only, nothing blocks. A `· stable:` or unstamped contract is never nudged.
- The mid-turn pulse now follows the active contract — `REPORT_PULSE_TEXT` → the contract's first
  meaningful line (frame and stamp stripped) → the hardcoded fallback — so an override is reminded
  in its own words.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (its `reporting` topic). Enable it per project with `claude plugin install reporting@optimiziramsi --scope project`.
- The injected contract can be replaced per repo: `REPORT_CONTRACT_FILE` → `.agent/output-contract.md`
  → `.claude/output-contract.md` → the shipped text; a broken override prints a visible DISARMED line.
- `REPORT_PULSE_TEXT` replaces the mid-turn pulse one-liner.
