#!/usr/bin/env bash
# todo-readonly-guard.sh — two roles, one file:
#   PreToolUse (Edit|Write|MultiEdit|NotebookEdit|Bash): DENIES any agent write to `.todo`.
#     `.todo` is the USER's parking lot — LLM-readonly. Agent deferrals go to `.todo-inbox`
#     instead (always writable); the user triages them into `.todo` themselves (or via a
#     `triage-todo` session).
#   UserPromptSubmit (--prompt-scan): arms writes for THIS session when the user's prompt
#     contains "ALLOW TODO" (case-insensitive; "allow .todo" also matches). Flag is
#     session-scoped — a triage-todo session edits `.todo` constantly, so the user arms it once.
# Bypass (one-off, user-authorized bash): prefix the command with TODO_GUARD_SKIP=1.
# Toggle off:  export TODO_GUARD_DISABLE=1
# Self-test:   bash todo-readonly-guard.sh --test
set -uo pipefail
[ "${TODO_GUARD_DISABLE:-0}" = "1" ] && exit 0

flag_path() { printf '%s/claude-todo-allow-%s' "${TMPDIR:-/tmp}" "$1"; }

if [ "${1:-}" = "--test" ]; then
  SID="todo-guard-selftest-$$"
  rm -f "$(flag_path "$SID")" "$(flag_path other-$$)"
  invoke() { printf '{"session_id":"%s","tool_name":"%s","tool_input":%s}' "$SID" "$1" "$2" | bash "$0"; }
  fails=0
  chk() { local name="$1" want="$2" out="$3"
    if [ "$want" = deny ]; then grep -q '"deny"' <<<"$out" && echo "PASS  $name" || { echo "FAIL  $name: $out"; fails=$((fails+1)); }
    else [ -z "$out" ] && echo "PASS  $name" || { echo "FAIL  $name: $out"; fails=$((fails+1)); }; fi; }
  chk "deny Edit .todo (unarmed)"        deny  "$(invoke Edit '{"file_path":"/repo/.todo"}')"
  chk "deny Write .todo (unarmed)"       deny  "$(invoke Write '{"file_path":"/repo/.todo"}')"
  chk "allow Edit .todo-inbox"           allow "$(invoke Edit '{"file_path":"/repo/.todo-inbox"}')"
  chk "allow Edit ordinary file"         allow "$(invoke Edit '{"file_path":"/repo/src/x.ts"}')"
  chk "deny Bash append to .todo"        deny  "$(invoke Bash '{"command":"echo x >> .todo"}')"
  chk "deny Bash truncate-redirect"      deny  "$(invoke Bash '{"command":"sort items > .todo"}')"
  chk "deny Bash sed -i on .todo"        deny  "$(invoke Bash '{"command":"sed -i \"\" s/a/b/ .todo"}')"
  chk "deny Bash tee -a .todo"           deny  "$(invoke Bash '{"command":"echo x | tee -a .todo"}')"
  chk "deny Bash mv onto .todo"          deny  "$(invoke Bash '{"command":"mv draft.md .todo"}')"
  chk "allow Bash read of .todo"         allow "$(invoke Bash '{"command":"cat .todo"}')"
  chk "allow Bash rg with stderr-redirect" allow "$(invoke Bash '{"command":"rg -n x .todo bin/loop 2>/dev/null | head -20"}')"
  chk "allow Bash grep pipe on .todo"    allow "$(invoke Bash '{"command":"grep -n foo .todo | head"}')"
  chk "allow Bash write to .todo-inbox"  allow "$(invoke Bash '{"command":"echo x >> .todo-inbox"}')"
  touch "$(flag_path "$SID")"
  chk "allow Edit .todo (session armed)" allow "$(invoke Edit '{"file_path":"/repo/.todo"}')"
  rm -f "$(flag_path "$SID")"
  out=$(printf '{"session_id":"%s","prompt":"ok, ALLOW TODO for this one"}' "$SID" | bash "$0" --prompt-scan)
  [ -f "$(flag_path "$SID")" ] && echo "PASS  prompt-scan arms session" || { echo "FAIL  prompt-scan arms session: $out"; fails=$((fails+1)); }
  chk "allow Edit .todo (armed via prompt)" allow "$(invoke Edit '{"file_path":"/repo/.todo"}')"
  rm -f "$(flag_path "$SID")"
  out=$(printf '{"session_id":"%s","prompt":"nothing relevant"}' "$SID" | bash "$0" --prompt-scan)
  [ ! -f "$(flag_path "$SID")" ] && echo "PASS  prompt-scan ignores plain prompt" || { echo "FAIL  prompt-scan ignores plain prompt"; fails=$((fails+1)); }
  if [ "$fails" -eq 0 ]; then echo "all tests passed"; else echo "$fails FAILED"; fi; exit "$fails"
fi

# Fail-open but LOUD — a missing dependency must never disarm the guard silently.
if ! command -v jq >/dev/null 2>&1; then
  printf '{"systemMessage":"⚠️ todo-readonly-guard DISARMED — jq not found; .todo readonly protection is OFF."}\n'
  exit 0
fi

INPUT=$(cat)
SID=$(printf '%s' "$INPUT" | jq -r '.session_id // empty')

if [ "${1:-}" = "--prompt-scan" ]; then
  PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // empty')
  if printf '%s' "$PROMPT" | grep -qiE 'allow[[:space:]]+\.?todo'; then
    [ -n "$SID" ] && touch "$(flag_path "$SID")"
    printf '{"systemMessage":"🔓 .todo writes ARMED for this session (user ALLOW)."}\n'
  fi
  exit 0
fi

# Session armed by the user's ALLOW prompt → everything through.
[ -n "$SID" ] && [ -f "$(flag_path "$SID")" ] && exit 0

TOOL=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')
deny() {
  jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}
REASON=".todo is LLM-readonly (user-owned parking lot). Park deferrals in .todo-inbox instead. If this write is genuinely wanted, the USER replies with 'ALLOW TODO' to arm this session (or prefixes bash with TODO_GUARD_SKIP=1)."

case "$TOOL" in
  Bash)
    CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
    case "$CMD" in TODO_GUARD_SKIP=1\ *) exit 0 ;; esac
    CLEAN=${CMD//.todo-inbox/}                     # inbox writes are the blessed path
    # Deny only when .todo is a WRITE TARGET (redirect / tee / in-place edit / file op),
    # not on mere mentions or unrelated redirects like `2>/dev/null`.
    if printf '%s' "$CLEAN" | grep -qE '((^|[^0-9&])>{1,2}[[:space:]]*"?'"'"'?([A-Za-z0-9_./-]*/)?\.todo([[:space:]"'"'"']|$))|(\btee\b[^|;&]*\.todo)|(\b(sed|perl)[[:space:]]+-i[^|;&]*\.todo)|(\b(mv|cp|rm|truncate|install)\b[^|;&]*[[:space:]]"?'"'"'?([A-Za-z0-9_./-]*/)?\.todo([[:space:]"'"'"']|$))|(\bof=[^[:space:]]*\.todo)'; then
      deny "todo-readonly-guard: bash command writes to .todo. $REASON"
    fi
    ;;
  Edit|Write|MultiEdit|NotebookEdit)
    while IFS= read -r FILE; do
      [ -z "$FILE" ] && continue
      case "$FILE" in
        .todo|*/.todo) deny "todo-readonly-guard: '$FILE' targets .todo. $REASON" ;;
      esac
    done < <(printf '%s' "$INPUT" | jq -r '[.tool_input | .. | objects | (.file_path? // empty, .notebook_path? // empty)] | .[]' 2>/dev/null; printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty, .tool_input.notebook_path // empty' 2>/dev/null)
    ;;
esac
exit 0
