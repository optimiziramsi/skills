#!/usr/bin/env python3
"""UserPromptSubmit — inject the output contract, from the project's override if it has one.

First hit wins, project-relative: $REPORT_CONTRACT_FILE → .agent/output-contract.md →
.claude/output-contract.md → the shipped hooks/brevity-reminder.txt. An override that exists but
cannot be read prints a visible DISARMED line instead of silently falling back.

When the active contract's first line is stamped `· rc: <date> v<n>` and older than REPORT_RC_DAYS
(default 7), one advisory line is appended — once per session — nudging /calibrate. Advisory only;
a `· stable:` or unstamped contract is never nudged.

Off: REPORT_GUARD_OFF=1 (silences inject, pulse, and Stop guard)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _contract as c  # noqa: E402


def main():
    if c.hookio.flag("REPORT_GUARD_OFF"):
        return
    data = c.hookio.payload()
    text, warning = c.active(c.hookio.project_dir(data))
    if warning:
        print(f"⚠️ brevity-reminder DISARMED — {warning}.")
        return
    text = text.rstrip()
    nudge = c.rc_nudge(text, c.rc_days())
    if nudge and c.hookio.first_time("contract-rc", data.get("session_id"), nudge):
        text += "\n\n" + nudge
    print(text)


c.hookio.guard(main)
