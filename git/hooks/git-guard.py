#!/usr/bin/env python3
"""PreToolUse[Bash] guard — mechanically enforce git safety (destructive / remote / history ops).

Hard-blocks (exit 2, reason fed back to the model):
  - git push / git pull / git fetch   the user owns ALL remote sync (`git push .` is a LOCAL
                                      ref update — a landing move, not a remote op)
  - git add -A / --all / .            bulk staging sweeps in strays — stage files by name
  - plain git merge                   merge means rebase + `merge --ff-only`; a merge commit is
                                      never the agent's to make (`--ff-only/--abort/--continue/
                                      --quit` pass)
  - protected-branch ops              `checkout`/`switch` onto the protected branch, and push
                                      refspecs targeting it (`HEAD:<protected>`, `:<protected>`,
                                      `--delete`). Name(s) from GIT_GUARD_PROTECTED_BRANCH; unset,
                                      the repo's OWN default branch is detected (origin/HEAD →
                                      first existing of main/master/develop/trunk → repo-local
                                      init.defaultBranch), so `develop`-based projects need no
                                      config. EXCEPTION: a fast-forward landing push into the
                                      declared GIT_GUARD_INTEGRATION_BRANCH passes even when that
                                      branch is also protected (single-branch repos) — see below
  - git reset --soft <moving-ref>     soft-reset squashes only against HEAD~N / a sha — a branch
                                      or remote ref can advance underneath you
  - git filter-branch                 history rewrite
  - git reset --hard / --merge / --keep   clobbers the worktree (plain `git reset <file>`
                                          / `--staged` to unstage is allowed)
  - git commit --no-verify            never skip hooks
  - discarding uncommitted work: git clean -f, stash drop|clear, checkout -- / checkout .,
    git restore (only `restore --staged` / `-S` to unstage is allowed) — the tree may hold WIP

Allowed by default (rebase + FF-only landing flows need them):
  - git rebase (all forms), git commit --amend, git checkout <ref> -- <path> (fix-forward
    restore of a file from a ref). Re-block via GIT_GUARD_STRICT (below).

This is the SAFETY net only — it says nothing about commit message style. The house commit format
(single line, no trailers) lives in the separate `commit` plugin's commit-format hook; enable that
plugin if you want the format enforced too.

Fail-open by design: any unexpected error exits 0 so a broken hook can never brick a
session. Escape hatches (user-set only — the hook reads its own process env):
  GIT_GUARD_OFF=1               disable everything.
  GIT_GUARD_STRICT              comma-separated tokens RE-ENABLING blocks the default leaves off:
                                `rebase`, `amend`, `checkout-file`, `reset` (block ALL `git reset`,
                                even unstage / soft-to-HEAD~N — for repos that forbid ANY
                                index/history manipulation by the agent).
  GIT_GUARD_ALLOW               comma-separated tokens RELAXING workflow blocks for projects that
                                need them: `fetch`, `bulk-add`, `merge`, `protected-branch`,
                                `soft-reset`. (The destructive core — push/pull, reset --hard,
                                discards, --no-verify — has no allow token; use GIT_GUARD_OFF.)
  GIT_GUARD_ALLOW_FETCH         comma-separated REMOTE names — permit `git fetch <remote>` for those
                                remotes only (narrower than the all-or-nothing `fetch` token). Bare
                                `git fetch`, `--all`, and `--multiple` stay blocked.
  GIT_GUARD_PROTECTED_BRANCH    comma-separated protected branch name(s). UNSET → auto-detect the
                                repo's default branch (see above); set it explicitly when the
                                protected branch differs from the default (e.g. `main` protected
                                while day-to-day work lands on `develop`), or to protect several
                                (`main,release`). Empty string = protect nothing.
  GIT_GUARD_INTEGRATION_BRANCH  ONE branch name — where day-to-day work lands (`develop` in a
                                two-tier repo, the single branch in a GitHub-flow one). Only
                                needed when it is ALSO protected: then `git push . HEAD:<it>` —
                                the worktree protocol's fast-forward land — is permitted, while
                                `checkout`/`switch`/`merge` onto it and every force (`+`) or
                                delete (`:<it>`, `--delete`) refspec stay blocked. Leave unset in
                                a two-tier repo: `develop` isn't protected, so lands already pass.
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


def self_test():
    fails = 0
    env_keys = ("GIT_GUARD_ALLOW", "GIT_GUARD_ALLOW_FETCH", "GIT_GUARD_STRICT",
                "GIT_GUARD_PROTECTED_BRANCH", "GIT_GUARD_INTEGRATION_BRANCH")

    def chk(name, want_blocked, cmd, allow="", strict="", protected="main", allow_fetch="",
            integration=""):
        # `protected` defaults to an EXPLICIT "main" so these cases never depend on the branch
        # layout of whatever repo the self-test runs in (auto-detection is covered separately).
        nonlocal fails
        saved = {k: os.environ.get(k) for k in env_keys}
        os.environ["GIT_GUARD_ALLOW"] = allow
        os.environ["GIT_GUARD_ALLOW_FETCH"] = allow_fetch
        os.environ["GIT_GUARD_STRICT"] = strict
        os.environ["GIT_GUARD_PROTECTED_BRANCH"] = protected
        os.environ["GIT_GUARD_INTEGRATION_BRANCH"] = integration
        try:
            reason = check(cmd)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        got_blocked = reason is not None
        if got_blocked == want_blocked:
            print(f"PASS  {name}")
        else:
            print(f"FAIL  {name}: reason={reason!r}")
            fails += 1

    # remote sync
    chk("push to remote blocked", True, "git push origin main")
    chk("bare push blocked", True, "git push")
    chk("push -u blocked", True, "git push -u origin feature")
    chk("local-dot push allowed", False, "git push . HEAD:develop")
    chk("local-dot push with flag allowed", False, "git push --force-with-lease . HEAD:develop")
    chk("pull blocked", True, "git pull")
    chk("fetch blocked", True, "git fetch origin")
    chk("bare fetch blocked", True, "git fetch")
    chk("fetch allowed via GIT_GUARD_ALLOW", False, "git fetch origin", allow="fetch")
    chk("git -C push blocked", True, "git -C /x/y push origin develop")

    # per-remote fetch allow (GIT_GUARD_ALLOW_FETCH) — narrower than the blanket `fetch` token
    chk("fetch named remote allowed via ALLOW_FETCH", False, "git fetch origin", allow_fetch="origin")
    chk("fetch other remote blocked under ALLOW_FETCH", True, "git fetch upstream", allow_fetch="origin")
    chk("fetch named among several allowed", False, "git fetch upstream", allow_fetch="origin,upstream")
    chk("fetch named remote + refspec allowed", False, "git fetch origin main", allow_fetch="origin")
    chk("bare fetch still blocked under ALLOW_FETCH", True, "git fetch", allow_fetch="origin")
    chk("fetch --all blocked under ALLOW_FETCH", True, "git fetch --all", allow_fetch="origin")
    chk("fetch --multiple blocked under ALLOW_FETCH", True,
        "git fetch --multiple origin upstream", allow_fetch="origin,upstream")
    chk("blanket fetch token still allows any remote", False, "git fetch upstream", allow="fetch")

    # protected branch
    chk("push refspec to protected blocked", True, "git push . HEAD:main")
    chk("push refspec to refs/heads/protected blocked", True, "git push . HEAD:refs/heads/main")
    chk("push forced refspec to protected blocked", True, "git push . +HEAD:main")
    chk("push delete-refspec to protected blocked", True, "git push . :main")
    chk("push --delete protected blocked", True, "git push . --delete main")
    chk("push refspec to develop allowed", False, "git push . HEAD:develop")
    chk("checkout protected blocked", True, "git checkout main")
    chk("switch protected blocked", True, "git switch main")
    chk("checkout file named like protected allowed", False, "git checkout main-menu.ts")
    chk("checkout other branch allowed", False, "git checkout develop")
    chk("switch -c off protected allowed", False, "git switch -c feat main")
    chk("custom protected branch blocked", True, "git checkout master", protected="master")
    chk("default protected not blocked under custom", False, "git checkout main",
        protected="master")
    chk("multi protected branches blocked", True, "git switch trunk", protected="main,trunk")
    chk("protected-branch allow token relaxes", False, "git checkout main",
        allow="protected-branch")

    # integration branch == protected branch (single-branch repo): the land passes, nothing else
    chk("land into protected integration allowed", False, "git push . HEAD:main",
        integration="main")
    chk("land into refs/heads/<integration> allowed", False, "git push . HEAD:refs/heads/main",
        integration="main")
    chk("land from a named branch allowed", False, "git push . feature/x:main",
        integration="main")
    chk("forced land into integration blocked", True, "git push . +HEAD:main", integration="main")
    chk("delete-refspec of integration blocked", True, "git push . :main", integration="main")
    chk("--delete of integration blocked", True, "git push . --delete main", integration="main")
    chk("checkout of protected integration still blocked", True, "git checkout main",
        integration="main")
    chk("integration naming a DIFFERENT branch does not unlock protected", True,
        "git push . HEAD:main", integration="develop")
    chk("integration unset keeps protected push blocked", True, "git push . HEAD:main")
    chk("land into one protected leaves the others blocked", True, "git push . HEAD:release",
        protected="main,release", integration="main")

    # staging discipline
    chk("add -A blocked", True, "git add -A")
    chk("add --all blocked", True, "git add --all")
    chk("add . blocked", True, "git add .")
    chk("add -f . blocked", True, "git add -f .")
    chk("add -fA blocked", True, "git add -fA")
    chk("add in chain blocked", True, "cd /x && git add -A && git commit -m x")
    chk("add by name allowed", False, "git add src/foo.ts src/bar.ts")
    chk("add ./relative path allowed", False, "git add ./src/foo.ts")
    chk("add -p path allowed", False, "git add -p src/foo.ts")
    chk("add -u dir allowed", False, "git add -u src/")
    chk("bulk-add allow token relaxes", False, "git add -A", allow="bulk-add")

    # merge discipline
    chk("plain merge blocked", True, "git merge feature/foo")
    chk("merge --ff-only allowed", False, "git merge --ff-only feature/foo")
    chk("merge --abort allowed", False, "git merge --abort")
    chk("merge --continue allowed", False, "git merge --continue")
    chk("merge-base allowed", False, "git merge-base HEAD develop")
    chk("merge allow token relaxes", False, "git merge feature/foo", allow="merge")

    # history — rebase/amend allowed by default, strict re-blocks
    chk("rebase allowed by default", False, "git rebase develop")
    chk("rebase -i allowed by default", False, "git rebase -i HEAD~3")
    chk("rebase blocked via GIT_GUARD_STRICT", True, "git rebase develop", strict="rebase")
    chk("amend allowed by default", False, "git commit --amend --no-edit")
    chk("amend blocked via GIT_GUARD_STRICT", True, "git commit --amend", strict="amend")
    chk("rebase+amend chain allowed by default", False,
        "git rebase develop && git commit --amend")
    chk("filter-branch blocked", True, "git filter-branch --all")
    chk("no-verify blocked", True, "git commit --no-verify -m x")
    chk("-n commit blocked", True, "git commit -n -m x")

    # reset
    chk("reset --hard blocked", True, "git reset --hard HEAD~1")
    chk("reset --merge blocked", True, "git reset --merge")
    chk("reset soft HEAD~N allowed", False, "git reset --soft HEAD~3")
    chk("reset soft HEAD^ allowed", False, "git reset --soft HEAD^")
    chk("reset soft sha allowed", False, "git reset --soft 679e56b8")
    chk("bare reset soft allowed", False, "git reset --soft")
    chk("reset soft branch blocked", True, "git reset --soft develop")
    chk("reset soft origin ref blocked", True, "git reset --soft origin/develop")
    chk("reset soft upstream blocked", True, "git reset --soft @{u}")
    chk("soft-reset allow token relaxes", False, "git reset --soft develop", allow="soft-reset")
    chk("reset file allowed", False, "git reset src/app.ts")
    # GIT_GUARD_STRICT=reset — paranoid mode blocks ALL reset forms
    chk("reset soft HEAD~N blocked via strict=reset", True, "git reset --soft HEAD~3", strict="reset")
    chk("reset file blocked via strict=reset", True, "git reset src/app.ts", strict="reset")
    chk("reset --hard blocked via strict=reset", True, "git reset --hard HEAD~1", strict="reset")
    chk("bare reset blocked via strict=reset", True, "git reset", strict="reset")

    # discards
    chk("clean -f blocked", True, "git clean -fd")
    chk("clean -n allowed", False, "git clean -n")
    chk("stash drop blocked", True, "git stash drop")
    chk("stash push allowed", False, "git stash push -m wip")
    chk("checkout branch allowed", False, "git checkout feature-x")
    chk("checkout -- path blocked", True, "git checkout -- src/app.ts")
    chk("checkout . blocked", True, "git checkout .")
    chk("checkout ref -- path allowed by default", False, "git checkout abc123 -- src/app.ts")
    chk("checkout ref -- path blocked via GIT_GUARD_STRICT", True,
        "git checkout abc123 -- src/app.ts", strict="checkout-file")
    chk("checkout -- path blocked regardless of strict", True,
        "git checkout -- src/app.ts", strict="checkout-file")
    chk("restore path blocked", True, "git restore src/app.ts")
    chk("restore --staged allowed", False, "git restore --staged src/app.ts")
    chk("restore -S allowed (same as long form)", False, "git restore -S src/app.ts")
    chk("restore -S -W blocked (touches worktree)", True, "git restore -S -W src/app.ts")
    chk("restore --staged --worktree blocked", True, "git restore --staged --worktree src/app.ts")

    chk("non-git command allowed", False, "ls -la && echo done")

    # --- protected-branch auto-detection (no GIT_GUARD_PROTECTED_BRANCH set) ---
    import shutil
    import tempfile

    def det(name, want, setup):
        """Build a throwaway repo, run detection from inside it, compare to `want`."""
        nonlocal fails
        tmp = tempfile.mkdtemp()
        cwd = os.getcwd()
        saved = {k: os.environ.get(k)
                 for k in ("GIT_GUARD_PROTECTED_BRANCH", "GIT_CEILING_DIRECTORIES")}
        os.environ.pop("GIT_GUARD_PROTECTED_BRANCH", None)
        # stop git walking ABOVE the throwaway dir — otherwise the "not a repo" case finds
        # whatever repo happens to contain $TMPDIR on this machine and the test flakes
        os.environ["GIT_CEILING_DIRECTORIES"] = os.path.dirname(tmp)
        try:
            setup(tmp)
            os.chdir(tmp)
            got = protected_branches()
        finally:
            os.chdir(cwd)
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            shutil.rmtree(tmp, ignore_errors=True)
        if got == want:
            print(f"PASS  {name}")
        else:
            print(f"FAIL  {name}: got {got!r}, want {want!r}")
            fails += 1

    def g(cwd, *args):
        subprocess.run(("git", "-C", cwd) + args, capture_output=True, text=True, timeout=5)

    def repo(branch):
        def setup(tmp):
            g(tmp, "init", "-q", "-b", branch)
            g(tmp, "-c", "user.email=t@t", "-c", "user.name=t",
              "commit", "-q", "--allow-empty", "-m", "init")
        return setup

    def repo_with_origin_head(branch):
        def setup(tmp):
            repo(branch)(tmp)
            # simulate a clone's origin/HEAD symref without needing a real remote
            g(tmp, "update-ref", f"refs/remotes/origin/{branch}", "HEAD")
            g(tmp, "symbolic-ref", "refs/remotes/origin/HEAD", f"refs/remotes/origin/{branch}")
        return setup

    det("detect: origin/HEAD -> develop", {"develop"}, repo_with_origin_head("develop"))
    det("detect: origin/HEAD -> main", {"main"}, repo_with_origin_head("main"))
    det("detect: no origin, local develop only", {"develop"}, repo("develop"))
    det("detect: no origin, local trunk only", {"trunk"}, repo("trunk"))
    det("detect: not a repo -> main,master fallback", {"main", "master"}, lambda tmp: None)

    saved = os.environ.get("GIT_GUARD_PROTECTED_BRANCH")
    os.environ["GIT_GUARD_PROTECTED_BRANCH"] = ""
    got = protected_branches()
    if got == set():
        print("PASS  explicit empty GIT_GUARD_PROTECTED_BRANCH protects nothing")
    else:
        print(f"FAIL  explicit empty protects nothing: got {got!r}")
        fails += 1
    if saved is None:
        os.environ.pop("GIT_GUARD_PROTECTED_BRANCH", None)
    else:
        os.environ["GIT_GUARD_PROTECTED_BRANCH"] = saved

    print("all tests passed" if fails == 0 else f"{fails} FAILED")
    return fails


def main():
    if "--test" in sys.argv:
        sys.exit(self_test())
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
