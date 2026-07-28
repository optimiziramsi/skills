#!/usr/bin/env python3
"""SessionStart — nudge toward the `/worktree` protocol when this chat is rooted in one.

A session whose cwd is a LINKED worktree is almost certainly parallel, isolated work. Nudge,
never force; silent in the main checkout or outside a repo.
Off: WORKTREE_GUARD_DISABLE=1 (the same switch as the write guard)
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

NUDGE = (
    "Worktree detected: this session is rooted in a linked git worktree, so this is almost "
    "certainly **worktree work** (parallel, isolated development). Consider invoking the "
    "`/worktree` skill to load the protocol — by default it reserves a board row in "
    "`.agent/worktrees.md` and lands work chunk-by-chunk. Skip only if the coordinator said "
    "no reserve / no announcement / no worktree record is needed."
)


def main():
    if hookio.flag("WORKTREE_GUARD_DISABLE"):
        return
    # SessionStart carries no cwd worth trusting — the project dir is the session's root
    if hookio.linked_worktree(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()):
        print(NUDGE)


hookio.guard(main)
