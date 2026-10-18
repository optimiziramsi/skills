#!/usr/bin/env python3
"""SessionStart — say when an installed plugin has a newer version in its marketplace, or a
marketplace this project installs from has gained a plugin; then refresh the marketplaces in the
background (throttled) so the next session sees what's new.

Reads Claude Code's plugin records only — no network in the hook itself. Silent when there is
nothing to say. A repeated identical report is shown once a day, not every session.

Config: UPKEEP_MARKETPLACES (comma-separated; default: every marketplace this project installs
        from), UPKEEP_REFRESH_HOURS (default 24; 0 = never refresh)
Off: UPKEEP_OFF=1
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _upkeep as up  # noqa: E402

REPEAT_SECS = 24 * 3600


def main():
    if up.hookio.flag("UPKEEP_OFF"):
        return
    project = up.hookio.project_dir(up.hookio.payload())
    rep = up.report(project)
    up.refresh_in_background(rep["marketplaces"])
    line = up.summary(rep)
    if not line:
        return
    marker = os.path.join(up.data_dir(), "last-report-" + hashlib.sha1(os.path.realpath(project).encode()).hexdigest()[:12])
    digest = hashlib.sha1(line.encode()).hexdigest()
    try:
        with open(marker) as handle:
            old = handle.read()
        if old == digest and time.time() - os.path.getmtime(marker) < REPEAT_SECS and not rep["new"]:
            return
    except OSError:
        pass
    try:
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        with open(marker, "w") as handle:
            handle.write(digest)
    except OSError:
        pass
    print(json.dumps({"systemMessage": line, "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": line + " If the user asks to apply it, use the upkeep skill."}}))


if __name__ == "__main__":
    up.hookio.guard(main)
