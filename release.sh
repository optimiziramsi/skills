#!/usr/bin/env bash
# release.sh — cut a public release of the marketplace from `develop` onto `main`.
#
# `main` is what the world installs: the marketplace clone a consumer gets is SHALLOW and tracks
# `main` only (refspec +refs/heads/main:refs/remotes/origin/main), so `develop` never reaches
# them. `main` therefore carries the PLUGINS and nothing else — no `.agent/`, no `.todo`, no
# CLAUDE.md, no test harness — while `develop` keeps the full working repo.
#
# Plugins version independently. A release ships every plugin whose tree differs from `main`;
# each of those must carry a final version `main` doesn't already ship and a `## <version>`
# section in its own <plugin>/CHANGELOG.md, and gets the tag `<plugin>--v<version>` — the shape
# Claude Code resolves version-constrained plugin dependencies against. An unchanged plugin keeps
# its version; its next edit is forced onto a fresh -dev series by tests.sh § 8.
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
#   ./release.sh --dry-run   # show what would ship and the tree that would land, change nothing
#   ./release.sh             # cut it
set -euo pipefail
cd "$(dirname "$0")"

DEV_BRANCH=develop
PUB_BRANCH=main

# The marketplace is named per branch: develop registers locally as the dev marketplace, so a
# machine can carry it beside the published one (names key marketplaces globally); the release
# renames it in the published tree.
DEV_MARKETPLACE=optimiziramsi-dev
PUB_MARKETPLACE=optimiziramsi

# Development-only paths — present on $DEV_BRANCH, never on $PUB_BRANCH. Everything else is
# SHIPPED content. (Root lib/ is the source vendor.sh copies into each plugin — the copies ship.)
DEV_ONLY=(.agent .claude .todo .todo-inbox CLAUDE.md tests.sh release.sh vendor.sh lib .gitignore)

DRY_RUN=0
SKIP_TESTS=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    -h|--help) sed -n '2,27p' "$0"; exit 0 ;;
    *) echo "release: unknown argument '$arg'" >&2; exit 2 ;;
  esac
done

die() { echo "release: $*" >&2; exit 1; }

# --- preconditions -------------------------------------------------------------------------
HEAD_BRANCH=$(git rev-parse --abbrev-ref HEAD)
[ "$HEAD_BRANCH" = "$DEV_BRANCH" ] || die "run from $DEV_BRANCH (on $HEAD_BRANCH)"
[ -z "$(git status --porcelain)" ] || die "working tree is dirty — commit first"
git rev-parse --verify --quiet "$PUB_BRANCH" >/dev/null || die "no local $PUB_BRANCH branch"
MP_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['name'])")
[ "$MP_NAME" = "$DEV_MARKETPLACE" ] || die "marketplace.json is named '$MP_NAME' on $DEV_BRANCH — it must be '$DEV_MARKETPLACE'"

# Which plugins ship: every <plugin>/ whose tree differs from $PUB_BRANCH's (or is new there).
# One line per plugin: "<name> <version> <version on $PUB_BRANCH, or ->".
SHIPPING=$(python3 - "$PUB_BRANCH" <<'PY'
import glob, json, os, subprocess, sys
pub = sys.argv[1]
def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True)
for pj in sorted(glob.glob('*/.claude-plugin/plugin.json')):
    d = os.path.dirname(os.path.dirname(pj))
    if git('rev-parse', f'HEAD:{d}').stdout == git('rev-parse', f'{pub}:{d}').stdout:
        continue
    cur = json.load(open(pj))['version']
    r = git('show', f'{pub}:{pj}')
    old = json.loads(r.stdout)['version'] if r.returncode == 0 else '-'
    print(d, cur, old)
PY
)
[ -n "$SHIPPING" ] || die "no plugin differs from $PUB_BRANCH — nothing to release"

TAGS=()
PROBLEMS=()
while read -r name version old; do
  case "$version" in
    # ANY pre-release series — -dev.N on develop, -<branch-slug>.N on a feature branch, -rc.N —
    # is local-only by construction and must never land on $PUB_BRANCH.
    *-*) PROBLEMS+=("$name is $version, a pre-release series — bump it to a final version"); continue ;;
  esac
  # Consumers re-materialize only on a version CHANGE — shipping a new tree under the version
  # already on $PUB_BRANCH reaches nobody. .agent/lessons/plugin-version-bump-on-edit.md
  [ "$version" != "$old" ] || PROBLEMS+=("$name changed but $PUB_BRANCH already ships $version — bump it")
  tag="$name--v$version"
  ! git rev-parse --verify --quiet "refs/tags/$tag" >/dev/null || PROBLEMS+=("tag $tag already exists — bump $name")
  grep -q "^## $version" "$name/CHANGELOG.md" || PROBLEMS+=("$name/CHANGELOG.md has no '## $version' section")
  TAGS+=("$tag")
done <<<"$SHIPPING"
echo "release: shipping —"
while read -r name version old; do echo "  $name $old → $version"; done <<<"$SHIPPING"
if [ "${#PROBLEMS[@]}" -gt 0 ]; then
  printf 'release: %s\n' "${PROBLEMS[@]}" >&2
  [ "$DRY_RUN" -eq 1 ] || die "${#PROBLEMS[@]} problem(s) above — nothing released"
fi
SUBJECT="release $(while read -r name version _; do printf '%s %s, ' "$name" "$version"; done <<<"$SHIPPING")"
SUBJECT=${SUBJECT%, }

if [ "$SKIP_TESTS" -eq 0 ]; then
  ./tests.sh >/dev/null || die "tests.sh is not green — nothing ships red"
  echo "release: tests.sh ALL GREEN"
fi

# --- build the filtered tree on a temp branch off $PUB_BRANCH -------------------------------
TMP_BRANCH="release/$(date +%Y%m%d-%H%M%S)"
WORKTREE=$(mktemp -d "${TMPDIR:-/tmp}/release-XXXX")
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

  # 4. the published marketplace name
  python3 - "$PUB_MARKETPLACE" <<'PY'
import json, sys
p = '.claude-plugin/marketplace.json'
m = json.load(open(p))
m['name'] = sys.argv[1]
open(p, 'w').write(json.dumps(m, indent=2, ensure_ascii=False) + '\n')
PY
  git add .claude-plugin/marketplace.json

  # 5. a .gitignore that matches what the public tree can actually accumulate
  cat > .gitignore <<'IGNORE'
__pycache__/
*.pyc
.DS_Store
IGNORE
  git add .gitignore
)

# --- report / land -------------------------------------------------------------------------
echo "release: what changes on $PUB_BRANCH:"
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

git -C "$WORKTREE" commit -q -m "$SUBJECT"
git push -q . "$TMP_BRANCH:$PUB_BRANCH"          # local fast-forward land; no remote involved
for tag in "${TAGS[@]}"; do git tag "$tag" "$PUB_BRANCH"; done

echo "release: $PUB_BRANCH is now $(git rev-parse --short "$PUB_BRANCH") — $SUBJECT"
echo "release: tagged ${TAGS[*]}"
echo "release: yours to publish —"
echo "  git push origin $PUB_BRANCH ${TAGS[*]} && git push origin $DEV_BRANCH"
