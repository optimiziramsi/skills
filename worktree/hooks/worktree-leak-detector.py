#!/usr/bin/env python3
"""PostToolUse[Edit|Write|MultiEdit|NotebookEdit] — surface a leak that already happened.

A worktree-rooted edit can still land in the main checkout (claude-code#36182, Class 2). This
cannot prevent that — the write is done — so it checks whether the SAME relative path went
dirty in the main checkout and says so loudly, rather than letting the edit vanish.
Off: WORKTREE_LEAK_DETECT_DISABLE=1
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
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
            "LEAK SUSPECTED (#36182 Class-2): a worktree edit also dirtied the main checkout at:\n"
            + "\n".join(leaked)
            + "\nThe edit may have landed in main, not the worktree. Verify, then recover with:\n"
            f"  git -C {ctx['main_root']} checkout -- <path>   # discard the leaked copy in main\n"
            f"and re-apply the edit using a path under {ctx['wt_root']}/.",
            file=sys.stderr,
        )
        sys.exit(2)


hookio.guard(main)
