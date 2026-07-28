#!/usr/bin/env bash
# worktree-bash-guard.sh — PreToolUse: Bash
# Blocks a shell command that uses a write-verb against a main-checkout path while NOT also naming the
# worktree path. Covers the #36182 "shell channel" (agents falling back to sed -i / redirection).
# Enable (off by default — false-positive-prone): export WORKTREE_BASH_GUARD_ENABLE=1
# Block mode:  export WORKTREE_GUARD_MODE=json|exit2   (default json)
set -uo pipefail
[ "${WORKTREE_BASH_GUARD_ENABLE:-0}" = "1" ] || exit 0   # opt-in: false-positive-prone, off by default
MODE="${WORKTREE_GUARD_MODE:-json}"

INPUT=$(cat)
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CWD" ] || [ -z "$CMD" ] && exit 0
git -C "$CWD" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
WT_ROOT=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null) || exit 0
GIT_DIR=$(git -C "$CWD" rev-parse --absolute-git-dir 2>/dev/null) || exit 0
GIT_COMMON=$(cd "$CWD" && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd) || exit 0
[ "$GIT_DIR" = "$GIT_COMMON" ] && exit 0
MAIN_ROOT=$(dirname "$GIT_COMMON")

# write-verb present AND references a MAIN_ROOT path AND does not also reference the worktree path
# (redirect match excludes fd redirects — `2>/dev/null`, `2>&1`, `>&2` are not file writes)
if printf '%s' "$CMD" | grep -Eq '((^|[^0-9>])>>?[^>&]|[[:space:]]sed[[:space:]]+-i|[[:space:]]tee[[:space:]]|[[:space:]]dd[[:space:]]|[[:space:]]install[[:space:]]|python3?[[:space:]]+-c)' \
   && printf '%s' "$CMD" | grep -qF "$MAIN_ROOT/" \
   && ! printf '%s' "$CMD" | grep -qF "$WT_ROOT/"; then
  REASON="worktree-bash-guard (#36182 shell channel): command writes into the main checkout '$MAIN_ROOT' from worktree '$WT_ROOT' without naming the worktree path. If intentional (e.g. recovery), reference the worktree path, or unset WORKTREE_BASH_GUARD_ENABLE to turn this guard off."
  if [ "$MODE" = "exit2" ]; then
    printf '%s\n' "$REASON" >&2
    exit 2
  else
    jq -n --arg r "$REASON" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
    exit 0
  fi
fi
exit 0
