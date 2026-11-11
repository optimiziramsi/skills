#!/usr/bin/env python3
"""Stop — one user-visible line naming idea branches older than CODE_FIRST_STALE_DAYS.

A housekeeping fact for the user, never a job for the model: it is a `systemMessage` only, shown
once per session per distinct text, never while stop_hook_active, and it never blocks. Silent when
there are none, and in a linked git worktree unless NUDGES_IN_WORKTREE=1.

Config: CODE_FIRST_STALE_DAYS (default 7; empty = off), NUDGES_IN_WORKTREE=1
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
    data = cf.hookio.payload()
    if data.get("stop_hook_active") or data.get("hook_event_name", "Stop") != "Stop":
        return
    project = cf.hookio.project_dir(data)
    if cf.hookio.linked_worktree(project) and not cf.hookio.flag("NUDGES_IN_WORKTREE"):
        return
    stale = [(b, age) for b, age, _ in cf.idea_branches(project) if age >= days]
    if not stale:
        return
    names = ", ".join(f"{b} ({age}d)" for b, age in stale)
    text = f"[code-first] idea branches older than {days}d: {names} (/idea list shows them)."
    if cf.hookio.first_time("code-first-stale", data.get("session_id"), text):
        cf.hookio.notice(text)


if __name__ == "__main__":
    cf.hookio.guard(main)
