#!/usr/bin/env python3
"""SessionStart — a tiny state snapshot plus freshness nudges, as session context.

stdout becomes the context. Every line is CONDITIONAL: absent files never error, so this is
safe in any repo. Keep it short — it runs on every start / resume / clear.

Off: SESSION_START_OFF=1 (the git line fires in ANY git repo, not just opsi-scaffolded ones,
so a project that doesn't want it needs a switch)
"""
import datetime
import os
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
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


def main():
    if hookio.flag("SESSION_START_OFF"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if hookio.git(project, "rev-parse", "--is-inside-work-tree") != "true":
        return

    branch = hookio.git(project, "branch", "--show-current") or "?"
    dirty = len((hookio.git(project, "status", "--porcelain") or "").splitlines())
    last = hookio.git(project, "log", "-1", "--format=%h %s (%cr)") or "?"
    lines = [f"[session] branch={branch} · {dirty} uncommitted file(s) · last: {last}"]

    handoff = os.path.join(project, ".agent", "handoff.md")
    if os.path.isfile(handoff):
        age = hookio.git(project, "log", "-1", "--format=%cr", "--", ".agent/handoff.md")
        lines.append(f"[session] .agent/handoff.md last updated {age or 'never committed'} "
                     "— read it before working (/continue).")

    todo = os.path.join(project, ".todo")
    if os.path.isfile(todo):
        items = [ln for ln in pathlib.Path(todo).read_text(errors="replace").splitlines()
                 if ln.strip() and not ln.lstrip().startswith("#")]
        if items:
            lines.append(f"[session] .todo has {len(items)} item line(s).")

    # a missing interpreter disarms the python guards SILENTLY (they fail open by design)
    if shutil.which("python3") is None:
        lines.append("[session] ⚠️ python3 not found — the guard hooks cannot run; enforcement "
                     "is DISARMED until fixed.")

    days = audit_age_days(os.path.join(project, ".agent", "instructions-changelog.md"))
    if days is not None and days > AUDIT_STALE_DAYS:
        lines.append(f"[session] last instructions-audit {days}d ago (>{AUDIT_STALE_DAYS}) — "
                     "consider an instructions audit (/instructions-audit if available).")

    print("\n".join(lines))


hookio.guard(main)
