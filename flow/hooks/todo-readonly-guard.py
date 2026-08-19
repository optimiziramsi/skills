#!/usr/bin/env python3
"""`.todo` is the USER's parking lot — LLM-readonly. Two roles, one file:

  PreToolUse[Edit|Write|MultiEdit|NotebookEdit|Bash]  deny any agent write to `.todo`; agent
      deferrals belong in `.todo-inbox` (always writable), which the user triages themselves.
  UserPromptSubmit (--prompt-scan)  arm writes for THIS session when the user's prompt says
      "ALLOW TODO" — a triage-todo session edits `.todo` constantly, so the user arms it once.

Off: TODO_GUARD_DISABLE=1 · one-off bash bypass: prefix the command with TODO_GUARD_SKIP=1
"""
import os
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

ARM_PHRASE = re.compile(r"allow\s+\.?todo", re.I)

# `.todo` as a WRITE TARGET — not a mere mention, and not an unrelated redirect like
# `2>/dev/null`. One readable alternative per channel; add a channel by adding a row.
#
# Two anti-false-positive rules, both learned the hard way (2026-08-19: a `python3 - <<EOF` whose
# PROSE said "install for project" and, twelve lines later, "stale .todo item", was denied as a
# write): a verb counts only at the START of a command segment, so a quoted or heredoc'd mention
# is inert, and no rule may pair a verb on one line with a target on another.
SEGMENT = r"(?:^|[\n;|&(])\s*(?:\w+=\S+\s+)*"   # start of a command, past any env prefix
SAME_LINE = r"[^|;&\n]*"                        # a verb and its target share one line
# Trailing boundary as a lookahead, not a character: the old `(["'\s]|$)` missed every target
# followed by shell punctuation — `(rm .todo)`, `rm .todo; echo x`. `(?![\w.-])` still refuses
# `.todos` / `.todo.bak` / `.todo-inbox`.
DOT_TODO = r"""["']?([\w./-]*/)?\.todo(?![\w.-])"""
WRITES_TODO = re.compile("|".join((
    r"""(^|[^0-9&])>{1,2}[^\S\n]*""" + DOT_TODO,  # echo x > .todo   /  sort f >> .todo
    r"\btee\b" + SAME_LINE + r"\.todo",           # ... | tee -a .todo
    SEGMENT + r"(sed|perl)\s+-i" + SAME_LINE + r"\.todo",   # sed -i '' s/a/b/ .todo
    SEGMENT + r"(mv|cp|rm|truncate|install)\b" + SAME_LINE + r"\s" + DOT_TODO,
    r"\bof=\S*\.todo",                           # dd of=.todo
)))

REASON = (".todo is LLM-readonly (user-owned parking lot). Park deferrals in .todo-inbox "
          "instead. If this write is genuinely wanted, the USER replies with 'ALLOW TODO' to "
          "arm this session (or prefixes bash with TODO_GUARD_SKIP=1).")


def arm_flag(session_id):
    """Path of this session's arm marker. Session-scoped so arming never outlives the chat."""
    return os.path.join(tempfile.gettempdir(), f"claude-todo-allow-{session_id}")


def main():
    if hookio.flag("TODO_GUARD_DISABLE"):
        return
    data = hookio.payload()
    session_id = data.get("session_id") or ""

    if "--prompt-scan" in sys.argv:
        if ARM_PHRASE.search(data.get("prompt") or ""):
            if session_id:
                pathlib.Path(arm_flag(session_id)).touch()
            hookio.notice("🔓 .todo writes ARMED for this session (user ALLOW).")
        return

    if session_id and os.path.exists(arm_flag(session_id)):
        return                                       # the user armed this session

    tool = data.get("tool_name") or ""
    if tool == "Bash":
        command = (data.get("tool_input") or {}).get("command", "")
        if command.startswith("TODO_GUARD_SKIP=1 "):
            return
        if WRITES_TODO.search(command.replace(".todo-inbox", "")):  # inbox is the blessed path
            hookio.deny(f"todo-readonly-guard: bash command writes to .todo. {REASON}")
    elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        for path in hookio.tool_paths(data):
            if path == ".todo" or path.endswith("/.todo"):
                hookio.deny(f"todo-readonly-guard: '{path}' targets .todo. {REASON}")


hookio.guard(main)
