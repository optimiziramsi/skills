#!/usr/bin/env python3
"""UserPromptSubmit + PostToolUse — say how full the context window is, and when to hand off.

The CCD UI no longer shows a context bar, so this is the signal. Usage is read from the
transcript: the last main-thread assistant message's `usage` (input + cache-creation +
cache-read + output tokens) against CONTEXT_WINDOW_TOKENS. Each threshold in CONTEXT_NUDGE_AT
nudges once per session; the LAST one is the handoff level, where the nudge says plainly that a
handoff is needed (`/repack`, then `/clear` → `/continue`). A hook cannot clear or compact a
session itself — it can only say so.

The user answers a pending nudge in plain words, caught on their next prompt:
  "remind me later" / "snooze" / "not now"   → nudge again after CONTEXT_SNOOZE_PCT more
  "keep going" / "no handoff" / "stop reminding" → silence this level (a higher one still nudges)
  "topic done" / "already done"              → the handoff is moot: no more nudges this session

Config: CONTEXT_WINDOW_TOKENS (default 1000000), CONTEXT_NUDGE_AT (default 30,50,60 — percent),
        CONTEXT_SNOOZE_PCT (default 5)
Off: CONTEXT_NUDGE_OFF=1
"""
import json
import os
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402

TAIL_BYTES = 2 * 1024 * 1024
SNOOZE = re.compile(r"\b(remind me( again)? later|snooze|not now|later please)\b", re.I)
QUIET = re.compile(r"\b(keep going|no handoff|don'?t remind|stop reminding)\b", re.I)
DONE = re.compile(r"\b(topic (is )?(already )?done|already done|topic'?s done)\b", re.I)


def window():
    return max(1, hookio.setting_int("CONTEXT_WINDOW_TOKENS", 1_000_000))


def levels():
    raw = hookio.setting("CONTEXT_NUDGE_AT", "30,50,60")
    out = sorted({int(x) for x in re.findall(r"\d+", raw) if 0 < int(x) <= 100})
    return out or [30, 50, 60]


def snooze_tokens():
    return max(1, hookio.setting_int("CONTEXT_SNOOZE_PCT", 5)) * window() // 100


def used_tokens(transcript):
    """Tokens in context as of the last main-thread assistant message, or None."""
    try:
        with open(transcript, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - TAIL_BYTES))
            lines = handle.read().decode("utf-8", "replace").splitlines()
    except (OSError, TypeError):
        return None
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        usage = (entry.get("message") or {}).get("usage") or {}
        keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
        total = sum(int(usage.get(k) or 0) for k in keys)
        if total:
            return total
    return None


def state_path(session_id):
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or tempfile.gettempdir()
    return os.path.join(base, f"context-nudge-{session_id or 'unknown'}.json")


def load(path):
    try:
        with open(path) as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def save(path, state):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as handle:
            json.dump(state, handle)
    except OSError:
        pass


def fmt(tokens):
    return f"{tokens / 1_000_000:.2f}M" if tokens >= 1_000_000 else f"{tokens // 1000}k"


def nudge(pct, level, tokens, handoff):
    """(user-visible line, model context) for crossing `level`."""
    head = f"[context] {pct}% of {fmt(window())} used ({fmt(tokens)} tokens)"
    if handoff:
        return (f"{head} — time for a handoff: /repack writes it, then /clear → /continue. "
                "Reply 'remind me later', 'keep going', or 'topic done' to override.",
                f"Context usage is {pct}% of the window — the handoff level. Tell the user plainly, "
                "at the next stopping point (finish the current step first), that a handoff is "
                "needed now: offer /repack (writes the handoff; then they run /clear and /continue). "
                "If they say 'remind me later', 'keep going', or 'topic done', accept it — this "
                "hook records the answer.")
    return (f"{head} — fine for now; plan a handoff at the next topic boundary.",
            f"Context usage is {pct}% of the window (nudge level {level}%). Mention it in one line "
            "at the next natural pause; no action is needed yet.")


def emit(event, user_line=None, context=None):
    out = {}
    if user_line:
        out["systemMessage"] = user_line
    if context:
        out["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": context}
    if out:
        print(json.dumps(out))


def main():
    if hookio.flag("CONTEXT_NUDGE_OFF"):
        return
    data = hookio.payload()
    event = data.get("hook_event_name") or "UserPromptSubmit"
    path = state_path(data.get("session_id"))
    state = load(path)
    if state.get("done"):
        return
    tokens = used_tokens(data.get("transcript_path"))

    # the user's answer to a pending nudge
    prompt = data.get("prompt") or ""
    if event == "UserPromptSubmit" and state.get("pending") and prompt:
        ack = None
        if DONE.search(prompt):
            state.update(done=True, pending=None)
            ack = "The user says the topic is done, so no handoff is needed: offer /clear when they are ready. No more context nudges this session."
        elif SNOOZE.search(prompt) and tokens:
            state.update(renudge_at=tokens + snooze_tokens(), pending=None)
            ack = f"The user snoozed the context nudge; it will remind again at ~{fmt(tokens + snooze_tokens())} tokens."
        elif QUIET.search(prompt):
            state.update(renudge_at=None, pending=None)
            ack = f"The user chose to keep going; the {state.get('shown')}% context nudge is silenced."
        if ack:
            save(path, state)
            emit(event, context=ack)
            return

    if not tokens:
        return
    pct = tokens * 100 // window()
    crossed = [l for l in levels() if pct >= l]
    if not crossed:
        return
    level, handoff = crossed[-1], crossed[-1] == levels()[-1]
    renudge = state.get("renudge_at")
    if level > state.get("shown", 0) or (renudge and tokens >= renudge):
        state.update(shown=level, pending=level, renudge_at=None)
        save(path, state)
        emit(event, *nudge(pct, level, tokens, handoff))


if __name__ == "__main__":
    hookio.guard(main)
