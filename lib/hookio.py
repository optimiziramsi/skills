"""Shared hook plumbing: payload in, verdict out, git-worktree facts.

Every hook in this plugin speaks the same protocol, so it lives here once instead of being
re-derived — and re-bugged — in each one. Python rather than bash+jq: jq is not installed by
default, and a guard that disarms itself when a dependency is missing is not a guard.

Import from a hook at <plugin>/<topic>/hooks/x.py:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
    import hookio
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

# ── input ───────────────────────────────────────────────────────────────────


def payload():
    """The hook payload from stdin — {} when it is absent or not JSON."""
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def flag(name):
    """True when env var `name` is exactly "1" (every kill-switch and opt-in uses this)."""
    return os.environ.get(name) == "1"


def tool_paths(data):
    """Every file_path / notebook_path anywhere under tool_input.

    Recursive because MultiEdit nests its targets; Edit/Write/NotebookEdit keep them at
    the top level.
    """
    found, stack = [], [(data or {}).get("tool_input") or {}]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("file_path", "notebook_path") and isinstance(value, str) and value:
                    found.append(value)
                else:
                    stack.append(value)
        elif isinstance(node, list):
            stack.extend(node)
    return found


# ── output ──────────────────────────────────────────────────────────────────


def deny(reason, mode="json"):
    """Block a PreToolUse call and exit. `mode="exit2"` reports on stderr instead of as JSON."""
    if mode == "exit2":
        print(reason, file=sys.stderr)
        sys.exit(2)
    _verdict("deny", reason)


def ask(reason):
    """Route a PreToolUse call to the user for approval, and exit."""
    _verdict("ask", reason)


def _verdict(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def notice(message):
    """Surface a message to the session without blocking anything."""
    print(json.dumps({"systemMessage": message}))


WROTE_FILES = re.compile(r'"name": ?"(Edit|Write|MultiEdit|NotebookEdit)"')


def wrote_files(transcript):
    """True unless the transcript proves this session never used a file-writing tool.

    Lets a Stop hook skip read-only / chat sessions. An absent or unreadable transcript
    answers True: nagging is the safe default when we cannot tell.
    """
    if not transcript or not os.path.isfile(transcript):
        return True
    try:
        with open(transcript, encoding="utf-8", errors="replace") as handle:
            return any(WROTE_FILES.search(line) for line in handle)
    except OSError:
        return True


def first_time(tag, session_id, state):
    """True the first time `state` is seen for this session under `tag`, False after.

    How a Stop hook nags once per distinct situation instead of on every stop. The marker is
    a temp file keyed by session, so it dies with the machine's temp dir and never leaks
    between sessions.
    """
    marker = os.path.join(tempfile.gettempdir(), f"opsi-{tag}-{session_id or 'unknown'}")
    digest = hashlib.sha1(state.encode()).hexdigest()
    try:
        if os.path.exists(marker):
            with open(marker) as handle:
                if handle.read() == digest:
                    return False
        with open(marker, "w") as handle:
            handle.write(digest)
    except OSError:
        pass
    return True


def guard(body):
    """Run a hook fail-open: an unexpected error exits 0 rather than bricking the session."""
    try:
        body()
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)


# ── git ─────────────────────────────────────────────────────────────────────


def git(cwd, *args):
    """`git -C <cwd> <args>` stdout, or None on any failure. Never raises."""
    try:
        done = subprocess.run(("git", "-C", cwd or ".") + args,
                              capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def worktree(cwd):
    """{wt_root, main_root, branch, is_linked} for `cwd`, or None outside a work tree.

    `is_linked` is True only in a LINKED worktree (its git-dir differs from the shared
    common dir) — the one case where a write can escape into another checkout. Paths are
    realpath-resolved so downstream comparisons are apples-to-apples (macOS /var →
    /private/var would otherwise make every prefix test fail).
    """
    if git(cwd, "rev-parse", "--is-inside-work-tree") != "true":
        return None
    top = git(cwd, "rev-parse", "--show-toplevel")
    gitdir = git(cwd, "rev-parse", "--absolute-git-dir")
    common = git(cwd, "rev-parse", "--git-common-dir")
    if not (top and gitdir and common):
        return None
    if not os.path.isabs(common):
        common = os.path.join(cwd, common)
    common = os.path.realpath(common)
    return {
        "wt_root": os.path.realpath(top),
        "main_root": os.path.dirname(common),
        "branch": git(cwd, "rev-parse", "--abbrev-ref", "HEAD") or "?",
        "is_linked": os.path.realpath(gitdir) != common,
    }


def linked_worktree(cwd):
    """`worktree(cwd)` narrowed to the linked case — None when there is nothing to leak into."""
    ctx = worktree(cwd)
    return ctx if ctx and ctx["is_linked"] else None


def under(path, root):
    """True when `path` sits inside directory `root` (both compared as realpaths)."""
    return os.path.realpath(path).startswith(root.rstrip("/") + os.sep)
