#!/usr/bin/env python3
"""PostToolUse — re-inject a one-line output-contract reminder every Nth tool call.

The UserPromptSubmit reminder decays over a long agentic turn; this keeps it in force for
almost no tokens (fires 1-in-REPORT_PULSE_EVERY).

Config: REPORT_PULSE_EVERY (default 10) · off: REPORT_GUARD_OFF=1 (disables the pulse too)
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

REMINDER = ("OUTPUT CONTRACT in force: no text between tool calls; final message = 1 outcome "
            "line + <=5 fact bullets + numbered Q list (omit if none). No narration, headers, "
            "or tables.")


def main():
    if hookio.flag("REPORT_GUARD_OFF"):
        return
    try:
        every = max(1, int(os.environ.get("REPORT_PULSE_EVERY", "10")))
    except ValueError:
        every = 10
    session_id = hookio.payload().get("session_id") or "default"
    counter = pathlib.Path(tempfile.gettempdir()) / f"claude-contract-pulse-{session_id}"
    try:
        count = int(counter.read_text()) + 1
    except (OSError, ValueError):
        count = 1
    counter.write_text(str(count))
    if count % every == 0:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": REMINDER}}))


hookio.guard(main)
