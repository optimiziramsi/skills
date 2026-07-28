#!/usr/bin/env python3
"""Self-tests for file-guard. Run: python3 instructions/tests/test_file_guard.py"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, load_module  # noqa: E402

check = Check()
guard = load_module(hook("instructions/hooks/file-guard.py"), "file_guard")
os.environ.pop("CLAUDE_PROJECT_DIR", None)           # cases below control the anchor explicitly


def asks(name, want_ask, data):
    check(name, (guard.decide(data) is not None) == want_ask)


def edit(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": path}, "cwd": "/repo"}


asks("ask on .claude/settings.json", True, edit("/repo/.claude/settings.json"))
asks("ask on .claude/settings.local.json", True, edit("/repo/.claude/settings.local.json"))
asks("ask on a hook script", True, edit("/repo/.claude/hooks/x.sh"))
asks("allow an ordinary file", False, edit("/repo/src/x.ts"))
asks("allow .claude/skills (audit-guarded only)", False, edit("/repo/.claude/skills/a/SKILL.md"))
asks("allow a relative non-guarded path", False,
     {"tool_name": "Edit", "tool_input": {"file_path": "src/x.ts"}})
asks("ask on a relative guarded path", True,
     {"tool_name": "Write", "tool_input": {"file_path": ".claude/hooks/g.py"}})
asks("ignore the Bash tool", False,
     {"tool_name": "Bash", "tool_input": {"command": "echo x > .claude/hooks/g.py"}})
asks("notebook_path is guarded too", True,
     {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": ".claude/hooks/x.ipynb"}})

os.environ["FILE_GUARD_EXTRA"] = "tools/git-hooks/"
asks("ask on a FILE_GUARD_EXTRA prefix", True, edit("/repo/tools/git-hooks/pre-push"))
del os.environ["FILE_GUARD_EXTRA"]

# the anchor is the PROJECT root, not the session cwd — an absolute write issued from a
# subdir must still resolve to the guarded repo-relative prefix
os.environ["CLAUDE_PROJECT_DIR"] = "/repo"
asks("ask on an absolute guarded path from a subdir cwd", True,
     {"tool_name": "Edit", "tool_input": {"file_path": "/repo/.claude/hooks/g.py"},
      "cwd": "/repo/sub"})
asks("allow an ordinary absolute path from a subdir cwd", False,
     {"tool_name": "Edit", "tool_input": {"file_path": "/repo/src/x.ts"}, "cwd": "/repo/sub"})
del os.environ["CLAUDE_PROJECT_DIR"]

sys.exit(check.done())
