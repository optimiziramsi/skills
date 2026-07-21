#!/usr/bin/env bash
# Stop — nudge to commit uncommitted work (the commit skill's "commit as you go" cadence).
# Fires ONCE per distinct dirty state, only if the session actually wrote files, and never when
# stop_hook_active (prevents loops). Fails open. Escape hatch (user-set only): STOP_NUDGE_OFF=1.
#
# Opt-in: COMMIT_NUDGE_EXTRA_DIRS=../gitops,../infra also flags dirty *sibling* trees (comma-
# separated paths) the current repo can't see — folded into the nudge and the one-shot state.
# Self-test: bash commit-nudge.sh --test
set -uo pipefail
[ "${STOP_NUDGE_OFF:-0}" = "1" ] && exit 0

commit_nudge_siblings() {
  # Echo "<dir> (<N> dirty)" per non-clean dir in COMMIT_NUDGE_EXTRA_DIRS. Unset/absent → nothing.
  local raw="${COMMIT_NUDGE_EXTRA_DIRS:-}"
  [ -n "$raw" ] || return 0
  local d ds n IFS=','
  local -a dirs=()
  read -ra dirs <<<"$raw"
  for d in "${dirs[@]}"; do
    d="${d#"${d%%[![:space:]]*}"}"; d="${d%"${d##*[![:space:]]}"}"   # trim surrounding ws
    [ -n "$d" ] || continue
    ds=$(git -C "$d" status --porcelain 2>/dev/null || true)
    [ -n "$ds" ] && { n=$(printf '%s\n' "$ds" | grep -c .); printf '%s (%s dirty)\n' "$d" "$n"; }
  done
}

if [ "${1:-}" = "--test" ]; then
  fails=0
  t() { if [ "$3" = "$2" ]; then echo "PASS  $1"; else echo "FAIL  $1 (want $2, got $3)"; fails=$((fails + 1)); fi; }
  g() { git -C "$1" -c user.email=t@t -c user.name=t "${@:2}"; }
  tmp=$(mktemp -d)
  git init -q "$tmp/main"; echo a > "$tmp/main/a"; g "$tmp/main" add a; g "$tmp/main" commit -qm a
  git init -q "$tmp/sib";  echo b > "$tmp/sib/b";  g "$tmp/sib" add b;  g "$tmp/sib" commit -qm b
  echo dirty >> "$tmp/sib/b"

  out=$(cd "$tmp/main" && COMMIT_NUDGE_EXTRA_DIRS="../sib" commit_nudge_siblings)
  case "$out" in *"../sib"*dirty*) echo "PASS  dirty sibling reported" ;; *) echo "FAIL  dirty sibling: $out"; fails=$((fails + 1)) ;; esac
  out=$(cd "$tmp/main" && commit_nudge_siblings)
  [ -z "$out" ] && echo "PASS  unset COMMIT_NUDGE_EXTRA_DIRS → nothing" || { echo "FAIL  unset: $out"; fails=$((fails + 1)); }
  g "$tmp/sib" checkout -q -- b
  out=$(cd "$tmp/main" && COMMIT_NUDGE_EXTRA_DIRS="../sib" commit_nudge_siblings)
  [ -z "$out" ] && echo "PASS  clean sibling → nothing" || { echo "FAIL  clean sib: $out"; fails=$((fails + 1)); }

  tr="$tmp/t.jsonl"; printf '{"message":{"content":[{"type":"tool_use","name":"Edit"}]}}\n' > "$tr"
  echo dirty >> "$tmp/sib/b"
  json=$(printf '{"session_id":"cn-%s","transcript_path":"%s"}' "$$" "$tr")
  out=$(TMPDIR="$tmp" CLAUDE_PROJECT_DIR="$tmp/main" COMMIT_NUDGE_EXTRA_DIRS="../sib" bash "$0" <<<"$json" 2>&1); rc=$?
  t "clean main + dirty sibling → nag (exit 2)" 2 "$rc"
  case "$out" in *"../sib"*) echo "PASS  nag names the sibling" ;; *) echo "FAIL  nag msg: $out"; fails=$((fails + 1)) ;; esac

  g "$tmp/sib" checkout -q -- b
  json=$(printf '{"session_id":"cn2-%s","transcript_path":"%s"}' "$$" "$tr")
  out=$(TMPDIR="$tmp" CLAUDE_PROJECT_DIR="$tmp/main" COMMIT_NUDGE_EXTRA_DIRS="../sib" bash "$0" <<<"$json"); rc=$?
  t "clean main + clean sibling → no nag (exit 0)" 0 "$rc"

  rm -rf "$tmp"
  [ "$fails" -eq 0 ] && { echo "all tests passed"; exit 0; }
  echo "$fails FAILED"; exit 1
fi

input=$(cat 2>/dev/null || true)
# never re-block a continuation we caused
printf '%s' "$input" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true' && exit 0

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || exit 0
status=$(git status --porcelain 2>/dev/null || true)
extra=$(commit_nudge_siblings)
[ -z "$status" ] && [ -z "$extra" ] && exit 0

# only nag sessions that actually wrote files (skip read-only / chat sessions).
# jq is optional: if absent, transcript stays empty and we fall through to nagging on a dirty tree.
transcript=$(printf '%s' "$input" | jq -r '.transcript_path // empty' 2>/dev/null || true)
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  grep -Eq '"name": ?"(Edit|Write|MultiEdit|NotebookEdit)"' "$transcript" 2>/dev/null || exit 0
fi

# one-shot per distinct state (current tree + siblings) — don't nag twice for the same state
session_id=$(printf '%s' "$input" | jq -r '.session_id // "unknown"' 2>/dev/null || echo unknown)
state_hash=$(printf '%s\n%s' "$status" "$extra" | shasum 2>/dev/null | cut -d' ' -f1)
marker="${TMPDIR:-/tmp}/opsi-commit-nudge-${session_id}"
[ -f "$marker" ] && [ "$(cat "$marker" 2>/dev/null)" = "$state_hash" ] && exit 0
printf '%s' "$state_hash" > "$marker" 2>/dev/null || true

reason="[commit-nudge] "
if [ -n "$status" ]; then
  here=$(printf '%s' "$status" | grep -c .)
  reason="${reason}${here} uncommitted change(s) here"
fi
if [ -n "$extra" ]; then
  [ -n "$status" ] && reason="${reason}; "
  sib=$(printf '%s' "$extra" | tr '\n' ','); sib="${sib%,}"; sib="${sib//,/, }"
  reason="${reason}dirty sibling tree(s): ${sib}"
fi
reason="${reason}. Commit as you go (single-line message, per the commit skill), or say in one line why these stay uncommitted — then finish."
[ -f .agent/handoff.md ] && reason="${reason} If the session is winding down, also refresh the handoff (/handoff)."
printf '%s\n' "$reason" >&2
exit 2
