"""Shared logic for the upkeep hook and the `upkeep` CLI: what's installed here, what's available.

Reads Claude Code's own plugin records under <claude-config>/plugins/ — installed_plugins.json
(what is installed, at which scope, which version), known_marketplaces.json (where each
marketplace's copy lives) and each marketplace's manifest + plugin manifests. Nothing here
contacts the network; the background refresh (`claude plugin marketplace update`) is what moves
those copies forward, and it is throttled.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import hookio  # noqa: E402


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def _json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def data_dir():
    return os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(config_dir(), "plugins", "data", "upkeep")


def installs(project):
    """[{id, name, marketplace, scope, version}] installed for `project` (user scope, or a
    project/local row whose projectPath is this project)."""
    blob = _json(os.path.join(config_dir(), "plugins", "installed_plugins.json")) or {}
    here = os.path.realpath(project)
    rows = []
    for pid, entries in (blob.get("plugins") or {}).items():
        if "@" not in pid:
            continue
        name, market = pid.rsplit("@", 1)
        for e in entries or []:
            scope = e.get("scope")
            if scope == "user" or (e.get("projectPath") and os.path.realpath(e["projectPath"]) == here):
                rows.append({"id": pid, "name": name, "marketplace": market, "scope": scope,
                             "version": e.get("version") or "unknown"})
    return rows


def marketplace_plugins(market):
    """{name: {version, description}} offered by a registered marketplace, from its local copy."""
    known = _json(os.path.join(config_dir(), "plugins", "known_marketplaces.json")) or {}
    loc = (known.get(market) or {}).get("installLocation")
    manifest = _json(os.path.join(loc, ".claude-plugin", "marketplace.json")) if loc else None
    out = {}
    for entry in (manifest or {}).get("plugins") or []:
        name, version = entry.get("name"), entry.get("version")
        source = entry.get("source")
        if not version and isinstance(source, str) and source.startswith("."):
            pj = _json(os.path.join(loc, source, ".claude-plugin", "plugin.json")) or {}
            version = pj.get("version")
        if name:
            out[name] = {"version": version, "description": entry.get("description", "")}
    return out


def watched(rows):
    """Marketplaces worth watching: those this project already installs from, narrowed by
    UPKEEP_MARKETPLACES (comma-separated) when set."""
    only = {m.strip() for m in hookio.setting("UPKEEP_MARKETPLACES", "").split(",") if m.strip()}
    markets = sorted({r["marketplace"] for r in rows})
    return [m for m in markets if not only or m in only]


def _seen_path():
    return os.path.join(data_dir(), "seen.json")


def report(project, remember=True):
    """{"updates": [(id, scope, installed, available)], "new": [(marketplace, name, description)]}.

    "new" means new to the marketplace since this project first looked: the first look records a
    baseline silently, so a big marketplace doesn't announce its whole catalogue.
    """
    rows = installs(project)
    markets = watched(rows)
    catalog = {m: marketplace_plugins(m) for m in markets}
    updates = []
    for r in rows:
        if r["marketplace"] not in markets:
            continue
        avail = (catalog[r["marketplace"]].get(r["name"]) or {}).get("version")
        if avail and r["version"] not in ("unknown", avail):
            updates.append((r["id"], r["scope"], r["version"], avail))
    seen = _json(_seen_path()) or {}
    key = os.path.realpath(project)
    mine = seen.setdefault(key, {})
    installed = {(r["marketplace"], r["name"]) for r in rows}
    new = []
    for m in markets:
        names = set(catalog[m])
        if m not in mine:
            mine[m] = sorted(names)          # baseline: nothing is "new" on the first look
            continue
        for n in sorted(names - set(mine[m])):
            if (m, n) not in installed:
                new.append((m, n, catalog[m][n]["description"]))
        if remember:
            mine[m] = sorted(names | set(mine[m]))
    if remember:
        try:
            os.makedirs(data_dir(), exist_ok=True)
            with open(_seen_path(), "w") as handle:
                json.dump(seen, handle, indent=1)
        except OSError:
            pass
    return {"updates": updates, "new": new, "marketplaces": markets}


def refresh_in_background(markets):
    """Fire-and-forget `claude plugin marketplace update <m>` for each watched marketplace, at most
    once per UPKEEP_REFRESH_HOURS (default 24; 0 = never). Returns the marketplaces started."""
    hours = hookio.setting_int("UPKEEP_REFRESH_HOURS", 24)
    claude = shutil.which("claude")
    if hours <= 0 or not claude or not markets:
        return []
    stamp = os.path.join(data_dir(), "last-refresh")
    try:
        if time.time() - os.path.getmtime(stamp) < hours * 3600:
            return []
    except OSError:
        pass
    try:
        os.makedirs(data_dir(), exist_ok=True)
        pathlib.Path(stamp).touch()
        for m in markets:
            subprocess.Popen([claude, "plugin", "marketplace", "update", m], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        return []
    return list(markets)


def summary(rep):
    """One line for the user, or "" when there is nothing to say."""
    parts = []
    if rep["updates"]:
        parts.append("updates: " + ", ".join(f"{pid} {old} → {new}" for pid, _, old, new in rep["updates"]))
    if rep["new"]:
        parts.append("new: " + ", ".join(f"{n}@{m}" for m, n, _ in rep["new"]))
    return ("[upkeep] " + "; ".join(parts) + " — /upkeep to apply.") if parts else ""
