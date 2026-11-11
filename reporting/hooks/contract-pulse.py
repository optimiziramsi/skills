#!/usr/bin/env python3
"""PostToolUse — keep the output contract in force during a long agentic turn.

Two reminders, at most one per tool call:

  react   the turn's newest assistant text is quoted back the first time a tool call follows it —
          text between tool calls is exactly what the contract forbids, so the correction lands
          at the slip instead of up to N calls later. It also says so when the app's own "the
          user hasn't heard from you" reminder asked for that text. Once per text.
  pulse   otherwise, every Nth tool call re-injects a one-line reminder (fires
          1-in-REPORT_PULSE_EVERY): REPORT_PULSE_TEXT → the active contract's first meaningful
          line → the hardcoded fallback, so an override is reminded in its own words.

Config: REPORT_PULSE_EVERY (default 10), REPORT_PULSE_TEXT (replaces the one-liner)
Off: REPORT_REACT_OFF=1 (the react half only) · REPORT_GUARD_OFF=1 (everything)
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _contract as c  # noqa: E402

REMINDER = ("OUTPUT CONTRACT in force: no text between tool calls; final message = 1 outcome "
            "line + <=5 fact bullets + numbered Q list (omit if none). No narration, headers, "
            "or tables.")
CORRECTION = ("You wrote text between tool calls ({quote}). The user reads one report at the end "
              "and has turned progress lines off: write nothing more until the task is done or "
              "you are blocked on a decision.")
REMINDED = " That holds when the app says the user hasn't heard from you, too."
TAIL_BYTES = 512 * 1024
QUOTE_CHARS = 60


def pulse_text(data):
    """REPORT_PULSE_TEXT → the active contract's first meaningful line → the hardcoded REMINDER."""
    explicit = c.hookio.setting("REPORT_PULSE_TEXT", "")
    if explicit:
        return explicit
    text, warning = c.active(c.hookio.project_dir(data))
    if not warning:
        line = c.pulse_line(text)
        if line:
            return line
    return REMINDER


def state_file(tag, session_id):
    return pathlib.Path(tempfile.gettempdir()) / f"claude-contract-{tag}-{session_id}"


def correction(data, session_id):
    """The react line for the turn's newest text between tool calls, or None. Once per text."""
    if c.hookio.flag("REPORT_REACT_OFF"):
        return None
    seen = c.turns(data.get("transcript_path"), TAIL_BYTES)
    found = c.last_text(seen[-1]["events"]) if seen else None
    if not found:
        return None
    uuid, text, reminded = found
    key = uuid or text[:QUOTE_CHARS]
    marker = state_file("react", session_id)
    try:
        if marker.read_text() == key:
            return None
    except OSError:
        pass
    marker.write_text(key)
    first = text.splitlines()[0]
    quote = json.dumps(first[:QUOTE_CHARS] + ("…" if len(first) > QUOTE_CHARS else ""),
                       ensure_ascii=False)
    return CORRECTION.format(quote=quote) + (REMINDED if reminded else "")


def main():
    if c.hookio.flag("REPORT_GUARD_OFF"):
        return
    try:
        every = max(1, int(os.environ.get("REPORT_PULSE_EVERY", "10")))
    except ValueError:
        every = 10
    data = c.hookio.payload()
    session_id = data.get("session_id") or "default"
    counter = state_file("pulse", session_id)
    try:
        count = int(counter.read_text()) + 1
    except (OSError, ValueError):
        count = 1
    counter.write_text(str(count))
    line = correction(data, session_id) or (pulse_text(data) if count % every == 0 else None)
    if line:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": line}}))


c.hookio.guard(main)
