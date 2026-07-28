#!/usr/bin/env python3
"""Self-tests for the caps hook. Run: python3 instructions/tests/test_caps.py"""
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke  # noqa: E402

check = Check()
CAPS = hook("instructions/hooks/caps.py")
WROTE = '{"message":{"content":[{"type":"tool_use","name":"Edit"}]}}\n'
READ_ONLY = '{"message":{"content":[{"type":"tool_use","name":"Read"}]}}\n'

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

    def run(project, event="SessionStart", env=None, transcript=wrote, fresh=True):
        if fresh:
            session[0] += 1
        return invoke(CAPS, {"hook_event_name": event, "transcript_path": transcript,
                             "session_id": f"caps-{os.getpid()}-{session[0]}"},
                      env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": project, **(env or {})})

    # ── SessionStart: informational context ────────────────────────────────
    check("a clean repo is silent", run(clean)[1] == "")
    check("an oversized CLAUDE.md is surfaced", "CLAUDE.md 7000c > 6000c" in run(fat)[1])
    check("SessionStart never blocks", run(fat)[0] == 0)
    check("an env override raises the cap", run(fat, env={"CAP_CLAUDE": "8000"})[1] == "")
    check("kill-switch disarms", run(fat, env={"CAPS_GUARD_OFF": "1"})[1] == "")

    # ── per-glob and count caps ────────────────────────────────────────────
    os.makedirs(os.path.join(fat, ".claude", "commands"), exist_ok=True)
    pathlib.Path(fat, ".claude", "commands", "big.md").write_text("x" * 900)
    check("an oversized command is surfaced",
          ".claude/commands/big.md 900c > 800c" in run(fat)[1])
    for n in range(13):
        os.makedirs(os.path.join(fat, ".claude", "skills", f"s{n}"), exist_ok=True)
    check("a count budget is surfaced", "13 skills > 12" in run(fat)[1])
    check("a count budget honors its env override",
          "13 skills" not in run(fat, env={"MAX_SKILLS": "20"})[1])
    os.makedirs(os.path.join(fat, ".agent", "lessons"), exist_ok=True)
    pathlib.Path(fat, ".agent", "lessons", "README.md").write_text("x" * 5000)
    check("the lessons README is exempt from the per-lesson cap",
          ".agent/lessons/README.md 5000c > 4000c" not in run(fat)[1])

    # ── Stop: blocking nudge, gated and one-shot ───────────────────────────
    rc, _, err = run(fat, event="Stop")
    check("Stop blocks with exit 2", rc == 2 and "over cap" in err, err)
    check("a read-only session is not nudged",
          run(fat, event="Stop", transcript=readonly)[0] == 0)
    check("stop_hook_active is never re-blocked", invoke(
        CAPS, {"hook_event_name": "Stop", "stop_hook_active": True, "transcript_path": wrote},
        env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": fat})[0] == 0)
    session[0] += 1
    check("the first Stop on a breach-set nudges", run(fat, event="Stop", fresh=False)[0] == 2)
    check("the same breach-set does not nudge twice", run(fat, event="Stop", fresh=False)[0] == 0)
    pathlib.Path(fat, "AGENTS.md").write_text("y" * 7000)
    check("a changed breach-set nudges again", run(fat, event="Stop", fresh=False)[0] == 2)

    # ── meta-lint supersedes ───────────────────────────────────────────────
    os.makedirs(os.path.join(fat, ".agent"), exist_ok=True)
    pathlib.Path(fat, ".agent", "meta-lint.json").write_text("{}")
    check("meta-lint.json present → caps stands down", run(fat)[1] == "")
    check("meta-lint.json present → Stop does not block", run(fat, event="Stop")[0] == 0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
