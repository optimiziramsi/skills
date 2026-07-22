#!/usr/bin/env python3
"""PreToolUse[Bash] guard — enforce the `commit` skill's MESSAGE FORMAT (single line, no trailers).

Hard-blocks (exit 2, reason fed back to the model) a model-authored `git commit` whose message
isn't a bare single line:
  - a `Co-Authored-By` trailer
  - a heredoc body (`<<` outside quotes)
  - a message read from a file (`-F` / `--file` — multi-line by construction)
  - multiple `-m` / `--message`, or a quoted `-m` value containing a newline

This is the OPINIONATED half of the old git plugin — the commit *style*, split out so a project can
adopt the git safety net (`git` plugin's git-guard) WITHOUT this house commit format. It says nothing
about destructive git ops; that's the `git` plugin's job.

Fail-open by design: any unexpected error exits 0 so a broken hook can never brick a session.
Escape hatch (user-set only): COMMIT_FORMAT_OFF=1.
"""
import json
import os
import re
import shlex
import sys


def deny(reason: str):
    print(f"[commit-format] BLOCKED: {reason}", file=sys.stderr)
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


def strip_quotes(text: str):
    return re.sub(r"'[^']*'|\"[^\"]*\"", "", text)


def m_values(tokens):
    """Yield the message values of -m/--message flags in a token list."""
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("-m", "--message"):
            if i + 1 < len(tokens):
                yield tokens[i + 1]
            i += 2
            continue
        if t.startswith("--message="):
            yield t[len("--message="):]
        elif t.startswith("-m") and len(t) > 2:
            yield t[2:]
        i += 1


def multiline_m(command: str):
    """True when a -m/--message value spans lines (a quoted multi-line body).

    Parsed on the WHOLE command — a newline inside quotes would otherwise split the segment
    scan and slip through. When quoting is unparseable, err toward blocking (RR lesson-guards
    [commit-msg]): a multi-line command carrying -m is treated as a body.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return ("\n" in command and "commit" in command
                and re.search(r"(^|\s)(-m|--message)(\s|=|$)", command) is not None)
    if "commit" not in tokens:
        return False
    return any("\n" in v for v in m_values(tokens))


def check(command: str):
    """Return a block reason, or None if clean."""
    if re.search(r"\bgit\b", command) and multiline_m(command):
        return "commit messages are a single line — the -m message contains a newline (no body)"
    for seg in segments(command):
        parsed = parse_git(tokenize(seg))
        if not parsed:
            continue
        sub, args = parsed
        if sub != "commit":
            continue
        if re.search(r"co-authored-by", command, re.IGNORECASE):
            return "commit messages are a single line with no trailers — drop the Co-Authored-By"
        if "<<" in strip_quotes(seg):
            return "commit messages are a single line — use `git commit -m '<intent>'` (no heredoc body)"
        if any(a in ("-F", "--file") or a.startswith("--file=")
               or (a.startswith("-F") and len(a) > 2) for a in args):
            return ("commit messages are a single line typed with `-m` — "
                    "`-F/--file` reads a multi-line message from a file")
        if sum(1 for a in args if a in ("-m", "--message")) > 1:
            return "commit messages are a single line — use one `-m`, no body"
    return None


def self_test():
    fails = 0

    def chk(name, want_blocked, cmd):
        nonlocal fails
        reason = check(cmd)
        got_blocked = reason is not None
        if got_blocked == want_blocked:
            print(f"PASS  {name}")
        else:
            print(f"FAIL  {name}: reason={reason!r}")
            fails += 1

    chk("clean single-line commit allowed", False, "git commit -m 'fix(git): allow local pushes'")
    chk("quoted multi-line -m blocked", True, 'git commit -m "line one\nline two"')
    chk("quoted multi-line -m (single quotes) blocked", True, "git commit -m 'line one\nline two'")
    chk("multi-line with unbalanced quote blocked", True, 'git commit -m "line one\nline two')
    chk("-F blocked", True, "git commit -F msg.txt")
    chk("-F- (stdin) blocked", True, "git commit -F-")
    chk("--file blocked", True, "git commit --file msg.txt")
    chk("--file= blocked", True, "git commit --file=msg.txt")
    chk("heredoc blocked", True, "git commit <<EOF")
    chk("quoted << prose allowed", False, "git commit -m 'fix: shift a << 2 overflow'")
    chk("quoted << prose (double quotes) allowed", False, 'git commit -m "docs: explain a << b"')
    chk("double -m blocked", True, "git commit -m one -m two")
    chk("co-authored-by blocked", True, "git commit -m 'x Co-Authored-By: C'")
    chk("non-commit git allowed", False, "git status && git log --oneline -5")
    chk("multi-line command with single-line -m allowed", False, "npm test\ngit commit -m 'ok'")
    print("all tests passed" if fails == 0 else f"{fails} FAILED")
    return fails


def main():
    if "--test" in sys.argv:
        sys.exit(self_test())
    if os.environ.get("COMMIT_FORMAT_OFF") == "1":
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
