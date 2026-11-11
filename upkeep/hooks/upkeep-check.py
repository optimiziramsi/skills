#!/usr/bin/env python3
"""Stop — tell the USER when an installed plugin has a newer version in its marketplace, or a
marketplace this project installs from has gained a plugin; then refresh the marketplaces in the
background (throttled) so the next session sees what's new.

A note, not a job: it is a `systemMessage` (the user sees it, it is not model context) and it
never blocks the stop. The check runs once per session, at its first Stop — nothing is printed at
session start, so a chat does the work it was opened for. Silent in a linked git worktree (a
worktree is for one topic; cleanup belongs to the main checkout's chat) unless
NUDGES_IN_WORKTREE=1.

Reads Claude Code's plugin records only — no network in the hook itself. Silent when there is
nothing to say. A repeated identical report is shown once a day, not every session.

Config: UPKEEP_MARKETPLACES (comma-separated; default: every marketplace this project installs
        from), UPKEEP_REFRESH_HOURS (default 24; 0 = never refresh)
Off: UPKEEP_OFF=1
"""
import hashlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _upkeep as up  # noqa: E402

REPEAT_SECS = 24 * 3600


def main():
    if up.hookio.flag("UPKEEP_OFF"):
        return
    data = up.hookio.payload()
    if data.get("stop_hook_active"):
        return
    project = up.hookio.project_dir(data)
    if up.hookio.linked_worktree(project) and not up.hookio.flag("NUDGES_IN_WORKTREE"):
        return
    # one check per session: report() consumes "new" as it reads, so a second look in the same
    # session would only repeat part of the first
    session = data.get("session_id")
    if session and not up.hookio.first_time("upkeep", session, "checked"):
        return
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
    up.hookio.notice(line)


if __name__ == "__main__":
    up.hookio.guard(main)
