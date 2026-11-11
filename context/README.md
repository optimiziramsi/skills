# context — know when the context window is getting full

The `context@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

The CCD UI no longer shows a context bar, so this plugin says it: how full the window is, at a
few thresholds — first a hint for you, then that it's time for a handoff, then that it is needed
now. `/repack` writes the handoff
so a fresh session (`/clear` → `/continue`) picks the work up with none of the weight.

## Contents

- name: `context-nudge`
  kind: hook
  purpose:
    UserPromptSubmit + PostToolUse — reads the last main-thread assistant message's `usage` from
    the transcript (input + cache-creation + cache-read + output tokens; subagent turns don't
    count) and nudges once per threshold per session, in three tiers (below). Defaults:
    **20% / 30% / 55% of a 1M window** — 200k / 300k / 550k tokens. Fails open.

- name: `repack`
  kind: skill + command
  purpose:
    Closes what's open, writes the handoff (through the [`session`](../session) plugin's
    `handoff` skill when enabled, else `.agent/handoff.md` directly), then hands you `/clear` →
    `/continue`. A topic that's already done skips the handoff and just offers `/clear`.

## The three tiers

What a threshold says depends on its place in the sorted `CONTEXT_NUDGE_AT` list:

- **Hint** (default 20%) — a one-line note for you only. The model is told nothing, so it does not
  stop to mention it mid-task.
- **Action** (default 30%) — the note for you says it's time for a handoff, and the model is told to
  say so at its next stopping point and offer `/repack`.
- **Red alert** (default 55%) — past the safe range. The note says to hand off now, and the model is
  told to finish the step it is in, start nothing new, and say in its next report that a handoff is
  needed now.

The last level is always the red alert and the one before it the action level; every earlier level
is a hint. With two levels the first is the action level; a single level is the action level.

## Answering a nudge

Reply in plain words on your next prompt — the hook records it for the session:

- **"remind me later"** / "snooze" / "not now" — nudge again after another `CONTEXT_SNOOZE_PCT`
  (default 5%) of the window.
- **"keep going"** / "no handoff" / "stop reminding" — silence that level; a higher one still
  nudges.
- **"topic done"** / "already done" — the handoff is moot: no more nudges this session.

Only an answer to a pending nudge counts, so "keep going" in an ordinary prompt changes nothing.
A hook can't run `/clear` or `/compact` — those stay yours.

## Settings

In a settings.json `env` block — `~/.claude/settings.json` for every project, the project's
`.claude/settings.json` to share, `.claude/settings.local.json` for yourself:

- `CONTEXT_WINDOW_TOKENS` — window size, default `1000000`. Set `200000` for 200k-window models.
- `CONTEXT_NUDGE_AT` — percent thresholds, default `20,30,55`; any number of levels. The last is
  the red alert, the one before it the action level, earlier ones are hints (see above).
- `CONTEXT_SNOOZE_PCT` — how much more a "remind me later" waits, default `5`.

## Escape hatches

`CONTEXT_NUDGE_OFF=1` — off entirely.

## Enable

```bash
claude plugin install context@optimiziramsi --scope project
```
