"""Shared hook plumbing: payload in, verdict out, git-worktree facts.

Every hook in this plugin speaks the same protocol, so it lives here once instead of being
re-derived — and re-bugged — in each one. Python rather than bash+jq: jq is not installed by
default, and a guard that disarms itself when a dependency is missing is not a guard.

This root `lib/` is the single source; every plugin that imports a module here carries a
vendored copy in its own `lib/` (a plugin can reach nothing outside its own directory). Edit
here, then run the marketplace's ./vendor.sh. Import from a hook at <plugin>/hooks/x.py:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
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


# ── settings ────────────────────────────────────────────────────────────────
# Every plugin knob is an env var, so it is set in a settings.json `env` block at whichever scope
# fits — `~/.claude/settings.json` (personal, every project), the project's `.claude/settings.json`
# (shared), or its `.claude/settings.local.json` (personal, this project). Claude Code merges them
# local > project > user before a hook ever runs. A plugin `userConfig` option of the same name
# (exported as CLAUDE_PLUGIN_OPTION_<NAME>) is the fallback.


def setting(name, default=""):
    """A plugin knob: env `name`, else `CLAUDE_PLUGIN_OPTION_<name>`, else `default`."""
    value = os.environ.get(name)
    if value is None:
        value = os.environ.get("CLAUDE_PLUGIN_OPTION_" + name)
    return default if value is None else value


def setting_int(name, default):
    """`setting` as an int; a missing or malformed value falls back to `default`."""
    try:
        return int(str(setting(name, default)).strip())
    except ValueError:
        return default


def project_dir(data=None):
    """The project root: $CLAUDE_PROJECT_DIR, else the payload's cwd, else the process cwd."""
    return (os.environ.get("CLAUDE_PROJECT_DIR") or (data or {}).get("cwd") or os.getcwd())


def override_text(env_name, candidates, shipped, project):
    """Text from the first of: $env_name, each project-relative candidate, the shipped file.

    Returns (text, warning). The env path is explicit, so a missing one warns; a candidate that
    does not exist is simply skipped; an override that exists but cannot be read warns and
    returns None — a broken override never silently falls through to the default.
    """
    explicit = os.environ.get(env_name, "").strip()
    chain = []
    if explicit:
        chain.append((explicit if os.path.isabs(explicit) else os.path.join(project, explicit), True))
    chain += [(os.path.join(project, c), False) for c in candidates]
    for path, must_exist in chain:
        if not os.path.exists(path):
            if must_exist:
                return None, f"{env_name}={explicit} does not exist"
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read(), None
        except OSError as e:
            return None, f"{path} is unreadable ({e.__class__.__name__})"
    try:
        with open(shipped, encoding="utf-8") as handle:
            return handle.read(), None
    except OSError:
        return None, f"shipped default {os.path.basename(shipped)} is unreadable"


def render(text, values):
    """Substitute `{{KEY}}` placeholders from `values`; unknown ones are left as written."""
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: str(values.get(m.group(1), m.group(0))), text)


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
    marker = os.path.join(tempfile.gettempdir(), f"optimiziramsi-{tag}-{session_id or 'unknown'}")
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


_DEFAULT_BRANCH = {}


def default_branch(cwd=None):
    """The repo's OWN default branch, so `main` is never assumed. Memoized per cwd.

    Order: origin's HEAD symref (what the remote calls default) → the first of
    main/master/develop/trunk that exists as a local branch → a repo-local `init.defaultBranch`.
    None when nothing resolves (not a repo, no branches yet). Deliberately never reads the
    GLOBAL `init.defaultBranch`: that is the machine's taste, not the project's. Shared by
    git-guard and code-first so the two can never disagree about which branch is which.
    """
    key = os.path.realpath(cwd or os.getcwd())
    if key not in _DEFAULT_BRANCH:
        _DEFAULT_BRANCH[key] = _detect_default_branch(key)
    return _DEFAULT_BRANCH[key]


def _detect_default_branch(cwd):
    if git(cwd, "rev-parse", "--is-inside-work-tree") != "true":
        return None
    ref = git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD") or ""
    if ref.startswith("origin/"):
        return ref[len("origin/"):]
    for cand in ("main", "master", "develop", "trunk"):
        if git(cwd, "show-ref", "--verify", "--quiet", f"refs/heads/{cand}") is not None:
            return cand
    return git(cwd, "config", "--local", "--get", "init.defaultBranch") or None


def protected_branches(cwd=None):
    """GIT_GUARD_PROTECTED_BRANCH (comma-separated; empty protects nothing), else the detected
    default branch, else {main, master}."""
    env = os.environ.get("GIT_GUARD_PROTECTED_BRANCH")
    if env is not None:
        return {b.strip() for b in env.split(",") if b.strip()}
    detected = default_branch(cwd)
    return {detected} if detected else {"main", "master"}


def integration_branch():
    """GIT_GUARD_INTEGRATION_BRANCH — the one branch day-to-day work lands into — or ""."""
    return os.environ.get("GIT_GUARD_INTEGRATION_BRANCH", "").strip()


def linked_worktree(cwd):
    """`worktree(cwd)` narrowed to the linked case — None when there is nothing to leak into."""
    ctx = worktree(cwd)
    return ctx if ctx and ctx["is_linked"] else None


def under(path, root):
    """True when `path` sits inside directory `root` (both compared as realpaths)."""
    return os.path.realpath(path).startswith(root.rstrip("/") + os.sep)
