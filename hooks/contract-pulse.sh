#!/usr/bin/env bash
# contract-pulse.sh — PostToolUse hook: re-inject a one-line output-contract reminder every Nth
# tool call. The UserPromptSubmit reminder decays over a long agentic turn; this keeps it in
# force without meaningful token cost (fires 1-in-EVERY calls).
# Config: REPORT_PULSE_EVERY (default 10) · escape hatch REPORT_GUARD_OFF=1 (disables the pulse too)
[ "${REPORT_GUARD_OFF:-0}" = "1" ] && exit 0
EVERY="${REPORT_PULSE_EVERY:-10}"
sid=$(python3 -c 'import sys,json;print(json.load(sys.stdin).get("session_id","default"))' 2>/dev/null || echo default)
f="${TMPDIR:-/tmp}/claude-contract-pulse-${sid}"
n=$(($(cat "$f" 2>/dev/null || echo 0) + 1))
echo "$n" > "$f"
if [ $((n % EVERY)) -eq 0 ]; then
  printf '%s' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"OUTPUT CONTRACT in force: no text between tool calls; final message = 1 outcome line + <=5 fact bullets + numbered Q list (omit if none). No narration, headers, or tables."}}'
fi
exit 0
