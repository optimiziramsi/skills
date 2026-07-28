"""Test plumbing shared by every `<topic>/tests/*.py`.

Kept out of the shipped hooks on purpose: a guard should read as its decision, not as its
test suite. `tests.sh` runs each test file and counts a non-zero exit as failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile


class Check:
    """PASS/FAIL tallier. A test file's whole epilogue is `sys.exit(check.done())`."""

    def __init__(self):
        self.fails = 0

    def __call__(self, name, ok, detail=""):
        if ok:
            print(f"PASS  {name}")
        else:
            print(f"FAIL  {name}{': ' + str(detail) if detail else ''}")
            self.fails += 1

    def done(self):
        print("all tests passed" if not self.fails else f"{self.fails} FAILED")
        return self.fails


def plugin_root():
    """The plugin root — this file lives at <root>/lib/selftest.py."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hook(rel):
    """Absolute path to a shipped hook, named relative to the plugin root."""
    return os.path.join(plugin_root(), rel)


def invoke(script, data=None, env=None, args=()):
    """Run a hook the way Claude Code does. Returns (exit_code, stdout, stderr)."""
    runner = "bash" if script.endswith(".sh") else sys.executable
    done = subprocess.run(
        [runner, script, *args],
        input=json.dumps(data or {}), capture_output=True, text=True,
        env={**os.environ, **(env or {})},
    )
    return done.returncode, done.stdout, done.stderr


class scratch_repo:
    """Context manager yielding a throwaway repo with one linked worktree.

    Attributes: `main` (the checkout) and `wt` (the linked worktree). Realpath-resolved,
    because macOS hands out /var/... tmpdirs that git reports back as /private/var/...
    """

    def __init__(self, files=None):
        self.files = files or {}

    def __enter__(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.main = os.path.join(self.tmp, "repo")
        self.wt = os.path.join(self.tmp, "wt")
        run = lambda *a: subprocess.run(a, capture_output=True, check=True)
        run("git", "init", "-q", "-b", "main", self.main)
        for rel, text in self.files.items():
            path = os.path.join(self.main, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(text)
            run("git", "-C", self.main, "add", rel)
        run("git", "-C", self.main, "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-q", "--allow-empty", "-m", "init")
        run("git", "-C", self.main, "worktree", "add", "-q", self.wt, "-b", "wtbranch")
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False
