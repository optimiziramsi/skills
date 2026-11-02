"""Shared logic for the reporting hooks and the `calibrate` CLI (imported by path, not shipped as a hook).

The injected contract, its mid-turn pulse, and /calibrate must agree on which text is in force, how
its `· rc:` / `· stable:` stamp reads, and what the turn's reports were — so it lives here once.
"""
import datetime
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402

SHIPPED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brevity-reminder.txt")
CONTRACT_CANDIDATES = (".agent/output-contract.md", ".claude/output-contract.md")
ENV = "REPORT_CONTRACT_FILE"


def active(project):
    """(text, warning) — the contract in force: $REPORT_CONTRACT_FILE → .agent → .claude → shipped."""
    return hookio.override_text(ENV, CONTRACT_CANDIDATES, SHIPPED, project)


def active_source(project):
    """The path of the override in force, or None when the shipped text is what's active."""
    explicit = os.environ.get(ENV, "").strip()
    chain = [explicit if os.path.isabs(explicit) else os.path.join(project, explicit)] if explicit else []
    chain += [os.path.join(project, c) for c in CONTRACT_CANDIDATES]
    for path in chain:
        if os.path.exists(path):
            return path
    return None


def rc_days():
    """REPORT_RC_DAYS (default 7) — how stale an `rc:` contract gets before the nudge fires."""
    return hookio.setting_int("REPORT_RC_DAYS", 7)


# ── the `· rc:` / `· stable:` stamp on the first line ────────────────────────────

_STAMP = re.compile(r"·\s*(rc|stable):\s*(\d{4}-\d{2}-\d{2})(?:\s+v(\d+))?", re.I)


def first_line(text):
    """The first non-empty, stripped line of `text` — '' when there is none."""
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def parse_stamp(text):
    """{'kind','date','version'} from the first line's `· rc: DATE vN` / `· stable: DATE`, or None."""
    m = _STAMP.search(first_line(text))
    if not m:
        return None
    return {"kind": m.group(1).lower(), "date": m.group(2),
            "version": int(m.group(3)) if m.group(3) else None}


def days_since(date_str, today=None):
    """Whole days from an ISO date to `today` (default: today). None when the date won't parse."""
    try:
        then = datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None
    return ((today or datetime.date.today()) - then).days


def rc_nudge(text, threshold, today=None):
    """One advisory line when the active contract is `rc:` and older than `threshold` days, else None."""
    stamp = parse_stamp(text)
    if not stamp or stamp["kind"] != "rc":
        return None
    age = days_since(stamp["date"], today)
    if age is None or age < threshold:
        return None
    return f"contract is rc since {stamp['date']} ({age} d) — run /calibrate to confirm or edit"


# ── the mid-turn pulse's one line ────────────────────────────────────────────────

def pulse_line(text):
    """The active contract's first meaningful line — the `=== … ===` frame and the stamp stripped."""
    line = re.sub(r"^=+\s*|\s*=+$", "", first_line(text)).strip()
    return _STAMP.sub("", line).rstrip(" ·").strip()


# ── the turn's reports, from the transcript JSONL ────────────────────────────────

def _text_of(content):
    """The plain text of a message's content — '' for a tool_result-only (no text) message."""
    if isinstance(content, list):
        parts = [c.get("text", "") for c in content
                 if isinstance(c, dict) and c.get("type") == "text"]
        return "\n".join(p for p in parts if p.strip())
    return content if isinstance(content, str) else ""


def turn_finals(path):
    """Each completed turn's final assistant text, oldest-first — a real user prompt closes a turn.

    Generalises report-guard's `final_assistant_text` (the last one) so /calibrate can read the last
    N. Tool-result messages carry no text, so they never falsely close a turn.
    """
    finals, final = [], None
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                kind = entry.get("type")
                if kind == "user" and not entry.get("isMeta"):
                    if _text_of((entry.get("message") or {}).get("content")).strip():
                        if final is not None:
                            finals.append(final)
                        final = None
                elif kind == "assistant":
                    text = _text_of((entry.get("message") or {}).get("content"))
                    if text.strip():
                        final = text
    except (OSError, TypeError):
        return []
    if final is not None:
        finals.append(final)
    return finals
