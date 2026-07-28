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
Self-test: python3 file-guard.py --test
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


def self_test():
    fails = 0
    os.environ.pop("CLAUDE_PROJECT_DIR", None)  # cases below control the anchor explicitly

    def chk(name, want_ask, data):
        nonlocal fails
        got = decide(data) is not None
        if got == want_ask:
            print(f"PASS  {name}")
        else:
            print(f"FAIL  {name}")
            fails += 1

    e = lambda f: {"tool_name": "Edit", "tool_input": {"file_path": f}, "cwd": "/repo"}
    chk("ask on .claude/settings.json", True, e("/repo/.claude/settings.json"))
    chk("ask on .claude/settings.local.json", True, e("/repo/.claude/settings.local.json"))
    chk("ask on .claude/hooks/x.sh", True, e("/repo/.claude/hooks/x.sh"))
    chk("allow ordinary file", False, e("/repo/src/x.ts"))
    chk("allow .claude/skills (audit-guarded only)", False, e("/repo/.claude/skills/a/SKILL.md"))
    chk("allow relative non-guarded", False, {"tool_name": "Edit", "tool_input": {"file_path": "src/x.ts"}})
    chk("ask on relative guarded", True, {"tool_name": "Write", "tool_input": {"file_path": ".claude/hooks/g.py"}})
    chk("ignore Bash tool", False, {"tool_name": "Bash", "tool_input": {"command": "echo x > .claude/hooks/g.py"}})
    os.environ["FILE_GUARD_EXTRA"] = "tools/git-hooks/"
    chk("ask on FILE_GUARD_EXTRA prefix", True, e("/repo/tools/git-hooks/pre-push"))
    del os.environ["FILE_GUARD_EXTRA"]
    chk("notebook_path also guarded", True,
        {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": ".claude/hooks/x.ipynb"}})
    os.environ["CLAUDE_PROJECT_DIR"] = "/repo"
    chk("ask on absolute guarded path from subdir cwd", True,
        {"tool_name": "Edit", "tool_input": {"file_path": "/repo/.claude/hooks/g.py"}, "cwd": "/repo/sub"})
    chk("allow ordinary absolute path from subdir cwd", False,
        {"tool_name": "Edit", "tool_input": {"file_path": "/repo/src/x.ts"}, "cwd": "/repo/sub"})
    del os.environ["CLAUDE_PROJECT_DIR"]
    print("all tests passed" if fails == 0 else f"{fails} FAILED")
    return fails


def main():
    if "--test" in sys.argv:
        sys.exit(self_test())
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
