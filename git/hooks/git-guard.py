#!/usr/bin/env python3
"""PreToolUse[Bash] — the git safety net: destructive, remote, and history operations.

Blocks (exit 2, reason fed back to the model): remote sync (push/pull/fetch — `git push .` is a
LOCAL ref update and passes), bulk staging, non-FF merge, protected-branch moves, soft-reset to a
moving ref, filter-branch, `reset --hard`, `--no-verify`, and every discard of uncommitted work.
Allowed by default because rebase + FF-only landing needs them: `rebase`, `commit --amend`,
`checkout <ref> -- <path>`.

Commit MESSAGE style is deliberately not here — that is the `commit` topic's commit-format hook.

Fail-open: any unexpected error exits 0, so a broken guard can never brick a session.

Every rule, every env switch, and why each exists: ../README.md. In short —
GIT_GUARD_OFF=1 disables everything; GIT_GUARD_STRICT re-blocks what the defaults allow;
GIT_GUARD_ALLOW / GIT_GUARD_ALLOW_FETCH relax individual workflow blocks;
GIT_GUARD_PROTECTED_BRANCH names the protected branch(es) (unset → the repo's OWN default branch
is detected, so develop/trunk projects need no config); GIT_GUARD_INTEGRATION_BRANCH permits the
worktree protocol's fast-forward land when the integration branch is itself protected.
Tests: python3 git/tests/test_git_guard.py
"""
import json
import os
import re
import shlex
import subprocess
import sys


def deny(reason: str):
    print(f"[git-guard] BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)


def segments(command: str):
    for seg in re.split(r"(?:&&|\|\||[;|\n])", command):
        seg = seg.strip()
        if seg:
            yield seg


def tokenize(seg: str):
    try:
        tokens = shlex.split(seg)
    except ValueError:
        tokens = seg.split()
    while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        tokens = tokens[1:]  # skip leading env assignments
    return tokens


def parse_git(tokens):
    """Return (subcommand, args) if tokens are a git invocation, else None."""
    if not tokens or os.path.basename(tokens[0]) != "git":
        return None
    rest, i = tokens[1:], 0
    while i < len(rest):
        t = rest[i]
        if t in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
            i += 2
            continue
        if t.startswith("-"):
            i += 1
            continue
        return t, rest[i + 1:]
    return None


def env_tokens(name: str):
    return {t.strip() for t in os.environ.get(name, "").split(",") if t.strip()}


_DETECT_CACHE = {}


def detected_default_branch():
    """The repo's OWN default branch, so `main` is never assumed.

    Order: origin's HEAD symref (what the remote calls default) → the first of
    main/master/develop/trunk that actually EXISTS as a local branch → a repo-local
    `init.defaultBranch`. Returns None when nothing resolves (not a repo, no branches yet).

    Deliberately never reads GLOBAL `init.defaultBranch`: that is a property of the user's
    machine, not of the project, and would make every repo on the box look like `main`.
    Any git failure returns None; this must never raise inside a PreToolUse hook.

    Memoized per cwd: this costs several `git` subprocesses (~30 ms), and the hook runs on
    EVERY Bash tool call. Callers must also reach it lazily — see `check()`.
    """
    key = os.getcwd()
    if key in _DETECT_CACHE:
        return _DETECT_CACHE[key]
    _DETECT_CACHE[key] = value = _detect_default_branch_uncached()
    return value


def _detect_default_branch_uncached():
    def run(*args):
        try:
            return subprocess.run(("git",) + args, capture_output=True, text=True, timeout=2)
        except Exception:
            return None

    def out(*args):
        r = run(*args)
        return r.stdout.strip() if r is not None and r.returncode == 0 else ""

    def ok(*args):
        r = run(*args)
        return r is not None and r.returncode == 0

    if out("rev-parse", "--is-inside-work-tree") != "true":
        return None
    ref = out("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if ref.startswith("origin/"):
        return ref[len("origin/"):]
    for cand in ("main", "master", "develop", "trunk"):
        if ok("show-ref", "--verify", "--quiet", f"refs/heads/{cand}"):
            return cand
    return out("config", "--local", "--get", "init.defaultBranch") or None


def protected_branches():
    """Protected branch names: the explicit env wins; otherwise detect this repo's default.

    Projects that work on `develop`, `trunk`, or anything else get the right answer without
    configuring anything — a hardcoded `main` would silently protect a branch they don't use
    while leaving their real integration branch open.
    """
    env = os.environ.get("GIT_GUARD_PROTECTED_BRANCH")
    if env is not None:
        return {b.strip() for b in env.split(",") if b.strip()}
    detected = detected_default_branch()
    return {detected} if detected else {"main", "master"}


def integration_branch():
    """The ONE branch day-to-day work lands into, or "" when the project didn't declare it.

    Only load-bearing where the integration branch is ALSO protected — a single-branch repo,
    where `main` is both the production branch and the one worktrees are cut from and land
    into. Without this the protected-branch rule blocks the worktree protocol's own
    `git push . HEAD:<integration>` and no slice can ever land.
    """
    return os.environ.get("GIT_GUARD_INTEGRATION_BRANCH", "").strip()


# safe soft-reset targets: nothing (defaults HEAD), HEAD~N/HEAD^-style, or a sha
SAFE_SOFT_TARGET = re.compile(r"^(?:(?:HEAD|@)(?:[~^][0-9]*)*|[0-9a-fA-F]{7,40})$")


def check(command):
    """Return a block reason for the first offending git segment, or None if clean."""
    allow = env_tokens("GIT_GUARD_ALLOW")
    strict = env_tokens("GIT_GUARD_STRICT")
    # LAZY: resolving the protected set can shell out to git (~30 ms) and this runs on every
    # Bash call — only the two rules that consult it may pay that cost, and only when reached.
    protected = None

    def protected_set():
        nonlocal protected
        if protected is None:
            protected = protected_branches()
        return protected

    for seg in segments(command):
        parsed = parse_git(tokenize(seg))
        if not parsed:
            continue
        sub, args = parsed
        positional = [a for a in args if not a.startswith("-")]

        # remote sync — the user owns it; `git push .` (local-dot remote) is a LOCAL ref update
        if sub == "push":
            if positional[:1] != ["."]:
                return ("`git push` is forbidden — the user owns remote sync "
                        "(local landing `git push . <ref>` is fine)")
            if "protected-branch" not in allow:
                deleting = "--delete" in args or "-d" in args
                integration = integration_branch()
                for spec in positional[1:]:
                    forced = spec.startswith("+")
                    src, sep, dst = spec.lstrip("+").partition(":")
                    dest = dst if sep else src
                    if dest.startswith("refs/heads/"):
                        dest = dest[len("refs/heads/"):]
                    if not ((sep or deleting) and dest in protected_set()):
                        continue
                    # the worktree protocol's land: a NON-forced, non-deleting push of a real
                    # source ref into the branch this project declared as its integration branch
                    if integration and dest == integration and sep and src \
                            and not forced and not deleting:
                        continue
                    return (f"push refspec targets protected branch `{dest}` — protected "
                            "branches are never the agent's to move "
                            "(GIT_GUARD_PROTECTED_BRANCH to change which; "
                            "GIT_GUARD_INTEGRATION_BRANCH to permit the fast-forward land)")
        if sub == "pull":
            return "`git pull` is forbidden — the user owns remote sync"
        if sub == "fetch" and "fetch" not in allow:
            allow_fetch = env_tokens("GIT_GUARD_ALLOW_FETCH")
            target = positional[0] if positional else ""     # `git fetch <remote> [refspec...]`
            multi = any(a in ("--all", "--multiple") for a in args)
            if multi or not (allow_fetch and target and target in allow_fetch):
                return ("`git fetch` syncs the remote — the user owns remote sync "
                        "(GIT_GUARD_ALLOW=fetch for all remotes, or "
                        "GIT_GUARD_ALLOW_FETCH=<remote,...> to permit named remotes only)")

        # staging discipline — bulk adds sweep in files you didn't mean to commit
        if sub == "add" and "bulk-add" not in allow:
            if any(a in ("-A", "--all") for a in args) \
                    or any(re.match(r"^-[a-zA-Z]*A", a) for a in args) \
                    or any(p in (".", "./") for p in positional):
                return ("bulk staging (`git add -A` / `--all` / `.`) sweeps in strays — "
                        "stage files by name: `git add <path> <path>`")

        # merge discipline — merge means rebase + FF-only; no merge commits
        if sub == "merge" and "merge" not in allow:
            if not any(a in ("--ff-only", "--abort", "--continue", "--quit") for a in args):
                return ("plain `git merge` can create a merge commit — rebase, then "
                        "`git merge --ff-only` (a non-FF merge is never the agent's to make)")

        # history rewrites
        if sub == "rebase" and "rebase" in strict:
            return ("`git rebase` rewrites history — blocked by GIT_GUARD_STRICT in this "
                    "project; ask the user")
        if sub == "filter-branch":
            return "`git filter-branch` rewrites history — not without the user"
        if sub == "reset":
            if "reset" in strict:
                return ("`git reset` is blocked by GIT_GUARD_STRICT in this project — no index/"
                        "history manipulation by the agent; the user runs any reset themselves")
            if any(a in ("--hard", "--merge", "--keep") for a in args):
                return ("`git reset --hard` clobbers the worktree — check what's there first; "
                        "plain `git reset <file>` to unstage is fine")
            if "--soft" in args and "soft-reset" not in allow:
                target = positional[0] if positional else ""
                if target and not SAFE_SOFT_TARGET.match(target):
                    return (f"`git reset --soft {target}` resolves a MOVING ref — if it advanced "
                            "since you branched, the squash silently reverts other commits. "
                            "Soft-reset only against your own base: `HEAD~<N>` or a sha")

        # commit safety (history / hooks) — message FORMAT lives in the commit plugin
        if sub == "commit":
            if "--amend" in args and "amend" in strict:
                return ("`git commit --amend` rewrites history — blocked by GIT_GUARD_STRICT "
                        "in this project; make a new commit instead")
            if "--no-verify" in args or "-n" in args:
                return "`git commit --no-verify` skips hooks — fix the underlying issue instead"

        # protected branch — never checkout/switch onto it
        if sub in ("checkout", "switch") and "protected-branch" not in allow:
            dd = args.index("--") if "--" in args else len(args)
            head_positional = [a for a in args[:dd] if not a.startswith("-")]
            if head_positional[:1] and head_positional[0] in protected_set():
                return (f"`git {sub} {head_positional[0]}` — the protected branch is off-limits "
                        "to the agent; work on a feature branch "
                        "(GIT_GUARD_PROTECTED_BRANCH to change which)")

        # never discard uncommitted work — the tree may hold the user's WIP
        if sub == "clean" and (any(re.match(r"^-[a-zA-Z]*f", a) for a in args) or "--force" in args):
            return ("`git clean -f` deletes untracked work — if the user wants this, they run it "
                    "(`git clean -n` dry-run is fine)")
        if sub == "stash" and positional[:1] in (["drop"], ["clear"]):
            return f"`git stash {positional[0]}` destroys stashed work — user-only operation"
        if sub == "checkout":
            dd = args.index("--") if "--" in args else -1
            ref_before = dd > 0 and any(not a.startswith("-") for a in args[:dd])
            if ref_before:
                # `git checkout <ref> -- <path>` — fix-forward restore of a file from a ref;
                # allowed by default (rebase-based flows use it), re-block via GIT_GUARD_STRICT
                if "checkout-file" in strict:
                    return ("`git checkout <ref> -- <path>` overwrites <path> with the version "
                            "from <ref> — blocked by GIT_GUARD_STRICT in this project")
            elif dd >= 0 or "." in positional:
                return ("`git checkout -- <path>` / `checkout .` discards uncommitted changes — "
                        "branch switches are fine, this is not")
        if sub == "restore":
            staged = "--staged" in args or "-S" in args
            touches_worktree = "--worktree" in args or "-W" in args
            if not (staged and not touches_worktree):
                return ("`git restore` discards worktree changes — only `git restore --staged` / "
                        "`-S <path>` to unstage is allowed")
    return None


def main():
    if os.environ.get("GIT_GUARD_OFF") == "1":
        return
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    command = (data.get("tool_input") or {}).get("command", "")
    reason = check(command)
    if reason:
        deny(reason)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail-open: never brick the session on a hook bug
