# context — know when the context window is getting full

The `context@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

The CCD UI no longer shows a context bar, so this plugin says it: how full the window is, at a
few thresholds, and — at the last one — that it's time for a handoff. `/repack` writes the handoff
so a fresh session (`/clear` → `/continue`) picks the work up with none of the weight.

## Contents

- name: `context-nudge`
  kind: hook
  purpose:
    UserPromptSubmit + PostToolUse — reads the last main-thread assistant message's `usage` from
    the transcript (input + cache-creation + cache-read + output tokens; subagent turns don't
    count) and nudges once per threshold per session: a one-line note for you, a matching line
    for the model. Defaults: **30% / 50% / 60% of a 1M window**. The last threshold is the
    handoff level, where the nudge says plainly that a handoff is needed. Fails open.

- name: `repack`
  kind: skill + command
  purpose:
    Closes what's open, writes the handoff (through the [`session`](../session) plugin's
    `handoff` skill when enabled, else `.agent/handoff.md` directly), then hands you `/clear` →
    `/continue`. A topic that's already done skips the handoff and just offers `/clear`.

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
- `CONTEXT_NUDGE_AT` — percent thresholds, default `30,50,60`; the last is the handoff level.
- `CONTEXT_SNOOZE_PCT` — how much more a "remind me later" waits, default `5`.

## Escape hatches

`CONTEXT_NUDGE_OFF=1` — off entirely.

## Enable

```bash
claude plugin install context@optimiziramsi --scope project
```
