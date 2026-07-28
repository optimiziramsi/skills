#!/usr/bin/env bash
# worktree-detect.sh — SessionStart nudge: if this chat is rooted in a LINKED git worktree
# (git-dir ≠ common-dir), it is almost certainly worktree work (parallel, isolated). Nudge
# toward the `/worktree` protocol; never force it. Silent when the cwd is the main checkout
# (or not a git repo at all).
# Toggle off:  export WORKTREE_GUARD_DISABLE=1   (same switch as the worktree write guard)
# Self-test:   bash worktree-detect.sh --test
[ "${WORKTREE_GUARD_DISABLE:-0}" = "1" ] && exit 0

if [ "${1:-}" = "--test" ]; then
  T=$(mktemp -d); T=$(cd "$T" && pwd -P); trap 'rm -rf "$T"' EXIT
  git -C "$T" init -q -b main repo && git -C "$T/repo" commit -q --allow-empty -m init
  git -C "$T/repo" worktree add -q "$T/wt" -b wtbranch
  fails=0
  out=$(CLAUDE_PROJECT_DIR="$T/repo" bash "$0")
  [ -z "$out" ] && echo "PASS  main checkout → silent" || { echo "FAIL  main checkout: $out"; fails=$((fails+1)); }
  out=$(CLAUDE_PROJECT_DIR="$T/wt" bash "$0")
  grep -q 'Worktree detected' <<<"$out" && echo "PASS  linked worktree → nudge" || { echo "FAIL  linked worktree: $out"; fails=$((fails+1)); }
  out=$(WORKTREE_GUARD_DISABLE=1 CLAUDE_PROJECT_DIR="$T/wt" bash "$0")
  [ -z "$out" ] && echo "PASS  WORKTREE_GUARD_DISABLE=1 → silent" || { echo "FAIL  kill-switch: $out"; fails=$((fails+1)); }
  mkdir -p "$T/plain"
  out=$(CLAUDE_PROJECT_DIR="$T/plain" bash "$0")
  [ -z "$out" ] && echo "PASS  non-repo → silent" || { echo "FAIL  non-repo: $out"; fails=$((fails+1)); }
  if [ "$fails" -eq 0 ]; then echo "all tests passed"; else echo "$fails FAILED"; fi; exit "$fails"
fi

DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
git -C "$DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
GIT_DIR=$(git -C "$DIR" rev-parse --absolute-git-dir 2>/dev/null) || exit 0
GIT_COMMON=$(cd "$DIR" && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd) || exit 0
[ "$GIT_DIR" = "$GIT_COMMON" ] && exit 0          # main checkout → no nudge
cat <<'MSG'
Worktree detected: this session is rooted in a linked git worktree, so this is almost certainly **worktree work** (parallel, isolated development). Consider invoking the `/worktree` skill to load the protocol — by default it reserves a board row in `.agent/worktrees.md` and lands work chunk-by-chunk. Skip only if the coordinator said no reserve / no announcement / no worktree record is needed.
MSG
exit 0
