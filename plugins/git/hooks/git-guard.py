#!/usr/bin/env python3
"""PreToolUse[Bash] guard — mechanically enforce git safety (destructive / remote / history ops).

Hard-blocks (exit 2, reason fed back to the model), branch-agnostic:
  - git push / git pull               the user owns remote sync (git fetch is fine; `git push .`
                                      is a LOCAL ref update — a landing move, not a remote op)
  - git commit --amend                history is append-only — make a new commit
  - git rebase / git filter-branch    history rewrite
  - git reset --hard / --merge / --keep   clobbers the worktree (plain `git reset <file>`
                                          / `--staged` to unstage is allowed)
  - git commit --no-verify            never skip hooks
  - discarding uncommitted work: git clean -f, stash drop|clear, checkout -- / checkout .,
    git restore (only `restore --staged` / `-S` to unstage is allowed) — the tree may hold WIP

This is the SAFETY net only — it says nothing about commit message style. The house commit format
(single line, no trailers) lives in the separate `commit` plugin's commit-format hook; enable that
plugin if you want the format enforced too.

Fail-open by design: any unexpected error exits 0 so a broken hook can never brick a
session. Escape hatches (user-set only): GIT_GUARD_OFF=1 disables everything;
GIT_GUARD_ALLOW is a comma-separated token list that suppresses individual blocks —
`rebase` (rebase-based landing flows), `amend`, `checkout-file` (`git checkout <ref> -- <path>`).
"""
import json
import os
import re
import shlex
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


def allow_tokens():
    return {t.strip() for t in os.environ.get("GIT_GUARD_ALLOW", "").split(",") if t.strip()}


def check(command):
    """Return a block reason for the first offending git segment, or None if clean."""
    allow = allow_tokens()
    for seg in segments(command):
        parsed = parse_git(tokenize(seg))
        if not parsed:
            continue
        sub, args = parsed
        positional = [a for a in args if not a.startswith("-")]

        # remote sync — the user owns it; `git push .` (local-dot remote) is a LOCAL ref update
        if sub == "push" and positional[:1] != ["."]:
            return ("`git push` is forbidden — the user owns remote sync "
                    "(local landing `git push . <ref>` is fine)")
        if sub == "pull":
            return "`git pull` is forbidden — the user owns remote sync (`git fetch` is fine)"

        # history rewrites
        if sub == "rebase" and "rebase" not in allow:
            return ("`git rebase` rewrites history — not without the user "
                    "(GIT_GUARD_ALLOW=rebase if your landing flow rebases)")
        if sub == "filter-branch":
            return "`git filter-branch` rewrites history — not without the user"
        if sub == "reset" and any(a in ("--hard", "--merge", "--keep") for a in args):
            return ("`git reset --hard` clobbers the worktree — check what's there first; "
                    "plain `git reset <file>` to unstage is fine")

        # commit safety (history / hooks) — message FORMAT lives in the commit plugin
        if sub == "commit":
            if "--amend" in args and "amend" not in allow:
                return ("`git commit --amend` rewrites history — make a new commit instead "
                        "(GIT_GUARD_ALLOW=amend to permit)")
            if "--no-verify" in args or "-n" in args:
                return "`git commit --no-verify` skips hooks — fix the underlying issue instead"

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
                # `git checkout <ref> -- <path>` — overwrites <path> with the ref's version
                if "checkout-file" not in allow:
                    return ("`git checkout <ref> -- <path>` overwrites <path> with the version "
                            "from <ref> — GIT_GUARD_ALLOW=checkout-file to permit")
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

    def chk(name, want_blocked, cmd, allow=""):
        nonlocal fails
        old = os.environ.get("GIT_GUARD_ALLOW")
        os.environ["GIT_GUARD_ALLOW"] = allow
        try:
            reason = check(cmd)
        finally:
            if old is None:
                os.environ.pop("GIT_GUARD_ALLOW", None)
            else:
                os.environ["GIT_GUARD_ALLOW"] = old
        got_blocked = reason is not None
        if got_blocked == want_blocked:
            print(f"PASS  {name}")
        else:
            print(f"FAIL  {name}: reason={reason!r}")
            fails += 1

    chk("push to remote blocked", True, "git push origin main")
    chk("bare push blocked", True, "git push")
    chk("push -u blocked", True, "git push -u origin feature")
    chk("local-dot push allowed", False, "git push . HEAD:develop")
    chk("local-dot push with flag allowed", False, "git push --force-with-lease . HEAD:develop")
    chk("pull blocked", True, "git pull")
    chk("fetch allowed", False, "git fetch origin")
    chk("rebase blocked by default", True, "git rebase develop")
    chk("rebase allowed via GIT_GUARD_ALLOW", False, "git rebase develop", allow="rebase")
    chk("filter-branch blocked even with allow", True, "git filter-branch --all", allow="rebase")
    chk("amend blocked by default", True, "git commit --amend")
    chk("amend allowed via GIT_GUARD_ALLOW", False, "git commit --amend", allow="amend")
    chk("no-verify blocked", True, "git commit --no-verify -m x")
    chk("reset --hard blocked", True, "git reset --hard HEAD~1")
    chk("reset soft allowed", False, "git reset --soft HEAD~3")
    chk("clean -f blocked", True, "git clean -fd")
    chk("clean -n allowed", False, "git clean -n")
    chk("stash drop blocked", True, "git stash drop")
    chk("stash push allowed", False, "git stash push -m wip")
    chk("checkout branch allowed", False, "git checkout feature-x")
    chk("checkout -- path blocked", True, "git checkout -- src/app.ts")
    chk("checkout . blocked", True, "git checkout .")
    chk("checkout ref -- path blocked by default", True, "git checkout abc123 -- src/app.ts")
    chk("checkout ref -- path allowed via GIT_GUARD_ALLOW", False,
        "git checkout abc123 -- src/app.ts", allow="checkout-file")
    chk("checkout -- path blocked even with checkout-file", True,
        "git checkout -- src/app.ts", allow="checkout-file")
    chk("restore path blocked", True, "git restore src/app.ts")
    chk("restore --staged allowed", False, "git restore --staged src/app.ts")
    chk("restore -S allowed (same as long form)", False, "git restore -S src/app.ts")
    chk("restore -S -W blocked (touches worktree)", True, "git restore -S -W src/app.ts")
    chk("restore --staged --worktree blocked", True, "git restore --staged --worktree src/app.ts")
    chk("combined allow tokens", False, "git rebase develop && git commit --amend",
        allow="rebase,amend")
    chk("non-git command allowed", False, "ls -la && echo done")
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
