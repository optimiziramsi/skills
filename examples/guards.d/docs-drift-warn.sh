#!/usr/bin/env bash
# docs-drift-warn — tripwire-guard project guard, WARN-ONLY: a landing push
# (`git push . HEAD:<integration>`) that changes source but touches no docs. Ported from RR's
# lesson-guards.sh land_warn(). Heuristic: pure refactors/tests legitimately skip docs — hence
# exit 3 (non-blocking warning; the engine surfaces it as a systemMessage), never a block.
#
# Config (env): TRIPWIRE_INTEGRATION_BRANCH (default develop), TRIPWIRE_SRC_RX (default
# '^(packages|apps)/'), TRIPWIRE_DOCS_RX (default '^\.docs/'). Fail-open on any git error.
set -u

IB="${TRIPWIRE_INTEGRATION_BRANCH:-develop}"
SRC_RX="${TRIPWIRE_SRC_RX:-^(packages|apps)/}"
DOCS_RX="${TRIPWIRE_DOCS_RX:-^\\.docs/}"
P='(^|[;&|(]|\$\()[[:space:]]*git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+'

docs_drift() {
  # $1 = the Bash command string. Prints the advisory and returns 3 on a hit; 0 clean.
  local cmd="$1"
  grep -qE "${P}push([[:space:]]+-[^[:space:]]+)*[[:space:]]+\.[[:space:]]+HEAD:${IB}([[:space:]]|$)" <<<"$cmd" || return 0

  local changed
  changed=$(git diff "$IB"..HEAD --name-only 2>/dev/null) || return 0
  [ -n "$changed" ] || return 0
  if grep -qE "$SRC_RX" <<<"$changed" && ! grep -qE "$DOCS_RX" <<<"$changed"; then
    echo "⚠️ tripwire [docs-drift]: this land changes source ($SRC_RX) but touches no docs ($DOCS_RX) — if the change altered behavior or shape, update the docs in the same land. Advisory only."
    return 3
  fi
  return 0
}

tripwire_test() {
  local fails=0 tmp repo rc
  t() { if [ "$3" = "$2" ]; then echo "PASS  $1"; else echo "FAIL  $1 (want $2, got $3)"; fails=$((fails + 1)); fi; }
  g() { git -C "$repo" -c user.email=t@t -c user.name=t "$@"; }

  tmp=$(mktemp -d); repo="$tmp/repo"
  git init -q "$repo" && g checkout -q -b "$IB"
  echo base > "$repo/base.txt" && g add base.txt && g commit -qm base

  land_check_cmd='git push . HEAD:'"$IB"
  docs_drift 'git status' >/dev/null; t "non-landing command → clean" 0 "$?"

  # source touched, no docs → warn (exit 3)
  g checkout -q -b topic-drift && mkdir -p "$repo/packages/x"
  echo code > "$repo/packages/x/f.ts" && g add packages/x/f.ts && g commit -qm src
  ( cd "$repo" && docs_drift "$land_check_cmd" >/dev/null ); rc=$?
  t "source without docs → warn (3)" 3 "$rc"

  # source + docs touched → clean
  mkdir -p "$repo/.docs" && echo doc > "$repo/.docs/x.md" && g add .docs/x.md && g commit -qm docs
  ( cd "$repo" && docs_drift "$land_check_cmd" >/dev/null ); t "source with docs → clean" 0 "$?"

  # docs-only land → clean
  g checkout -q "$IB" && g checkout -q -b topic-docsonly
  mkdir -p "$repo/.docs" && echo more > "$repo/.docs/y.md" && g add .docs/y.md && g commit -qm docsonly
  ( cd "$repo" && docs_drift "$land_check_cmd" >/dev/null ); t "docs-only land → clean" 0 "$?"

  rm -rf "$tmp"
  return "$fails"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ "${1:-}" = "--test" ]; then tripwire_test; exit $?; fi
  docs_drift "${TRIPWIRE_COMMAND:-}"
  exit $?
fi
