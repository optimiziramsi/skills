#!/usr/bin/env python3
"""Surface instruction-surface cap breaches, so the caps the docs DESCRIBE get enforced.

  SessionStart  list the current breaches as context (informational, every start/resume/clear)
  Stop          nudge ONCE per distinct breach-set, and only if the session wrote files, so
                bloat introduced this session is caught before the chat ends

Only paths that EXIST are checked — a safe no-op in any repo. Nothing is ever raised to make
content fit: compact instead (merge → route → tighten → retire).

Off: CAPS_GUARD_OFF=1 · every cap below is env-overridable · a project shipping
`.agent/meta-lint.json` opted into the meta-lint engine, whose caps supersede these.
"""
import glob
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

# path → env var → default char cap, over the house instruction layout
FILE_CAPS = (
    ("CLAUDE.md", "CAP_CLAUDE", 6000),
    ("AGENTS.md", "CAP_AGENTS", 6000),
    (".agent/handoff.md", "CAP_HANDOFF", 4000),
    (".agent/instructions-changelog.md", "CAP_CHANGELOG", 8000),
    (".agent/lessons/README.md", "CAP_LESSONS_INDEX", 8000),
)
# glob → env var → default char cap → basename to skip
GLOB_CAPS = (
    (".claude/skills/*/SKILL.md", "CAP_SKILL", 9000, None),
    (".claude/agents/*.md", "CAP_AGENT", 4000, None),
    (".claude/rules/*.md", "CAP_RULE", 2000, None),
    (".claude/commands/*.md", "CAP_COMMAND", 800, None),      # thin wrappers
    (".agent/lessons/*.md", "CAP_LESSON", 4000, "README.md"),
)
# glob → env var → default count budget → label
COUNT_CAPS = (
    (".claude/skills/*/", "MAX_SKILLS", 12, "skills"),
    (".claude/agents/*.md", "MAX_AGENTS", 6, "agents"),
    (".claude/rules/*.md", "MAX_RULES", 10, "rules"),
)

NUDGE = ("[caps] instruction-surface over cap — compact (merge → route → tighten → retire), "
         "don't raise the cap:")
CONTEXT = ("[caps] instruction-surface over cap — compact these when you touch them "
           "(don't just raise caps):")


def cap(env_var, default):
    try:
        return int(os.environ[env_var])
    except (KeyError, ValueError):
        return default


def breaches(project):
    """["<path> 7000c > 6000c", "14 skills > 12", …] — empty when everything fits."""
    found = []
    for rel, env_var, default in FILE_CAPS:
        path = os.path.join(project, rel)
        limit = cap(env_var, default)
        if os.path.isfile(path) and os.path.getsize(path) > limit:
            found.append(f"{rel} {os.path.getsize(path)}c > {limit}c")
    for pattern, env_var, default, skip in GLOB_CAPS:
        limit = cap(env_var, default)
        for path in sorted(glob.glob(os.path.join(project, pattern))):
            if not os.path.isfile(path) or os.path.basename(path) == skip:
                continue
            if os.path.getsize(path) > limit:
                rel = os.path.relpath(path, project)
                found.append(f"{rel} {os.path.getsize(path)}c > {limit}c")
    for pattern, env_var, default, label in COUNT_CAPS:
        limit = cap(env_var, default)
        count = len(glob.glob(os.path.join(project, pattern)))
        if count > limit:
            found.append(f"{count} {label} > {limit}")
    return found


def main():
    if hookio.flag("CAPS_GUARD_OFF"):
        return
    data = hookio.payload()
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if os.path.isfile(os.path.join(project, ".agent", "meta-lint.json")):
        return                                       # the meta-lint engine's caps supersede these
    found = breaches(project)
    if not found:
        return
    bullets = "\n".join(f"  • {b}" for b in found)

    if data.get("hook_event_name") == "Stop":
        if data.get("stop_hook_active") or not hookio.wrote_files(data.get("transcript_path")):
            return
        if not hookio.first_time("caps", data.get("session_id"), "\n".join(found)):
            return
        print(f"{NUDGE}\n{bullets}", file=sys.stderr)
        sys.exit(2)
    print(f"{CONTEXT}\n{bullets}")                   # SessionStart (or anything else) → context


hookio.guard(main)
