#!/usr/bin/env bash
# land-check — tripwire-guard project guard: repo-state asserts on a LANDING push
# (`git push . HEAD:<integration>`). Ported from RR's lesson-guards.sh land_check().
#
# Blocks (exit 2):
#   [land-not-rebased]   HEAD's merge-base with the integration branch ≠ its current tip —
#                        the branch moved since your rebase; re-run the landing loop
#   [board-resurrection] the land RE-ADDS a board-file line (≥60 chars) that the integration
#                        branch's history deleted — a stale-context write or a conflict
#                        resolved from memory, reverting a sibling's board change
#
# Config (env): TRIPWIRE_INTEGRATION_BRANCH (default develop), TRIPWIRE_BOARD_FILE
# (default .agent/worktrees.md). Fail-open on any git error.
set -u

IB="${TRIPWIRE_INTEGRATION_BRANCH:-develop}"
BOARD="${TRIPWIRE_BOARD_FILE:-.agent/worktrees.md}"
# command-position prefix + optional `git -C <path>`
P='(^|[;&|(]|\$\()[[:space:]]*git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+'

land_check() {
  # $1 = the Bash command string. Echoes the block message and returns 2 on a hit; 0 clean.
  local cmd="$1"
  grep -qE "${P}push([[:space:]]+-[^[:space:]]+)*[[:space:]]+\.[[:space:]]+HEAD:${IB}([[:space:]]|$)" <<<"$cmd" || return 0

  local tip mb
  tip=$(git rev-parse "$IB" 2>/dev/null) || return 0
  mb=$(git merge-base HEAD "$IB" 2>/dev/null) || return 0

  # land-not-rebased — HEAD must sit ON the current tip at push time. Git would reject the
  # non-FF push anyway, but this fires BEFORE it with the protocol step to re-run, closing the
  # rebase→push race window with a clear message instead of a git error.
  if [ "$mb" != "$tip" ]; then
    echo "⛔ tripwire [land-not-rebased]: $IB moved — HEAD is not rebased onto the CURRENT tip (merge-base ${mb:0:8} ≠ $IB ${tip:0:8}). Re-run the landing loop from 'git rebase $IB' (verify again after), THEN push."
    return 2
  fi

  # board-resurrection — any added line ≥60 chars with -S history on the integration branch but
  # absent from its tip was deleted there; re-adding it reverts a sibling/coordinator board
  # change inside an innocent-looking commit, and the push is a clean FF.
  local line
  while IFS= read -r line; do
    [ "${#line}" -ge 60 ] || continue
    if [ -n "$(git log -n 1 --format=%H -S"$line" "$IB" -- "$BOARD" 2>/dev/null)" ]; then
      echo "⛔ tripwire [board-resurrection]: this land RE-ADDS a $BOARD line that $IB previously deleted: '${line:0:100}…' — a stale-context write or a conflict resolved from memory. Re-read the live board ('git show $IB:$BOARD'), re-apply ONLY your own row, recommit."
      return 2
    fi
  done < <(git diff "$IB"..HEAD -- "$BOARD" 2>/dev/null | grep '^+' | grep -v '^+++' | cut -c2-)

  return 0
}

tripwire_test() {
  local fails=0 tmp repo rc
  t() { if [ "$3" = "$2" ]; then echo "PASS  $1"; else echo "FAIL  $1 (want $2, got $3)"; fails=$((fails + 1)); fi; }
  g() { git -C "$repo" -c user.email=t@t -c user.name=t "$@"; }

  tmp=$(mktemp -d); repo="$tmp/repo"
  git init -q "$repo" && g checkout -q -b "$IB"
  echo base > "$repo/base.txt" && g add base.txt && g commit -qm base

  # not a landing command → allow without touching git
  land_check 'git status' >/dev/null; t "non-landing command → allow" 0 "$?"
  # different integration branch name → regex no match → allow
  ( IB=main; land_check 'git push . HEAD:develop' >/dev/null ); t "other integration branch → allow" 0 "$?"

  # rebased branch (HEAD on the tip) → allow
  g checkout -q -b topic-ok && echo ok > "$repo/ok.txt" && g add ok.txt && g commit -qm ok
  ( cd "$repo" && land_check 'git push . HEAD:'"$IB" >/dev/null ); t "HEAD on tip → allow" 0 "$?"

  # integration branch advanced under the topic → block
  g checkout -q "$IB" && echo moved > "$repo/moved.txt" && g add moved.txt && g commit -qm moved
  ( cd "$repo" && git checkout -q topic-ok && land_check 'git push . HEAD:'"$IB" >/dev/null ); rc=$?
  t "integration moved → block [land-not-rebased]" 2 "$rc"

  # board resurrection: a long line committed then deleted on IB, re-added on a fresh topic → block
  g checkout -q "$IB"
  local row='| worker-9 | very-long-topic-slug-for-the-parity-fixture | in-progress | 2026-01-01 |'
  mkdir -p "$repo/.agent" && printf '%s\n' "$row" > "$repo/.agent/worktrees.md"
  g add .agent/worktrees.md && g commit -qm board-add
  printf '' > "$repo/.agent/worktrees.md" && g add .agent/worktrees.md && g commit -qm board-del
  g checkout -q -b topic-resurrect
  printf '%s\n' "$row" > "$repo/.agent/worktrees.md" && g add .agent/worktrees.md && g commit -qm board-readd
  ( cd "$repo" && land_check 'git push . HEAD:'"$IB" >/dev/null ); rc=$?
  t "deleted board row re-added → block [board-resurrection]" 2 "$rc"

  # fresh short/board-untouched land stays clean
  g checkout -q "$IB" && g checkout -q -b topic-clean && echo fine > "$repo/fine.txt" && g add fine.txt && g commit -qm fine
  ( cd "$repo" && land_check 'git push . HEAD:'"$IB" >/dev/null ); t "clean land → allow" 0 "$?"

  rm -rf "$tmp"
  return "$fails"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ "${1:-}" = "--test" ]; then tripwire_test; exit $?; fi
  land_check "${TRIPWIRE_COMMAND:-}"
  exit $?
fi
