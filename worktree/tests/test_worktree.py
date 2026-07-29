#!/usr/bin/env python3
"""Self-tests for the four worktree guards. Run: python3 worktree/tests/test_worktree.py"""
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke, scratch_repo  # noqa: E402

check = Check()
WRITE = hook("worktree/hooks/worktree-write-guard.py")
LEAK = hook("worktree/hooks/worktree-leak-detector.py")
BASH = hook("worktree/hooks/worktree-bash-guard.py")
DETECT = hook("worktree/hooks/worktree-detect.py")
ON = {"WORKTREE_BASH_GUARD_ENABLE": "1"}

with scratch_repo({"f.ts": "a\n"}) as repo:
    # a second worktree parked UNDER the main checkout — the layout the `worktree` skill
    # actually uses (.claude/worktrees/<name>), and the one a stray write can land in
    sibling = os.path.join(repo.main, ".claude", "worktrees", "other")
    subprocess.run(["git", "-C", repo.main, "worktree", "add", "-q", sibling, "-b", "other"],
                   capture_output=True, check=True)

    # ── write guard ────────────────────────────────────────────────────────
    def writes(path, env=None, tool="Edit"):
        return invoke(WRITE, {"cwd": repo.wt, "tool_name": tool,
                              "tool_input": {"file_path": path}}, env=env)

    check("deny a main-rooted path", '"deny"' in writes(f"{repo.main}/x.ts")[1])
    check("deny a sibling worktree's path", '"deny"' in writes(f"{sibling}/x.ts")[1])
    check("allow an in-worktree path", writes(f"{repo.wt}/x.ts")[1] == "")
    # the worktree root can itself sit under the main checkout, so the in-worktree test
    # has to win before the main-checkout test — this is the regression that proves it
    check("allow a nested in-worktree path", writes(f"{repo.wt}/.claude/hooks/x.sh")[1] == "")
    check("allow a path outside the repo", writes("/tmp/elsewhere.ts")[1] == "")
    check("allow a relative path", writes("src/x.ts")[1] == "")
    check("kill-switch disarms", writes(f"{repo.main}/x.ts", env={"WORKTREE_GUARD_DISABLE": "1"})[1] == "")
    rc, _, err = writes(f"{repo.main}/x.ts", env={"WORKTREE_GUARD_MODE": "exit2"})
    check("exit2 mode reports on stderr", rc == 2 and "worktree-write-guard" in err)
    check("notebook_path is guarded", '"deny"' in invoke(
        WRITE, {"cwd": repo.wt, "tool_input": {"notebook_path": f"{repo.main}/n.ipynb"}})[1])
    check("MultiEdit's nested paths are guarded", '"deny"' in invoke(
        WRITE, {"cwd": repo.wt, "tool_input": {"edits": [{"file_path": f"{repo.main}/x.ts"}]}})[1])
    check("main checkout cwd → inert", invoke(
        WRITE, {"cwd": repo.main, "tool_input": {"file_path": f"{repo.main}/x.ts"}})[1] == "")

    # ── bash guard ─────────────────────────────────────────────────────────
    def runs(command, cwd=None, env=ON):
        return invoke(BASH, {"cwd": cwd or repo.wt, "tool_input": {"command": command}}, env=env)

    check("deny a redirect into the main checkout", '"deny"' in runs(f"echo hi > {repo.main}/x.ts")[1])
    check("deny sed -i into the main checkout", '"deny"' in runs(f"sed -i '' s/a/b/ {repo.main}/x.ts")[1])
    check("deny a leading sed -i (no preceding space)", '"deny"' in runs(f"sed -i '' s/a/b/ {repo.main}/x.ts")[1])
    check("allow a write inside the worktree", runs(f"echo hi > {repo.wt}/x.ts")[1] == "")
    check("allow when the worktree path is also named",
          runs(f"cat {repo.main}/f.ts | tee {repo.wt}/f.ts")[1] == "")
    check("allow a read-only command (2>/dev/null is not a write)",
          runs(f"grep -r foo {repo.main}/ 2>/dev/null")[1] == "")
    check("allow a read-only command (2>&1 is not a write)",
          runs(f"ls {repo.main}/ 2>&1")[1] == "")
    check("main checkout cwd → inert", runs(f"echo hi > {repo.main}/x.ts", cwd=repo.main)[1] == "")
    check("off without WORKTREE_BASH_GUARD_ENABLE",
          runs(f"echo hi > {repo.main}/x.ts", env={"WORKTREE_BASH_GUARD_ENABLE": "0"})[1] == "")

    # ── bash guard: relative escapes ───────────────────────────────────────
    # The substring-matching version of this guard saw NONE of these — a command that walks out
    # with `cd`, or writes through `../`, never spells the main checkout's path. Reported from a
    # live worktree session, 2026-07-29. `up` is the relative route out of the worktree; it is
    # computed, not hardcoded, so these hold for a sibling worktree AND a nested one.
    up = os.path.relpath(repo.main, repo.wt)
    check("deny `cd <up> && redirect` (the reported bypass)",
          '"deny"' in runs(f"cd {up} && echo x > ./LEAK.md")[1])
    check("deny chained cd hops",
          '"deny"' in runs("cd " + " && cd ".join(up.split("/")) + " && printf x > LEAK.md")[1])
    check("deny a bare relative redirect", '"deny"' in runs(f"echo x > {up}/LEAK.md")[1])
    check("deny inside a subshell", '"deny"' in runs(f"(cd {up}; echo x > LEAK.md)")[1])
    check("deny tee via a relative path", '"deny"' in runs(f"echo x | tee {up}/LEAK.md")[1])
    check("deny dd of= via a relative path",
          '"deny"' in runs(f"dd if=/dev/null of={up}/LEAK.md")[1])
    check("deny an interpreter write after cd (target opaque, cwd is not)",
          '"deny"' in runs(f"cd {up} && python3 -c \"open('LEAK.md','w')\"")[1])
    # the layout the skill actually uses — worktree NESTED under the main checkout, where every
    # escape is a plain `../..` and the in-worktree test has to win before the main-checkout one
    nested_up = os.path.relpath(repo.main, sibling)
    check("deny a relative escape from a nested worktree", '"deny"' in invoke(
        BASH, {"cwd": sibling,
               "tool_input": {"command": f"cd {nested_up} && echo x > LEAK.md"}}, env=ON)[1])
    check("allow a write that stays inside a nested worktree", invoke(
        BASH, {"cwd": sibling, "tool_input": {"command": "echo x > ./x.ts"}}, env=ON)[1] == "")
    check("allow a relative write that stays in the worktree", runs("echo x > ./x.ts")[1] == "")
    check("allow `cd` to a subdir then write", runs("cd src && echo x > x.ts")[1] == "")
    check("allow a relative read from the main checkout", runs(f"cat {up}/f.ts")[1] == "")
    check("allow an interpreter write with the cwd still in the worktree",
          runs("python3 -c \"open('x.ts','w')\"")[1] == "")
    check("allow a write outside the repo entirely", runs("echo x > /tmp/elsewhere.ts")[1] == "")

    # ── bash guard: the session cwd is a SUBDIRECTORY of the worktree ──────
    # Every `../` is counted from where the shell is standing, so resolving from the worktree
    # ROOT instead of the payload's cwd is off by one hop per level of nesting — it both misses
    # real escapes and denies writes that never leave the worktree. The Bash tool's cwd persists
    # across calls, so a subdir cwd is ordinary, not exotic.
    for label, wt in (("sibling", repo.wt), ("nested", sibling)):
        sub = os.path.join(wt, "src")
        os.makedirs(sub, exist_ok=True)
        out = os.path.relpath(repo.main, sub)                # the real route out, from the cwd
        check(f"deny a relative escape from a subdir of a {label} worktree",
              '"deny"' in runs(f"echo x > {out}/LEAK.md", cwd=sub)[1])
        check(f"allow a subdir-relative write that stays in a {label} worktree",
              runs("echo x > ../f.ts", cwd=sub)[1] == "")
        check(f"allow `cd ..` within a {label} worktree, then write",
              runs("cd .. && echo x > f.ts", cwd=sub)[1] == "")

    # ── detect ─────────────────────────────────────────────────────────────
    def detects(dirpath, env=None):
        return invoke(DETECT, {}, env={"CLAUDE_PROJECT_DIR": dirpath, **(env or {})})[1]

    check("linked worktree → nudge", "Worktree detected" in detects(repo.wt))
    check("main checkout → silent", detects(repo.main) == "")
    check("non-repo → silent", detects(repo.tmp) == "")
    check("kill-switch disarms", detects(repo.wt, {"WORKTREE_GUARD_DISABLE": "1"}) == "")

    # ── leak detector ──────────────────────────────────────────────────────
    def detect_leak(path, env=None):
        return invoke(LEAK, {"cwd": repo.wt, "tool_input": {"file_path": path}}, env=env)

    check("a clean write is silent", detect_leak(f"{repo.wt}/f.ts")[0] == 0)
    with open(os.path.join(repo.main, "f.ts"), "a") as fh:
        fh.write("dirty\n")
    rc, _, err = detect_leak(f"{repo.wt}/f.ts")
    check("a dirtied twin in main is reported", rc == 2 and "LEAK SUSPECTED" in err)
    check("a main-rooted path is not its own leak", detect_leak(f"{repo.main}/f.ts")[0] == 0)
    check("kill-switch disarms",
          detect_leak(f"{repo.wt}/f.ts", env={"WORKTREE_LEAK_DETECT_DISABLE": "1"})[0] == 0)

sys.exit(check.done())
