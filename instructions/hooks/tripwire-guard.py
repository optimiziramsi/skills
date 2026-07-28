#!/usr/bin/env python3
"""PreToolUse[Bash] ENGINE for project-owned command tripwires.

The engine ships here; the PROJECT supplies the guards as `.agent/guards.d/*.sh`. No dir / no
guards → silent no-op, so projects opt IN. Guards are asserts on the Bash tool's command,
surfaced at the moment of risk (git/commit rules live in git-guard and commit-format instead).

Guard contract — each `*.sh`, run in sorted order with cwd = the project dir:
  · the command arrives in $TRIPWIRE_COMMAND; the full tool-input JSON in $TRIPWIRE_INPUT and
    on stdin (byte-identical, so a guard may parse it however it likes)
  · print a reason and exit 2 → BLOCK; the first block wins and its reason reaches the agent
  · exit 0                    → allow
  · any other exit            → LOUD non-blocking warning carrying whatever it printed, so an
                                advisory or a crash is surfaced rather than swallowed
  · optionally define a `tripwire_test` function (PASS/FAIL lines, returns #fails) and gate the
    top-level dispatch with `[ "${BASH_SOURCE[0]}" = "$0" ]`, so it can be sourced and tested.
    See instructions/examples/guards.d/ in this plugin.

Escape hatches (guards have no shell parser — false positives happen):
  TRIPWIRE_SKIP=1 …     prefixed to the ONE command that false-positives (one-shot, visible)
  TRIPWIRE_GUARD_OFF=1  kill switch
  TRIPWIRE_GUARDS_DIR   override the discovery dir (default .agent/guards.d)
"""
import glob
import json
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

SKIP = re.compile(r"(^|\s)TRIPWIRE_SKIP=1(\s|$)")


def guards_dir(project):
    """The project's guard directory — absolute, whether configured relative or absolute."""
    configured = os.environ.get("TRIPWIRE_GUARDS_DIR") or os.path.join(".agent", "guards.d")
    return configured if os.path.isabs(configured) else os.path.join(project, configured)


def main():
    if hookio.flag("TRIPWIRE_GUARD_OFF"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    guards = sorted(glob.glob(os.path.join(guards_dir(project), "*.sh")))
    if not guards:
        return
    raw = sys.stdin.read()                           # forwarded verbatim — guards may parse it
    command = (json.loads(raw).get("tool_input") or {}).get("command", "")
    if not command or SKIP.search(command):
        return

    env = {**os.environ, "TRIPWIRE_COMMAND": command, "TRIPWIRE_INPUT": raw}
    warnings = []
    for guard in guards:
        done = subprocess.run(["bash", guard], cwd=project, env=env, input=raw,
                              capture_output=True, text=True)
        output = (done.stdout + done.stderr).strip()
        name = os.path.basename(guard)
        if done.returncode == 2:
            print(output or f"⛔ tripwire-guard: blocked by {name} (no reason printed)",
                  file=sys.stderr)
            sys.exit(2)
        if done.returncode != 0:
            warnings.append(f"{name}: {output or f'exit {done.returncode} with no message'}")
    if warnings:
        hookio.notice("⚠️ tripwire-guard: " + " · ".join(warnings))


hookio.guard(main)
