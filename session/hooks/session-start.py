#!/usr/bin/env python3
"""SessionStart — a one-line state snapshot, as session context.

stdout becomes the context, so it carries only what the work at hand needs: the branch, the
uncommitted count, the last commit. Housekeeping facts (handoff age, `.todo` count, audit age)
are NOT printed here — they are user notes at Stop (`session-end.py`). Keep it short: it runs on
every start / resume / clear.

Off: SESSION_START_OFF=1 (the git line fires in ANY git repo, not just scaffolded ones,
so a project that doesn't want it needs a switch)
"""
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402


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

    # a missing interpreter disarms the python guards SILENTLY (they fail open by design)
    if shutil.which("python3") is None:
        lines.append("[session] ⚠️ python3 not found — the guard hooks cannot run; enforcement "
                     "is DISARMED until fixed.")

    print("\n".join(lines))


hookio.guard(main)
