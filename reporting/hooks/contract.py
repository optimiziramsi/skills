#!/usr/bin/env python3
"""UserPromptSubmit — inject the output contract, from the project's override if it has one.

First hit wins, project-relative: $REPORT_CONTRACT_FILE → .agent/output-contract.md →
.claude/output-contract.md → the shipped hooks/brevity-reminder.txt. An override that exists but
cannot be read prints a visible DISARMED line instead of silently falling back.

Off: REPORT_GUARD_OFF=1 (silences inject, pulse, and Stop guard)
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402

SHIPPED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brevity-reminder.txt")


def main():
    if hookio.flag("REPORT_GUARD_OFF"):
        return
    text, warning = hookio.override_text(
        "REPORT_CONTRACT_FILE", (".agent/output-contract.md", ".claude/output-contract.md"),
        SHIPPED, hookio.project_dir(hookio.payload()))
    print(f"⚠️ brevity-reminder DISARMED — {warning}." if warning else text.rstrip())


hookio.guard(main)
