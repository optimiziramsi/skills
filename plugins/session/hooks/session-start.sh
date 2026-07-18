#!/usr/bin/env bash
# SessionStart — inject a tiny state snapshot + freshness nudges as session context.
# stdout becomes the context. Everything is CONDITIONAL: absent files/deps never error,
# so this is safe in any repo. Keep output short — it runs on every start / resume / clear.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

branch=$(git branch --show-current 2>/dev/null || echo '?')
dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
last=$(git log -1 --format='%h %s (%cr)' 2>/dev/null || echo '?')
echo "[session] branch=${branch} · ${dirty} uncommitted file(s) · last: ${last}"

# handoff freshness — the session plugin's continuity file
if [ -f .agent/handoff.md ]; then
  age=$(git log -1 --format='%cr' -- .agent/handoff.md 2>/dev/null || echo 'never committed')
  echo "[session] .agent/handoff.md last updated ${age} — read it before working (/continue)."
fi

# pending todos
if [ -f .todo ]; then
  n=$(grep -cve '^[[:space:]]*#' -e '^[[:space:]]*$' .todo 2>/dev/null || echo 0)
  [ "${n:-0}" -gt 0 ] && echo "[session] .todo has ${n} item line(s)."
fi

# enforcement health — a missing interpreter disarms python guards SILENTLY (they fail open)
command -v python3 >/dev/null 2>&1 \
  || echo "[session] ⚠️ python3 not found — python guard hooks (e.g. git-guard) cannot run; enforcement is DISARMED until fixed."

# instructions-audit freshness — 'Last audit:' stamp older than 30 days
stamp=$(grep -m1 -oE 'Last audit: [0-9]{4}-[0-9]{2}-[0-9]{2}' .agent/instructions-changelog.md 2>/dev/null \
        | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
if [ -n "${stamp:-}" ]; then
  now=$(date +%s)
  then_=$(date -j -f '%Y-%m-%d' "$stamp" +%s 2>/dev/null || date -d "$stamp" +%s 2>/dev/null || echo "$now")
  days=$(( (now - then_) / 86400 ))
  [ "$days" -gt 30 ] && echo "[session] last instructions-audit ${days}d ago (>30) — consider /instructions-audit."
fi
exit 0
