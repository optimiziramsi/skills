#!/usr/bin/env python3
"""Self-tests for the reporting topic — the Stop guard, the contract inject + rc nudge,
the mid-turn pulse, the shared contract helpers, and the calibrate CLI.

Run: python3 reporting/tests/test_reporting.py
"""
import datetime
import json
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, load_module, run_cli  # noqa: E402

# Settings the developer's own shell may carry must not leak into the fixtures.
for var in [v for v in os.environ
            if v.startswith(("REPORT_", "CLAUDE_PLUGIN_OPTION_")) or v == "CLAUDE_PROJECT_DIR"]:
    del os.environ[var]

check = Check()
PULSE = hook("hooks/contract-pulse.py")
CONTRACT = hook("hooks/contract.py")
CLI = hook("bin/calibrate")
sys.path.insert(0, os.path.dirname(CONTRACT))  # the hooks dir, so `import _contract` resolves
_contract = load_module(hook("hooks/_contract.py"), "_contract")
report_guard = load_module(hook("hooks/report-guard.py"), "report_guard")


# ── report-guard: what counts as a contract violation ──────────────────────
def clean(name, want_clean, text):
    problems = report_guard.violations(text)
    check(name, (not problems) == want_clean, problems)


clean("a plain report passes", True,
      "Guard shipped and self-tests pass.\n- 17 tests green\n- wired into hooks.json\n"
      "Q:\n1. enable in CI?")
clean("narration is caught", False, "Let me check the config first.")
clean("\"now I'll\" is caught", False, "Now I'll wire the hook into settings.")
clean("\"I'm going to\" is caught", False, "I'm going to refactor the parser next.")
clean("markdown headers are caught", False, "## Summary\nAll done.")
clean("a table is caught", False, "| a | b |\n|---|---|\n| 1 | 2 |")
clean("over-length is caught", False, "\n".join(f"line {i}" for i in range(25)))
clean("fenced code is exempt from the shape checks", True,
      "Done.\n```\nlet me check inside code is fine\n## header in code fine\n```\n- one fact")
clean("exactly 18 lines still passes", True, "\n".join(f"- fact {i}" for i in range(18)))
# quoting a banned phrase / header / pipe is talking *about* it, not doing it — not a violation
clean("a double-quoted banned phrase is not flagged", True,
      'Guard ships — it blanks the "Let me check" example before matching.\n- one fact')
clean("a backticked banned phrase is not flagged", True,
      "Guard ships — the `now I'll` case no longer self-trips.\n- one fact")
clean("a single-quoted banned phrase is not flagged", True,
      "Guard ships — the 'Let me look' phrase is quoted, not narrated.\n- one fact")
clean("a quoted markdown header is not flagged", True,
      'Done — a report may now name a "## Summary" header.\n- one fact')
clean("a quoted table row is not flagged", True,
      'Done — mentioning a "| a | b |" row is fine now.\n- one fact')
# but real narration must still be caught, even next to an apostrophe pair or a legit quote
clean("real narration beside an apostrophe pair is still caught", False,
      "Now I'll wire it; that's the last step.")
clean("real narration beside a quoted span is still caught", False,
      'The guard blanks "quotes" but I\'m going to refactor anyway.')


# ── _contract: the stamp parser ─────────────────────────────────────────────
def stamp(name, text, want):
    check(name, _contract.parse_stamp(text) == want, _contract.parse_stamp(text))


stamp("an rc stamp with a version parses", "=== X · rc: 2026-11-02 v2 ===",
      {"kind": "rc", "date": "2026-11-02", "version": 2})
stamp("a stable stamp parses", "=== X · stable: 2026-10-01 ===",
      {"kind": "stable", "date": "2026-10-01", "version": None})
stamp("an rc stamp without a version parses", "head · rc: 2026-01-09",
      {"kind": "rc", "date": "2026-01-09", "version": None})
stamp("an unstamped first line is None", "=== OUTPUT CONTRACT (hard rule) ===", None)
stamp("only the first line is read", "plain head\n· rc: 2026-11-02 v9", None)

check("the shipped contract is stamped stable", (_contract.parse_stamp(open(_contract.SHIPPED).read()) or {}).get("kind") == "stable")


# ── _contract: the pulse line (frame + stamp stripped) ──────────────────────
check("pulse_line strips the frame and the stamp",
      _contract.pulse_line("=== OUTPUT CONTRACT (hard rule) · stable: 2026-11-02 ===\nbody")
      == "OUTPUT CONTRACT (hard rule)")
check("pulse_line keeps an unframed, unstamped line as-is",
      _contract.pulse_line("say less, dev\nmore below") == "say less, dev")
check("the shipped contract pulses to its title line",
      "OUTPUT CONTRACT" in _contract.pulse_line(open(_contract.SHIPPED).read())
      and "stable:" not in _contract.pulse_line(open(_contract.SHIPPED).read()))


# ── _contract: the rc nudge ─────────────────────────────────────────────────
TODAY = datetime.date(2026, 11, 2)


def days_ago(n):
    return (TODAY - datetime.timedelta(days=n)).isoformat()


check("an rc contract past the threshold nudges",
      _contract.rc_nudge(f"=== X · rc: {days_ago(30)} v1 ===", 7, TODAY) is not None)
check("the nudge names the date, the age, and /calibrate",
      all(s in _contract.rc_nudge(f"=== X · rc: {days_ago(30)} v1 ===", 7, TODAY)
          for s in (days_ago(30), "30 d", "/calibrate")))
check("a fresh rc contract does not nudge",
      _contract.rc_nudge(f"=== X · rc: {days_ago(2)} v1 ===", 7, TODAY) is None)
check("a stable contract never nudges",
      _contract.rc_nudge(f"=== X · stable: {days_ago(999)} ===", 7, TODAY) is None)
check("an unstamped contract never nudges",
      _contract.rc_nudge("=== OUTPUT CONTRACT ===", 7, TODAY) is None)
check("the threshold is respected",
      _contract.rc_nudge(f"=== X · rc: {days_ago(5)} v1 ===", 7, TODAY) is None
      and _contract.rc_nudge(f"=== X · rc: {days_ago(5)} v1 ===", 3, TODAY) is not None)


# ── _contract: the transcript reader (turn finals) ──────────────────────────
TRANSCRIPT = "".join(json.dumps(e) + "\n" for e in [
    {"type": "user", "message": {"content": "first prompt"}},
    {"type": "assistant", "message": {"content": [{"type": "text", "text": "working..."}]}},
    {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {}}]}},
    {"type": "user", "message": {"content": [{"type": "tool_result", "content": "file bytes"}]}},
    {"type": "assistant", "message": {"content": [{"type": "text", "text": "turn 1 final"}]}},
    {"type": "user", "message": {"content": "second prompt"}},
    {"type": "user", "isMeta": True, "message": {"content": "a system reminder"}},
    {"type": "assistant", "message": {"content": [{"type": "text", "text": "turn 2 final"}]}},
])

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    tpath = os.path.join(tmp, "session.jsonl")
    pathlib.Path(tpath).write_text(TRANSCRIPT)
    check("turn_finals returns each turn's last assistant text",
          _contract.turn_finals(tpath) == ["turn 1 final", "turn 2 final"])
    check("report-guard's final text is the last turn final",
          report_guard.final_assistant_text(tpath) == "turn 2 final")
    check("a missing transcript is empty, not a crash", _contract.turn_finals(os.path.join(tmp, "nope.jsonl")) == [])

    # ── the mid-turn pulse ──────────────────────────────────────────────────
    cleanp = os.path.join(tmp, "clean")        # a project with no override → the shipped contract
    os.makedirs(cleanp)

    def fire(session_id, times=1, env=None):
        """Call the pulse `times` times; return the output of the LAST call."""
        out = ""
        for _ in range(times):
            out = invoke(PULSE, {"session_id": session_id},
                         env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": cleanp, **(env or {})})[1]
        return out

    sid = f"pulse-{os.getpid()}"
    check("calls 1-9 stay silent", all(fire(f"{sid}-a") == "" for _ in range(9)))
    check("the 10th call re-injects the contract", "additionalContext" in fire(f"{sid}-b", times=10))
    check("the default pulse is the active contract's first line",
          "overrides any default" in fire(f"{sid}-c", times=10))
    check("REPORT_PULSE_EVERY tunes the cadence",
          "additionalContext" in fire(f"{sid}-d", times=3, env={"REPORT_PULSE_EVERY": "3"}))
    check("kill-switch disarms", fire(f"{sid}-e", times=10, env={"REPORT_GUARD_OFF": "1"}) == "")
    check("a bad REPORT_PULSE_EVERY falls back to the default",
          "additionalContext" in fire(f"{sid}-f", times=10, env={"REPORT_PULSE_EVERY": "junk"}))
    check("counters are per session",
          fire(f"{sid}-g", times=5) == "" and fire(f"{sid}-h", times=5) == "")
    check("REPORT_PULSE_TEXT replaces the one-liner",
          "say less" in fire(f"{sid}-i", times=10, env={"REPORT_PULSE_TEXT": "say less"}))

    # an override's own first line drives the pulse
    op = os.path.join(tmp, "ovr")
    os.makedirs(os.path.join(op, ".agent"))
    pathlib.Path(op, ".agent", "output-contract.md").write_text(
        "=== DEV REPORTS · rc: 2020-01-01 v3 ===\nbuddy talk, plain words\n")
    pulsed = invoke(PULSE, {"session_id": f"{sid}-j"}, env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": op}, )
    for _ in range(9):
        pulsed = invoke(PULSE, {"session_id": f"{sid}-j"}, env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": op})
    out_j = pulsed[1]
    check("an override drives the pulse, frame and stamp stripped",
          "DEV REPORTS" in out_j and "2020-01-01" not in out_j and "===" not in out_j)
    check("the hardcoded REMINDER is the last resort when the contract is unreadable",
          "no text between tool calls" in
          fire(f"{sid}-k", times=10, env={"REPORT_CONTRACT_FILE": "nope.md"}))

    # ── the injected contract and its per-repo override chain ───────────────
    project = os.path.join(tmp, "proj")
    os.makedirs(os.path.join(project, ".agent"))
    os.makedirs(os.path.join(project, ".claude"))

    def contract(env=None):
        return invoke(CONTRACT, {"cwd": project}, env={"CLAUDE_PROJECT_DIR": project, **(env or {})})[1]

    check("no override → the shipped contract", "OUTPUT CONTRACT" in contract())
    pathlib.Path(project, ".claude", "output-contract.md").write_text("claude-dir contract\n")
    check(".claude/output-contract.md overrides the shipped one", contract().strip() == "claude-dir contract")
    pathlib.Path(project, ".agent", "output-contract.md").write_text("agent-dir contract\n")
    check(".agent/output-contract.md wins over .claude/", contract().strip() == "agent-dir contract")
    pathlib.Path(project, "mine.md").write_text("explicit contract\n")
    check("REPORT_CONTRACT_FILE wins over both",
          contract({"REPORT_CONTRACT_FILE": "mine.md"}).strip() == "explicit contract")
    check("a missing REPORT_CONTRACT_FILE is a loud DISARM, not a silent fallback",
          "DISARMED" in contract({"REPORT_CONTRACT_FILE": "nope.md"}))
    unreadable = pathlib.Path(project, ".agent", "output-contract.md")
    unreadable.chmod(0)
    if not os.access(unreadable, os.R_OK):   # root ignores modes; skip there
        check("an unreadable override is a loud DISARM", "DISARMED" in contract())
    unreadable.chmod(0o644)
    check("REPORT_GUARD_OFF=1 silences the contract", contract({"REPORT_GUARD_OFF": "1"}) == "")

    # ── the rc nudge, appended once per session ─────────────────────────────
    rcp = os.path.join(tmp, "rcproj")
    os.makedirs(os.path.join(rcp, ".agent"))
    rc_file = pathlib.Path(rcp, ".agent", "output-contract.md")

    def rc_contract(stamp_line, sid, env=None):
        rc_file.write_text(stamp_line + "\nthe body\n")
        return invoke(CONTRACT, {"cwd": rcp, "session_id": sid},
                      env={"CLAUDE_PROJECT_DIR": rcp, "TMPDIR": tmp, **(env or {})})[1]

    out1 = rc_contract("=== X · rc: 2000-01-01 v1 ===", "rc-once")
    check("a stale rc contract gets the nudge", "run /calibrate" in out1 and "the body" in out1)
    check("the nudge fires only once per session",
          "run /calibrate" not in rc_contract("=== X · rc: 2000-01-01 v1 ===", "rc-once"))
    check("a fresh rc contract is not nudged",
          "run /calibrate" not in rc_contract(f"=== X · rc: {datetime.date.today().isoformat()} v1 ===", "rc-fresh"))
    check("a stable contract is not nudged",
          "run /calibrate" not in rc_contract("=== X · stable: 2000-01-01 ===", "rc-stable"))
    check("REPORT_RC_DAYS raises the bar",
          "run /calibrate" not in rc_contract("=== X · rc: 2000-01-01 v1 ===", "rc-days",
                                               env={"REPORT_RC_DAYS": "999999"}))

    # ── the calibrate CLI ───────────────────────────────────────────────────
    msg = run_cli(CLI, ["messages", "2", "--transcript", tpath])[1]
    check("calibrate messages frames the last N reports",
          "--- report 1 ---" in msg and "turn 1 final" in msg and "turn 2 final" in msg)
    one = run_cli(CLI, ["messages", "1", "--transcript", tpath])[1]
    check("calibrate messages N takes only the last N", "turn 2 final" in one and "turn 1 final" not in one)
    code, _, err = run_cli(CLI, ["messages", "--transcript", os.path.join(tmp, "nope.jsonl")])
    check("calibrate messages with no reports exits non-zero", code != 0)

    con = run_cli(CLI, ["contracts"], env={"CLAUDE_PROJECT_DIR": cleanp})[1]
    check("calibrate contracts reports the shipped text when no override",
          "active-source: shipped" in con and "OUTPUT CONTRACT" in con and "--- shipped ---" not in con)
    con2 = run_cli(CLI, ["contracts"], env={"CLAUDE_PROJECT_DIR": op})[1]
    check("calibrate contracts hands over the shipped text to compare against an override",
          "active-source:" in con2 and "rc 2020-01-01" in con2
          and "--- active ---" in con2 and "--- shipped ---" in con2)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
