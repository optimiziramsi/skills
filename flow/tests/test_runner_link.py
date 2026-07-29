#!/usr/bin/env python3
"""Self-tests for runner-link (the .agent/bin/{loop,grind} symlink chain).

Run: python3 flow/tests/test_runner_link.py

The end-to-end case matters most: a two-hop symlink must still EXECUTE the runner, because
the whole design rests on it (CPython resolves sys.path[0] through symlinks, so the sibling
`_flowlib` import survives — this test is what keeps that assumption honest).
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke, plugin_root  # noqa: E402

check = Check()
HOOK = hook("flow/hooks/runner-link.py")
ROOT = plugin_root()

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    config = os.path.join(tmp, "config")
    project = os.path.join(tmp, "repo")
    bindir = os.path.join(project, ".agent", "bin")
    os.makedirs(bindir)
    pointer = os.path.join(config, "plugins", "data", "optimiziramsi-skills", "current")
    env = {"CLAUDE_CONFIG_DIR": config, "CLAUDE_PROJECT_DIR": project}

    def fire(extra=None):
        return invoke(HOOK, {}, env={**env, **(extra or {})})

    code, out, err = fire()
    check("the hook exits 0", code == 0, err)
    check("the pointer is created", os.path.islink(pointer) and os.readlink(pointer) == ROOT)
    check("a fresh stamp announces itself", "runner links now resolve" in out, out)
    check("nothing is created in .agent/bin", os.listdir(bindir) == [], os.listdir(bindir))

    check("an unchanged pointer says nothing", fire()[1] == "")

    # a version bump: the pointer moves, and every repo link follows it without being touched
    os.remove(pointer)
    os.symlink(os.path.join(tmp, "old-version"), pointer)
    check("a stale pointer is re-stamped", fire()[0] == 0 and os.readlink(pointer) == ROOT)

    for tool in ("loop", "grind"):
        link = os.path.join(bindir, tool)
        os.symlink(os.path.join(tmp, "somewhere", tool), link)
    fire()
    check("an existing link is re-aimed at the pointer",
          os.readlink(os.path.join(bindir, "loop")) == os.path.join(pointer, "flow", "bin", "loop"))
    check("both runners are handled",
          os.readlink(os.path.join(bindir, "grind")).endswith("/flow/bin/grind"))

    # a link straight into today's cache resolves to the right file but rots on the next update
    os.remove(os.path.join(bindir, "loop"))
    os.symlink(os.path.join(ROOT, "flow", "bin", "loop"), os.path.join(bindir, "loop"))
    fire()
    check("a version-pinned link is normalized onto the pointer",
          os.readlink(os.path.join(bindir, "loop")).startswith(pointer))

    # someone's own file at that path is not ours to replace
    os.remove(os.path.join(bindir, "grind"))
    pathlib.Path(bindir, "grind").write_text("#!/bin/sh\necho mine\n")
    fire()
    check("a real file is left alone", pathlib.Path(bindir, "grind").read_text().endswith("mine\n"))

    off = os.path.join(bindir, "loop")
    os.remove(off)
    os.symlink("/nowhere/loop", off)
    fire({"FLOW_LINK_OFF": "1"})
    check("FLOW_LINK_OFF=1 disarms it", os.readlink(off) == "/nowhere/loop")

    # end to end: run the real runner through pointer → plugin, links made as a skill makes them
    for tool in ("loop", "grind"):
        link = os.path.join(bindir, tool)
        os.remove(link)
        os.symlink(os.path.join(pointer, "flow", "bin", tool), link)
    done = subprocess.run([os.path.join(bindir, "loop"), "--help"],
                          capture_output=True, text=True, cwd=project)
    check("the runner executes through the two-hop link",
          done.returncode == 0 and "the flow looper runner" in done.stdout, done.stderr)
    done = subprocess.run([os.path.join(bindir, "grind"), "--help"],
                          capture_output=True, text=True, cwd=project)
    check("so does grind (the sibling _flowlib import survives)",
          done.returncode == 0 and "the flow grind runner" in done.stdout, done.stderr)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
