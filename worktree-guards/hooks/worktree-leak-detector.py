#!/usr/bin/env python3
"""PostToolUse[Edit|Write|MultiEdit|NotebookEdit] — surface a leak that already happened.

A worktree-rooted edit can still land in the main checkout (claude-code#36182, Class 2). This
cannot prevent that — the write is done — so it checks whether the SAME relative path went
dirty in the main checkout and reports it, rather than letting the edit vanish. The report gives
no recovery command: a dirty same-path file in the main checkout can be the user's own edit, so
what happens there is the user's call.
Off: WORKTREE_LEAK_DETECT_DISABLE=1
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402


def main():
    if hookio.flag("WORKTREE_LEAK_DETECT_DISABLE"):
        return
    data = hookio.payload()
    ctx = hookio.linked_worktree(data.get("cwd", ""))
    if not ctx:
        return
    leaked = []
    for path in hookio.tool_paths(data):
        if not hookio.under(path, ctx["wt_root"]):
            continue                                # only paths the tool claims it wrote in-worktree
        rel = os.path.relpath(os.path.realpath(path), ctx["wt_root"])
        if hookio.git(ctx["main_root"], "status", "--porcelain", "--", rel):
            leaked.append(f"  • {os.path.join(ctx['main_root'], rel)}")
    if leaked:
        print(
            "worktree-leak-detector: leak suspected — after this worktree edit, the same path "
            "is also modified in the main checkout:\n"
            + "\n".join(leaked)
            + "\nThe edit may have landed there, or it may be the user's own change. Do not change "
            "anything in the main checkout. Stop and tell the user.",
            file=sys.stderr,
        )
        sys.exit(2)


hookio.guard(main)
