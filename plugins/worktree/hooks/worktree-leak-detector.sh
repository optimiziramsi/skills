#!/usr/bin/env bash
# worktree-leak-detector.sh — PostToolUse: Edit|Write|MultiEdit|NotebookEdit
# After a file-tool call that targeted a path INSIDE the worktree, checks whether the SAME relative path
# became dirty in the main checkout — the signature of the #36182 Class-2 leak (a git-tracked file whose
# worktree-rooted edit still resolved to main). Cannot prevent it (already happened) but surfaces it loudly
# so the edit isn't silently lost. Toggle off: export WORKTREE_LEAK_DETECT_DISABLE=1
set -uo pipefail
[ "${WORKTREE_LEAK_DETECT_DISABLE:-0}" = "1" ] && exit 0

INPUT=$(cat)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
[ -z "$CWD" ] && exit 0
git -C "$CWD" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
WT_ROOT=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null) || exit 0
GIT_DIR=$(git -C "$CWD" rev-parse --absolute-git-dir 2>/dev/null) || exit 0
GIT_COMMON=$(cd "$CWD" && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd) || exit 0
[ "$GIT_DIR" = "$GIT_COMMON" ] && exit 0
MAIN_ROOT=$(dirname "$GIT_COMMON")

LEAKED=""
while IFS= read -r FILE; do
  [ -z "$FILE" ] && continue
  case "$FILE" in
    "$WT_ROOT"/*) REL="${FILE#"$WT_ROOT"/}" ;;
    *) continue ;;                                # only files the tool claims to have written in-worktree
  esac
  if [ -n "$(git -C "$MAIN_ROOT" status --porcelain -- "$REL" 2>/dev/null)" ]; then
    LEAKED="${LEAKED}\n  • $MAIN_ROOT/$REL"
  fi
done < <(printf '%s' "$INPUT" | jq -r '[.tool_input | .. | objects | (.file_path // empty), (.notebook_path // empty)] | .[]' 2>/dev/null)

if [ -n "$LEAKED" ]; then
  printf 'LEAK SUSPECTED (#36182 Class-2): a worktree edit also dirtied the main checkout at:%b\nThe edit may have landed in main, not the worktree. Verify, then recover with:\n  git -C %s checkout -- <path>   # discard the leaked copy in main\nand re-apply the edit using a path under %s/.\n' "$LEAKED" "$MAIN_ROOT" "$WT_ROOT" >&2
  exit 2
fi
exit 0
