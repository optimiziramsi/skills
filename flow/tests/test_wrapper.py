#!/usr/bin/env python3
"""Self-tests for the bin/loop + bin/grind wrapper template.

Run: python3 flow/tests/test_wrapper.py — it had none until now, despite being the file every
consumer project copies and commits.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, plugin_root  # noqa: E402

check = Check()
TEMPLATE = hook("flow/examples/runner-wrapper.sh")

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    bindir = os.path.join(tmp, "bin")
    os.makedirs(bindir)
    for name in ("loop", "grind", "nonsense"):
        shutil.copy(TEMPLATE, os.path.join(bindir, name))
        os.chmod(os.path.join(bindir, name), 0o755)

    def run(name, args=("--help",), env=None):
        done = subprocess.run([os.path.join(bindir, name), *args], capture_output=True, text=True,
                              env={**os.environ, "FLOW_RUNNER_ROOT": "", "CLAUDE_PLUGIN_ROOT": "",
                                   **(env or {})})
        return done.returncode, done.stdout, done.stderr

    root = {"FLOW_RUNNER_ROOT": plugin_root()}
    check("FLOW_RUNNER_ROOT resolves the runner", "the flow looper runner" in run("loop", env=root)[1])
    check("the wrapper dispatches on its own filename",
          "the flow grind runner" in run("grind", env=root)[1])
    check("CLAUDE_PLUGIN_ROOT also resolves",
          "the flow looper runner" in run("loop", env={"CLAUDE_PLUGIN_ROOT": plugin_root()})[1])
    check("FLOW_RUNNER_ROOT wins over CLAUDE_PLUGIN_ROOT", "the flow looper runner" in run(
        "loop", env={**root, "CLAUDE_PLUGIN_ROOT": "/nonexistent"})[1])
    check("arguments are forwarded verbatim",
          "the flow looper runner" in run("loop", ("--help", "--status"), env=root)[1])

    rc, _, err = run("loop", env={"HOME": "/nonexistent"})
    check("an unresolvable runner exits 127", rc == 127, rc)
    check("the failure says how to install", "claude plugin install" in err, err)
    check("the failure names FLOW_RUNNER_ROOT", "FLOW_RUNNER_ROOT" in err, err)

    # a name other than loop/grind resolves nothing — there is no such runner to exec
    check("an unexpected filename fails rather than guessing",
          run("nonsense", env=root)[0] == 127)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
