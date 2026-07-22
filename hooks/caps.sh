#!/usr/bin/env bash
# caps — surface instruction-surface cap breaches (file sizes + counts), so the governance caps
# the instructions system DESCRIBES get mechanically enforced instead of only checked by hand.
#
#   SessionStart : list current breaches as context (informational; every start/resume/clear).
#   Stop         : nudge ONCE per distinct breach-set, only if the session actually wrote files
#                  (so bloat introduced this session gets caught before the chat ends).
#
# Only files/dirs that EXIST are checked, so this is a safe no-op in any repo. Every cap is
# env-overridable (see below); nothing is raised to make content fit — compact instead
# (merge → route → tighten → retire). Fails open. Escape hatch (user-set): CAPS_GUARD_OFF=1.
# Self-test: bash caps.sh --test
set -uo pipefail

if [ "${1:-}" = "--test" ]; then
  fails=0
  tmp=$(mktemp -d)
  mkdir -p "$tmp/clean" "$tmp/fat"
  head -c 7000 /dev/zero | tr '\0' x > "$tmp/fat/CLAUDE.md"
  out=$(CAPS_GUARD_OFF=0 CLAUDE_PROJECT_DIR="$tmp/clean" bash "$0" <<<'{"hook_event_name":"SessionStart"}')
  if [ -z "$out" ]; then echo "PASS  clean repo → silent"; else echo "FAIL  clean repo: $out"; fails=$((fails+1)); fi
  out=$(CAPS_GUARD_OFF=0 CLAUDE_PROJECT_DIR="$tmp/fat" bash "$0" <<<'{"hook_event_name":"SessionStart"}')
  if printf '%s' "$out" | grep -q 'CLAUDE.md 7000c > 6000c'; then echo "PASS  oversized CLAUDE.md surfaced"; else echo "FAIL  oversized CLAUDE.md: $out"; fails=$((fails+1)); fi
  out=$(CAPS_GUARD_OFF=0 CAP_CLAUDE=8000 CLAUDE_PROJECT_DIR="$tmp/fat" bash "$0" <<<'{"hook_event_name":"SessionStart"}')
  if [ -z "$out" ]; then echo "PASS  CAP_CLAUDE override respected"; else echo "FAIL  override: $out"; fails=$((fails+1)); fi
  mkdir -p "$tmp/fat/.agent" && echo '{}' > "$tmp/fat/.agent/meta-lint.json"
  out=$(CAPS_GUARD_OFF=0 CLAUDE_PROJECT_DIR="$tmp/fat" bash "$0" <<<'{"hook_event_name":"SessionStart"}')
  if [ -z "$out" ]; then echo "PASS  meta-lint.json present → caps skips (engine supersedes)"; else echo "FAIL  supersede: $out"; fails=$((fails+1)); fi
  rm -rf "$tmp"
  [ "$fails" -eq 0 ] && { echo "all tests passed"; exit 0; }
  echo "$fails FAILED"; exit 1
fi

[ "${CAPS_GUARD_OFF:-0}" = "1" ] && exit 0

# meta-lint supersedes caps: a project that ships .agent/meta-lint.json opted into the
# config-driven engine (bin/meta-lint, SessionStart --fast pulse) — its size/count caps are a
# superset of these house defaults, so skip to avoid double-reporting.
[ -f "${CLAUDE_PROJECT_DIR:-$(pwd)}/.agent/meta-lint.json" ] && exit 0

input=$(cat 2>/dev/null || true)
event=$(printf '%s' "$input" | jq -r '.hook_event_name // empty' 2>/dev/null || true)
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || exit 0

# ── cap config (all env-overridable) ────────────────────────────────────────
# path : char-cap  — the house-layout instruction surface (absent files are skipped)
FILE_CAPS=(
  "CLAUDE.md:${CAP_CLAUDE:-6000}"
  "AGENTS.md:${CAP_AGENTS:-6000}"
  ".agent/handoff.md:${CAP_HANDOFF:-4000}"
  ".agent/instructions-changelog.md:${CAP_CHANGELOG:-8000}"
  ".agent/lessons/README.md:${CAP_LESSONS_INDEX:-8000}"
)
SKILL_CAP="${CAP_SKILL:-9000}"       # chars per .claude/skills/*/SKILL.md
AGENT_CAP="${CAP_AGENT:-4000}"       # chars per .claude/agents/*.md
RULE_CAP="${CAP_RULE:-2000}"         # chars per .claude/rules/*.md
COMMAND_CAP="${CAP_COMMAND:-800}"    # chars per .claude/commands/*.md (thin wrappers)
LESSON_CAP="${CAP_LESSON:-4000}"     # chars per .agent/lessons/*.md (excluding README)
MAX_SKILLS="${MAX_SKILLS:-12}"
MAX_AGENTS="${MAX_AGENTS:-6}"
MAX_RULES="${MAX_RULES:-10}"

# ── breach detection ────────────────────────────────────────────────────────
breaches=()
size() { wc -c < "$1" 2>/dev/null | tr -d ' '; }

for entry in "${FILE_CAPS[@]}"; do
  p=${entry%%:*}; cap=${entry##*:}
  [ -f "$p" ] || continue
  sz=$(size "$p"); [ -n "${sz:-}" ] && [ "$sz" -gt "$cap" ] && breaches+=("$p ${sz}c > ${cap}c")
done

# per-file char caps over a glob (unmatched glob stays literal → the -f test skips it)
check_glob() { # $1=glob  $2=cap  $3=skip-basename (optional)
  local p sz
  for p in $1; do
    [ -f "$p" ] || continue
    [ -n "${3:-}" ] && [ "$(basename "$p")" = "$3" ] && continue
    sz=$(size "$p"); [ -n "${sz:-}" ] && [ "$sz" -gt "$2" ] && breaches+=("$p ${sz}c > ${2}c")
  done
}
check_glob ".claude/skills/*/SKILL.md" "$SKILL_CAP"
check_glob ".claude/agents/*.md" "$AGENT_CAP"
check_glob ".claude/rules/*.md" "$RULE_CAP"
check_glob ".claude/commands/*.md" "$COMMAND_CAP"
check_glob ".agent/lessons/*.md" "$LESSON_CAP" "README.md"

# count budgets (glob loop, not `ls` — matched paths stay intact even with odd characters)
count() { # $1=glob (unmatched glob stays literal → the -e test skips it)
  local n=0 p
  for p in $1; do [ -e "$p" ] && n=$((n+1)); done
  echo "$n"
}
n=$(count ".claude/skills/*/");   [ "$n" -gt "$MAX_SKILLS" ] && breaches+=("$n skills > $MAX_SKILLS")
n=$(count ".claude/agents/*.md"); [ "$n" -gt "$MAX_AGENTS" ] && breaches+=("$n agents > $MAX_AGENTS")
n=$(count ".claude/rules/*.md");  [ "$n" -gt "$MAX_RULES" ] && breaches+=("$n rules > $MAX_RULES")

[ ${#breaches[@]} -eq 0 ] && exit 0

# ── emit per event ──────────────────────────────────────────────────────────
if [ "$event" = "Stop" ]; then
  printf '%s' "$input" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true' && exit 0
  # only nudge sessions that actually wrote files (skip read-only / chat sessions)
  transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null || true)
  if [ -n "$transcript" ] && [ -f "$transcript" ]; then
    grep -Eq '"name": ?"(Edit|Write|MultiEdit|NotebookEdit)"' "$transcript" 2>/dev/null || exit 0
  fi
  # one-shot per distinct breach-set per session — don't nag twice for the same state
  session_id=$(printf '%s' "$input" | jq -r '.session_id // "unknown"' 2>/dev/null || echo unknown)
  joined=$(printf '%s\n' "${breaches[@]}")
  state_hash=$(printf '%s' "$joined" | shasum 2>/dev/null | cut -d' ' -f1)
  marker="${TMPDIR:-/tmp}/opsi-caps-${session_id}"
  [ -f "$marker" ] && [ "$(cat "$marker" 2>/dev/null)" = "$state_hash" ] && exit 0
  printf '%s' "$state_hash" > "$marker" 2>/dev/null || true
  {
    echo "[caps] instruction-surface over cap — compact (merge → route → tighten → retire), don't raise the cap:"
    printf '  • %s\n' "${breaches[@]}"
  } >&2
  exit 2
fi

# SessionStart (and any other event): stdout becomes context
echo "[caps] instruction-surface over cap — compact these when you touch them (don't just raise caps):"
printf '  • %s\n' "${breaches[@]}"
exit 0
