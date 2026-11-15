#!/usr/bin/env python3
"""Stop — housekeeping facts as a note for the USER: handoff age, `.todo` count, audit age.

Shown at the end of a turn, never at session start, so a chat does the work it was opened for
instead of treating these as jobs. The note is a `systemMessage`: the user sees it, it is not
model context, and it never blocks the stop. The handoff and audit facts are shown once per
session and again only when they change (the handoff got a new commit). The `.todo` count is
shown only when it CHANGED since it was last noted for this repo — a parking lot that sits
still is not news to every new chat; the last noted count lives in the plugin's data dir.
Every line is conditional on its file existing, so this is safe in any repo.

Silent in a linked git worktree — a worktree is for one topic, cleanup belongs to the main
checkout's chat. NUDGES_IN_WORKTREE=1 shows the notes there too.

Off: SESSION_START_OFF=1 (the same switch as the SessionStart snapshot)
"""
import datetime
import hashlib
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


def todo_marker(project):
    """Where this repo's last noted `.todo` count is kept — outside the repo, across sessions."""
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    data = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(config, "plugins", "data", "session")
    return os.path.join(data, "todo-" + hashlib.sha1(os.path.realpath(project).encode()).hexdigest()[:12])


def noted_todo(project):
    """The `.todo` count last noted for this repo, or None when none was."""
    try:
        return int(pathlib.Path(todo_marker(project)).read_text().strip())
    except (OSError, ValueError):
        return None


def remember_todo(project, count):
    """Record `count` as noted; an emptied `.todo` (0) forgets, so a refill is news again."""
    marker = todo_marker(project)
    try:
        if count:
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            pathlib.Path(marker).write_text(str(count))
        elif os.path.exists(marker):
            os.remove(marker)
    except OSError:
        pass


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
        was = noted_todo(project)
        if not items:
            remember_todo(project, 0)
        elif len(items) != was:
            found.append(("todo", str(len(items)), f"[session] .todo has {len(items)} item line(s)"
                          + (f" (was {was})." if was is not None else ".")))

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
    project = hookio.session_root(data)
    if hookio.git(project, "rev-parse", "--is-inside-work-tree") != "true":
        return
    if hookio.linked_worktree(project) and not hookio.flag("NUDGES_IN_WORKTREE"):
        return
    session = data.get("session_id")
    lines = []
    for tag, state, line in facts(project):
        if hookio.first_time(f"session-{tag}", session, state):
            lines.append(line)
            if tag == "todo":
                remember_todo(project, int(state))
    if lines:
        hookio.notice("\n".join(lines))


hookio.guard(main)
