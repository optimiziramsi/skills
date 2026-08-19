#!/usr/bin/env bash
# release.sh — cut a public release of the plugin from `develop` onto `main`.
#
# `main` is what the world installs: the marketplace clone a consumer gets is SHALLOW and tracks
# `main` only (refspec +refs/heads/main:refs/remotes/origin/main), so `develop` never reaches
# them. `main` therefore carries the PLUGIN and nothing else — no `.agent/`, no `.todo`, no
# CLAUDE.md, no test harness — while `develop` keeps the full working repo.
#
# Mechanism: a filtered TREE-COPY, never a merge. A merge between a branch that keeps the dev
# files and one that deletes them re-conflicts on those paths at every release, forever. Instead
# each release builds ONE commit on a temp branch off `main` whose tree IS develop's tree minus
# $DEV_ONLY, then fast-forwards `main` onto it. Both histories are preserved; `main`'s history
# becomes the release list.
#
# Local only, by construction: no remote is ever contacted. Pushing `main` and the tag is the
# user's — this stops at the local tag and prints what to push. (It runs OUTSIDE the agent's
# git-guard, which inspects Bash tool calls and not a script's internals; every git call below is
# deliberately one the guard would permit anyway.)
#
#   ./release.sh --dry-run   # show the tree that would land, change nothing
#   ./release.sh             # cut it, then open the next -dev series on develop
#   ./release.sh --no-open   # cut it and leave develop's version alone
set -euo pipefail
cd "$(dirname "$0")"

DEV_BRANCH=develop
PUB_BRANCH=main

# Development-only paths — present on $DEV_BRANCH, never on $PUB_BRANCH. Everything else is
# SHIPPED content; tests.sh § 8 parses this one line to know which is which, so keep it one line.
DEV_ONLY=(.agent .claude .todo .todo-inbox CLAUDE.md tests.sh release.sh .gitignore)

DRY_RUN=0
SKIP_TESTS=0
OPEN_NEXT=1
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    --no-open) OPEN_NEXT=0 ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "release: unknown argument '$arg'" >&2; exit 2 ;;
  esac
done

die() { echo "release: $*" >&2; exit 1; }

# --- preconditions -------------------------------------------------------------------------
HEAD_BRANCH=$(git rev-parse --abbrev-ref HEAD)
[ "$HEAD_BRANCH" = "$DEV_BRANCH" ] || die "run from $DEV_BRANCH (on $HEAD_BRANCH)"
[ -z "$(git status --porcelain)" ] || die "working tree is dirty — commit first"
git rev-parse --verify --quiet "$PUB_BRANCH" >/dev/null || die "no local $PUB_BRANCH branch"

VERSION=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
TAG="v$VERSION"
case "$VERSION" in
  # ANY pre-release series — -dev.N on develop, -<branch-slug>.N on a feature branch, -rc.N —
  # is local-only by construction and must never land on $PUB_BRANCH. tests.sh § 8 is the other
  # half of this: it keeps those series distinct per branch.
  *-*) die "version $VERSION is a pre-release series — bump to a final version first" ;;
esac
if git rev-parse --verify --quiet "refs/tags/$TAG" >/dev/null; then
  die "tag $TAG already exists — bump the version in .claude-plugin/plugin.json"
fi
# Consumers re-materialize only on a version CHANGE — shipping a new tree under the version
# already on $PUB_BRANCH reaches nobody. .agent/lessons/plugin-version-bump-on-edit.md
PUB_VERSION=$(git show "$PUB_BRANCH:.claude-plugin/plugin.json" |
  python3 -c "import json,sys; print(json.load(sys.stdin)['version'])")
[ "$VERSION" != "$PUB_VERSION" ] || die "$PUB_BRANCH already ships $VERSION — bump the version in .claude-plugin/plugin.json"
grep -q "^## $VERSION" CHANGELOG.md || die "CHANGELOG.md has no '## $VERSION' section"

if [ "$SKIP_TESTS" -eq 0 ]; then
  ./tests.sh >/dev/null || die "tests.sh is not green — nothing ships red"
  echo "release: tests.sh ALL GREEN"
fi

# --- build the filtered tree on a temp branch off $PUB_BRANCH -------------------------------
TMP_BRANCH="release/$TAG"
WORKTREE=$(mktemp -d "${TMPDIR:-/tmp}/release-$VERSION-XXXX")
cleanup() {
  git worktree remove --force "$WORKTREE" 2>/dev/null || true
  git branch -D "$TMP_BRANCH" >/dev/null 2>&1 || true
}
git branch -D "$TMP_BRANCH" >/dev/null 2>&1 || true
trap cleanup EXIT

git worktree add --quiet -b "$TMP_BRANCH" "$WORKTREE" "$PUB_BRANCH"

(
  cd "$WORKTREE"

  # 1. drop what $PUB_BRANCH still carries but $DEV_BRANCH has deleted
  comm -23 <(git ls-tree -r --name-only HEAD | sort) <(git ls-tree -r --name-only "$DEV_BRANCH" | sort) \
    | while IFS= read -r f; do
        [ -n "$f" ] && git rm -q --ignore-unmatch -- "$f"
      done

  # 2. take develop's tree wholesale
  git checkout "$DEV_BRANCH" -- .

  # 3. strip the development-only paths
  for p in "${DEV_ONLY[@]}"; do
    git rm -r -q --cached --ignore-unmatch -- "$p" >/dev/null 2>&1 || true
    rm -rf -- "$p"
  done

  # 4. a .gitignore that matches what the public tree can actually accumulate
  cat > .gitignore <<'IGNORE'
__pycache__/
*.pyc
.DS_Store
IGNORE
  git add .gitignore
)

# --- report / land -------------------------------------------------------------------------
echo "release: $TAG — what changes on $PUB_BRANCH:"
git -C "$WORKTREE" diff --cached --stat "$PUB_BRANCH" | tail -6
echo "release: resulting top-level entries:"
(cd "$WORKTREE" && git ls-files | cut -d/ -f1 | sort -u | sed 's/^/  /')

if [ "$DRY_RUN" -eq 1 ]; then
  echo "release: --dry-run — nothing committed, $PUB_BRANCH untouched"
  exit 0
fi

if git -C "$WORKTREE" diff --cached --quiet "$PUB_BRANCH"; then
  die "no difference from $PUB_BRANCH — nothing to release"
fi

git -C "$WORKTREE" commit -q -m "release $TAG"
git push -q . "$TMP_BRANCH:$PUB_BRANCH"          # local fast-forward land; no remote involved
git tag "$TAG" "$PUB_BRANCH"

echo "release: $PUB_BRANCH is now $(git rev-parse --short "$PUB_BRANCH"), tagged $TAG"

# Open the next development series. The local marketplace is folder-bound, so switching this
# checkout between branches switches what every project on this machine loads — and the install
# cache is version-keyed. If develop and main ever carried the SAME version, the switch would be
# invisible. A -dev suffix keeps them distinct, and release.sh refuses to publish one.
if [ "$OPEN_NEXT" -eq 1 ]; then
  NEXT=$(python3 - "$VERSION" <<'PY'
import sys
major, minor, patch = (sys.argv[1].split('.') + ['0', '0'])[:3]
print(f"{major}.{minor}.{int(patch) + 1}-dev.1")
PY
)
  python3 - "$NEXT" <<'PY'
import json, re, sys
p = '.claude-plugin/plugin.json'
s = open(p).read()
open(p, 'w').write(re.sub(r'("version":\s*")[^"]+(")', r'\g<1>' + sys.argv[1] + r'\g<2>', s, count=1))
assert json.load(open(p))['version'] == sys.argv[1]
PY
  git add .claude-plugin/plugin.json
  git commit -q -m "open $NEXT"
  echo "release: $DEV_BRANCH opened at $NEXT"
fi

echo "release: yours to publish —"
echo "  git push origin $PUB_BRANCH && git push origin $TAG && git push origin $DEV_BRANCH"
