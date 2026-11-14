#!/usr/bin/env python3
"""Self-tests for commit-format. Run: python3 commit/tests/test_commit_format.py"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, load_module  # noqa: E402

check = Check()
guard = load_module(hook("hooks/commit-format.py"), "commit_format")


def blocks(name, want_blocked, command, convention=None):
    reason = guard.check(command, convention)
    check(name, (reason is not None) == want_blocked, repr(reason))


def project_with(text):
    """A temp project dir whose .agent/commit.json holds `text` (None → no file)."""
    root = tempfile.mkdtemp()
    if text is not None:
        os.makedirs(os.path.join(root, ".agent"))
        with open(os.path.join(root, ".agent", "commit.json"), "w") as handle:
            handle.write(text)
    return root


CONFIG = {
    "pattern": r"^(feat|fix|docs)\([a-z0-9._-]+\): ",
    "types": ["feat", "fix", "docs"],
    "scopes": [{"name": "api", "covers": "the HTTP API"}, {"name": "ui", "covers": "the web UI"}],
    "examples": ["fix(api): reject empty queries"],
}
open_conv = guard.load_convention(project_with(json.dumps(CONFIG)))
closed_conv = guard.load_convention(project_with(json.dumps({**CONFIG, "scopes_open": False})))


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

# ── project convention (.agent/commit.json) ──
check("a missing commit.json is no convention", guard.load_convention(project_with(None)) is None)
check("a bad-JSON commit.json is no convention (fail open)",
      guard.load_convention(project_with("{not json")) is None)
check("an uncompilable pattern is no convention (fail open)",
      guard.load_convention(project_with(json.dumps({"pattern": "(unclosed"}))) is None)
check("a valid commit.json loads", open_conv is not None and closed_conv is not None)
blocks("a message matching the pattern is allowed", False,
       "git commit -m 'fix(api): reject empty queries'", open_conv)
blocks("a message not matching the pattern is blocked", True,
       "git commit -m 'reject empty queries'", open_conv)
blocks("the pattern is checked behind a chained command", True,
       "git add a.py && git commit -m 'reject empty queries'", open_conv)
blocks("a ; or | inside the message doesn't split it", False,
       "git commit -m 'fix(api): a; b | c' && git log -1", open_conv)
blocks("an unknown scope is allowed while scopes are open", False,
       "git commit -m 'feat(billing): add invoices'", open_conv)
blocks("an unknown scope is blocked when scopes_open is false", True,
       "git commit -m 'feat(billing): add invoices'", closed_conv)
blocks("a listed scope is allowed when scopes_open is false", False,
       "git commit -m 'feat(ui): add dark mode'", closed_conv)
blocks("the single-line rule still applies under a convention", True,
       "git commit -m 'fix(api): a' -m 'body'", open_conv)
blocks("a non-commit command ignores the convention", False, "git status", open_conv)
blocks("-am with a bad message is blocked", True, "git commit -am 'reject empty queries'", open_conv)
blocks("-am with a good message is allowed", False,
       "git commit -am 'fix(api): reject empty queries'", open_conv)
blocks("-sm with a good message is allowed", False,
       "git commit -sm 'fix(api): reject empty queries'", open_conv)
check("--amend carries no message", guard.commit_messages("git commit --amend --no-edit") == [])
check("-Cmain is -C main, not a -m message", guard.commit_messages("git commit -Cmain") == [])

project = project_with(json.dumps({**CONFIG, "scopes_open": False}))
code, _, err = invoke(hook("hooks/commit-format.py"),
                      {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'feat(x): y'"}},
                      env={"CLAUDE_PROJECT_DIR": project})
check("the hook reads the project's commit.json end to end", code == 2 and "scope `x`" in err, err)
code, _, err = invoke(hook("hooks/commit-format.py"),
                      {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'add y'"}},
                      env={"CLAUDE_PROJECT_DIR": project_with(None)})
check("without commit.json the bare message passes end to end", code == 0, err)

sys.exit(check.done())
