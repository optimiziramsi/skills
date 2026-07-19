#!/usr/bin/env python3
"""pattern-guards — deterministic pattern-registry surfacing on Write/Edit tool calls.

The pattern-gating rule and each pattern's `#### Rules — write-time checklist` only work if the
working agent actually looks at them at the moment of editing. This hook closes that memory-decay gap
with two wire-ups over the same routes table (`<registry>/pattern-routes.tsv`, generated from every
pattern's `paths:` frontmatter by generate-pattern-routes.py):

  PreToolUse(Write|Edit)  — HARD GATE: block (exit 2) when the target file is governed ONLY by
                            non-blessed pattern(s). That mechanizes the gating rule ("decided/TODO →
                            STOP, don't improvise"). If ANY blessed pattern also governs the path we
                            do NOT block (there's a blessed shape to follow); the non-blessed one is
                            surfaced as a STOP-warning through the PostToolUse reminder instead.
  PostToolUse(Write|Edit) — REMINDER: once per (pattern, session), inject additionalContext naming
                            the pattern file(s) that govern the just-edited path and telling the agent
                            to read their Rules checklists. Only `route=edit` rows remind; `route=land`
                            rows are the codebase-wide always-on rules covered by land-time review.
                            AUTO-REGEN: a write to a registry `*.md` re-runs generate-pattern-routes.py
                            so the TSV can't silently go stale; if it changed, the context reminds to
                            commit it with the pattern change.

Fail-open by design (same posture as the worktree write-guard): unparsable input, missing routes
file, any internal error → allow silently. Disable entirely with PATTERN_GUARDS_OFF=1. The registry
dir is `.agent/patterns/` by default; override with PATTERN_REGISTRY_DIR (repo-relative).

Self-test: python3 <plugin>/hooks/pattern-guards.py --test
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile

TSV_NAME = "pattern-routes.tsv"


def registry_rel() -> str:
    reg = os.environ.get("PATTERN_REGISTRY_DIR", os.path.join(".agent", "patterns"))
    return reg.rstrip("/" + os.sep)  # normalized — a trailing slash must not break path regexes


def glob_to_regex(glob: str) -> "re.Pattern[str]":
    """gitignore-ish: `**` crosses directories, `*`/`?` stay within one segment."""
    out = []
    i = 0
    while i < len(glob):
        c = glob[i]
        if c == "*":
            if glob[i : i + 2] == "**":
                out.append(".*")
                i += 2
                if i < len(glob) and glob[i] == "/":
                    i += 1  # `**/` — the `.*` already absorbs the separator
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def regen_tsv(root: str) -> None:
    import subprocess

    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate-pattern-routes.py")
    try:
        subprocess.run(
            [sys.executable, gen],
            env={**os.environ, "CLAUDE_PROJECT_DIR": root},
            capture_output=True,
            timeout=30,
        )
    except Exception:
        pass  # fail-open


def load_routes(root: str):
    path = os.path.join(root, registry_rel(), TSV_NAME)
    routes = []
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        # No routes TSV. A registry-less project is a SILENT no-op — never a DISARMED message.
        # If the registry dir exists the TSV just hasn't been generated yet: try one regen.
        if not os.path.isdir(os.path.join(root, registry_rel())):
            return []
        regen_tsv(root)
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except OSError:
            return []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 4:
            continue
        glob, pattern, status, route = parts
        routes.append((glob_to_regex(glob), glob, pattern, status, route))
    return routes


def match_patterns(routes, rel_path: str):
    """Return {pattern-file: (status, route, specificity)} for routes matching rel_path.

    Specificity = literal path segments in the matching glob (max across a pattern's globs);
    used to list the most file-specific patterns first when many match at once.
    """
    hits = {}
    for rx, glob, pattern, status, route in routes:
        if rx.match(rel_path):
            spec = sum(1 for seg in glob.split("/") if seg and "*" not in seg and "?" not in seg)
            prev = hits.get(pattern)
            if prev is None or spec > prev[2]:
                hits[pattern] = (status, route, spec)
    return hits


def state_file(session_id: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"claude-pattern-guards-{session_id or 'default'}")


def already_reminded(session_id: str):
    try:
        with open(state_file(session_id), encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except OSError:
        return set()


def mark_reminded(session_id: str, patterns) -> None:
    with open(state_file(session_id), "a", encoding="utf-8") as f:
        for p in patterns:
            f.write(p + "\n")


def relativize(file_path: str, root: str):
    ap = os.path.abspath(file_path)
    aroot = os.path.abspath(root)
    if not ap.startswith(aroot + os.sep):
        return None
    return os.path.relpath(ap, aroot)


def maybe_regen_routes(root: str, rel: str):
    """A registry-file write regenerates the routes TSV; returns a commit reminder on change."""
    if os.sep != "/":
        rel = rel.replace(os.sep, "/")
    reg = registry_rel().replace(os.sep, "/")
    if not re.match(rf"^{re.escape(reg)}/[^/]+\.md$", rel) or rel.endswith("README.md"):
        return None
    tsv = os.path.join(root, registry_rel(), TSV_NAME)
    try:
        with open(tsv, encoding="utf-8") as f:
            before = f.read()
    except OSError:
        before = ""
    try:
        regen_tsv(root)
        with open(tsv, encoding="utf-8") as f:
            after = f.read()
    except Exception:
        return None  # fail-open
    if after != before:
        return (
            f"⚙️ {TSV_NAME} auto-regenerated (this write touched `{rel}`) — commit the "
            "TSV together with the pattern change."
        )
    return None


def handle(payload: dict) -> int:
    if os.environ.get("PATTERN_GUARDS_OFF") == "1":
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        return 0
    rel = relativize(str(file_path), root)
    if rel is None:
        return 0

    event = payload.get("hook_event_name", "")
    if event == "PostToolUse":
        regen_msg = maybe_regen_routes(root, rel)
        if regen_msg:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUse", "additionalContext": regen_msg}}))
            return 0

    hits = match_patterns(load_routes(root), rel)
    if not hits:
        return 0
    blessed = {p for p, (s, _, _spec) in hits.items() if s == "blessed"}
    unblessed = {p: s for p, (s, _, _spec) in hits.items() if s != "blessed"}

    if event == "PreToolUse":
        # Mechanized gating rule: the path is governed EXCLUSIVELY by non-blessed pattern(s).
        if unblessed and not blessed:
            listing = ", ".join(f"{p} [{s}]" for p, s in sorted(unblessed.items()))
            sys.stderr.write(
                f"⛔ pattern-gate: `{rel}` is governed only by a non-blessed pattern — {listing}. "
                "Per the pattern-gating rule: STOP, don't improvise. Bless/walk the pattern via the "
                "manage-patterns skill (or get an explicit human go) before editing this area. "
                "(Set PATTERN_GUARDS_OFF=1 to disable.)"
            )
            return 2
        return 0

    if event == "PostToolUse":
        session_id = str(payload.get("session_id", "default"))
        seen = already_reminded(session_id)
        fresh_edit = sorted(
            (p for p, (s, route, _spec) in hits.items() if route == "edit" and p not in seen),
            key=lambda p: (-hits[p][2], p),  # most file-specific first
        )
        if not fresh_edit:
            return 0
        mark_reminded(session_id, fresh_edit)
        listed, rest = fresh_edit[:6], fresh_edit[6:]
        warn = [p for p in fresh_edit if p in unblessed]
        lines = []
        if warn:
            lines.append(
                "⛔ STOP-warning: non-blessed pattern(s) also govern this path — "
                + ", ".join(f"{p} [{unblessed[p]}]" for p in warn)
                + " — follow only the blessed shape; walking the non-blessed topic needs a human."
            )
        more = f" (+{len(rest)} broader: {', '.join(rest)})" if rest else ""
        lines.append(
            f"⚡ pattern-route: `{rel}` is governed by "
            + ", ".join(listed)
            + more
            + " — Read each file's `#### Rules — write-time checklist` before further edits in "
            "this area (this reminder fires once per pattern per session)."
        )
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": " ".join(lines)}}))
        return 0

    return 0


def run_tests() -> int:
    import subprocess
    import uuid

    s1, s2, s3 = (f"test-{uuid.uuid4().hex[:8]}" for _ in range(3))
    root = tempfile.mkdtemp(prefix="pattern-guards-test-")
    reg = os.path.join(root, ".agent", "patterns")
    os.makedirs(reg)
    with open(os.path.join(reg, TSV_NAME), "w") as f:
        f.write("# test\n")
        f.write("src/server/reactors/**\t.agent/patterns/server-projection.md\tblessed\tedit\n")
        f.write("packages/*/src/**/*.ts\t.agent/patterns/universal-satisfies.md\tblessed\tland\n")
        f.write("apps/web/forms/**\t.agent/patterns/apps-web-form-handling.md\tTODO\tedit\n")
        f.write("src/server/reactors/**\t.agent/patterns/server-stream-fifo.md\tdecided\tedit\n")

    env = {**os.environ, "CLAUDE_PROJECT_DIR": root}
    me = os.path.abspath(__file__)

    def invoke(event, file_path, session="", extra_env=None):
        session = session or s1
        payload = {"hook_event_name": event, "session_id": session, "cwd": root,
                   "tool_input": {"file_path": os.path.join(root, file_path)}}
        return subprocess.run([sys.executable, me], input=json.dumps(payload),
                              capture_output=True, text=True, env={**env, **(extra_env or {})})

    failures = []

    def check(name, cond, detail=""):
        if not cond:
            failures.append(f"{name}: {detail}")
        print(("ok " if cond else "FAIL ") + name)

    r = invoke("PreToolUse", "apps/web/forms/login.tsx")
    check("block: TODO-only governed path", r.returncode == 2, r.stderr)
    check("block cites the pattern", "apps-web-form-handling" in r.stderr, r.stderr)

    r = invoke("PreToolUse", "src/server/reactors/update-x.ts")
    check("allow: blessed coverage beats decided overlap", r.returncode == 0, r.stderr)

    r = invoke("PreToolUse", "README.md")
    check("allow: unmatched path", r.returncode == 0, r.stderr)

    r = invoke("PostToolUse", "src/server/reactors/update-x.ts", s2)
    check("remind: first edit emits context", "pattern-route" in r.stdout, r.stdout)
    check("remind includes scoped pattern", "server-projection" in r.stdout, r.stdout)
    check("remind excludes land-routed pattern", "universal-satisfies" not in r.stdout, r.stdout)
    check("remind warns on decided overlap", "STOP-warning" in r.stdout and "stream-fifo" in r.stdout, r.stdout)

    r = invoke("PostToolUse", "src/server/reactors/other.ts", s2)
    check("remind: second edit same session is silent", r.stdout.strip() == "", r.stdout)

    r = invoke("PostToolUse", "src/server/services/foo.ts", s3)
    check("remind: land-only match stays silent", r.stdout.strip() == "", r.stdout)

    # auto-regen: a registry-file write regenerates the TSV (generator is this hook's real sibling)
    with open(os.path.join(reg, "x-new.md"), "w") as f:
        f.write('---\nstatus: blessed\npaths:\n  - "packages/x/**"\n---\nbody\n')
    r = invoke("PostToolUse", ".agent/patterns/x-new.md", s3)
    check("regen: pattern write regenerates TSV", "auto-regenerated" in r.stdout, r.stdout)
    with open(os.path.join(reg, TSV_NAME)) as f:
        check("regen: TSV now carries the new glob", "packages/x/**" in f.read(), "")
    r = invoke("PostToolUse", ".agent/patterns/x-new.md", s3)
    check("regen: unchanged rewrite stays silent", r.stdout.strip() == "", r.stdout)
    r = invoke("PreToolUse", ".agent/patterns/x-new.md", s3)
    check("regen: PreToolUse never regenerates", r.returncode == 0 and r.stdout.strip() == "", r.stdout)

    # trailing-slash PATTERN_REGISTRY_DIR must not break the regen-trigger regex
    with open(os.path.join(reg, "y-new.md"), "w") as f:
        f.write('---\nstatus: blessed\npaths:\n  - "packages/y/**"\n---\nbody\n')
    r = invoke("PostToolUse", ".agent/patterns/y-new.md", s3,
               extra_env={"PATTERN_REGISTRY_DIR": ".agent/patterns/"})
    check("regen: trailing-slash registry dir still triggers", "auto-regenerated" in r.stdout, r.stdout)

    # registry-less project: no registry dir at all → SILENT no-op (no DISARMED spam)
    bare = tempfile.mkdtemp(prefix="pattern-guards-bare-")
    payload = {"hook_event_name": "PreToolUse", "session_id": s3, "cwd": bare,
               "tool_input": {"file_path": os.path.join(bare, "src/app.ts")}}
    r = subprocess.run([sys.executable, me], input=json.dumps(payload), capture_output=True,
                       text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": bare})
    check("no registry: silent no-op (no DISARMED)",
          r.returncode == 0 and r.stdout.strip() == "", r.stdout)

    # registry dir present but TSV missing → one regen attempt restores gating
    root2 = tempfile.mkdtemp(prefix="pattern-guards-regen-")
    reg2 = os.path.join(root2, ".agent", "patterns")
    os.makedirs(reg2)
    with open(os.path.join(reg2, "z.md"), "w") as f:
        f.write('---\nstatus: TODO\npaths:\n  - "apps/z/**"\n---\nbody\n')
    payload = {"hook_event_name": "PreToolUse", "session_id": s3, "cwd": root2,
               "tool_input": {"file_path": os.path.join(root2, "apps/z/main.ts")}}
    r = subprocess.run([sys.executable, me], input=json.dumps(payload), capture_output=True,
                       text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": root2})
    check("missing TSV: regen attempt restores gating", r.returncode == 2 and "z.md" in r.stderr, r.stderr)
    check("missing TSV: TSV generated", os.path.isfile(os.path.join(reg2, TSV_NAME)), "")

    r = subprocess.run([sys.executable, me], input="not json", capture_output=True, text=True, env=env)
    check("fail-open: garbage stdin allows", r.returncode == 0, r.stderr)

    r = subprocess.run([sys.executable, me], input=json.dumps({"hook_event_name": "PreToolUse",
        "tool_input": {"file_path": os.path.join(root, "apps/web/forms/login.tsx")}}),
        capture_output=True, text=True, env={**env, "PATTERN_GUARDS_OFF": "1"})
    check("escape hatch: PATTERN_GUARDS_OFF allows", r.returncode == 0, r.stderr)

    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


def disarmed(reason: str) -> int:
    print(json.dumps({"systemMessage": f"⚠️ pattern-guards DISARMED ({reason}) — gate/reminder not applied to this call."}))
    return 0


def main() -> int:
    if "--test" in sys.argv:
        return run_tests()
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return disarmed("unparsable hook input")
    try:
        return handle(payload)
    except Exception as e:
        return disarmed(f"internal error: {type(e).__name__}")


if __name__ == "__main__":
    sys.exit(main())
