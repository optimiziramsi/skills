#!/usr/bin/env bash
# tests.sh — the marketplace done-gate, mechanized (CLAUDE.md § Hard rules: "Done means validated").
# The repo root IS the single optimiziramsi-skills plugin, organized TOPIC-FIRST: one <topic>/ folder
# per concern, each owning its skills/ commands/ agents/ hooks/. Run from the repo root:
#   1. marketplace.json / plugin.json / every <topic>/hooks/hooks.json parse
#   2. marketplace.json lists exactly the one root-sourced plugin, name matching plugin.json
#   3. every path in plugin.json's skills/commands/agents/hooks arrays exists on disk
#   4. every hook / bin tool that ships a --test self-test passes it
set -u
cd "$(dirname "$0")" || exit 1
fails=0
note() { echo "$@"; }
fail() { echo "FAIL  $*"; fails=$((fails + 1)); }

note "=== 1. JSON validity ==="
for f in .claude-plugin/marketplace.json .claude-plugin/plugin.json */hooks/hooks.json; do
  if [ ! -f "$f" ]; then
    fail "$f missing"
  elif python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
    note "ok    $f"
  else
    fail "$f does not parse"
  fi
done

note ""
note "=== 2. marketplace <-> plugin agree ==="
if python3 - <<'EOF'
import json, sys
mp = json.load(open('.claude-plugin/marketplace.json'))['plugins']
pj = json.load(open('.claude-plugin/plugin.json'))
ok = (len(mp) == 1 and mp[0]['name'] == pj['name'] and mp[0]['source'] in ('./', '.'))
sys.exit(0 if ok else 1)
EOF
then
  note "ok    single root-sourced plugin, names agree"
else
  fail "marketplace must list exactly one plugin, name matching plugin.json, source ./"
fi

note ""
note "=== 3. plugin.json component paths all exist ==="
if python3 - <<'EOF'
import json, os, sys
pj = json.load(open('.claude-plugin/plugin.json'))
missing = []
for key in ('skills', 'commands', 'agents', 'hooks'):
    for p in pj.get(key, []):
        if not os.path.exists(p):
            missing.append(f"{key}: {p}")
if missing:
    print('\n'.join(missing)); sys.exit(1)
sys.exit(0)
EOF
then
  note "ok    every skills/commands/agents/hooks path resolves"
else
  fail "plugin.json references a path that does not exist (see above)"
fi

note ""
note "=== 4. self-tests (every hook / bin tool that advertises --test) ==="
for h in */hooks/*.py */hooks/*.sh */bin/*; do
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
