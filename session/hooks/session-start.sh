#!/usr/bin/env bash
# SessionStart — inject a tiny state snapshot + freshness nudges as session context.
# stdout becomes the context. Everything is CONDITIONAL: absent files/deps never error,
# so this is safe in any repo. Keep output short — it runs on every start / resume / clear.
# Escape hatch (user-set): SESSION_START_OFF=1 — the git one-liner fires in ANY git repo,
# not only opsi-scaffolded ones, so a project that doesn't want it needs a switch.
# Self-test: bash session-start.sh --test
set -uo pipefail
[ "${SESSION_START_OFF:-0}" = "1" ] && exit 0

if [ "${1:-}" = "--test" ]; then
  T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
  fails=0
  git -C "$T" init -q -b main repo && git -C "$T/repo" commit -q --allow-empty -m init
  out=$(CLAUDE_PROJECT_DIR="$T/repo" bash "$0")
  grep -q '\[session\] branch=main' <<<"$out" && echo "PASS  git repo → state line" || { echo "FAIL  state line: $out"; fails=$((fails+1)); }
  out=$(SESSION_START_OFF=1 CLAUDE_PROJECT_DIR="$T/repo" bash "$0")
  [ -z "$out" ] && echo "PASS  SESSION_START_OFF=1 → silent" || { echo "FAIL  kill-switch: $out"; fails=$((fails+1)); }
  mkdir -p "$T/plain"
  out=$(CLAUDE_PROJECT_DIR="$T/plain" bash "$0")
  [ -z "$out" ] && echo "PASS  non-repo → silent" || { echo "FAIL  non-repo: $out"; fails=$((fails+1)); }
  mkdir -p "$T/repo/.agent" && : > "$T/repo/.agent/handoff.md"
  out=$(CLAUDE_PROJECT_DIR="$T/repo" bash "$0")
  grep -q 'handoff.md last updated' <<<"$out" && echo "PASS  handoff freshness surfaced" || { echo "FAIL  handoff line: $out"; fails=$((fails+1)); }
  if [ "$fails" -eq 0 ]; then echo "all tests passed"; else echo "$fails FAILED"; fi; exit "$fails"
fi

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
  n=$(grep -cve '^[[:space:]]*#' -e '^[[:space:]]*$' .todo 2>/dev/null || true)
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
  [ "$days" -gt 30 ] && echo "[session] last instructions-audit ${days}d ago (>30) — consider an instructions audit (/instructions-audit if available)."
fi
exit 0
