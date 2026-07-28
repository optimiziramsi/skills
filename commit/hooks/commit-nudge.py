#!/usr/bin/env python3
"""Stop — nudge to commit uncommitted work (the commit skill's "commit as you go" cadence).

Fires ONCE per distinct dirty state, only for sessions that actually wrote files, and never
while stop_hook_active (which would loop).

Off: STOP_NUDGE_OFF=1
Opt-in: COMMIT_NUDGE_EXTRA_DIRS=../gitops,../infra also flags dirty SIBLING trees the current
repo cannot see — folded into both the nudge and the one-shot state.
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402


def dirty_siblings(project):
    """["<dir> (N dirty)"] for each non-clean COMMIT_NUDGE_EXTRA_DIRS entry. Unset → [].

    Relative entries resolve against the PROJECT dir (`../gitops` means a sibling of the repo,
    not of wherever the hook happened to be invoked from).
    """
    out = []
    for raw in (os.environ.get("COMMIT_NUDGE_EXTRA_DIRS") or "").split(","):
        directory = raw.strip()
        if not directory:
            continue
        status = hookio.git(os.path.join(project, directory), "status", "--porcelain")
        if status:
            out.append(f"{directory} ({len(status.splitlines())} dirty)")
    return out


def main():
    if hookio.flag("STOP_NUDGE_OFF"):
        return
    data = hookio.payload()
    if data.get("stop_hook_active"):
        return                                       # never re-block a continuation we caused
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    status = hookio.git(project, "status", "--porcelain") or ""
    siblings = dirty_siblings(project)
    if not status and not siblings:
        return
    if not hookio.wrote_files(data.get("transcript_path")):
        return                                       # read-only / chat session — nothing to commit
    # one-shot per distinct state (this tree + siblings), so a stop that changes nothing is silent
    if not hookio.first_time("commit-nudge", data.get("session_id"),
                             "\n".join([status, *siblings])):
        return

    parts = []
    if status:
        parts.append(f"{len(status.splitlines())} uncommitted change(s) here")
    if siblings:
        parts.append("dirty sibling tree(s): " + ", ".join(siblings))
    reason = ("[commit-nudge] " + "; ".join(parts) + ". Commit as you go (single-line message, "
              "per the commit skill), or say in one line why these stay uncommitted — then finish.")
    if os.path.isfile(os.path.join(project, ".agent", "handoff.md")):
        reason += " If the session is winding down, also refresh the handoff (/handoff)."
    print(reason, file=sys.stderr)
    sys.exit(2)


hookio.guard(main)
