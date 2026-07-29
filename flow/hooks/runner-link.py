#!/usr/bin/env python3
"""SessionStart — keep the flow runner links aimed at the plugin version that is loaded.

`.agent/bin/loop` and `.agent/bin/grind` are per-user symlinks: machine-local, gitignored,
never committed. They do not point into the versioned plugin cache directly — they hop
through ONE stable path, `<claude-config>/plugins/data/optimiziramsi-skills/current`, which this
hook re-stamps to the running plugin on every session start. A plugin update therefore moves every
repo's runner links at once, and nothing on disk encodes a version.

The hook resolves that version from its OWN location, not from $CLAUDE_PLUGIN_ROOT: the file
executing IS the active plugin, which is the only answer that cannot be stale.

Why not `${CLAUDE_PLUGIN_DATA}` (Claude Code's own per-plugin data dir): its name carries the
install identity — `optimiziramsi-skills-<marketplace>` — so it moves when the plugin is installed
from a differently-named marketplace or inline. A pointer every repo hardcodes has to be one
address for all install shapes, so it uses the plugin's bare name inside that same `data/` dir.

Creates nothing. The `looper` / `grind` / `scaffold` skills make the links when the user asks
for them; this only refreshes what is already there, and only when it is a symlink.

Off: FLOW_LINK_OFF=1
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import hookio  # noqa: E402

TOOLS = ("loop", "grind")


def pointer_path():
    """`<claude-config>/plugins/data/optimiziramsi-skills/current` — one address, every repo."""
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(config, "plugins", "data", "optimiziramsi-skills", "current")


def relink(link, target):
    """Aim `link` at `target`, atomically. Returns True when it actually moved.

    Compares the literal target string, not the resolved path: a hand-made link straight into
    today's version cache resolves to the same file yet is exactly the stale-tomorrow shape
    this hook exists to replace. Refuses to touch a path that exists as anything other than a
    symlink — a real file there is someone's own work, not ours to eat.
    """
    if os.path.lexists(link) and not os.path.islink(link):
        return False
    if os.path.islink(link) and os.readlink(link) == target:
        return False
    os.makedirs(os.path.dirname(link), exist_ok=True)
    tmp = link + ".tmp"
    if os.path.lexists(tmp):
        os.remove(tmp)
    os.symlink(target, tmp)
    os.replace(tmp, link)
    return True


def main():
    if hookio.flag("FLOW_LINK_OFF"):
        return
    root = str(pathlib.Path(__file__).resolve().parents[2])
    pointer = pointer_path()
    moved = relink(pointer, root)

    # Existing repo links follow the pointer, so they only ever need fixing when they were
    # made by hand (or by an older plugin) against a versioned path.
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    for tool in TOOLS:
        link = os.path.join(project, ".agent", "bin", tool)
        if os.path.islink(link):
            relink(link, os.path.join(pointer, "flow", "bin", tool))

    if moved:
        print(f"[flow] runner links now resolve to {root}")


hookio.guard(main)
