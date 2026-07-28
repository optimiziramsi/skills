#!/usr/bin/env python3
"""PreToolUse[Bash] — the shell channel of the same worktree leak (claude-code#36182).

The write guard only sees file-tool targets; an agent can still reach the main checkout with
`sed -i`, a redirect, or `python3 -c`. Blocks a command that uses a write verb against a
main-checkout path WITHOUT also naming the worktree path.

Off by default (false-positive-prone). On: WORKTREE_BASH_GUARD_ENABLE=1
Report as stderr+exit 2 instead of JSON: WORKTREE_GUARD_MODE=exit2
"""
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

# A redirect counts only when it writes to a FILE: `2>/dev/null`, `2>&1` and `>&2` move file
# descriptors around and are not writes, so the leading char must not be a digit and the target
# must not start with & or >.
WRITE_VERB = re.compile(
    r"(^|[^0-9>])>>?[^>&]"
    r"|(^|\s)(sed\s+-i|tee\s|dd\s|install\s)"
    r"|python3?\s+-c"
)


def main():
    if not hookio.flag("WORKTREE_BASH_GUARD_ENABLE"):
        return
    data = hookio.payload()
    command = (data.get("tool_input") or {}).get("command", "")
    ctx = hookio.linked_worktree(data.get("cwd", ""))
    if not command or not ctx:
        return
    if (WRITE_VERB.search(command)
            and ctx["main_root"] + "/" in command
            and ctx["wt_root"] + "/" not in command):
        hookio.deny(
            f"worktree-bash-guard (#36182 shell channel): command writes into the main checkout "
            f"'{ctx['main_root']}' from worktree '{ctx['wt_root']}' without naming the worktree "
            f"path. If intentional (e.g. recovery), reference the worktree path, or unset "
            f"WORKTREE_BASH_GUARD_ENABLE to turn this guard off.",
            mode=os.environ.get("WORKTREE_GUARD_MODE", "json"),
        )


hookio.guard(main)
