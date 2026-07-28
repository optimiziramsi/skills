#!/usr/bin/env bash
# worktree-bash-guard.sh — PreToolUse: Bash
# Blocks a shell command that uses a write-verb against a main-checkout path while NOT also naming the
# worktree path. Covers the #36182 "shell channel" (agents falling back to sed -i / redirection).
# Enable (off by default — false-positive-prone): export WORKTREE_BASH_GUARD_ENABLE=1
# Block mode:  export WORKTREE_GUARD_MODE=json|exit2   (default json)
# Self-test:   bash worktree-bash-guard.sh --test
set -uo pipefail

if [ "${1:-}" = "--test" ]; then
  command -v jq >/dev/null 2>&1 || { echo "FAIL  jq is required to run --test"; exit 1; }
  T=$(mktemp -d); T=$(cd "$T" && pwd -P); trap 'rm -rf "$T"' EXIT   # realpath: macOS /var → /private/var
  git -C "$T" init -q -b main repo && git -C "$T/repo" commit -q --allow-empty -m init
  git -C "$T/repo" worktree add -q "$T/wt" -b wtbranch
  invoke() { printf '{"cwd":"%s","tool_input":{"command":%s}}' "$T/wt" "$(jq -Rn --arg c "$1" '$c')" \
             | WORKTREE_BASH_GUARD_ENABLE=1 bash "$0"; }
  fails=0
  out=$(invoke "echo hi > $T/repo/x.ts")
  grep -q '"deny"' <<<"$out" && echo "PASS  deny redirect into main checkout" || { echo "FAIL  deny redirect: $out"; fails=$((fails+1)); }
  out=$(invoke "sed -i '' s/a/b/ $T/repo/x.ts")
  grep -q '"deny"' <<<"$out" && echo "PASS  deny sed -i into main checkout" || { echo "FAIL  deny sed -i: $out"; fails=$((fails+1)); }
  out=$(invoke "echo hi > $T/wt/x.ts")
  [ -z "$out" ] && echo "PASS  allow write inside the worktree" || { echo "FAIL  allow in-worktree: $out"; fails=$((fails+1)); }
  out=$(invoke "cat $T/repo/x.ts | tee $T/wt/x.ts")
  [ -z "$out" ] && echo "PASS  allow when the worktree path is also named" || { echo "FAIL  allow both-named: $out"; fails=$((fails+1)); }
  out=$(invoke "grep -r foo $T/repo/ 2>/dev/null")
  [ -z "$out" ] && echo "PASS  allow read-only command (fd redirect is not a write)" || { echo "FAIL  allow read-only: $out"; fails=$((fails+1)); }
  out=$(printf '{"cwd":"%s","tool_input":{"command":"echo hi > %s/x.ts"}}' "$T/repo" "$T/repo" | WORKTREE_BASH_GUARD_ENABLE=1 bash "$0")
  [ -z "$out" ] && echo "PASS  main checkout cwd → guard inert" || { echo "FAIL  main-cwd inert: $out"; fails=$((fails+1)); }
  out=$(printf '{"cwd":"%s","tool_input":{"command":"echo hi > %s/x.ts"}}' "$T/wt" "$T/repo" | bash "$0")
  [ -z "$out" ] && echo "PASS  off by default without WORKTREE_BASH_GUARD_ENABLE" || { echo "FAIL  default-off: $out"; fails=$((fails+1)); }
  if [ "$fails" -eq 0 ]; then echo "all tests passed"; else echo "$fails FAILED"; fi; exit "$fails"
fi

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
if printf '%s' "$CMD" | grep -Eq '((^|[^0-9>])>>?[^>&]|(^|[[:space:]])sed[[:space:]]+-i|(^|[[:space:]])tee[[:space:]]|(^|[[:space:]])dd[[:space:]]|(^|[[:space:]])install[[:space:]]|python3?[[:space:]]+-c)' \
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
