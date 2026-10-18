#!/usr/bin/env python3
"""PreToolUse[Edit|Write|MultiEdit|NotebookEdit] — T3 enforcement surfaces ask the user.

Editing the files that ENFORCE a project's rules (Claude settings, hook scripts) is a T3
structural change in the house governance model: it needs the user's OK, mechanically — a
confused session must not be able to silently neuter its own guards. The hook answers "ask",
so the user sees the edit and decides; nothing is hard-blocked.

Rules/skills/agents/commands stay audit-guarded only (T3 by policy, but prompting on every
planner doc edit would be noise). Fail-open on unexpected errors.

Config:
  FILE_GUARD_EXTRA  colon-separated extra repo-relative prefixes to guard
                    (e.g. "tools/git-hooks/:.claude/scripts/")
  FILE_GUARD_OFF=1  escape hatch (user-set only)
Tests: python3 instructions/tests/test_file_guard.py
"""
import json
import os
import sys

GUARDED_PREFIXES = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/hooks/",
)


def guarded_prefixes():
    extra = tuple(p for p in os.environ.get("FILE_GUARD_EXTRA", "").split(":") if p)
    return GUARDED_PREFIXES + extra


def decide(data):
    """Return the hook JSON dict for an 'ask', or None to allow."""
    if data.get("tool_name") not in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        return None
    ti = data.get("tool_input") or {}
    fp = ti.get("file_path", "") or ti.get("notebook_path", "") or ""
    # anchor on the project root, NOT the session cwd — an absolute-path write issued from a
    # subdir cwd must still resolve to the guarded repo-relative prefix
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd", "") or ""
    rel = os.path.relpath(fp, root) if os.path.isabs(fp) and root else fp
    rel = rel.replace(os.sep, "/")
    if any(rel == p or rel.startswith(p) for p in guarded_prefixes()):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    f"T3 enforcement surface ({rel}): changing guards/settings needs the "
                    "user's OK — a session must not silently rewrite its own guards. "
                    "Approve if this edit was asked for."
                ),
            }
        }
    return None


def main():
    if os.environ.get("FILE_GUARD_OFF") == "1":
        return
    data = json.load(sys.stdin)
    out = decide(data)
    if out:
        print(json.dumps(out))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
