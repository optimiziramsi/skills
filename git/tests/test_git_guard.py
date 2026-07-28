#!/usr/bin/env python3
"""Self-tests for git-guard. Run: python3 git/tests/test_git_guard.py

Two halves: a case table over `check()` (does this command get blocked?), then
protected-branch AUTO-DETECTION against throwaway repos.
"""
import contextlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, load_module  # noqa: E402

check = Check()
guard = load_module(hook("git/hooks/git-guard.py"), "git_guard")

ENV_KEYS = ("GIT_GUARD_ALLOW", "GIT_GUARD_ALLOW_FETCH", "GIT_GUARD_STRICT",
            "GIT_GUARD_PROTECTED_BRANCH", "GIT_GUARD_INTEGRATION_BRANCH")


@contextlib.contextmanager
def env(**overrides):
    """Set the guard's env vars for one case and restore whatever was there before."""
    saved = {k: os.environ.get(k) for k in ENV_KEYS}
    os.environ.update({k: v for k, v in overrides.items()})
    try:
        yield
    finally:
        for key, value in saved.items():
            os.environ.pop(key, None) if value is None else os.environ.update({key: value})


def blocks(name, want_blocked, command, allow="", strict="", protected="main",
           allow_fetch="", integration=""):
    """`protected` defaults to an EXPLICIT "main" so no case depends on the branch layout
    of whatever repo the suite happens to run in — detection is covered separately below."""
    with env(GIT_GUARD_ALLOW=allow, GIT_GUARD_ALLOW_FETCH=allow_fetch, GIT_GUARD_STRICT=strict,
             GIT_GUARD_PROTECTED_BRANCH=protected, GIT_GUARD_INTEGRATION_BRANCH=integration):
        reason = guard.check(command)
    check(name, (reason is not None) == want_blocked, repr(reason))


# ── remote sync — the user owns it ─────────────────────────────────────────
blocks("push to remote blocked", True, "git push origin main")
blocks("bare push blocked", True, "git push")
blocks("push -u blocked", True, "git push -u origin feature")
blocks("local-dot push allowed", False, "git push . HEAD:develop")
blocks("local-dot push with flag allowed", False, "git push --force-with-lease . HEAD:develop")
blocks("pull blocked", True, "git pull")
blocks("fetch blocked", True, "git fetch origin")
blocks("bare fetch blocked", True, "git fetch")
blocks("fetch allowed via GIT_GUARD_ALLOW", False, "git fetch origin", allow="fetch")
blocks("git -C push blocked", True, "git -C /x/y push origin develop")

# per-remote fetch allow — narrower than the blanket `fetch` token
blocks("fetch named remote allowed via ALLOW_FETCH", False, "git fetch origin", allow_fetch="origin")
blocks("fetch other remote blocked under ALLOW_FETCH", True, "git fetch upstream", allow_fetch="origin")
blocks("fetch named among several allowed", False, "git fetch upstream", allow_fetch="origin,upstream")
blocks("fetch named remote + refspec allowed", False, "git fetch origin main", allow_fetch="origin")
blocks("bare fetch still blocked under ALLOW_FETCH", True, "git fetch", allow_fetch="origin")
blocks("fetch --all blocked under ALLOW_FETCH", True, "git fetch --all", allow_fetch="origin")
blocks("fetch --multiple blocked under ALLOW_FETCH", True,
       "git fetch --multiple origin upstream", allow_fetch="origin,upstream")
blocks("blanket fetch token still allows any remote", False, "git fetch upstream", allow="fetch")

# ── protected branch ───────────────────────────────────────────────────────
blocks("push refspec to protected blocked", True, "git push . HEAD:main")
blocks("push refspec to refs/heads/protected blocked", True, "git push . HEAD:refs/heads/main")
blocks("push forced refspec to protected blocked", True, "git push . +HEAD:main")
blocks("push delete-refspec to protected blocked", True, "git push . :main")
blocks("push --delete protected blocked", True, "git push . --delete main")
blocks("push refspec to develop allowed", False, "git push . HEAD:develop")
blocks("checkout protected blocked", True, "git checkout main")
blocks("switch protected blocked", True, "git switch main")
blocks("checkout file named like protected allowed", False, "git checkout main-menu.ts")
blocks("checkout other branch allowed", False, "git checkout develop")
blocks("switch -c off protected allowed", False, "git switch -c feat main")
blocks("custom protected branch blocked", True, "git checkout master", protected="master")
blocks("default protected not blocked under custom", False, "git checkout main", protected="master")
blocks("multi protected branches blocked", True, "git switch trunk", protected="main,trunk")
blocks("protected-branch allow token relaxes", False, "git checkout main", allow="protected-branch")

# integration branch == protected branch (single-branch repo): the land passes, nothing else
blocks("land into protected integration allowed", False, "git push . HEAD:main", integration="main")
blocks("land into refs/heads/<integration> allowed", False, "git push . HEAD:refs/heads/main",
       integration="main")
blocks("land from a named branch allowed", False, "git push . feature/x:main", integration="main")
blocks("forced land into integration blocked", True, "git push . +HEAD:main", integration="main")
blocks("delete-refspec of integration blocked", True, "git push . :main", integration="main")
blocks("--delete of integration blocked", True, "git push . --delete main", integration="main")
blocks("checkout of protected integration still blocked", True, "git checkout main",
       integration="main")
blocks("integration naming a DIFFERENT branch does not unlock protected", True,
       "git push . HEAD:main", integration="develop")
blocks("integration unset keeps protected push blocked", True, "git push . HEAD:main")
blocks("land into one protected leaves the others blocked", True, "git push . HEAD:release",
       protected="main,release", integration="main")

# ── staging discipline ─────────────────────────────────────────────────────
blocks("add -A blocked", True, "git add -A")
blocks("add --all blocked", True, "git add --all")
blocks("add . blocked", True, "git add .")
blocks("add -f . blocked", True, "git add -f .")
blocks("add -fA blocked", True, "git add -fA")
blocks("add in chain blocked", True, "cd /x && git add -A && git commit -m x")
blocks("add by name allowed", False, "git add src/foo.ts src/bar.ts")
blocks("add ./relative path allowed", False, "git add ./src/foo.ts")
blocks("add -p path allowed", False, "git add -p src/foo.ts")
blocks("add -u dir allowed", False, "git add -u src/")
blocks("bulk-add allow token relaxes", False, "git add -A", allow="bulk-add")

# ── merge discipline ───────────────────────────────────────────────────────
blocks("plain merge blocked", True, "git merge feature/foo")
blocks("merge --ff-only allowed", False, "git merge --ff-only feature/foo")
blocks("merge --abort allowed", False, "git merge --abort")
blocks("merge --continue allowed", False, "git merge --continue")
blocks("merge-base allowed", False, "git merge-base HEAD develop")
blocks("merge allow token relaxes", False, "git merge feature/foo", allow="merge")

# ── history — rebase/amend allowed by default, strict re-blocks ────────────
blocks("rebase allowed by default", False, "git rebase develop")
blocks("rebase -i allowed by default", False, "git rebase -i HEAD~3")
blocks("rebase blocked via GIT_GUARD_STRICT", True, "git rebase develop", strict="rebase")
blocks("amend allowed by default", False, "git commit --amend --no-edit")
blocks("amend blocked via GIT_GUARD_STRICT", True, "git commit --amend", strict="amend")
blocks("rebase+amend chain allowed by default", False, "git rebase develop && git commit --amend")
blocks("filter-branch blocked", True, "git filter-branch --all")
blocks("no-verify blocked", True, "git commit --no-verify -m x")
blocks("-n commit blocked", True, "git commit -n -m x")

# ── reset ──────────────────────────────────────────────────────────────────
blocks("reset --hard blocked", True, "git reset --hard HEAD~1")
blocks("reset --merge blocked", True, "git reset --merge")
blocks("reset soft HEAD~N allowed", False, "git reset --soft HEAD~3")
blocks("reset soft HEAD^ allowed", False, "git reset --soft HEAD^")
blocks("reset soft sha allowed", False, "git reset --soft 679e56b8")
blocks("bare reset soft allowed", False, "git reset --soft")
blocks("reset soft branch blocked", True, "git reset --soft develop")
blocks("reset soft origin ref blocked", True, "git reset --soft origin/develop")
blocks("reset soft upstream blocked", True, "git reset --soft @{u}")
blocks("soft-reset allow token relaxes", False, "git reset --soft develop", allow="soft-reset")
blocks("reset file allowed", False, "git reset src/app.ts")
blocks("reset soft HEAD~N blocked via strict=reset", True, "git reset --soft HEAD~3", strict="reset")
blocks("reset file blocked via strict=reset", True, "git reset src/app.ts", strict="reset")
blocks("reset --hard blocked via strict=reset", True, "git reset --hard HEAD~1", strict="reset")
blocks("bare reset blocked via strict=reset", True, "git reset", strict="reset")

# ── never discard uncommitted work ─────────────────────────────────────────
blocks("clean -f blocked", True, "git clean -fd")
blocks("clean -n allowed", False, "git clean -n")
blocks("stash drop blocked", True, "git stash drop")
blocks("stash push allowed", False, "git stash push -m wip")
blocks("checkout branch allowed", False, "git checkout feature-x")
blocks("checkout -- path blocked", True, "git checkout -- src/app.ts")
blocks("checkout . blocked", True, "git checkout .")
blocks("checkout ref -- path allowed by default", False, "git checkout abc123 -- src/app.ts")
blocks("checkout ref -- path blocked via GIT_GUARD_STRICT", True,
       "git checkout abc123 -- src/app.ts", strict="checkout-file")
blocks("checkout -- path blocked regardless of strict", True,
       "git checkout -- src/app.ts", strict="checkout-file")
blocks("restore path blocked", True, "git restore src/app.ts")
blocks("restore --staged allowed", False, "git restore --staged src/app.ts")
blocks("restore -S allowed (same as long form)", False, "git restore -S src/app.ts")
blocks("restore -S -W blocked (touches worktree)", True, "git restore -S -W src/app.ts")
blocks("restore --staged --worktree blocked", True, "git restore --staged --worktree src/app.ts")

blocks("non-git command allowed", False, "ls -la && echo done")


# ── protected-branch AUTO-DETECTION (no GIT_GUARD_PROTECTED_BRANCH set) ────
def git(cwd, *args):
    subprocess.run(("git", "-C", cwd) + args, capture_output=True, text=True, timeout=5)


def repo(branch, with_origin_head=False):
    def setup(tmp):
        git(tmp, "init", "-q", "-b", branch)
        git(tmp, "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-q", "--allow-empty", "-m", "init")
        if with_origin_head:
            # a clone's origin/HEAD symref, without needing a real remote
            git(tmp, "update-ref", f"refs/remotes/origin/{branch}", "HEAD")
            git(tmp, "symbolic-ref", "refs/remotes/origin/HEAD", f"refs/remotes/origin/{branch}")
    return setup


def detects(name, want, setup):
    """Build a throwaway repo, resolve the protected set from inside it, compare."""
    tmp = tempfile.mkdtemp()
    cwd = os.getcwd()
    saved = os.environ.get("GIT_CEILING_DIRECTORIES")
    os.environ.pop("GIT_GUARD_PROTECTED_BRANCH", None)
    # stop git walking ABOVE the throwaway dir — otherwise the "not a repo" case finds
    # whatever repo happens to contain $TMPDIR on this machine and the test flakes
    os.environ["GIT_CEILING_DIRECTORIES"] = os.path.dirname(tmp)
    try:
        setup(tmp)
        os.chdir(tmp)
        guard._DETECT_CACHE.clear()                  # the guard memoizes per cwd
        got = guard.protected_branches()
    finally:
        os.chdir(cwd)
        os.environ.pop("GIT_CEILING_DIRECTORIES", None) if saved is None \
            else os.environ.update({"GIT_CEILING_DIRECTORIES": saved})
        shutil.rmtree(tmp, ignore_errors=True)
    check(name, got == want, f"got {got!r}, want {want!r}")


detects("detect: origin/HEAD -> develop", {"develop"}, repo("develop", with_origin_head=True))
detects("detect: origin/HEAD -> main", {"main"}, repo("main", with_origin_head=True))
detects("detect: no origin, local develop only", {"develop"}, repo("develop"))
detects("detect: no origin, local trunk only", {"trunk"}, repo("trunk"))
detects("detect: not a repo -> main,master fallback", {"main", "master"}, lambda tmp: None)

with env(GIT_GUARD_PROTECTED_BRANCH=""):
    check("an explicit empty GIT_GUARD_PROTECTED_BRANCH protects nothing",
          guard.protected_branches() == set())

sys.exit(check.done())
