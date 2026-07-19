#!/usr/bin/env bash
# worktree-detect.sh — SessionStart nudge: if this chat is rooted in a LINKED git worktree
# (git-dir ≠ common-dir), it is almost certainly worktree work (parallel, isolated). Nudge
# toward the `/worktree` protocol; never force it. Silent when the cwd is the main checkout
# (or not a git repo at all).
DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
git -C "$DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
GIT_DIR=$(git -C "$DIR" rev-parse --absolute-git-dir 2>/dev/null) || exit 0
GIT_COMMON=$(cd "$DIR" && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd) || exit 0
[ "$GIT_DIR" = "$GIT_COMMON" ] && exit 0          # main checkout → no nudge
cat <<'MSG'
Worktree detected: this session is rooted in a linked git worktree, so this is almost certainly **worktree work** (parallel, isolated development). Consider invoking the `/worktree` skill to load the protocol — by default it reserves a board row in `.agent/worktrees.md` and lands work chunk-by-chunk. Skip only if the coordinator said no reserve / no announcement / no worktree record is needed.
MSG
exit 0
