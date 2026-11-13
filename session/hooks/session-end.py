#!/usr/bin/env python3
"""Stop — housekeeping facts as a note for the USER: handoff age, `.todo` count, audit age.

Shown at the end of a turn, never at session start, so a chat does the work it was opened for
instead of treating these as jobs. The note is a `systemMessage`: the user sees it, it is not
model context, and it never blocks the stop. Each fact is shown once per session and again only
when it changes (the handoff got a new commit, the `.todo` count moved). Every line is
conditional on its file existing, so this is safe in any repo.

Silent in a linked git worktree — a worktree is for one topic, cleanup belongs to the main
checkout's chat. NUDGES_IN_WORKTREE=1 shows the notes there too.

Off: SESSION_START_OFF=1 (the same switch as the SessionStart snapshot)
"""
import datetime
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402

AUDIT_STAMP = re.compile(r"Last audit: (\d{4}-\d{2}-\d{2})")
AUDIT_STALE_DAYS = 30


def audit_age_days(path):
    """Days since the `Last audit: YYYY-MM-DD` stamp, or None when absent/unparseable."""
    try:
        match = AUDIT_STAMP.search(pathlib.Path(path).read_text(errors="replace"))
        if not match:
            return None
        stamped = datetime.date.fromisoformat(match.group(1))
    except (OSError, ValueError):
        return None
    return (datetime.date.today() - stamped).days


def facts(project):
    """[(tag, state, line)] — `state` is what makes a fact distinct, so a relative age that
    merely ticks ("4 minutes ago" → "5 minutes ago") is not a new note."""
    found = []

    if os.path.isfile(os.path.join(project, ".agent", "handoff.md")):
        commit = hookio.git(project, "log", "-1", "--format=%H %cr", "--", ".agent/handoff.md")
        sha, _, age = (commit or "").partition(" ")
        found.append(("handoff", sha or "uncommitted",
                      f"[session] .agent/handoff.md last updated {age}." if sha else
                      "[session] .agent/handoff.md has never been committed."))

    todo = os.path.join(project, ".todo")
    if os.path.isfile(todo):
        items = [ln for ln in pathlib.Path(todo).read_text(errors="replace").splitlines()
                 if ln.strip() and not ln.lstrip().startswith("#")]
        if items:
            found.append(("todo", str(len(items)),
                          f"[session] .todo has {len(items)} item line(s)."))

    days = audit_age_days(os.path.join(project, ".agent", "instructions-changelog.md"))
    if days is not None and days > AUDIT_STALE_DAYS:
        found.append(("audit", str(days),
                      f"[session] last /instructions:audit {days}d ago (>{AUDIT_STALE_DAYS})."))
    return found


def main():
    if hookio.flag("SESSION_START_OFF"):
        return
    data = hookio.payload()
    if data.get("stop_hook_active"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if hookio.git(project, "rev-parse", "--is-inside-work-tree") != "true":
        return
    if hookio.linked_worktree(project) and not hookio.flag("NUDGES_IN_WORKTREE"):
        return
    session = data.get("session_id")
    lines = [line for tag, state, line in facts(project)
             if hookio.first_time(f"session-{tag}", session, state)]
    if lines:
        hookio.notice("\n".join(lines))


hookio.guard(main)
