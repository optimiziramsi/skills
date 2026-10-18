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

    at(200_000)
    check("below 30% of 1M stays silent", fire() == {})
    at(310_000)
    first = fire()
    check("crossing 30% nudges the user", "31% of 1.00M" in first.get("systemMessage", ""), first)
    check("…and tells the model", "additionalContext" in first.get("hookSpecificOutput", {}))
    check("a level nudges only once", fire() == {})
    at(520_000)
    check("crossing 50% nudges again", "52%" in fire().get("systemMessage", ""))
    at(610_000)
    handoff = fire(event="PostToolUse")
    check("60% is the handoff level and says so", "time for a handoff" in handoff.get("systemMessage", ""), handoff)
    check("…mid-turn too (PostToolUse)", handoff.get("hookSpecificOutput", {}).get("hookEventName") == "PostToolUse")
    check("…and names the overrides", "remind me later" in handoff["systemMessage"])

    # overrides, answered on the next prompt
    ack = fire(prompt="remind me later, almost done")
    check("'remind me later' is acknowledged", "snoozed" in ack.get("hookSpecificOutput", {}).get("additionalContext", ""), ack)
    at(640_000)
    check("snoozed: no nudge before +5%", fire() == {})
    at(661_000)
    check("snoozed: it nudges again after +5%", "time for a handoff" in fire().get("systemMessage", ""))
    ack = fire(prompt="keep going")
    check("'keep going' silences the level", "silenced" in ack.get("hookSpecificOutput", {}).get("additionalContext", ""))
    at(900_000)
    check("…and stays silent", fire() == {})

    at(610_000)
    fire(session="s2")
    ack = fire(session="s2", prompt="the topic is already done")
    check("'topic done' says no handoff is needed", "no handoff is needed" in
          ack.get("hookSpecificOutput", {}).get("additionalContext", ""), ack)
    at(990_000)
    check("…and ends the nudges for the session", fire(session="s2") == {})

    check("an answer without a pending nudge is ignored", fire(session="s3", prompt="keep going").get(
        "systemMessage", "").startswith("[context]"))

    # configuration
    at(150_000)
    check("CONTEXT_WINDOW_TOKENS=200000 rescales (75% → handoff level)",
          "time for a handoff" in fire(session="s4", env={"CONTEXT_WINDOW_TOKENS": "200000"}).get("systemMessage", ""))
    check("CONTEXT_NUDGE_AT sets the levels",
          fire(session="s5", env={"CONTEXT_NUDGE_AT": "10"}).get("systemMessage", "").startswith("[context] 15%"))
    check("CONTEXT_NUDGE_OFF=1 disarms it", fire(session="s6", env={"CONTEXT_NUDGE_OFF": "1",
                                                                     "CONTEXT_NUDGE_AT": "10"}) == {})
    at(100_000, sidechain_tokens=900_000)
    check("subagent (sidechain) usage doesn't count", fire(session="s7") == {})
    pathlib.Path(transcript).write_text("not json\n")
    check("an unreadable transcript fails open", fire(session="s8") == {})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
