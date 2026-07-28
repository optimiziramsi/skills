#!/usr/bin/env python3
"""Stop hook — enforce the output contract on the turn's final assistant message.

Reads the hook payload from stdin, pulls the last assistant text message out of the
transcript JSONL, and blocks the stop (forcing a compact rewrite) when the message
violates the contract: process narration, headers, tables, or gross over-length.
Blocks at most once per turn — stop_hook_active guards the re-entry loop.

Config: REPORT_GUARD_MAX_LINES (default 18) · escape hatch REPORT_GUARD_OFF=1
Tests: python3 reporting/tests/test_reporting.py
"""
import json
import os
import re
import sys

BANNED = [
    (r"\blet me (check|look|start|see|first|try|run|dig|inspect|examine|verify|fix|now)\b",
     'process narration ("Let me check/look/…")'),
    (r"\bnow i(?:'| wi)ll\b", 'process narration ("Now I\'ll …")'),
    (r"\bi(?:'| wi)ll (start|begin|now|first)\b", 'process narration ("I\'ll start …")'),
    (r"\bi'm going to\b", 'process narration ("I\'m going to …")'),
    (r"^\s*(first|next|then),? i(?:'| wi)ll\b", "step-by-step narration"),
]


def max_lines():
    try:
        return int(os.environ.get("REPORT_GUARD_MAX_LINES", "18"))
    except ValueError:
        return 18


def final_assistant_text(path):
    last = None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                content = (entry.get("message") or {}).get("content") or []
                texts = [c.get("text", "") for c in content
                         if isinstance(c, dict) and c.get("type") == "text"]
                joined = "\n".join(t for t in texts if t.strip())
                if joined.strip():
                    last = joined
    except OSError:
        return None
    return last


def violations(text):
    stripped = re.sub(r"```.*?```", "", text, flags=re.S)  # fenced code is exempt from shape checks
    problems = []
    for pattern, label in BANNED:
        if re.search(pattern, stripped, flags=re.I | re.M):
            problems.append(label)
    lines = [l for l in stripped.splitlines() if l.strip()]
    if len(lines) > max_lines():
        problems.append(f"{len(lines)} non-empty lines (contract: 1 outcome line + <=5 bullets + Q list)")
    if any(re.match(r"\s*#{1,6}\s", l) for l in lines):
        problems.append("markdown headers")
    if sum(1 for l in lines if l.lstrip().startswith("|")) >= 2:
        problems.append("a table")
    return problems


def main():
    if os.environ.get("REPORT_GUARD_OFF") == "1":
        return
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    if data.get("stop_hook_active"):
        return
    text = final_assistant_text(data.get("transcript_path", ""))
    if not text:
        return
    problems = violations(text)
    if problems:
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Final message violates the output contract: " + "; ".join(problems)
                + ". Rewrite the report now as exactly: one outcome line, <=5 terse fact bullets, "
                  "then a numbered 'Q:' list (omit if none). No headers, tables, prose paragraphs, "
                  "or narration. Do not run tools — just restate the report in that shape."
            ),
        }))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        pass
