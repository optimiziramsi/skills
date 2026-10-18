#!/usr/bin/env bash
# tests.sh — the marketplace done-gate, mechanized (CLAUDE.md § Hard rules: "Done means validated").
# The repo root is a MARKETPLACE of one plugin per topic: every <plugin>/ folder with a
# .claude-plugin/plugin.json is a self-contained plugin (default layout: skills/ commands/ agents/
# hooks/hooks.json). Run from the repo root:
#   1. marketplace.json / every plugin.json / every hooks.json parse
#   2. marketplace.json lists exactly the plugin dirs, each `./<name>`, names agreeing
#   3. declared component paths + dependencies resolve
#   4. every script a hooks.json invokes via ${CLAUDE_PLUGIN_ROOT} exists inside that plugin
#   5. every /command has the same-named skill it shims, in the same plugin
#   6. `claude plugin validate --strict` on the marketplace and each plugin (skipped without the CLI)
#   7. every plugin test suite and every hook / bin tool that ships a --test self-test passes;
#      every vendored copy matches its source (./vendor.sh --check)
#   8. version discipline, per plugin: a plugin's shipped files never change without its own
#      version moving, and on a feature branch a changed plugin carries a -<branch-slug>.N series
#      (the install cache is version-keyed, so an unmoved version reaches nobody)
set -u
cd "$(dirname "$0")" || exit 1
fails=0
note() { echo "$@"; }
fail() { echo "FAIL  $*"; fails=$((fails + 1)); }

note "=== 1. JSON validity ==="
for f in .claude-plugin/marketplace.json */.claude-plugin/plugin.json */hooks/hooks.json; do
  if [ ! -f "$f" ]; then
    fail "$f missing"
  elif python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
    note "ok    $f"
  else
    fail "$f does not parse"
  fi
done

note ""
note "=== 2. marketplace <-> plugins agree ==="
if out=$(python3 - <<'EOF'
import glob, json, os, sys
bad = []
if os.path.exists('.claude-plugin/plugin.json'):
    bad.append("the repo root is a marketplace only — .claude-plugin/plugin.json must not exist")
dirs = {os.path.dirname(os.path.dirname(p)) for p in glob.glob('*/.claude-plugin/plugin.json')}
entries = json.load(open('.claude-plugin/marketplace.json'))['plugins']
listed = {e['name'] for e in entries}
for e in entries:
    if e.get('source') != f"./{e['name']}":
        bad.append(f"marketplace entry {e['name']}: source must be ./{e['name']} (dir name = plugin name)")
for d in sorted(dirs - listed):
    bad.append(f"{d}/ has a plugin.json but no marketplace entry")
for n in sorted(listed - dirs):
    bad.append(f"marketplace lists {n} but {n}/.claude-plugin/plugin.json does not exist")
for d in sorted(dirs):
    name = json.load(open(f'{d}/.claude-plugin/plugin.json')).get('name')
    if name != d:
        bad.append(f"{d}/.claude-plugin/plugin.json: name '{name}' != dir '{d}'")
if bad:
    print('\n'.join(bad)); sys.exit(1)
print(len(dirs))
EOF
); then
  note "ok    $out plugins, each listed once as ./<name>"
else
  fail "marketplace and plugin dirs disagree:"
  echo "$out"
fi

note ""
note "=== 3. declared component paths + dependencies resolve ==="
if out=$(python3 - <<'EOF'
import glob, json, os, sys
missing = []
names = {os.path.dirname(os.path.dirname(p)) for p in glob.glob('*/.claude-plugin/plugin.json')}
for pj in sorted(glob.glob('*/.claude-plugin/plugin.json')):
    d = os.path.dirname(os.path.dirname(pj))
    m = json.load(open(pj))
    for key in ('skills', 'commands', 'agents', 'hooks'):
        v = m.get(key, [])
        for p in ([v] if isinstance(v, str) else v):
            if isinstance(p, str) and not os.path.exists(os.path.join(d, p)):
                missing.append(f"{pj} {key}: {p}")
    for dep in m.get('dependencies', []):
        n = dep if isinstance(dep, str) else dep.get('name', '')
        if '@' not in n and n not in names:
            missing.append(f"{pj} depends on '{n}', which is not a plugin in this marketplace")
if missing:
    print('\n'.join(missing)); sys.exit(1)
EOF
); then
  note "ok    every declared path and same-marketplace dependency resolves"
else
  fail "a plugin.json references something that does not exist:"
  echo "$out"
fi

note ""
note "=== 4. hooks.json commands point at files inside their plugin ==="
if out=$(python3 - <<'EOF'
import glob, json, os, re, sys
missing = []
seen = 0
for f in sorted(glob.glob('*/hooks/hooks.json')):
    plugin = f.split('/')[0]
    for cmd in re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}(/[^"\\\s]+)', json.dumps(json.load(open(f)))):
        seen += 1
        if not os.path.exists(plugin + cmd):
            missing.append(f"{f}: {cmd}")
if missing:
    print('\n'.join(missing)); sys.exit(1)
print(seen)
EOF
); then
  note "ok    all $out \${CLAUDE_PLUGIN_ROOT} hook targets resolve"
else
  fail "a hooks.json invokes a script that does not exist in its plugin:"
  echo "$out"
fi

note ""
note "=== 5. every command shims a same-named skill in its own plugin ==="
if out=$(python3 - <<'EOF'
import glob, os, sys
bad = []
total = 0
for c in sorted(glob.glob('*/commands/*.md')):
    plugin, name = c.split('/')[0], os.path.basename(c)[:-3]
    if not os.path.exists(f'{plugin}/skills/{name}/SKILL.md'):
        bad.append(f"{c}: no skill named '{name}' in {plugin}/")
for p in sorted(glob.glob('*/skills/*/SKILL.md')):
    total += 1
    d = os.path.basename(os.path.dirname(p))
    text = open(p).read()
    head = text.split('---')[1] if text.startswith('---') else ''
    if f"name: {d}" not in head:
        bad.append(f"{p}: frontmatter name does not match directory '{d}'")
if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f"{total} skills")
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
  for target in . */.claude-plugin/plugin.json; do
    [ "$target" = . ] || target=${target%%/.claude-plugin/plugin.json}
    if out=$(claude plugin validate "$target" --strict 2>&1); then
      note "ok    $target"
    else
      fail "claude plugin validate $target --strict:"
      echo "$out" | tail -20
    fi
  done
else
  note "skip  claude CLI not on PATH"
fi

note ""
note "=== 7a. plugin test suites (*/tests/*.py) ==="
for t in */tests/*.py; do
  [ -f "$t" ] || continue
  if out=$(python3 "$t" 2>&1); then
    note "ok    $t ($(grep -c '^PASS' <<<"$out" | tr -d ' ') tests)"
  else
    fail "$t:"
    echo "$out" | tail -15
  fi
done

note ""
note "=== 7b. inline self-tests (anything shipping --test) ==="
# Deliberately wider than the component dirs: examples/guards.d/ scripts ship self-tests too, and
# a narrower glob left them silently unrun for their whole life. Extension-blind on purpose —
# guards may be any language, so a `.sh` glob would repeat that bug the first time one isn't.
for h in */hooks/* */bin/* */examples/* */examples/*/*; do
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
note "=== 7c. vendored copies match their source ==="
if out=$(./vendor.sh --check 2>&1); then
  note "ok    $out"
else
  fail "vendored copies drifted:"
  echo "$out"
fi

note ""
note "=== 8. version discipline (per plugin) ==="
if out=$(python3 - <<'EOF'
import glob, json, os, re, subprocess, sys

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)

def ver_at(ref, plugin):
    r = sh('git', 'show', f'{ref}:{plugin}/.claude-plugin/plugin.json')
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)['version']
    except Exception:
        return None

def slug(branch):
    return re.sub(r'[^a-zA-Z0-9]+', '-', branch).strip('-').lower()

def next_dev(v):
    m = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-(.+)\.(\d+))?$', v)
    if not m:
        return '?'
    a, b, c, pre, n = m.groups()
    return f"{a}.{b}.{c}-{pre}.{int(n) + 1}" if pre else f"{a}.{b}.{int(c) + 1}-dev.1"

plugins = sorted(os.path.dirname(os.path.dirname(p)) for p in glob.glob('*/.claude-plugin/plugin.json'))
branch = sh('git', 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()

# what changed: the working tree when dirty, else the HEAD commit
porcelain = [l for l in sh('git', 'status', '--porcelain').stdout.splitlines() if l.strip()]
if porcelain:
    scope, ref = 'working tree', 'HEAD'
    changed = set()
    for line in porcelain:
        p = line[3:]
        if ' -> ' in p:
            p = p.split(' -> ')[1]
        changed.add(p.strip().strip('"'))
else:
    scope, ref = 'HEAD', 'HEAD~1'
    parents = sh('git', 'rev-list', '--parents', '-n', '1', 'HEAD').stdout.split()
    changed = (set() if len(parents) != 2 else   # root commit or merge — nothing to compare
               {p for p in sh('git', 'show', '--name-only', '--pretty=', 'HEAD').stdout.split('\n') if p})

problems, summary = [], []
for plugin in plugins:
    cur = json.load(open(f'{plugin}/.claude-plugin/plugin.json'))['version']
    summary.append(f"{plugin} {cur}")
    touched = sorted(p for p in changed if p.startswith(plugin + '/') and '__pycache__' not in p)
    if not touched:
        continue
    prev = ver_at(ref, plugin)
    if prev is not None and cur == prev:
        listed = ', '.join(touched[:4]) + (f" (+{len(touched) - 4} more)" if len(touched) > 4 else '')
        problems.append(
            f"{plugin}: shipped content changed in the {scope} but its version stayed {cur}\n"
            f"      changed: {listed}\n"
            f"      consumers re-materialize only on a version CHANGE (.agent/lessons/plugin-version-bump-on-edit.md)\n"
            f"      bump {plugin}/.claude-plugin/plugin.json to {next_dev(cur)} in the SAME commit")
    # A feature branch must carry its own series: the local marketplace is folder-bound and the
    # install cache version-keyed, so a branch sharing develop's version switches invisibly.
    if branch not in ('develop', 'main', 'HEAD'):
        want = slug(branch)
        pre = cur.split('-', 1)[1] if '-' in cur else ''
        if pre.split('.')[0] != want:
            base = re.match(r'^(\d+\.\d+\.\d+)', cur)
            problems.append(
                f"{plugin}: on branch '{branch}' its version is {cur} — a feature branch needs its own\n"
                f"      series so a branch switch is visible in the version-keyed install cache.\n"
                f"      use: {base.group(1) if base else cur}-{want}.1   (back on develop, restore the -dev series)")

if problems:
    print('\n'.join('    ' + p for p in problems))
    sys.exit(1)
print(f"on {branch}: " + ', '.join(summary))
EOF
); then
  note "ok    $out"
else
  fail "version discipline:"
  echo "$out"
fi

note ""
if [ "$fails" -eq 0 ]; then note "ALL GREEN"; else note "$fails FAILURE(S)"; fi
exit "$fails"
