#!/usr/bin/env python3
"""Self-tests for the caps hook. Run: python3 instructions/tests/test_caps.py"""
import json
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, scratch_repo  # noqa: E402

check = Check()
CAPS = hook("hooks/caps.py")
WROTE = '{"message":{"content":[{"type":"tool_use","name":"Edit"}]}}\n'
READ_ONLY = '{"message":{"content":[{"type":"tool_use","name":"Read"}]}}\n'
for var in ("CAPS_GUARD_OFF", "NUDGES_IN_WORKTREE"):
    os.environ.pop(var, None)

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    clean = os.path.join(tmp, "clean")
    fat = os.path.join(tmp, "fat")
    for d in (clean, fat):
        os.makedirs(d)
    pathlib.Path(fat, "CLAUDE.md").write_text("x" * 7000)
    wrote = os.path.join(tmp, "wrote.jsonl")
    readonly = os.path.join(tmp, "readonly.jsonl")
    pathlib.Path(wrote).write_text(WROTE)
    pathlib.Path(readonly).write_text(READ_ONLY)

    session = [0]

    def run(project, event="Stop", env=None, transcript=wrote, fresh=True, **payload):
        if fresh:
            session[0] += 1
        return invoke(CAPS, {"hook_event_name": event, "transcript_path": transcript,
                             "session_id": f"caps-{os.getpid()}-{session[0]}", **payload},
                      env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": project, **(env or {})})

    def note(*args, **kwargs):
        out = run(*args, **kwargs)[1]
        return json.loads(out).get("systemMessage", "") if out.strip() else ""

    # ── nothing at session start ───────────────────────────────────────────
    check("SessionStart is silent even over cap", run(fat, event="SessionStart")[1:] == ("", ""))
    wired = json.load(open(hook("hooks/hooks.json")))["hooks"]
    check("the plugin wires nothing at SessionStart", list(wired) == ["Stop"], list(wired))

    # ── Stop: a note for the user, never a block ───────────────────────────
    check("a clean repo is silent", run(clean)[1] == "")
    rc, out, err = run(fat)
    body = json.loads(out)
    check("an oversized CLAUDE.md is noted",
          body.get("systemMessage") == "[caps] instruction surface over cap:\n"
                                       "  • CLAUDE.md 7000c > 6000c", out)
    check("the note never blocks", rc == 0 and err == "" and "decision" not in body, (rc, err))
    check("the note is a systemMessage only", list(body) == ["systemMessage"], body)
    check("the note carries no instruction", "compact" not in out and "raise" not in out, out)
    check("a read-only session is noted too", "CLAUDE.md 7000c" in note(fat, transcript=readonly))
    check("stop_hook_active is never noted", run(fat, stop_hook_active=True)[1] == "")
    check("an env override raises the cap", run(fat, env={"CAP_CLAUDE": "8000"})[1] == "")
    check("kill-switch disarms", run(fat, env={"CAPS_GUARD_OFF": "1"})[1] == "")

    # ── per-glob and count caps ────────────────────────────────────────────
    os.makedirs(os.path.join(fat, ".claude", "commands"), exist_ok=True)
    pathlib.Path(fat, ".claude", "commands", "big.md").write_text("x" * 900)
    check("an oversized command is noted", ".claude/commands/big.md 900c > 800c" in note(fat))
    for n in range(13):
        os.makedirs(os.path.join(fat, ".claude", "skills", f"s{n}"), exist_ok=True)
    check("a count budget is noted", "13 skills > 12" in note(fat))
    check("a count budget honors its env override",
          "13 skills" not in note(fat, env={"MAX_SKILLS": "20"}))
    os.makedirs(os.path.join(fat, ".agent", "lessons"), exist_ok=True)
    pathlib.Path(fat, ".agent", "lessons", "README.md").write_text("x" * 5000)
    check("the lessons README is exempt from the per-lesson cap",
          ".agent/lessons/README.md 5000c > 4000c" not in note(fat))

    # ── once per session per distinct breach-set ───────────────────────────
    session[0] += 1
    check("the first Stop on a breach-set notes", "over cap" in note(fat, fresh=False))
    check("the same breach-set is not noted twice", run(fat, fresh=False)[1] == "")
    pathlib.Path(fat, "AGENTS.md").write_text("y" * 7000)
    check("a changed breach-set is noted again", "AGENTS.md 7000c" in note(fat, fresh=False))
    check("…and still never blocks", run(fat)[0] == 0)

    # ── a linked worktree is for one topic: no notes ───────────────────────
    with scratch_repo(files={"CLAUDE.md": "x" * 7000}) as r:
        check("the main checkout is noted", "CLAUDE.md 7000c" in note(r.main))
        check("a linked worktree is silent", run(r.wt)[1:] == ("", ""))
        check("NUDGES_IN_WORKTREE=1 restores the note there",
              "CLAUDE.md 7000c" in note(r.wt, env={"NUDGES_IN_WORKTREE": "1"}))

    # ── meta-lint supersedes ───────────────────────────────────────────────
    os.makedirs(os.path.join(fat, ".agent"), exist_ok=True)
    pathlib.Path(fat, ".agent", "meta-lint.json").write_text("{}")
    check("meta-lint.json present → caps stands down", run(fat)[1:] == ("", ""))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
