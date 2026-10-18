#!/usr/bin/env bash
# vendor.sh — copy shared code into every plugin that needs it (dev-only; tests.sh § 7c runs --check).
#
# A plugin reaches nothing outside its own directory at runtime: Claude Code copies each one into
# its own version-keyed cache dir, and a local-path marketplace (how develop is field-tested)
# drops symlinks that leave the plugin. So shared code ships as real copies. The single source
# stays here — edit it there, run this, commit the copies with it:
#
#   lib/<module>.py      → <plugin>/lib/<module>.py for every plugin that imports <module>
#   worktree-guards/{hooks,tests}/*.py + their lib → runners/vendor/worktree-guards/ (the runners'
#                          confinement injects those guards and runs their suite; one implementation)
#
#   ./vendor.sh           # sync (writes copies, removes stale ones)
#   ./vendor.sh --check   # report drift, change nothing, exit 1 on any
set -euo pipefail
cd "$(dirname "$0")"
exec python3 - "$@" <<'EOF'
import filecmp, glob, os, re, shutil, sys

check = sys.argv[1:] == ['--check']
if sys.argv[1:] not in ([], ['--check']):
    sys.exit("usage: ./vendor.sh [--check]")

MODULES = sorted(os.path.basename(p)[:-3] for p in glob.glob('lib/*.py'))
PLUGINS = sorted(os.path.dirname(os.path.dirname(p)) for p in glob.glob('*/.claude-plugin/plugin.json'))


def sources(root, skip=('lib', 'vendor')):
    """Every text file under root that is not itself vendored output."""
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        if rel.split(os.sep)[0] in skip or '__pycache__' in dirpath:
            dirnames[:] = []
            continue
        for f in filenames:
            yield os.path.join(dirpath, f)


def needed(files):
    """lib modules imported by any of `files` (`import m` / `from m import`)."""
    want = set()
    for f in files:
        try:
            text = open(f, errors='replace').read()
        except (IsADirectoryError, PermissionError):
            continue
        for m in MODULES:
            if re.search(rf'^\s*(import {m}\b|from {m} import)', text, re.M):
                want.add(m)
    return want


pairs = []  # (source, destination)
for p in PLUGINS:
    for m in sorted(needed(sources(p))):
        pairs.append((f'lib/{m}.py', f'{p}/lib/{m}.py'))

mirror = sorted(glob.glob('worktree-guards/hooks/*.py') + glob.glob('worktree-guards/tests/*.py'))
for src in mirror:
    pairs.append((src, f'runners/vendor/{src}'))
for m in sorted(needed(mirror)):
    pairs.append((f'lib/{m}.py', f'runners/vendor/worktree-guards/lib/{m}.py'))

expected = {dst for _, dst in pairs}
existing = set()
for p in PLUGINS:
    for d in (f'{p}/lib', f'{p}/vendor'):
        for dirpath, _, filenames in os.walk(d):
            if '__pycache__' not in dirpath:
                existing.update(os.path.join(dirpath, f) for f in filenames)

drift = [(s, d) for s, d in pairs if not os.path.exists(d) or not filecmp.cmp(s, d, shallow=False)]
stale = sorted(existing - expected)

if check:
    for s, d in drift:
        print(f"drift  {d} != {s}")
    for d in stale:
        print(f"stale  {d} (no source vendors it)")
    if drift or stale:
        print("run ./vendor.sh and commit the copies")
        sys.exit(1)
    print(f"{len(pairs)} vendored copies match their source")
    sys.exit(0)

for s, d in drift:
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(s, d)
    print(f"copied {s} → {d}")
for d in stale:
    os.remove(d)
    print(f"removed {d}")
print(f"{len(pairs)} vendored copies in sync")
EOF
