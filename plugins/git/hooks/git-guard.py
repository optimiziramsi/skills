#!/usr/bin/env python3
"""PreToolUse[Bash] guard — mechanically enforce git safety (destructive / remote / history ops).

Hard-blocks (exit 2, reason fed back to the model), branch-agnostic:
  - git push / git pull               the user owns remote sync (git fetch is fine)
  - git commit --amend                history is append-only — make a new commit
  - git rebase / git filter-branch    history rewrite
  - git reset --hard / --merge / --keep   clobbers the worktree (plain `git reset <file>`
                                          / `--staged` to unstage is allowed)
  - git commit --no-verify            never skip hooks
  - discarding uncommitted work: git clean -f, stash drop|clear, checkout -- / checkout .,
    git restore (only `restore --staged` to unstage is allowed) — the tree may hold WIP

This is the SAFETY net only — it says nothing about commit message style. The house commit format
(single line, no trailers) lives in the separate `commit` plugin's commit-format hook; enable that
plugin if you want the format enforced too.

Fail-open by design: any unexpected error exits 0 so a broken hook can never brick a
session. Escape hatch (user-set only): GIT_GUARD_OFF=1.
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


def main():
    if os.environ.get("GIT_GUARD_OFF") == "1":
        return
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    command = (data.get("tool_input") or {}).get("command", "")

    for seg in segments(command):
        parsed = parse_git(tokenize(seg))
        if not parsed:
            continue
        sub, args = parsed
        positional = [a for a in args if not a.startswith("-")]

        # remote sync — the user owns it
        if sub == "push":
            deny("`git push` is forbidden — the user owns remote sync")
        if sub == "pull":
            deny("`git pull` is forbidden — the user owns remote sync (`git fetch` is fine)")

        # history rewrites
        if sub == "rebase":
            deny("`git rebase` rewrites history — not without the user")
        if sub == "filter-branch":
            deny("`git filter-branch` rewrites history — not without the user")
        if sub == "reset" and any(a in ("--hard", "--merge", "--keep") for a in args):
            deny("`git reset --hard` clobbers the worktree — check what's there first; "
                 "plain `git reset <file>` to unstage is fine")

        # commit safety (history / hooks) — message FORMAT lives in the commit plugin
        if sub == "commit":
            if "--amend" in args:
                deny("`git commit --amend` rewrites history — make a new commit instead")
            if "--no-verify" in args or "-n" in args:
                deny("`git commit --no-verify` skips hooks — fix the underlying issue instead")

        # never discard uncommitted work — the tree may hold the user's WIP
        if sub == "clean" and (any(re.match(r"^-[a-zA-Z]*f", a) for a in args) or "--force" in args):
            deny("`git clean -f` deletes untracked work — if the user wants this, they run it "
                 "(`git clean -n` dry-run is fine)")
        if sub == "stash" and positional[:1] in (["drop"], ["clear"]):
            deny(f"`git stash {positional[0]}` destroys stashed work — user-only operation")
        if sub == "checkout" and ("--" in args or "." in positional):
            deny("`git checkout -- <path>` / `checkout .` discards uncommitted changes — "
                 "branch switches are fine, this is not")
        if sub == "restore" and not ("--staged" in args and "--worktree" not in args):
            deny("`git restore` discards worktree changes — only `git restore --staged <path>` "
                 "to unstage is allowed")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail-open: never brick the session on a hook bug
