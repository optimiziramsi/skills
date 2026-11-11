#!/usr/bin/env python3
"""Self-tests for the context nudge. Run: python3 context/tests/test_context.py"""
import json
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke  # noqa: E402

check = Check()
NUDGE = hook("hooks/context-nudge.py")
for var in [v for v in os.environ if v.startswith(("CONTEXT_", "CLAUDE_PLUGIN_"))]:
    del os.environ[var]

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    data_dir = os.path.join(tmp, "data")
    transcript = os.path.join(tmp, "t.jsonl")

    def at(tokens, sidechain_tokens=None):
        """Rewrite the transcript so the last main-thread message used `tokens`."""
        rows = [{"type": "user", "message": {"content": "hi"}},
                {"type": "assistant", "message": {"usage": {
                    "input_tokens": 2, "cache_creation_input_tokens": 1000,
                    "cache_read_input_tokens": tokens - 1102, "output_tokens": 100}}}]
        if sidechain_tokens:
            rows.append({"type": "assistant", "isSidechain": True,
                         "message": {"usage": {"input_tokens": sidechain_tokens}}})
        pathlib.Path(transcript).write_text("".join(json.dumps(r) + "\n" for r in rows))

    def fire(session="s1", event="UserPromptSubmit", prompt="next step", env=None):
        out = invoke(NUDGE, {"session_id": session, "hook_event_name": event, "prompt": prompt,
                             "transcript_path": transcript},
                     env={"CLAUDE_PLUGIN_DATA": data_dir, **(env or {})})[1]
        return json.loads(out) if out.strip() else {}

    ctx = lambda out: out.get("hookSpecificOutput", {}).get("additionalContext", "")

    at(150_000)
    check("below 20% of 1M stays silent", fire() == {})
    at(210_000)
    hint = fire()
    check("crossing 20% (the hint) tells the user", "21% of 1.00M" in hint.get("systemMessage", ""), hint)
    check("…and tells the model nothing", list(hint) == ["systemMessage"], hint)
    check("a level nudges only once", fire() == {})
    at(320_000)
    action = fire(event="PostToolUse")
    check("30% is the action level and says so", "time for a handoff" in action.get("systemMessage", ""), action)
    check("…to the model too", "the handoff level" in ctx(action) and "/repack" in ctx(action), action)
    check("…mid-turn too (PostToolUse)", action.get("hookSpecificOutput", {}).get("hookEventName") == "PostToolUse")
    check("…and names the overrides", "remind me later" in action["systemMessage"])

    # overrides, answered on the next prompt
    ack = fire(prompt="remind me later, almost done")
    check("'remind me later' is acknowledged", "snoozed" in ctx(ack), ack)
    at(350_000)
    check("snoozed: no nudge before +5%", fire() == {})
    at(371_000)
    check("snoozed: it nudges again after +5%", "time for a handoff" in fire().get("systemMessage", ""))
    ack = fire(prompt="keep going")
    check("'keep going' silences the level", "silenced" in ctx(ack))
    at(500_000)
    check("…and stays silent below the next level", fire() == {})
    at(560_000)
    alert = fire()
    check("55% is the red alert and says so", "past the safe range: hand off now" in alert.get("systemMessage", ""), alert)
    check("…to the model in its own words", "start nothing new" in ctx(alert) and "the handoff level" not in ctx(alert), alert)
    ack = fire(prompt="not now")
    check("the red alert can be snoozed", "snoozed" in ctx(ack), ack)
    at(600_000)
    check("…no nudge before +5%", fire() == {})
    at(611_000)
    check("…and it comes back as the red alert", "past the safe range" in fire().get("systemMessage", ""))
    ack = fire(prompt="keep going")
    check("the red alert can be silenced", "silenced" in ctx(ack))
    at(900_000)
    check("…and stays silent", fire() == {})

    at(560_000)
    fire(session="s2")
    report = "Subagent report: the user may answer 'topic done' or 'keep going'. " + "detail " * 40
    check("a long prompt that quotes an answer is not an answer", fire(session="s2", prompt=report) == {})
    ack = fire(session="s2", prompt="the topic is already done")
    check("'topic done' says no handoff is needed", "no handoff is needed" in ctx(ack), ack)
    at(990_000)
    check("…and ends the nudges for the session", fire(session="s2") == {})

    check("an answer without a pending nudge is ignored", fire(session="s3", prompt="keep going").get(
        "systemMessage", "").startswith("[context]"))

    # configuration
    at(150_000)
    check("CONTEXT_WINDOW_TOKENS=200000 rescales (75% → red alert)",
          "past the safe range" in fire(session="s4", env={"CONTEXT_WINDOW_TOKENS": "200000"}).get("systemMessage", ""))
    one = fire(session="s5", env={"CONTEXT_NUDGE_AT": "10"})
    check("CONTEXT_NUDGE_AT sets the levels", one.get("systemMessage", "").startswith("[context] 15%"))
    check("a single level is the action level", "time for a handoff" in one.get("systemMessage", "")
          and "the handoff level" in ctx(one), one)
    check("CONTEXT_NUDGE_OFF=1 disarms it", fire(session="s6", env={"CONTEXT_NUDGE_OFF": "1",
                                                                     "CONTEXT_NUDGE_AT": "10"}) == {})
    two = {"CONTEXT_NUDGE_AT": "10,20"}
    first = fire(session="s9", env=two)
    check("two levels: the first is the action level", "time for a handoff" in first.get("systemMessage", "")
          and "the handoff level" in ctx(first), first)
    at(250_000)
    last = fire(session="s9", env=two)
    check("two levels: the last is the red alert", "past the safe range" in last.get("systemMessage", "")
          and "start nothing new" in ctx(last), last)
    at(110_000)
    early = fire(session="s10", env={"CONTEXT_NUDGE_AT": "5,10,40,60"})
    check("four levels: everything before the last two is a hint",
          list(early) == ["systemMessage"] and "fine for now" in early["systemMessage"], early)
    at(100_000, sidechain_tokens=900_000)
    check("subagent (sidechain) usage doesn't count", fire(session="s7") == {})
    pathlib.Path(transcript).write_text("not json\n")
    check("an unreadable transcript fails open", fire(session="s8") == {})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
