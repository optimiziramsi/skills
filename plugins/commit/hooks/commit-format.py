#!/usr/bin/env python3
"""PreToolUse[Bash] guard — enforce the `commit` skill's MESSAGE FORMAT (single line, no trailers).

Hard-blocks (exit 2, reason fed back to the model) a model-authored `git commit` whose message
isn't a bare single line:
  - a `Co-Authored-By` trailer
  - a heredoc body (`<<`)
  - multiple `-m` / `--message` (a multi-line message)

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


def main():
    if os.environ.get("COMMIT_FORMAT_OFF") == "1":
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
        if sub != "commit":
            continue
        if re.search(r"co-authored-by", command, re.IGNORECASE):
            deny("commit messages are a single line with no trailers — drop the Co-Authored-By")
        if "<<" in seg:
            deny("commit messages are a single line — use `git commit -m '<intent>'` (no heredoc body)")
        if sum(1 for a in args if a in ("-m", "--message")) > 1:
            deny("commit messages are a single line — use one `-m`, no body")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)  # fail-open: never brick the session on a hook bug
