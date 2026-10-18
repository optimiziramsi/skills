#!/usr/bin/env python3
"""Self-tests for upkeep. Run: python3 upkeep/tests/test_upkeep.py"""
import json
import os
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, run_cli  # noqa: E402

check = Check()
CHECK_HOOK = hook("hooks/upkeep-check.py")
CLI = hook("bin/upkeep")
for var in [v for v in os.environ if v.startswith(("UPKEEP_", "CLAUDE_PLUGIN_", "CLAUDE_CONFIG_DIR"))]:
    del os.environ[var]

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    config = os.path.join(tmp, "config")
    market = os.path.join(tmp, "market")
    project = os.path.join(tmp, "proj")
    other = os.path.join(tmp, "other")
    for d in (project, other):
        os.makedirs(d)

    def write(path, obj):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pathlib.Path(path).write_text(json.dumps(obj))

    def offer(plugins):
        """The marketplace's local copy: {name: version}."""
        write(os.path.join(market, ".claude-plugin", "marketplace.json"), {
            "name": "mk", "plugins": [{"name": n, "source": f"./{n}", "description": f"about {n}"} for n in plugins]})
        for n, v in plugins.items():
            write(os.path.join(market, n, ".claude-plugin", "plugin.json"), {"name": n, "version": v})

    write(os.path.join(config, "plugins", "known_marketplaces.json"),
          {"mk": {"installLocation": market}, "big": {"installLocation": os.path.join(tmp, "nowhere")}})
    write(os.path.join(config, "plugins", "installed_plugins.json"), {"version": 2, "plugins": {
        "alpha@mk": [{"scope": "user", "version": "1.0.0"}],
        "beta@mk": [{"scope": "project", "projectPath": project, "version": "0.1.0"}],
        "gamma@mk": [{"scope": "project", "projectPath": other, "version": "0.1.0"}],
        "zeta@big": [{"scope": "project", "projectPath": other, "version": "9"}],
    }})
    offer({"alpha": "1.0.0", "beta": "0.1.0", "gamma": "0.2.0"})
    env = {"CLAUDE_CONFIG_DIR": config, "CLAUDE_PLUGIN_DATA": os.path.join(tmp, "data"),
           "CLAUDE_PROJECT_DIR": project, "UPKEEP_REFRESH_HOURS": "0"}

    def session(extra=None):
        out = invoke(CHECK_HOOK, {"cwd": project}, env={**env, **(extra or {})})[1]
        return json.loads(out) if out.strip() else {}

    check("nothing outdated, first look → silent (the baseline)", session() == {})
    offer({"alpha": "1.0.0", "beta": "0.2.0", "gamma": "0.2.0"})
    got = session().get("systemMessage", "")
    check("an outdated project-scope install is reported", "beta@mk 0.1.0 → 0.2.0" in got, got)
    check("another project's install is not", "gamma" not in got, got)
    check("an identical report isn't repeated the same day", session() == {})
    offer({"alpha": "1.1.0", "beta": "0.2.0", "gamma": "0.2.0", "delta": "0.1.0"})
    got = session().get("systemMessage", "")
    check("a user-scope install counts for every project", "alpha@mk 1.0.0 → 1.1.0" in got, got)
    check("a plugin new to the marketplace is announced", "new: delta@mk" in got, got)
    check("…once", "delta" not in session().get("systemMessage", ""))
    check("a marketplace the project doesn't use isn't watched",
          run_cli(CLI, ["marketplaces"], cwd=project, env=env)[1].split() == ["mk"])
    check("UPKEEP_MARKETPLACES narrows the watch",
          run_cli(CLI, ["marketplaces"], cwd=project, env={**env, "UPKEEP_MARKETPLACES": "big"})[1].strip() == "")
    rc, out, _ = run_cli(CLI, ["status", "--json"], cwd=project, env=env)
    rep = json.loads(out)
    check("the CLI reports the same updates as JSON",
          rc == 0 and ["alpha@mk", "user", "1.0.0", "1.1.0"] in rep["updates"], out)
    check("UPKEEP_OFF=1 silences it", session({"UPKEEP_OFF": "1"}) == {})
    os.remove(os.path.join(config, "plugins", "installed_plugins.json"))
    check("missing plugin records fail open", session() == {})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
