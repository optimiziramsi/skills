#!/usr/bin/env python3
"""Self-tests for todo-readonly-guard. Run: python3 flow/tests/test_todo_guard.py"""
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke  # noqa: E402

check = Check()
GUARD = hook("flow/hooks/todo-readonly-guard.py")
SID = f"todo-guard-selftest-{os.getpid()}"
FLAG = os.path.join(tempfile.gettempdir(), f"claude-todo-allow-{SID}")


def call(tool, tool_input, env=None):
    return invoke(GUARD, {"session_id": SID, "tool_name": tool, "tool_input": tool_input},
                  env=env)[1]


def denies(name, tool, tool_input):
    check(name, '"deny"' in call(tool, tool_input), call(tool, tool_input))


def allows(name, tool, tool_input, env=None):
    out = call(tool, tool_input, env=env)
    check(name, out == "", out)


pathlib.Path(FLAG).unlink(missing_ok=True)
try:
    # ── file tools ─────────────────────────────────────────────────────────
    denies("deny Edit .todo", "Edit", {"file_path": "/repo/.todo"})
    denies("deny Write .todo", "Write", {"file_path": "/repo/.todo"})
    denies("deny a bare relative .todo", "Edit", {"file_path": ".todo"})
    denies("deny MultiEdit's nested .todo", "MultiEdit", {"edits": [{"file_path": "/repo/.todo"}]})
    allows("allow .todo-inbox", "Edit", {"file_path": "/repo/.todo-inbox"})
    allows("allow an ordinary file", "Edit", {"file_path": "/repo/src/x.ts"})
    allows("allow a file merely named like .todo", "Edit", {"file_path": "/repo/my.todo.bak"})

    # ── bash write channels ────────────────────────────────────────────────
    denies("deny append redirect", "Bash", {"command": "echo x >> .todo"})
    denies("deny truncate redirect", "Bash", {"command": "sort items > .todo"})
    denies("deny a quoted redirect target", "Bash", {"command": 'echo x > "./.todo"'})
    denies("deny sed -i", "Bash", {"command": 'sed -i "" s/a/b/ .todo'})
    denies("deny perl -i", "Bash", {"command": "perl -i -pe s/a/b/ .todo"})
    denies("deny tee -a", "Bash", {"command": "echo x | tee -a .todo"})
    denies("deny mv onto .todo", "Bash", {"command": "mv draft.md .todo"})
    denies("deny rm", "Bash", {"command": "rm .todo"})
    denies("deny dd of=", "Bash", {"command": "dd if=x of=.todo"})
    denies("deny a verb after &&", "Bash", {"command": "cd /repo && rm .todo"})
    denies("deny a verb after ;", "Bash", {"command": "echo hi; rm .todo"})
    denies("deny a verb behind an env prefix", "Bash", {"command": "FOO=1 rm .todo"})
    denies("deny a verb in a subshell", "Bash", {"command": "(rm .todo)"})
    denies("deny a target followed by punctuation", "Bash", {"command": "rm .todo; echo done"})
    allows("allow a longer name that merely starts with .todo", "Bash",
           {"command": "echo x >> .todos"})

    # ── bash reads stay free ───────────────────────────────────────────────
    allows("allow a read", "Bash", {"command": "cat .todo"})
    allows("allow rg with a stderr redirect", "Bash",
           {"command": "rg -n x .todo bin/loop 2>/dev/null | head -20"})
    allows("allow a grep pipe", "Bash", {"command": "grep -n foo .todo | head"})
    allows("allow a write to .todo-inbox", "Bash", {"command": "echo x >> .todo-inbox"})
    allows("allow the TODO_GUARD_SKIP=1 bypass", "Bash",
           {"command": "TODO_GUARD_SKIP=1 echo x >> .todo"})
    # Regression 2026-08-19: a heredoc that PARKED text in .todo-inbox was denied because its
    # prose said "install for project" and, lines later, "stale .todo item".
    allows("allow a verb and a mention on different lines of a heredoc", "Bash",
           {"command": 'python3 - <<EOF\ns = "enabledPlugins true, install for project"\n'
                       't = "stale .todo item is superseded"\nEOF'})
    allows("allow a quoted mention mid-line", "Bash",
           {"command": 'git commit -m "install notes for the .todo file"'})
    allows("kill-switch disarms", "Edit", {"file_path": "/repo/.todo"},
           env={"TODO_GUARD_DISABLE": "1"})

    # ── arming ─────────────────────────────────────────────────────────────
    out = invoke(GUARD, {"session_id": SID, "prompt": "nothing relevant"}, args=["--prompt-scan"])[1]
    check("a plain prompt does not arm", not os.path.exists(FLAG), out)
    out = invoke(GUARD, {"session_id": SID, "prompt": "ok, ALLOW TODO for this one"},
                 args=["--prompt-scan"])[1]
    check("the ALLOW phrase arms the session", os.path.exists(FLAG), out)
    allows("an armed session may write .todo", "Edit", {"file_path": "/repo/.todo"})
    pathlib.Path(FLAG).unlink(missing_ok=True)
    denies("disarming restores the block", "Edit", {"file_path": "/repo/.todo"})
finally:
    pathlib.Path(FLAG).unlink(missing_ok=True)

sys.exit(check.done())
