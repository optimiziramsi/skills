#!/usr/bin/env bash
# tests.sh — the marketplace done-gate, mechanized (CLAUDE.md § Hard rules: "Done means validated").
# Run from the repo root before committing plugin changes:
#   1. every plugin.json / hooks.json / marketplace.json parses
#   2. marketplace.json ↔ plugins/ directory listing agree both ways
#   3. every hook that ships a --test self-test passes it
set -u
cd "$(dirname "$0")" || exit 1
fails=0
note() { echo "$@"; }
fail() { echo "FAIL  $*"; fails=$((fails + 1)); }

note "=== 1. JSON validity ==="
for f in .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/hooks/hooks.json; do
  [ -f "$f" ] || continue
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
    note "ok    $f"
  else
    fail "$f does not parse"
  fi
done

note ""
note "=== 2. marketplace <-> plugins/ agree ==="
listed=$(python3 -c "import json; print('\n'.join(sorted(p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'])))")
present=$(ls -d plugins/*/ | sed 's|plugins/||;s|/||' | sort)
if [ "$listed" = "$present" ]; then
  note "ok    $(echo "$listed" | wc -l | tr -d ' ') plugins, both ways"
else
  fail "mismatch — marketplace-only: [$(comm -23 <(echo "$listed") <(echo "$present") | tr '\n' ' ')] dir-only: [$(comm -13 <(echo "$listed") <(echo "$present") | tr '\n' ' ')]"
fi

note ""
note "=== 3. self-tests (every hook / bin tool that advertises --test) ==="
for h in plugins/*/hooks/*.py plugins/*/hooks/*.sh plugins/*/bin/*; do
  [ -f "$h" ] || continue
  grep -q -e '--test' "$h" || continue
  case "$h" in
    *.py) runner=python3 ;;
    *.sh) runner=bash ;;
    *) if head -1 "$h" | grep -q python; then runner=python3; else runner=bash; fi ;;
  esac
  if out=$("$runner" "$h" --test 2>&1); then
    note "ok    $h ($(grep -c -E '^(PASS|ok )' <<<"$out" | tr -d ' ') tests)"
  else
    fail "$h self-test:"
    echo "$out" | tail -15
  fi
done

note ""
if [ "$fails" -eq 0 ]; then note "ALL GREEN"; else note "$fails FAILURE(S)"; fi
exit "$fails"
