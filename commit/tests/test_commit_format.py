#!/usr/bin/env python3
"""Self-tests for commit-format. Run: python3 commit/tests/test_commit_format.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, load_module  # noqa: E402

check = Check()
guard = load_module(hook("commit/hooks/commit-format.py"), "commit_format")


def blocks(name, want_blocked, command):
    reason = guard.check(command)
    check(name, (reason is not None) == want_blocked, repr(reason))


blocks("a clean single-line commit is allowed", False, "git commit -m 'fix(git): allow local pushes'")
blocks("a quoted multi-line -m is blocked", True, 'git commit -m "line one\nline two"')
blocks("a single-quoted multi-line -m is blocked", True, "git commit -m 'line one\nline two'")
blocks("multi-line with an unbalanced quote is blocked", True, 'git commit -m "line one\nline two')
blocks("-F is blocked", True, "git commit -F msg.txt")
blocks("-F- (stdin) is blocked", True, "git commit -F-")
blocks("--file is blocked", True, "git commit --file msg.txt")
blocks("--file= is blocked", True, "git commit --file=msg.txt")
blocks("a heredoc is blocked", True, "git commit <<EOF")
blocks("quoted << prose is allowed", False, "git commit -m 'fix: shift a << 2 overflow'")
blocks("double-quoted << prose is allowed", False, 'git commit -m "docs: explain a << b"')
blocks("a double -m is blocked", True, "git commit -m one -m two")
blocks("a Co-Authored-By trailer is blocked", True, "git commit -m 'x Co-Authored-By: C'")
blocks("a non-commit git command is allowed", False, "git status && git log --oneline -5")
blocks("a multi-line command with a single-line -m is allowed", False,
       "npm test\ngit commit -m 'ok'")

sys.exit(check.done())
