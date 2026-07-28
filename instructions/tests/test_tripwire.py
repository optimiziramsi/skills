#!/usr/bin/env python3
"""Self-tests for the tripwire-guard engine. Run: python3 instructions/tests/test_tripwire.py

The shipped example guards carry their own `--test`; this covers the ENGINE — discovery,
the three exit-code outcomes, ordering, and the escape hatches.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke  # noqa: E402

check = Check()
GUARD = hook("instructions/hooks/tripwire-guard.py")

BLOCKER = 'case "${TRIPWIRE_COMMAND:-}" in *forbidden*) echo "⛔ forbidden command"; exit 2 ;; esac\n'
WARNER = 'case "${TRIPWIRE_COMMAND:-}" in *sketchy*) echo "heads-up: sketchy move"; exit 3 ;; esac\n'
# proves TRIPWIRE_INPUT and stdin arrive byte-identical, which the guard contract promises
PARITY = 'in=$(cat); [ "$in" = "${TRIPWIRE_INPUT:-}" ] || { echo "stdin/env mismatch"; exit 2; }\n'

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    def write_guards(name, scripts):
        d = os.path.join(tmp, name)
        os.makedirs(d, exist_ok=True)
        for filename, body in scripts.items():
            with open(os.path.join(d, filename), "w") as fh:
                fh.write("#!/usr/bin/env bash\n" + body + "exit 0\n")
        return d

    guards = write_guards("guards", {"10-block.sh": BLOCKER, "20-warn.sh": WARNER,
                                     "30-parity.sh": PARITY})
    ordered = write_guards("order", {"05-first.sh": 'echo "first wins"; exit 2\n',
                                     "10-block.sh": BLOCKER})
    empty = write_guards("empty", {})

    def run(directory, command, env=None):
        return invoke(GUARD, {"tool_input": {"command": command}},
                      env={"TRIPWIRE_GUARDS_DIR": directory, "CLAUDE_PROJECT_DIR": tmp,
                           **(env or {})})

    check("no guards dir → allow", run(os.path.join(tmp, "missing"), "echo forbidden")[0] == 0)
    check("empty guards dir → allow", run(empty, "echo forbidden")[0] == 0)
    rc, out, err = run(guards, "echo harmless")
    check("a clean command is allowed", rc == 0 and out == "", f"rc={rc} out={out} err={err}")
    rc, _, err = run(guards, "echo forbidden")
    check("a guard's exit 2 blocks", rc == 2, f"rc={rc}")
    check("the block reason reaches stderr", "forbidden command" in err, err)
    rc, out, _ = run(guards, "echo sketchy")
    check("a guard's other exit warns without blocking", rc == 0 and "sketchy move" in out, out)
    check("the warning is a systemMessage", "systemMessage" in out, out)
    rc, _, err = run(ordered, "echo forbidden")
    check("the first block wins", rc == 2 and "first wins" in err and "forbidden command" not in err, err)
    check("TRIPWIRE_SKIP=1 is a one-shot escape",
          run(guards, "TRIPWIRE_SKIP=1 echo forbidden")[0] == 0)
    check("TRIPWIRE_SKIP=1 mid-command also escapes",
          run(guards, "cd /x && TRIPWIRE_SKIP=1 echo forbidden")[0] == 0)
    check("kill-switch disarms",
          run(guards, "echo forbidden", env={"TRIPWIRE_GUARD_OFF": "1"})[0] == 0)
    check("a non-Bash payload with no command is ignored",
          invoke(GUARD, {"tool_input": {"file_path": "/x"}},
                 env={"TRIPWIRE_GUARDS_DIR": guards, "CLAUDE_PROJECT_DIR": tmp})[0] == 0)

    # a guard that itself crashes must warn, never block and never take the session down
    crashy = write_guards("crashy", {"10-boom.sh": "exit 7\n"})
    rc, out, _ = run(crashy, "anything")
    check("a crashing guard warns instead of blocking", rc == 0 and "exit 7" in out, out)

    # every shipped example guard is sourceable and its tripwire_test passes
    for example in sorted(pathlib.Path(hook("instructions/examples/guards.d")).glob("*.sh")):
        if "tripwire_test" not in example.read_text():
            continue
        done = subprocess.run(
            ["bash", "-c", f'source "$1"; declare -F tripwire_test >/dev/null && tripwire_test',
             "_", str(example)], capture_output=True, text=True)
        check(f"example guard {example.name} passes its tripwire_test",
              done.returncode == 0, done.stdout + done.stderr)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
