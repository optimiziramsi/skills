# reporting — the lean-reporting output contract, enforced

The `reporting@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

The house **output contract**: total silence while working (zero text between tool calls), then
exactly one short report — **the answer first (1–2 plain sentences) + 0–5 bullets that each carry
a fact or decision + a numbered `Q:` list** (omitted if empty). The answer comes at the barest
level that answers; more only when asked. It is written the way one dev talks to another: real
names not placeholders, plain words, a question is the thing + the two choices + your pick. It
stays on what was asked — no side-topics, no offers of other work — and a short report is no
reason for shallow work. No narration, headers or tables. Two things may be said mid-task: only the
`Q:` list when blocked on a decision, and one line naming what is being waited for when a turn has
to end while background work still runs. The app's own "the user hasn't heard from you" reminder
is not an exception.

**Opt-in and opinionated** (like the `commit` plugin): enable it only if you want this specific
convention. It's aggressive by design — the Stop guard *blocks* a violating final message and forces
a rewrite.

## Contents

- name: `contract`
  kind: hook
  purpose:
    UserPromptSubmit — injects the full contract text with every prompt. The text is the
    project's own when it has one — first hit wins, project-relative: `$REPORT_CONTRACT_FILE` →
    `.agent/output-contract.md` → `.claude/output-contract.md` → the shipped
    `hooks/brevity-reminder.txt`. An override that exists but can't be read (or a
    `REPORT_CONTRACT_FILE` that doesn't exist) prints a visible "⚠️ brevity-reminder DISARMED" line
    instead of silently falling back. When the active contract's first line is stamped `· rc: <date>
    v<n>` and older than `REPORT_RC_DAYS` (default 7), one advisory line is appended once per session
    — "run /calibrate to confirm or edit". A `· stable:` or unstamped contract is never nudged.

- name: `contract-pulse`
  kind: hook
  purpose:
    PostToolUse — two reminders, at most one per tool call. **React:** the first time a tool call
    follows a piece of assistant text, that text is quoted back with "you wrote text between tool
    calls" — the correction lands at the slip, once per text, and says so when the app's own "the
    user hasn't heard from you" reminder asked for it. **Pulse:** otherwise a one-line reminder
    every Nth tool call (default 10, `REPORT_PULSE_EVERY`), so the contract doesn't decay over a
    long agentic turn. The pulsed line follows the active contract: `REPORT_PULSE_TEXT` → the
    contract's first meaningful line (frame and stamp stripped) → a hardcoded fallback. So an
    override is reminded in its own words, for free.

- name: `report-guard`
  kind: hook
  purpose:
    Stop — reads the turn's final assistant message from the transcript; **blocks** it (one
    rewrite, `stop_hook_active`-guarded) on process narration, headers, tables, or gross
    over-length (`REPORT_GUARD_MAX_LINES`, default 18). Fenced code blocks are exempt from shape
    checks — limiting inline code is the [`code-first`](../code-first) plugin's job. Self-test:
    `tests/test_reporting.py`.

- name: `calibrate`
  kind: skill + command (`/calibrate`)
  purpose:
    Tune the contract on real reports without a chat like the one that first wrote it. `compare`
    A/Bs the session's last reports under the active contract vs. the shipped one and, when the
    active text wins, offers to flip its stamp `· rc:` → `· stable:`; `grill` re-sets the knobs by
    asking six plain questions. Edits only the project's own `.agent/output-contract.md`, never the
    shipped text; logs each run to `.agent/output-contract.calibration.md`. Backed by the read-only
    `calibrate` CLI (`bin/`, on PATH while the plugin is enabled). `calibrate midturn` counts the
    text written between tool calls across the project's sessions — per model and contract stamp,
    split into *unprompted* and *reminded* (asked for by the app's own reminder) — so a contract
    edit is judged by a number, not by feel.

## Why three hooks, not one

A single injection decays: models drift back to narrating over a 50-tool-call turn. The trio covers
the whole lifecycle — contract stated at prompt time, kept warm mid-turn, and *verified* at stop.
The Stop guard is what gives the convention teeth; the injections are what keep the guard from
firing often. `/calibrate` closes the loop: the contract itself improves from what the session saw.

## Settings (env)

| Var | Default | Effect |
|---|---|---|
| `REPORT_CONTRACT_FILE` | — | explicit contract path (project-relative or absolute); wins over the `.agent`/`.claude` lookup |
| `REPORT_PULSE_EVERY` | `10` | re-pulse cadence (1-in-N tool calls) |
| `REPORT_PULSE_TEXT` | — | replaces the pulse one-liner outright |
| `REPORT_REACT_OFF` | — | `1` turns off the quote-back of text between tool calls (the pulse stays) |
| `REPORT_GUARD_MAX_LINES` | `18` | the Stop guard's over-length threshold |
| `REPORT_RC_DAYS` | `7` | how stale an `rc:`-stamped contract gets before the once-per-session nudge |

The `· rc: <YYYY-MM-DD> v<n>` / `· stable: <YYYY-MM-DD>` stamp is an optional tail on the contract's
first line; it drives the nudge and the `/calibrate` flip, nothing else.

## Escape hatch

`REPORT_GUARD_OFF=1` (user-set) silences all three hooks. Fail-open: a missing dependency or
unreadable transcript never bricks a session.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "optimiziramsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "reporting@optimiziramsi": true }
}
```

One command — `/calibrate` — and its skill; everything else is pure enforcement of a reporting style.
