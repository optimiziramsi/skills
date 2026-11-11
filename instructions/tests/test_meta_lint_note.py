#!/usr/bin/env python3
"""The meta-lint Stop note, end to end as the hook runs it (the engine's own logic is covered by
`bin/meta-lint --test`). Run: python3 instructions/tests/test_meta_lint_note.py"""
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, scratch_repo  # noqa: E402

check = Check()
ENGINE = hook("bin/meta-lint")
CONFIG = json.dumps({"checks": ["size"],
                     "size": {"caps": [{"path": "CLAUDE.md", "cap": 100, "unit": "chars"}]}})
NOTE = "[meta-lint] 1 finding(s) — 1 size."
for var in ("META_LINT_OFF", "NUDGES_IN_WORKTREE"):
    os.environ.pop(var, None)

with scratch_repo(files={".agent/meta-lint.json": CONFIG, "CLAUDE.md": "x" * 200}) as r:
    def run(project, session, mode="--end-note", env=None, **payload):
        return invoke(ENGINE, {"hook_event_name": "Stop", "session_id": session, **payload},
                      env={"TMPDIR": r.tmp, "CLAUDE_PROJECT_DIR": project, **(env or {})},
                      args=[mode])

    rc, out, err = run(r.main, "n1")
    check("findings are a systemMessage for the user", json.loads(out) == {"systemMessage": NOTE}, out)
    check("the note never blocks", rc == 0 and err == "", (rc, err))
    check("the note carries no instruction", "Run the" not in out and "compact" not in out, out)
    check("the same text is not repeated in a session", run(r.main, "n1")[1:] == ("", ""))
    check("stop_hook_active is never noted", run(r.main, "n2", stop_hook_active=True)[1] == "")
    check("kill-switch disarms", run(r.main, "n3", env={"META_LINT_OFF": "1"})[1] == "")
    check("a linked worktree is silent", run(r.wt, "n4")[:2] == (0, ""))
    check("NUDGES_IN_WORKTREE=1 restores the note there",
          NOTE in json.loads(run(r.wt, "n4", env={"NUDGES_IN_WORKTREE": "1"})[1])["systemMessage"])
    check("--fast keeps working by hand", run(r.main, "n5", mode="--fast")[1].startswith(
        "meta: 1 finding(s) — 1 size."))

    os.remove(os.path.join(r.main, "CLAUDE.md"))
    check("a clean tree is silent", run(r.main, "n6")[:2] == (0, ""))

wired = json.load(open(hook("hooks/hooks.json")))["hooks"]
commands = [h["command"] for group in wired.get("Stop", []) for h in group["hooks"]]
check("the note and the gate are both wired at Stop",
      any("--end-note" in c for c in commands) and any(c.endswith("--stop") for c in commands), commands)
check("nothing is wired at SessionStart, and --fast is not a hook",
      list(wired) == ["Stop"] and not any("--fast" in c for c in commands), list(wired))

sys.exit(check.done())
