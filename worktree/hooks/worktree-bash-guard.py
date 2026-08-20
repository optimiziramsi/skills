#!/usr/bin/env python3
"""PreToolUse[Bash] — the shell channel of the same worktree leak (claude-code#36182).

The write guard only sees file-tool targets; an agent can still reach the main checkout with
`sed -i`, a redirect, or `python3 -c`. This one RESOLVES each write target the way the shell
would — against the cwd in effect at that point in the command, `cd` included — and blocks when
the result lands in the main checkout. Naming a path under the worktree anywhere in the command
is the escape hatch for a deliberate cross-tree read/write.

Resolving rather than string-matching is the whole point: `cd ../../.. && echo x > ./f` never
spells the main-checkout path, so a substring test cannot see it.

Off by default (false-positive-prone). On: WORKTREE_BASH_GUARD_ENABLE=1
Report as stderr+exit 2 instead of JSON: WORKTREE_GUARD_MODE=exit2
Tests: python3 worktree/tests/test_worktree.py
"""
import os
import pathlib
import re
import shlex
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

# A redirect counts only when it writes to a FILE: `2>/dev/null`, `2>&1` and `>&2` move file
# descriptors around and are not writes, so the leading char must not be a digit and the target
# must not start with & or >.
REDIRECT = re.compile(r"(?:^|[^0-9>&])>>?\s*(?![>&])([^\s;|&()<>]+)")
# verbs whose LAST positional argument is the thing written
WRITES_LAST = re.compile(r"(?:^|[\s;|&(])(sed\s+-i|tee|install|cp|mv|rsync)(?:\s|$)")
# a token that is a redirect, not an argument: `>`, `>>`, `2>`, `&>`, and their glued forms
# (`2>/dev/null`, `2>&1`). shlex keeps a glued redirect as ONE token, so without this the "last
# positional is the destination" rule reads `cp x /tmp/d/ 2>/dev/null` as writing to `2>/dev/null`.
REDIRECT_TOKEN = re.compile(r"^(?:\d*|&)>{1,2}")
DD_OF = re.compile(r"(?:^|\s)of=([^\s;|&()]+)")
# a write we cannot resolve — the interpreter owns the path, so fall back to judging the cwd
OPAQUE = re.compile(r"(?:^|\s)(python3?|perl|ruby|node)\s+-(c|e)\b")
CD = re.compile(r"^cd\s+(?!-)(.+)$")
SEPARATORS = re.compile(r"(?:&&|\|\||[;\n|])")


def segments(command):
    """Command split on the separators that sequence it — `cd` in one affects the next."""
    for seg in SEPARATORS.split(command):
        seg = seg.strip().lstrip("(").strip()
        if seg:
            yield seg


def tokens(seg):
    try:
        return shlex.split(seg)
    except ValueError:
        return seg.split()


def resolve(target, cwd):
    """`target` as the shell would see it from `cwd` — None when it is not a plain path."""
    target = target.strip("'\"")
    if not target or target.startswith(("$", "`", "~")):
        return None                                  # expansion we cannot evaluate
    if not os.path.isabs(target):
        target = os.path.join(cwd, target)
    return os.path.normpath(target)


def positional(seg):
    """The segment's argument tokens — flags dropped, and redirects dropped operator AND target.

    Redirect targets are already collected by REDIRECT; leaving them in here would let a plain
    `> out` steal the last-positional slot from the verb's real destination.
    """
    out, skip = [], False
    for tok in tokens(seg)[1:]:
        if skip:                                     # the target of a bare redirect operator
            skip = False
            continue
        m = REDIRECT_TOKEN.match(tok)
        if m:
            skip = m.end() == len(tok)               # bare `>` / `2>`: its target is the next token
            continue
        if tok.startswith("-"):
            continue
        out.append(tok)
    return out


def write_targets(seg, cwd):
    """Absolute paths this segment writes to, plus whether it writes somewhere unresolvable."""
    found, opaque = [], bool(OPAQUE.search(seg))
    raw = [m.group(1) for m in REDIRECT.finditer(seg)]
    raw += [m.group(1) for m in DD_OF.finditer(seg)]
    if WRITES_LAST.search(seg):
        args = positional(seg)
        if args:
            raw.append(args[-1])
    for target in raw:
        resolved = resolve(target, cwd)
        if resolved is None:
            opaque = True
        else:
            found.append(resolved)
    return found, opaque


def at_or_under(path, root):
    """`hookio.under`, widened to include the root itself — a cwd *of* the main checkout counts."""
    return os.path.realpath(path) == os.path.realpath(root) or hookio.under(path, root)


def escapes(command, cwd, wt_root, main_root):
    """The first resolved write target that lands in the main checkout, or None.

    A `cd` updates the running cwd for everything after it. Subshell scoping is deliberately
    ignored: over-blocking is recoverable (name the worktree path, or use the kill-switch),
    a missed escape is not.
    """
    for seg in segments(command):
        cd = CD.match(seg)
        if cd:
            moved = resolve(cd.group(1).split()[0], cwd)
            if moved:
                cwd = moved
            continue
        targets, opaque = write_targets(seg, cwd)
        # an unresolvable write is judged by where the shell is standing
        if opaque and at_or_under(cwd, main_root) and not at_or_under(cwd, wt_root):
            return os.path.join(cwd, "<unresolved>")
        for target in targets:
            if hookio.under(target, main_root) and not hookio.under(target, wt_root):
                return target
    return None


def main():
    if not hookio.flag("WORKTREE_BASH_GUARD_ENABLE"):
        return
    data = hookio.payload()
    command = (data.get("tool_input") or {}).get("command", "")
    ctx = hookio.linked_worktree(data.get("cwd", ""))
    if not command or not ctx:
        return
    if ctx["wt_root"] + "/" in command:               # deliberate cross-tree work, opted in
        return
    # start from where the shell actually IS, not the worktree root — the session cwd is often a
    # subdirectory, and every `../` in the command is counted from there
    cwd = data.get("cwd") or ctx["wt_root"]
    target = escapes(command, cwd, ctx["wt_root"], ctx["main_root"])
    if target:
        hookio.deny(
            f"worktree-bash-guard (#36182 shell channel): this command writes to '{target}', "
            f"inside the main checkout '{ctx['main_root']}', from worktree '{ctx['wt_root']}'. "
            f"Re-issue with a path under the worktree. If the cross-tree write is intentional "
            f"(e.g. recovery), name the worktree path in the command, or unset "
            f"WORKTREE_BASH_GUARD_ENABLE to turn this guard off.",
            mode=os.environ.get("WORKTREE_GUARD_MODE", "json"),
        )


hookio.guard(main)
