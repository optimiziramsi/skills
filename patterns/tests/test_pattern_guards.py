#!/usr/bin/env python3
"""Self-tests for pattern-guards. Run: python3 patterns/tests/test_pattern_guards.py

Driven end to end through the hook process, because the auto-regen path shells out to its
real sibling generator — mocking that would test the mock.
"""
import json
import os
import pathlib
import shutil
import sys
import tempfile
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, invoke, load_module  # noqa: E402

check = Check()
GUARD = hook("patterns/hooks/pattern-guards.py")
TSV_NAME = load_module(GUARD, "pattern_guards").TSV_NAME

REGISTRY = (
    "# test\n"
    "src/server/reactors/**\t.agent/patterns/server-projection.md\tblessed\tedit\n"
    "packages/*/src/**/*.ts\t.agent/patterns/universal-satisfies.md\tblessed\tland\n"
    "apps/web/forms/**\t.agent/patterns/apps-web-form-handling.md\tTODO\tedit\n"
    "src/server/reactors/**\t.agent/patterns/server-stream-fifo.md\tdecided\tedit\n"
)
S1, S2, S3 = (f"test-{uuid.uuid4().hex[:8]}" for _ in range(3))

roots = []
try:
    def scratch(prefix):
        root = tempfile.mkdtemp(prefix=prefix)
        roots.append(root)
        registry = os.path.join(root, ".agent", "patterns")
        os.makedirs(registry)
        return root, registry

    root, registry = scratch("pattern-guards-")
    pathlib.Path(registry, TSV_NAME).write_text(REGISTRY)

    def call(event, file_path, session=S1, project=None, env=None):
        project = project or root
        return invoke(GUARD, {"hook_event_name": event, "session_id": session, "cwd": project,
                              "tool_input": {"file_path": os.path.join(project, file_path)}},
                      env={"CLAUDE_PROJECT_DIR": project, **(env or {})})

    # ── the edit gate ──────────────────────────────────────────────────────
    rc, _, err = call("PreToolUse", "apps/web/forms/login.tsx")
    check("a TODO-only governed path is blocked", rc == 2, err)
    check("the block cites the pattern", "apps-web-form-handling" in err, err)
    check("blessed coverage beats a decided overlap",
          call("PreToolUse", "src/server/reactors/update-x.ts")[0] == 0)
    check("an unmatched path is allowed", call("PreToolUse", "README.md")[0] == 0)

    # ── the once-per-session reminder ──────────────────────────────────────
    rc, out, _ = call("PostToolUse", "src/server/reactors/update-x.ts", S2)
    check("the first edit emits pattern context", "pattern-route" in out, out)
    check("the reminder names the scoped pattern", "server-projection" in out, out)
    check("the reminder omits a land-routed pattern", "universal-satisfies" not in out, out)
    check("the reminder warns about a decided overlap",
          "STOP-warning" in out and "stream-fifo" in out, out)
    check("a second edit in the same session is silent",
          call("PostToolUse", "src/server/reactors/other.ts", S2)[1].strip() == "")
    check("a land-only match stays silent",
          call("PostToolUse", "src/server/services/foo.ts", S3)[1].strip() == "")

    # ── auto-regen of the routing TSV ──────────────────────────────────────
    pathlib.Path(registry, "x-new.md").write_text(
        '---\nstatus: blessed\npaths:\n  - "packages/x/**"\n---\nbody\n')
    rc, out, _ = call("PostToolUse", ".agent/patterns/x-new.md", S3)
    check("a pattern write regenerates the TSV", "auto-regenerated" in out, out)
    check("the regenerated TSV carries the new glob",
          "packages/x/**" in pathlib.Path(registry, TSV_NAME).read_text())
    check("an unchanged rewrite stays silent",
          call("PostToolUse", ".agent/patterns/x-new.md", S3)[1].strip() == "")
    rc, out, _ = call("PreToolUse", ".agent/patterns/x-new.md", S3)
    check("PreToolUse never regenerates", rc == 0 and out.strip() == "", out)

    pathlib.Path(registry, "y-new.md").write_text(
        '---\nstatus: blessed\npaths:\n  - "packages/y/**"\n---\nbody\n')
    rc, out, _ = call("PostToolUse", ".agent/patterns/y-new.md", S3,
                      env={"PATTERN_REGISTRY_DIR": ".agent/patterns/"})
    check("a trailing-slash registry dir still triggers regen", "auto-regenerated" in out, out)

    # ── projects without a registry ────────────────────────────────────────
    bare = tempfile.mkdtemp(prefix="pattern-guards-bare-")
    roots.append(bare)
    rc, out, _ = call("PreToolUse", "src/app.ts", S3, project=bare)
    check("no registry at all → silent no-op, not a DISARMED banner",
          rc == 0 and out.strip() == "", out)

    # registry dir present but the TSV missing → one regen attempt restores gating
    root2, registry2 = scratch("pattern-guards-regen-")
    pathlib.Path(registry2, "z.md").write_text(
        '---\nstatus: TODO\npaths:\n  - "apps/z/**"\n---\nbody\n')
    rc, _, err = call("PreToolUse", "apps/z/main.ts", S3, project=root2)
    check("a missing TSV is regenerated and gating resumes", rc == 2 and "z.md" in err, err)
    check("the TSV was written", os.path.isfile(os.path.join(registry2, TSV_NAME)))

    # ── fail-open ──────────────────────────────────────────────────────────
    check("garbage stdin allows the call", invoke(
        GUARD, None, env={"CLAUDE_PROJECT_DIR": root})[0] == 0)
    check("PATTERN_GUARDS_OFF allows the call",
          call("PreToolUse", "apps/web/forms/login.tsx", env={"PATTERN_GUARDS_OFF": "1"})[0] == 0)
finally:
    for path in roots:
        shutil.rmtree(path, ignore_errors=True)

sys.exit(check.done())
