#!/usr/bin/env python3
"""Stop — in a code-first turn, block a final message that carries more inline code than
CODE_FIRST_MAX_FENCE_LINES.

Acts only when the turn was code-first — the session opted in with the idea command, the turn's
last user prompt matches CODE_FIRST_TRIGGER_PATTERN, or CODE_FIRST_INJECT=always. Silent in any
other turn.

Code-first means the proposal is a branch diff, not a snippet in chat. The guard sums the
non-empty lines inside fenced blocks of the turn's final assistant message; over the limit, it
blocks once (stop_hook_active-guarded) and asks for a rewrite: commit it to an idea branch, chat
only the branch name + questions.

Not counted: fences in CODE_FIRST_EXEMPT_LANGS (default bash,sh,zsh,shell,console — commands for
the user to run). Lifted for the turn: the user's last prompt matches CODE_FIRST_ALLOW_PATTERN
(default: prompt / paste / inline / snippet / command) — they asked for paste-ready text.

Config: CODE_FIRST_MAX_FENCE_LINES (default 5; 0 = no counted fences at all)
Off: CODE_FIRST_GUARD_OFF=1 (keeps the injected reminder), CODE_FIRST_OFF=1 (everything)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _codefirst as cf  # noqa: E402


def verdict(prompt, final):
    """The block reason for this turn, or None."""
    if not final:
        return None
    if prompt and cf.allow_pattern().search(cf.user_words(prompt)):
        return None
    lines, limit = cf.counted_fence_lines(final), cf.max_fence_lines()
    if lines <= limit:
        return None
    return (f"code-first: the final message carries {lines} lines of inline code (limit {limit}). "
            f"Commit it to an idea branch instead (`/idea <topic>` → `{cf.prefix()}<topic>`), then "
            "rewrite the reply to carry only the branch name, the key decisions, and the open "
            "questions with a recommendation on each. If the user explicitly asked for paste-ready "
            "text, say so in one line and keep it.")


def main():
    if cf.off() or cf.hookio.flag("CODE_FIRST_GUARD_OFF"):
        return
    data = cf.hookio.payload()
    if data.get("stop_hook_active"):
        return
    prompt, final = cf.last_turn(data.get("transcript_path", ""))
    if not cf.code_first_turn(data.get("session_id"), prompt):
        return
    reason = verdict(prompt, final)
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    cf.hookio.guard(main)
