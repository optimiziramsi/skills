#!/usr/bin/env python3
"""PreToolUse[Bash] ENGINE for project-owned command tripwires.

The engine ships here; the PROJECT supplies the guards in `.agent/guards.d/`. No dir / no
guards → silent no-op, so projects opt IN. Guards are asserts on the Bash tool's command,
surfaced at the moment of risk (git/commit rules live in git-guard and commit-format instead).

A guard is written in whatever language the PROJECT wants — this engine being python is its own
business, not a contract imposed on consumers. Discovery + launch, in sorted order:
  · `*.sh` → run with `bash`, `*.py` → run with this python; neither needs the executable bit
  · any other file with the executable bit → run directly, so its own shebang picks the
    interpreter (node, ruby, a compiled binary, …)
  · anything else in the dir (READMEs, configs, disabled guards) is ignored

Guard contract — each guard runs with cwd = the project dir:
  · the command arrives in $TRIPWIRE_COMMAND; the full tool-input JSON in $TRIPWIRE_INPUT and
    on stdin (byte-identical, so a guard may parse it however it likes)
  · print a reason and exit 2 → BLOCK; the first block wins and its reason reaches the agent
  · exit 0                    → allow
  · any other exit            → LOUD non-blocking warning carrying whatever it printed, so an
                                advisory or a crash is surfaced rather than swallowed
  · self-tests are the guard's own business; the bash examples shipped in
    instructions/examples/guards.d/ define a `tripwire_test` function (PASS/FAIL lines, returns
    #fails) and gate the top-level dispatch with `[ "${BASH_SOURCE[0]}" = "$0" ]` so they can be
    sourced and tested.

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


def discover(project):
    """Every runnable guard in the dir, sorted — see the language rule in the module docstring."""
    found = []
    for path in sorted(glob.glob(os.path.join(guards_dir(project), "*"))):
        if os.path.isfile(path) and (path.endswith((".sh", ".py")) or os.access(path, os.X_OK)):
            found.append(path)
    return found


def launch(guard):
    """How to run one guard: a known extension names its interpreter, else its own shebang."""
    if guard.endswith(".sh"):
        return ["bash", guard]
    if guard.endswith(".py"):
        return [sys.executable, guard]
    return [guard]


def main():
    if hookio.flag("TRIPWIRE_GUARD_OFF"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    guards = discover(project)
    if not guards:
        return
    raw = sys.stdin.read()                           # forwarded verbatim — guards may parse it
    command = (json.loads(raw).get("tool_input") or {}).get("command", "")
    if not command or SKIP.search(command):
        return

    env = {**os.environ, "TRIPWIRE_COMMAND": command, "TRIPWIRE_INPUT": raw}
    warnings = []
    for guard in guards:
        name = os.path.basename(guard)
        try:
            done = subprocess.run(launch(guard), cwd=project, env=env, input=raw,
                                  capture_output=True, text=True)
        except OSError as err:                       # bad shebang, lost +x — warn, never block
            warnings.append(f"{name}: could not run ({err})")
            continue
        output = (done.stdout + done.stderr).strip()
        if done.returncode == 2:
            print(output or f"⛔ tripwire-guard: blocked by {name} (no reason printed)",
                  file=sys.stderr)
            sys.exit(2)
        if done.returncode != 0:
            warnings.append(f"{name}: {output or f'exit {done.returncode} with no message'}")
    if warnings:
        hookio.notice("⚠️ tripwire-guard: " + " · ".join(warnings))


hookio.guard(main)
