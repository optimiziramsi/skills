#!/usr/bin/env python3
"""Self-tests for the reporting topic — the Stop guard and the contract pulse.

Run: python3 reporting/tests/test_reporting.py
"""
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke, load_module  # noqa: E402

check = Check()
PULSE = hook("reporting/hooks/contract-pulse.py")
report_guard = load_module(hook("reporting/hooks/report-guard.py"), "report_guard")


# ── report-guard: what counts as a contract violation ──────────────────────
def clean(name, want_clean, text):
    problems = report_guard.violations(text)
    check(name, (not problems) == want_clean, problems)


clean("a terse report passes", True,
      "Guard shipped and self-tests pass.\n- 17 tests green\n- wired into hooks.json\n"
      "Q:\n1. enable in CI?")
clean("narration is caught", False, "Let me check the config first.")
clean("\"now I'll\" is caught", False, "Now I'll wire the hook into settings.")
clean("\"I'm going to\" is caught", False, "I'm going to refactor the parser next.")
clean("markdown headers are caught", False, "## Summary\nAll done.")
clean("a table is caught", False, "| a | b |\n|---|---|\n| 1 | 2 |")
clean("over-length is caught", False, "\n".join(f"line {i}" for i in range(25)))
clean("fenced code is exempt from the shape checks", True,
      "Done.\n```\nlet me check inside code is fine\n## header in code fine\n```\n- one fact")
clean("exactly 18 lines still passes", True, "\n".join(f"- fact {i}" for i in range(18)))


tmp = os.path.realpath(tempfile.mkdtemp())
try:
    def fire(session_id, times=1, env=None):
        """Call the pulse `times` times; return the output of the LAST call."""
        out = ""
        for _ in range(times):
            out = invoke(PULSE, {"session_id": session_id},
                         env={"TMPDIR": tmp, **(env or {})})[1]
        return out

    sid = f"pulse-{os.getpid()}"
    check("calls 1-9 stay silent",
          all(fire(f"{sid}-a") == "" for _ in range(9)))
    check("the 10th call re-injects the contract",
          "additionalContext" in fire(f"{sid}-b", times=10))
    check("the 20th call fires again", "OUTPUT CONTRACT" in fire(f"{sid}-c", times=20))
    check("REPORT_PULSE_EVERY tunes the cadence",
          "additionalContext" in fire(f"{sid}-d", times=3, env={"REPORT_PULSE_EVERY": "3"}))
    check("kill-switch disarms",
          fire(f"{sid}-e", times=10, env={"REPORT_GUARD_OFF": "1"}) == "")
    check("a bad REPORT_PULSE_EVERY falls back to the default",
          "additionalContext" in fire(f"{sid}-f", times=10, env={"REPORT_PULSE_EVERY": "junk"}))
    check("counters are per session",
          fire(f"{sid}-g", times=5) == "" and fire(f"{sid}-h", times=5) == "")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
