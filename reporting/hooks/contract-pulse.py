#!/usr/bin/env python3
"""PostToolUse — re-inject a one-line output-contract reminder every Nth tool call.

The UserPromptSubmit reminder decays over a long agentic turn; this keeps it in force for
almost no tokens (fires 1-in-REPORT_PULSE_EVERY).

The pulsed line follows the active contract, so an override is reminded in its own words:
REPORT_PULSE_TEXT → the active contract's first meaningful line → the hardcoded fallback.

Config: REPORT_PULSE_EVERY (default 10), REPORT_PULSE_TEXT (replaces the one-liner) · off: REPORT_GUARD_OFF=1 (disables the pulse too)
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


def main():
    if c.hookio.flag("REPORT_GUARD_OFF"):
        return
    try:
        every = max(1, int(os.environ.get("REPORT_PULSE_EVERY", "10")))
    except ValueError:
        every = 10
    data = c.hookio.payload()
    session_id = data.get("session_id") or "default"
    counter = pathlib.Path(tempfile.gettempdir()) / f"claude-contract-pulse-{session_id}"
    try:
        count = int(counter.read_text()) + 1
    except (OSError, ValueError):
        count = 1
    counter.write_text(str(count))
    if count % every == 0:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": pulse_text(data)}}))


c.hookio.guard(main)
