#!/usr/bin/env bash
# worktree-write-guard.sh — PreToolUse: Edit|Write|MultiEdit|NotebookEdit
# Blocks a file-mutating tool whose absolute target escapes the active git worktree into the main
# checkout (or a sibling worktree). Mitigates anthropics/claude-code#36182 (Class-1: main-rooted file_path).
# Toggle off:  export WORKTREE_GUARD_DISABLE=1
# Block mode:  export WORKTREE_GUARD_MODE=json|exit2   (default json — reliable for Edit/Write per #13744)
set -uo pipefail
[ "${WORKTREE_GUARD_DISABLE:-0}" = "1" ] && exit 0
MODE="${WORKTREE_GUARD_MODE:-json}"

INPUT=$(cat)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
[ -z "$CWD" ] && exit 0
git -C "$CWD" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
WT_ROOT=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null) || exit 0
GIT_DIR=$(git -C "$CWD" rev-parse --absolute-git-dir 2>/dev/null) || exit 0
GIT_COMMON=$(cd "$CWD" && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd) || exit 0
[ "$GIT_DIR" = "$GIT_COMMON" ] && exit 0          # not a linked worktree → nothing to leak to
MAIN_ROOT=$(dirname "$GIT_COMMON")

# every absolute file path anywhere in tool_input (Edit/Write/NotebookEdit top-level; MultiEdit nested)
while IFS= read -r FILE; do
  [ -z "$FILE" ] && continue
  case "$FILE" in
    /*) : ;;
    *) continue ;;                                # only absolute paths can leak
  esac
  case "$FILE" in
    "$WT_ROOT"/*) continue ;;                     # inside the worktree → fine
    "$MAIN_ROOT"/*)                               # escapes into main checkout / sibling worktree → block
      REASON="worktree-write-guard (#36182): target '$FILE' is outside this worktree ('$WT_ROOT') — it resolves into the main checkout '$MAIN_ROOT'. Re-issue with a path under $WT_ROOT/."
      if [ "$MODE" = "exit2" ]; then
        printf '%s\n' "$REASON" >&2
        exit 2
      else
        jq -n --arg r "$REASON" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
        exit 0
      fi
      ;;
    *) continue ;;                                # outside the repo entirely (~/.claude, /tmp, other repos) → allow
  esac
done < <(printf '%s' "$INPUT" | jq -r '[.tool_input | .. | objects | (.file_path // empty), (.notebook_path // empty)] | .[]' 2>/dev/null)
exit 0
