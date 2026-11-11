#!/usr/bin/env python3
"""Self-tests for the SessionStart snapshot. Run: python3 session/tests/test_session_start.py"""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, scratch_repo  # noqa: E402

check = Check()
START = hook("hooks/session-start.py")
os.environ.pop("SESSION_START_OFF", None)

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

    # ── housekeeping facts are Stop notes (test_session_end.py), never start context ──
    pathlib.Path(repo, ".agent").mkdir()
    pathlib.Path(repo, ".agent", "handoff.md").touch()
    pathlib.Path(repo, ".todo").write_text("- one\n- two\n")
    stale = datetime.date.today() - datetime.timedelta(days=45)
    pathlib.Path(repo, ".agent", "instructions-changelog.md").write_text(f"Last audit: {stale}\n")
    out = run(repo)
    check("the start context is the state line alone", len(out.splitlines()) == 1, out)
    check("no handoff / .todo / audit line at start",
          not any(word in out for word in ("handoff", ".todo", "audit")), out)

    # a no-python3 PATH that can still run git: the warning needs both
    bindir = os.path.join(tmp, "bin")
    os.makedirs(bindir)
    os.symlink(shutil.which("git"), os.path.join(bindir, "git"))
    check("a missing python3 still warns at start",
          "python3 not found" in run(repo, {"PATH": bindir}), run(repo, {"PATH": bindir}))

    with scratch_repo() as r:
        check("a linked worktree still gets the state line",
              "[session] branch=wtbranch" in run(r.wt), run(r.wt))

    wired = json.load(open(hook("hooks/hooks.json")))["hooks"]
    check("SessionStart runs the snapshot only",
          [h["command"].split("/hooks/")[1].rstrip('"') for group in wired["SessionStart"]
           for h in group["hooks"]] == ["session-start.py"], wired["SessionStart"])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
