"""Shared logic for the code-first hooks and the `code-first` CLI (imported by path, not shipped as a hook).

Everything resolves from env (the settings.json `env` block, read from the hook's own process env)
and from git — so the injected text, the Stop guard, the stale-idea nudge, and `/idea` agree.
"""
import json
import os
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402

SHIPPED_CONTRACT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code-first-reminder.txt")
CONTRACT_CANDIDATES = (".agent/code-first.md", ".claude/code-first.md")

DEFAULT_ALLOW = r"\b(prompt|paste|inline|snippet|command)s?\b"
DEFAULT_EXEMPT_LANGS = "bash,sh,zsh,shell,console"


def off():
    return hookio.flag("CODE_FIRST_OFF")


def prefix():
    return hookio.setting("CODE_FIRST_BRANCH_PREFIX", "idea/") or "idea/"


def commit_tag():
    return hookio.setting("CODE_FIRST_COMMIT_TAG", "IDEA") or "IDEA"


def surface():
    return hookio.setting("CODE_FIRST_REVIEW_SURFACE", "my IDE") or "my IDE"


def resolve_base(cwd=None):
    """(base, problem). CODE_FIRST_BASE_BRANCH → GIT_GUARD_INTEGRATION_BRANCH → the repo default.

    An explicit CODE_FIRST_BASE_BRANCH is the project's own decision and is trusted as given. A
    DERIVED base that is a protected branch is refused (problem set): ideas are cut from the
    integration branch, and guessing the protected one is exactly the mistake to stop and ask on.
    """
    explicit = hookio.setting("CODE_FIRST_BASE_BRANCH", "").strip()
    if explicit:
        return explicit, None
    base = hookio.integration_branch() or hookio.default_branch(cwd)
    if not base:
        return None, "no base branch resolves here (not a git repo, or no branches yet)"
    if base in hookio.protected_branches(cwd):
        return base, (f"the resolved base `{base}` is a protected branch — set CODE_FIRST_BASE_BRANCH "
                      "(or GIT_GUARD_INTEGRATION_BRANCH) to the integration branch")
    return base, None


def contract(project):
    """(text, warning) — the injected code-first contract, placeholders rendered."""
    text, warning = hookio.override_text("CODE_FIRST_CONTRACT_FILE", CONTRACT_CANDIDATES,
                                         SHIPPED_CONTRACT, project)
    if warning:
        return None, warning
    base, problem = resolve_base(project)
    shown_base = base if base and not problem else "<ask the user: no safe base branch is set>"
    return hookio.render(text, {"BASE": shown_base, "PREFIX": prefix(), "SURFACE": surface(),
                                "TAG": commit_tag()}).rstrip(), None


def idea_branches(cwd=None, now=None):
    """[(branch, age_days, subject)] for local branches under the idea prefix, oldest first."""
    pfx = prefix().rstrip("/")
    out = hookio.git(cwd, "for-each-ref", "--sort=committerdate",
                     "--format=%(refname:short)%09%(committerdate:unix)%09%(subject)", f"refs/heads/{pfx}/")
    now = now or time.time()
    rows = []
    for line in (out or "").splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 2 or not parts[1].isdigit():
            continue
        rows.append((parts[0], int((now - int(parts[1])) // 86400), parts[2] if len(parts) > 2 else ""))
    return rows


def stale_days():
    """CODE_FIRST_STALE_DAYS (default 7); None when set empty — the nudge is off."""
    raw = hookio.setting("CODE_FIRST_STALE_DAYS", "7")
    if not str(raw).strip():
        return None
    try:
        return max(0, int(raw))
    except ValueError:
        return 7


# ── the Stop guard's view of the turn ──────────────────────────────────────────

FENCE = re.compile(r"^```([^\n`]*)\n(.*?)^```", re.M | re.S)


def counted_fence_lines(text, exempt=None):
    """Lines inside fenced blocks, summed — fences in an exempt language don't count."""
    if exempt is None:
        exempt = {l.strip().lower() for l in
                  hookio.setting("CODE_FIRST_EXEMPT_LANGS", DEFAULT_EXEMPT_LANGS).split(",") if l.strip()}
    total = 0
    for lang, body in FENCE.findall(text or ""):
        tag = (lang.strip().split() or [""])[0].lower()
        if tag in exempt:
            continue
        total += len([l for l in body.splitlines() if l.strip()])
    return total


def max_fence_lines():
    return max(0, hookio.setting_int("CODE_FIRST_MAX_FENCE_LINES", 5))


def allow_pattern():
    raw = hookio.setting("CODE_FIRST_ALLOW_PATTERN", "") or DEFAULT_ALLOW
    try:
        return re.compile(raw, re.I)
    except re.error:
        return re.compile(DEFAULT_ALLOW, re.I)


def _text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
            return None
        return "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
    return None


def last_turn(transcript):
    """(last real user prompt, final assistant text) from the transcript JSONL — (None, None) on any failure."""
    prompt = final = None
    try:
        with open(transcript, encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                kind = entry.get("type")
                if kind == "user" and not entry.get("isMeta"):
                    text = _text_of((entry.get("message") or {}).get("content"))
                    if text and text.strip():
                        prompt, final = text, None
                elif kind == "assistant":
                    text = _text_of((entry.get("message") or {}).get("content"))
                    if text and text.strip():
                        final = text
    except (OSError, TypeError):
        return None, None
    return prompt, final
