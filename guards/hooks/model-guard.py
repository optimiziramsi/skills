#!/usr/bin/env python3
"""SessionStart + UserPromptSubmit — re-inject a trust reminder while the session runs on a model
the project does not trust to follow instructions in full (default: Opus 5.5).

The model is read from the SessionStart payload (the only hook payload that carries it) and cached
per session; a later prompt re-reads the transcript's last assistant `model`, so a mid-session
`/model` switch is honored. Text: $MODEL_GUARD_FILE → .agent/model-guard.md → .claude/model-guard.md
→ the shipped hooks/model-guard.txt (`{{MODEL}}` = the matched model id).

Config: MODEL_GUARD_MATCH (comma-separated substrings of the model id; default `opus-5-5`)
Off: MODEL_GUARD_OFF=1
"""
import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402

SHIPPED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model-guard.txt")
TAIL_BYTES = 512 * 1024


def marker(session_id):
    return os.path.join(tempfile.gettempdir(), f"optimiziramsi-model-{session_id or 'unknown'}")


def transcript_model(path):
    """The last main-thread assistant entry's `message.model` in the transcript's tail, or None.

    Parsed as JSON lines, not grepped: a `"model":"…"` string inside a tool result or a pasted
    document must not be able to re-label the session and switch the guard off.
    """
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - TAIL_BYTES))
            lines = handle.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        model = (entry.get("message") or {}).get("model")
        if isinstance(model, str) and model:
            return model
    return None


def session_model(data):
    """payload.model (SessionStart) → the transcript's last model → the per-session cache."""
    path = marker(data.get("session_id"))
    model = data.get("model") or transcript_model(data.get("transcript_path"))
    if model:
        try:
            with open(path, "w") as handle:
                handle.write(model)
        except OSError:
            pass
        return model
    try:
        with open(path) as handle:
            return handle.read().strip() or None
    except OSError:
        return None


def matches(model):
    wanted = [p.strip().lower() for p in hookio.setting("MODEL_GUARD_MATCH", "opus-5-5").split(",")]
    return any(p and p in model.lower() for p in wanted)


def guard_text(data):
    """The reminder to inject for this payload, or None when the model is trusted / unknown."""
    if hookio.flag("MODEL_GUARD_OFF"):
        return None
    model = session_model(data)
    if not model or not matches(model):
        return None
    text, warning = hookio.override_text(
        "MODEL_GUARD_FILE", (".agent/model-guard.md", ".claude/model-guard.md"),
        SHIPPED, hookio.project_dir(data))
    if warning:
        return f"⚠️ model-guard DISARMED — {warning}."
    if not text.strip():
        return "⚠️ model-guard DISARMED — the override file is empty."
    return hookio.render(text.rstrip(), {"MODEL": model})


def main():
    text = guard_text(hookio.payload())
    if text:
        print(text)


if __name__ == "__main__":
    hookio.guard(main)
