#!/usr/bin/env python3
"""Self-tests for the grind runner. Run: python3 flow/tests/test_grind.py

Pure logic imported directly, then end-to-end iterations against the fake `claude` CLI —
including the productivity gate, the dirty-tree guard, and the retry/reset state machine.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, load_module, run_cli, write_claude_stub  # noqa: E402

check = Check()
GRIND = hook("flow/bin/grind")
grind = load_module(GRIND, "flow_grind")

MISSION = "260101_120000_sweep.md"


def mission(status="active", **extra):
    fields = "".join(f"{k.replace('_', '-')}: {v}\n" for k, v in extra.items())
    return f"---\nstatus: {status}\ntitle: sweep it\n{fields}---\n\nSweep the thing.\n"


tmp = os.path.realpath(tempfile.mkdtemp())
try:
    # ── argument parsing ───────────────────────────────────────────────────
    opts = grind.parse_args(["m.md"])
    check("defaults: no caps, .agent/grind",
          opts["mission"] == "m.md" and opts["count"] is None and opts["dir"] == ".agent/grind")
    opts = grind.parse_args(["m.md", "--once", "--count", "3", "--reset", "-y", "--dir", "d"])
    check("every flag parses",
          opts["once"] and opts["count"] == 3 and opts["reset"] and opts["yes"]
          and opts["dir"] == "d")

    # ── the mission-name convention ────────────────────────────────────────
    check("a conforming name matches", grind.MISSION_NAME_RE.match(MISSION) is not None)
    for bad in ("sweep.md", "26010_120000_sweep.md", "260101_1200_sweep.md",
                "260101_120000_.md", "260101_120000_sweep.txt"):
        check(f"'{bad}' is rejected", grind.MISSION_NAME_RE.match(bad) is None)

    # ── done-check ─────────────────────────────────────────────────────────
    check("no done-check is never done", grind.run_done_check("") is False)
    check("an exit-0 done-check passes", grind.run_done_check("true") is True)
    check("a non-zero done-check does not pass", grind.run_done_check("false") is False)

    # ── end to end ─────────────────────────────────────────────────────────
    repo = os.path.join(tmp, "repo")
    subprocess.run(["git", "init", "-q", "-b", "main", repo], capture_output=True, check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "init"], capture_output=True, check=True)
    live = os.path.join(repo, ".agent", "grind")
    os.makedirs(live)
    path = os.path.join(live, MISSION)
    pathlib.Path(path).write_text(mission(max_iterations=3))
    # commit the mission, as a real project would: otherwise git reports the whole untracked
    # `.agent/` as one entry and the dirty-tree guard can never see past it
    subprocess.run(["git", "-C", repo, "add", "-f", f".agent/grind/{MISSION}"],
                   capture_output=True, check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "-m", "mission"], capture_output=True, check=True)
    stub = write_claude_stub(tmp)
    # FLOW_LONG_BACKOFF_BASE=0: a stub iteration finishes instantly, which the transient
    # branch would otherwise answer with a 10-minute sleep.
    env = {"CLAUDE_BIN": stub, "FLOW_ALLOW_NESTED": "1", "FLOW_LONG_BACKOFF_BASE": "0",
           "FLOW_ITER_PAUSE_SECS": "0"}

    def run(args, action="noop"):
        return run_cli(GRIND, args, cwd=repo, env={**env, "STUB_ACTION": action})

    rc, _, err = run([MISSION, "--status"])
    check("--status reports the mission", rc == 0 and "sweep it" in err, err)
    rc, _, err = run([MISSION, "--dry-run"])
    check("--dry-run runs nothing", rc == 0 and "nothing executed" in err, err)
    rc, _, err = run(["nope.md", "--status"])
    check("a missing mission is an error", rc != 0 and "not found" in err, err)
    pathlib.Path(live, "badname.md").write_text(mission())
    rc, _, err = run(["badname.md", "--status"])
    check("a non-conforming filename is rejected", rc != 0 and "convention" in err, err)
    os.remove(os.path.join(live, "badname.md"))

    rc, _, err = run([MISSION, "--once", "-y"], action="grind-commit")
    check("--once runs one productive iteration", rc == 0 and "productive" in err, err[-500:])
    check("the iteration counter persisted", grind.read_iter(path, live) == 1)
    check("the attempt counter is clear", grind.read_attempt(path, live) == 0)
    check("the tagged commit is visible to the gate", "item-1.txt" in subprocess.run(
        ["git", "-C", repo, "log", "--oneline", "-1", "--name-only"],
        capture_output=True, text=True).stdout)
    check("the memory log exists", os.path.isfile(os.path.join(live, "sweep.log".replace(
        "sweep", os.path.splitext(MISSION)[0]))))

    # an iteration that leaves partial work → attempt burned, retry armed (mission survives).
    # --once caps FRESH iterations, not retries, so a persistently dirty stub walks the whole
    # ladder: attempts 1..4, then a stop for triage with the counter parked at the last retry.
    rc, _, err = run([MISSION, "--once", "-y"], action="grind-dirty")
    check("an iteration leaving a dirty tree arms a retry",
          rc == 0 and "unproductive" in err and "dirty tree" in err, err[-500:])
    check("the retry ladder runs to the end",
          f"exhausted all {grind.MAX_ITER_ATTEMPTS} attempts" in err, err[-400:])
    check("the attempt counter is parked for triage, not reset",
          grind.read_attempt(path, live) == grind.MAX_ITER_ATTEMPTS - 1,
          grind.read_attempt(path, live))
    check("retries reuse the iteration number instead of advancing it",
          grind.read_iter(path, live) == 2, grind.read_iter(path, live))
    os.remove(os.path.join(repo, "half-done.txt"))

    # a session that produces nothing and returns instantly reads as a transient API failure:
    # long backoffs, attempt budget untouched, state preserved for a later re-launch
    rc, _, err = run([MISSION, "-y"])
    check("instant no-op iterations are treated as transient",
          "long backoff" in err and "attempt budget untouched" in err, err[-500:])
    check("sustained transient failure stops and preserves state",
          "sustained transient-API failure" in err, err[-300:])

    rc, _, err = run([MISSION, "--reset"])
    check("--reset clears both counters",
          rc == 0 and grind.read_iter(path, live) == 0 and grind.read_attempt(path, live) == 0)

    # dirty-tree guard: a fresh session refuses to start on uncommitted work
    pathlib.Path(repo, "stray.txt").write_text("uncommitted\n")
    rc, _, err = run([MISSION, "--once", "-y"])
    check("a dirty tree blocks a fresh iteration", "working tree dirty" in err, err[-400:])
    check("the guard names the offending file", "stray.txt" in err, err[-400:])
    os.remove(os.path.join(repo, "stray.txt"))

    # a done-check that passes ends the mission before any session runs
    pathlib.Path(path).write_text(mission(max_iterations=3, done_check="true"))
    rc, _, err = run([MISSION, "-y"])
    check("a passing done-check completes the mission", "done-check passed" in err, err[-400:])
    check("the mission is flipped to done", "status: done" in pathlib.Path(path).read_text())

    # a non-active mission refuses to run
    rc, _, err = run([MISSION, "-y"])
    check("a done mission will not run", rc != 0 and "not 'active'" in err, err[-300:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
