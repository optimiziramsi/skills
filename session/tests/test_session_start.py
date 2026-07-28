#!/usr/bin/env python3
"""Self-tests for the SessionStart snapshot. Run: python3 session/tests/test_session_start.py"""
import datetime
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke  # noqa: E402

check = Check()
START = hook("session/hooks/session-start.py")

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    repo = os.path.join(tmp, "repo")
    plain = os.path.join(tmp, "plain")
    os.makedirs(plain)
    subprocess.run(["git", "init", "-q", "-b", "main", repo], capture_output=True, check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "init"], capture_output=True, check=True)

    def run(project, env=None):
        return invoke(START, {}, env={"CLAUDE_PROJECT_DIR": project, **(env or {})})[1]

    check("a git repo yields a state line", "[session] branch=main" in run(repo), run(repo))
    check("the state line counts uncommitted files", "0 uncommitted file(s)" in run(repo))
    check("a non-repo is silent", run(plain) == "")
    check("kill-switch disarms", run(repo, {"SESSION_START_OFF": "1"}) == "")

    pathlib.Path(repo, ".agent").mkdir()
    pathlib.Path(repo, ".agent", "handoff.md").touch()
    check("handoff freshness is surfaced", "handoff.md last updated" in run(repo), run(repo))
    check("an uncommitted handoff says so", "never committed" in run(repo), run(repo))

    pathlib.Path(repo, ".todo").write_text("# a comment\n\n- one\n- two\n")
    check("todo items are counted, comments and blanks excluded",
          "[session] .todo has 2 item line(s)." in run(repo), run(repo))

    changelog = pathlib.Path(repo, ".agent", "instructions-changelog.md")
    changelog.write_text(f"Last audit: {datetime.date.today()}\n")
    check("a fresh audit stamp is silent", "instructions-audit" not in run(repo), run(repo))
    stale = datetime.date.today() - datetime.timedelta(days=45)
    changelog.write_text(f"Last audit: {stale}\n")
    check("a stale audit stamp nudges", "last instructions-audit 45d ago" in run(repo), run(repo))
    changelog.write_text("no stamp here\n")
    check("an unparseable stamp is ignored", "instructions-audit" not in run(repo), run(repo))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
