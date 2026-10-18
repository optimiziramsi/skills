#!/usr/bin/env python3
"""SessionStart — one line naming idea branches older than CODE_FIRST_STALE_DAYS, so they don't rot.

Silent when there are none. Config: CODE_FIRST_STALE_DAYS (default 7; empty = off).
Off: CODE_FIRST_OFF=1
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _codefirst as cf  # noqa: E402


def main():
    days = cf.stale_days()
    if cf.off() or days is None:
        return
    project = cf.hookio.project_dir(cf.hookio.payload())
    stale = [(b, age) for b, age, _ in cf.idea_branches(project) if age >= days]
    if stale:
        names = ", ".join(f"{b} ({age}d)" for b, age in stale)
        cf.hookio.notice(f"[code-first] idea branches older than {days}d: {names} — "
                         "promote, drop, or keep (/idea list).")


if __name__ == "__main__":
    cf.hookio.guard(main)
