#!/usr/bin/env bash
# tests.sh — the marketplace done-gate, mechanized (CLAUDE.md § Hard rules: "Done means validated").
# The repo root IS the single optimiziramsi-skills plugin, organized TOPIC-FIRST: one <topic>/ folder
# per concern, each owning its skills/ commands/ agents/ hooks/. Run from the repo root:
#   1. marketplace.json / plugin.json / every <topic>/hooks/hooks.json parse
#   2. marketplace.json lists exactly the one root-sourced plugin, name matching plugin.json
#   3. every path in plugin.json's skills/commands/agents/hooks arrays exists on disk
#   4. every script a hooks.json invokes via ${CLAUDE_PLUGIN_ROOT} exists on disk
#   5. every /command has the same-named skill it shims (CLAUDE.md § Authoring conventions)
#   6. `claude plugin validate . --strict` (skipped when the CLI is absent)
#   7. every hook / bin tool that ships a --test self-test passes it
#   8. the runner-wrapper template's version stamp matches plugin.json
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
note "=== 4. hooks.json commands point at files that exist ==="
if out=$(python3 - <<'EOF'
import glob, json, os, re, sys
missing = []
seen = 0
for f in sorted(glob.glob('*/hooks/hooks.json')):
    blob = json.load(open(f))
    for cmd in re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}(/[^"\\\s]+)', json.dumps(blob)):
        seen += 1
        if not os.path.exists('.' + cmd):
            missing.append(f"{f}: {cmd}")
if missing:
    print('\n'.join(missing)); sys.exit(1)
print(seen)
EOF
); then
  note "ok    all $out \${CLAUDE_PLUGIN_ROOT} hook targets resolve"
else
  fail "a hooks.json invokes a script that does not exist:"
  echo "$out"
fi

note ""
note "=== 5. every command shims a same-named skill ==="
if out=$(python3 - <<'EOF'
import glob, os, sys
bad = []
skills = {os.path.basename(os.path.dirname(p)) for p in glob.glob('*/skills/*/SKILL.md')}
for c in sorted(glob.glob('*/commands/*.md')):
    name = os.path.basename(c)[:-3]
    if name not in skills:
        bad.append(f"{c}: no skill named '{name}'")
for p in sorted(glob.glob('*/skills/*/SKILL.md')):
    d = os.path.basename(os.path.dirname(p))
    head = open(p).read().split('---')[1] if open(p).read().startswith('---') else ''
    if f"name: {d}" not in head:
        bad.append(f"{p}: frontmatter name does not match directory '{d}'")
if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f"{len(skills)} skills")
EOF
); then
  note "ok    command/skill pairing intact ($out)"
else
  fail "command/skill pairing broken:"
  echo "$out"
fi

note ""
note "=== 6. claude plugin validate --strict ==="
if command -v claude >/dev/null 2>&1; then
  if out=$(claude plugin validate . --strict 2>&1); then
    note "ok    manifests pass strict validation"
  else
    fail "claude plugin validate --strict:"
    echo "$out" | tail -20
  fi
else
  note "skip  claude CLI not on PATH"
fi

note ""
note "=== 7. self-tests (every hook / bin tool that advertises --test) ==="
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
note "=== 8. runner-wrapper version lock ==="
# The scaffolded bin/loop wrapper refuses to run against a plugin of a different version, so its
# stamp MUST track plugin.json — a forgotten bump here breaks every consumer's wrapper on update.
wrapper=flow/examples/runner-wrapper.sh
plugin_version=$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")
wrapper_version=$(sed -n 's/^WRAPPER_VERSION=\([^ ]*\).*/\1/p' "$wrapper" | head -1)
if [ "$wrapper_version" = "$plugin_version" ]; then
  note "ok    $wrapper stamped $wrapper_version"
else
  fail "$wrapper stamps WRAPPER_VERSION=$wrapper_version but plugin.json is $plugin_version"
fi

note ""
if [ "$fails" -eq 0 ]; then note "ALL GREEN"; else note "$fails FAILURE(S)"; fi
exit "$fails"
