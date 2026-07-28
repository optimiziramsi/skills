#!/usr/bin/env python3
"""Self-tests for commit-nudge. Run: python3 commit/tests/test_commit_nudge.py"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke  # noqa: E402

check = Check()
NUDGE = hook("commit/hooks/commit-nudge.py")
WROTE = '{"message":{"content":[{"type":"tool_use","name":"Edit"}]}}\n'
READ_ONLY = '{"message":{"content":[{"type":"tool_use","name":"Read"}]}}\n'

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    def git(repo, *args):
        subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                       capture_output=True, check=True)

    for name, content in (("main", "a"), ("sib", "b")):
        repo = os.path.join(tmp, name)
        subprocess.run(["git", "init", "-q", repo], capture_output=True, check=True)
        pathlib.Path(repo, content).write_text(content)
        git(repo, "add", content)
        git(repo, "commit", "-qm", content)
    main, sib = os.path.join(tmp, "main"), os.path.join(tmp, "sib")

    transcripts = {}
    for name, line in (("wrote", WROTE), ("readonly", READ_ONLY)):
        transcripts[name] = os.path.join(tmp, f"{name}.jsonl")
        pathlib.Path(transcripts[name]).write_text(line)

    session = [0]

    def run(transcript="wrote", extra=None, env=None, fresh=True):
        """One Stop-hook call. A fresh session id by default, so the one-shot marker is out of play."""
        if fresh:
            session[0] += 1
        return invoke(NUDGE, {"session_id": f"cn-{os.getpid()}-{session[0]}",
                              "transcript_path": transcripts[transcript]},
                      env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": main,
                           **({"COMMIT_NUDGE_EXTRA_DIRS": extra} if extra else {}),
                           **(env or {})})

    tracked = {main: "a", sib: "b"}

    def dirty(repo):
        with open(os.path.join(repo, tracked[repo]), "a") as fh:
            fh.write("dirty\n")

    def clean(repo):
        git(repo, "checkout", "-q", "--", tracked[repo])

    check("a clean tree is silent", run()[0] == 0)

    dirty(main)
    rc, _, err = run()
    check("a dirty tree nags with exit 2", rc == 2 and "uncommitted change(s)" in err, err)
    check("a read-only session is not nagged", run("readonly")[0] == 0)
    check("kill-switch disarms", run(env={"STOP_NUDGE_OFF": "1"})[0] == 0)
    check("stop_hook_active is never re-blocked", invoke(
        NUDGE, {"session_id": "x", "stop_hook_active": True,
                "transcript_path": transcripts["wrote"]},
        env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": main})[0] == 0)

    # one-shot: the same session + same tree state must not nag twice
    session[0] += 1
    check("the first stop on a state nags", run(fresh=False)[0] == 2)
    check("the same state does not nag again", run(fresh=False)[0] == 0)
    pathlib.Path(main, "untracked.txt").write_text("new")
    check("a changed state nags again", run(fresh=False)[0] == 2)

    os.unlink(os.path.join(main, "untracked.txt"))
    clean(main)

    # sibling trees
    check("a clean main and no siblings is silent", run()[0] == 0)
    dirty(sib)
    rc, _, err = run(extra="../sib")
    check("a dirty sibling nags", rc == 2 and "../sib" in err, err)
    check("an absolute sibling path also works", run(extra=sib)[0] == 2)
    check("a sibling path is resolved against the project, not the cwd",
          "../sib" in run(extra="../sib")[2])
    clean(sib)
    check("a clean sibling is silent", run(extra="../sib")[0] == 0)
    check("an unreadable sibling dir is ignored", run(extra="../nope")[0] == 0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
