#!/usr/bin/env bash
# Stop — nudge to commit uncommitted work (the commit skill's "commit as you go" cadence).
# Fires ONCE per distinct dirty-tree state, only if the session actually wrote files, and never
# when stop_hook_active (prevents loops). Fails open. Escape hatch (user-set only): STOP_NUDGE_OFF=1.
set -uo pipefail
[ "${STOP_NUDGE_OFF:-0}" = "1" ] && exit 0

input=$(cat 2>/dev/null || true)
# never re-block a continuation we caused
printf '%s' "$input" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true' && exit 0

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || exit 0
status=$(git status --porcelain 2>/dev/null || true)
[ -z "$status" ] && exit 0

# only nag sessions that actually wrote files (skip read-only / chat sessions).
# jq is optional: if absent, transcript stays empty and we fall through to nagging on a dirty tree.
transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null || true)
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  grep -Eq '"name": ?"(Edit|Write|MultiEdit|NotebookEdit)"' "$transcript" 2>/dev/null || exit 0
fi

# one-shot per distinct dirty state — don't nag twice for the same tree
session_id=$(printf '%s' "$input" | jq -r '.session_id // "unknown"' 2>/dev/null || echo unknown)
state_hash=$(printf '%s' "$status" | shasum 2>/dev/null | cut -d' ' -f1)
marker="${TMPDIR:-/tmp}/opsi-commit-nudge-${session_id}"
[ -f "$marker" ] && [ "$(cat "$marker" 2>/dev/null)" = "$state_hash" ] && exit 0
printf '%s' "$state_hash" > "$marker" 2>/dev/null || true

dirty=$(printf '%s' "$status" | wc -l | tr -d ' ')
reason="[commit-nudge] ${dirty} uncommitted change(s). Commit as you go (single-line message, per the commit skill), or say in one line why these stay uncommitted — then finish."
[ -f .agent/handoff.md ] && reason="${reason} If the session is winding down, also refresh the handoff (/handoff)."
printf '%s\n' "$reason" >&2
exit 2
