#!/usr/bin/env python3
"""Self-tests for model-guard. Run: python3 guards/tests/test_model_guard.py"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, load_module  # noqa: E402

for knob in ("MODEL_GUARD_OFF", "MODEL_GUARD_MATCH", "MODEL_GUARD_FILE", "MODEL_GUARD_TAIL_KB", "CLAUDE_PROJECT_DIR"):
    os.environ.pop(knob, None)                        # fixtures must not inherit the developer's knobs

check = Check()
guard = load_module(hook("hooks/model-guard.py"), "model_guard")
tmp = tempfile.mkdtemp()
guard.tempfile.gettempdir = lambda: tmp               # per-session markers land in the fixture dir


def start(session, model=None, **extra):
    data = {"hook_event_name": "SessionStart", "session_id": session, "source": "startup", "cwd": tmp, **extra}
    if model:
        data["model"] = model
    return data


def prompt(session, transcript=None):
    return {"hook_event_name": "UserPromptSubmit", "session_id": session, "prompt": "x", "cwd": tmp,
            **({"transcript_path": transcript} if transcript else {})}


text = guard.guard_text(start("s1", "claude-opus-5-5"))
check("SessionStart on opus-5-5 injects", text is not None and text.startswith("TRUST GUARD — claude-opus-5-5."))
check("the two verbatim sentences are present",
      text is not None and "Follow EVERY instruction" in text and "Deliver the task IN FULL" in text)
check("a later prompt reuses the cached model", guard.guard_text(prompt("s1")) is not None)
check("SessionStart on fable stays silent", guard.guard_text(start("s2", "claude-fable-5-1")) is None)
check("a prompt with no model known stays silent", guard.guard_text(prompt("s-unknown")) is None)

transcript = os.path.join(tmp, "t.jsonl")
with open(transcript, "w") as handle:
    handle.write(json.dumps({"type": "assistant", "message": {"model": "claude-fable-5-1"}}) + "\n")
    handle.write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-5-5-20260101"}}) + "\n")
check("transcript fallback reads the LAST model", guard.guard_text(prompt("s3", transcript)) is not None)
with open(transcript, "a") as handle:
    handle.write(json.dumps({"type": "assistant", "message": {"model": "claude-fable-5-1"}}) + "\n")
check("a /model switch away is honored", guard.guard_text(prompt("s3", transcript)) is None)
with open(transcript, "a") as handle:
    handle.write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-5-5"}}) + "\n")
    handle.write(json.dumps({"type": "user", "message": {"content": '{"model":"claude-fable-5-1"}'}}) + "\n")
    handle.write(json.dumps({"type": "assistant", "isSidechain": True, "message": {"model": "claude-fable-5-1"}}) + "\n")
    handle.write('not json {"model":"claude-fable-5-1"}\n')
check("a model string in user/tool/sidechain content cannot disarm", guard.guard_text(prompt("s3", transcript)) is not None)

# MODEL_GUARD_TAIL_KB — how far back the model is read. An assistant `model` line near the top,
# then > 1 KB of non-assistant padding, so a 1 KB tail can't reach the line above it.
far = os.path.join(tmp, "far.jsonl")
with open(far, "w") as handle:
    handle.write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-5-5"}}) + "\n")
    for _ in range(40):
        handle.write(json.dumps({"type": "user", "message": {"content": "x" * 40}}) + "\n")
check("tail knob: the default 512 KB window reads a model past 1 KB", guard.transcript_model(far) == "claude-opus-5-5")
os.environ["MODEL_GUARD_TAIL_KB"] = "1"
check("tail knob: a 1 KB tail hides a model beyond the window", guard.transcript_model(far) is None)
near = os.path.join(tmp, "near.jsonl")
with open(near, "w") as handle:
    for _ in range(40):
        handle.write(json.dumps({"type": "user", "message": {"content": "x" * 40}}) + "\n")
    handle.write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-5-5"}}) + "\n")
check("tail knob: a model inside the 1 KB tail is still read", guard.transcript_model(near) == "claude-opus-5-5")
os.environ["MODEL_GUARD_TAIL_KB"] = "garbage"
check("tail knob: a malformed value falls back to the default window", guard.transcript_model(far) == "claude-opus-5-5")
del os.environ["MODEL_GUARD_TAIL_KB"]

os.environ["MODEL_GUARD_MATCH"] = "sonnet, haiku-5"
check("MODEL_GUARD_MATCH: listed model injects", guard.guard_text(start("s4", "claude-haiku-5-5")) is not None)
check("MODEL_GUARD_MATCH: opus no longer matches", guard.guard_text(start("s5", "claude-opus-5-5")) is None)
del os.environ["MODEL_GUARD_MATCH"]

os.makedirs(os.path.join(tmp, ".agent"), exist_ok=True)
with open(os.path.join(tmp, ".agent", "model-guard.md"), "w") as handle:
    handle.write("custom {{MODEL}} text\n")
check("project override wins", guard.guard_text(start("s6", "claude-opus-5-5")) == "custom claude-opus-5-5 text")
with open(os.path.join(tmp, ".agent", "model-guard.md"), "w") as handle:
    handle.write("  \n")
text = guard.guard_text(start("s6b", "claude-opus-5-5"))
check("an empty override is loud, not silent", text is not None and "DISARMED" in text)
os.remove(os.path.join(tmp, ".agent", "model-guard.md"))
os.environ["MODEL_GUARD_FILE"] = "missing.md"
text = guard.guard_text(start("s7", "claude-opus-5-5"))
check("a missing explicit override is loud, not silent", text is not None and "DISARMED" in text)
del os.environ["MODEL_GUARD_FILE"]

os.environ["MODEL_GUARD_OFF"] = "1"
check("MODEL_GUARD_OFF silences", guard.guard_text(start("s8", "claude-opus-5-5")) is None)
del os.environ["MODEL_GUARD_OFF"]

code, out, _ = invoke(hook("hooks/model-guard.py"), start("s9", "claude-opus-5-5"),
                      env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": "/nonexistent-project"})
check("end-to-end: exit 0 + text on stdout", code == 0 and "TRUST GUARD" in out)
code, out, _ = invoke(hook("hooks/model-guard.py"), start("s10", "claude-fable-5-1"), env={"TMPDIR": tmp})
check("end-to-end: exit 0 + silent on a trusted model", code == 0 and out.strip() == "")
code, out, _ = invoke(hook("hooks/model-guard.py"), {}, env={"TMPDIR": tmp})
check("empty payload fails open", code == 0 and out.strip() == "")

sys.exit(check.done())
