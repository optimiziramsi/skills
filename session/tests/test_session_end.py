#!/usr/bin/env python3
"""Self-tests for the Stop notes. Run: python3 session/tests/test_session_end.py"""
import datetime
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, scratch_repo  # noqa: E402

check = Check()
END = hook("hooks/session-end.py")
for var in ("SESSION_START_OFF", "NUDGES_IN_WORKTREE"):
    os.environ.pop(var, None)

with scratch_repo(files={".agent/handoff.md": "next up\n"}) as r:
    plain = os.path.join(r.tmp, "plain")
    os.makedirs(plain)

    def stop(project, session, env=None, **payload):
        """(exit code, parsed stdout JSON or {}, raw stdout, stderr) for one Stop."""
        code, out, err = invoke(
            END, {"hook_event_name": "Stop", "session_id": session, **payload},
            env={"TMPDIR": r.tmp, "CLAUDE_PROJECT_DIR": project, **(env or {})})
        return code, (json.loads(out) if out.strip() else {}), out, err

    def note(project, session, env=None, **payload):
        return stop(project, session, env, **payload)[1].get("systemMessage", "")

    # ── the note: user-visible, never blocking, never model context ────────
    code, body, out, err = stop(r.main, "s1")
    check("a committed handoff's age is noted",
          body.get("systemMessage", "").startswith("[session] .agent/handoff.md last updated ")
          and body["systemMessage"].endswith(" ago."), out)
    check("the note carries no instruction", "read it" not in out and "/continue" not in out, out)
    check("the note never blocks", code == 0 and err == "" and "decision" not in body, (code, err))
    check("the note is a systemMessage only", list(body) == ["systemMessage"], body)

    # ── once per session per fact ──────────────────────────────────────────
    check("the same fact is not repeated in a session", stop(r.main, "s1")[2] == "")
    check("a new session notes it again", "handoff.md last updated" in note(r.main, "s2"))
    check("stop_hook_active is never noted", stop(r.main, "s3", stop_hook_active=True)[2] == "")
    check("kill-switch disarms", stop(r.main, "s4", {"SESSION_START_OFF": "1"})[2] == "")
    check("a non-repo is silent", stop(plain, "s5")[2] == "")

    pathlib.Path(r.main, ".todo").write_text("# a comment\n\n- one\n- two\n")
    got = note(r.main, "s1")
    check("todo items are counted, comments and blanks excluded",
          got == "[session] .todo has 2 item line(s).", got)
    pathlib.Path(r.main, ".todo").write_text("- one\n- two\n- three\n")
    got = note(r.main, "s1")
    check("a changed fact is noted again, alone",
          got == "[session] .todo has 3 item line(s).", got)

    pathlib.Path(r.main, ".agent", "handoff.md").write_text("rewritten\n")
    check("an uncommitted handoff edit is not a new fact", stop(r.main, "s1")[2] == "")
    subprocess.run(["git", "-C", r.main, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
                    "-q", "-am", "handoff"], capture_output=True, check=True)
    check("a newly committed handoff is", "handoff.md last updated" in note(r.main, "s1"))

    changelog = pathlib.Path(r.main, ".agent", "instructions-changelog.md")
    changelog.write_text(f"Last audit: {datetime.date.today()}\n")
    check("a fresh audit stamp is silent", stop(r.main, "s1")[2] == "")
    changelog.write_text(f"Last audit: {datetime.date.today() - datetime.timedelta(days=45)}\n")
    got = note(r.main, "s1")
    check("a stale audit stamp is noted, as a fact",
          got == "[session] last instructions-audit 45d ago (>30).", got)
    changelog.write_text("no stamp here\n")
    check("an unparseable stamp is ignored", "audit" not in note(r.main, "s6"))

    fresh = os.path.join(r.tmp, "fresh")
    subprocess.run(["git", "init", "-q", "-b", "main", fresh], capture_output=True, check=True)
    os.makedirs(os.path.join(fresh, ".agent"))
    pathlib.Path(fresh, ".agent", "handoff.md").touch()
    got = note(fresh, "s7")
    check("a never-committed handoff says so",
          got == "[session] .agent/handoff.md has never been committed.", got)

    # ── a linked worktree is for one topic: no notes ───────────────────────
    check("the worktree carries the same files",
          os.path.isfile(os.path.join(r.wt, ".agent", "handoff.md")))
    check("a linked worktree is silent", stop(r.wt, "w1")[2] == "")
    got = note(r.wt, "w1", {"NUDGES_IN_WORKTREE": "1"})
    check("NUDGES_IN_WORKTREE=1 restores the note there", "handoff.md last updated" in got, got)

wired = json.load(open(hook("hooks/hooks.json")))["hooks"]
check("the notes are wired at Stop, not at SessionStart",
      "session-end.py" in json.dumps(wired["Stop"])
      and "session-end.py" not in json.dumps(wired["SessionStart"]))

sys.exit(check.done())
