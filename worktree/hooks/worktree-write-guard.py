#!/usr/bin/env python3
"""PreToolUse[Edit|Write|MultiEdit|NotebookEdit] — keep a worktree's writes inside it.

Blocks a file-mutating tool whose absolute target escapes the active worktree into the main
checkout or a sibling (claude-code#36182, Class 1: main-rooted file_path).
Off: WORKTREE_GUARD_DISABLE=1 · report as stderr+exit 2 instead of JSON: WORKTREE_GUARD_MODE=exit2
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402


def main():
    if hookio.flag("WORKTREE_GUARD_DISABLE"):
        return
    data = hookio.payload()
    ctx = hookio.linked_worktree(data.get("cwd", ""))
    if not ctx:
        return                                      # main checkout / no repo → nothing to leak into
    for path in hookio.tool_paths(data):
        if not path.startswith("/"):
            continue                                # only an absolute path can escape
        if hookio.under(path, ctx["wt_root"]):
            continue                                # inside the worktree — tested FIRST, since the
        if hookio.under(path, ctx["main_root"]):    # worktree may itself sit under the main checkout
            hookio.deny(
                f"worktree-write-guard (#36182): target '{path}' is outside this worktree "
                f"('{ctx['wt_root']}') — it resolves into the main checkout "
                f"'{ctx['main_root']}'. Re-issue with a path under {ctx['wt_root']}/.",
                mode=os.environ.get("WORKTREE_GUARD_MODE", "json"),
            )
        # anywhere else (~/.claude, /tmp, an unrelated repo) is the agent's own business


hookio.guard(main)
