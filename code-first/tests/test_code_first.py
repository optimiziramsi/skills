#!/usr/bin/env python3
"""Self-tests for the code-first hooks and CLI. Run: python3 code-first/tests/test_code_first.py"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
from selftest import Check, hook, invoke, load_module, run_cli  # noqa: E402

check = Check()
INJECT = hook("hooks/inject.py")
GUARD = hook("hooks/idea-guard.py")
STALE = hook("hooks/stale-ideas.py")
CLI = hook("bin/code-first")
sys.path.insert(0, os.path.dirname(GUARD))
guard = load_module(GUARD, "idea_guard")

# Settings the developer's own shell may carry must not leak into the fixtures.
for var in [v for v in os.environ if v.startswith(("CODE_FIRST_", "GIT_GUARD_", "CLAUDE_PLUGIN_OPTION_"))]:
    del os.environ[var]

FENCE6 = "```python\n" + "".join(f"line{i}\n" for i in range(6)) + "```"


def chk(name, want_block, prompt, final, env=None):
    saved = dict(os.environ)
    os.environ.update(env or {})
    try:
        reason = guard.verdict(prompt, final)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    check(name, (reason is not None) == want_block, reason)


# ── the fence guard's verdicts ────────────────────────────────────────────────
chk("no code passes", False, "how would you do it?", "Branch idea/x, two questions.")
chk("a short fence passes (<= 5 lines)", False, "how?", "```python\na\nb\nc\n```")
chk("6 counted lines block", True, "how?", FENCE6)
chk("fences are summed", True, "how?", "```py\na\nb\nc\n```\ntext\n```js\nd\ne\nf\n```")
chk("blank lines inside a fence don't count", False, "how?", "```py\na\n\n\n\nb\n```")
chk("an untagged fence counts", True, "how?", "```\n" + "x\n" * 6 + "```")
chk("a bash fence is exempt (a command to run)", False, "how?", "```bash\n" + "echo x\n" * 20 + "```")
chk("CODE_FIRST_EXEMPT_LANGS replaces the exempt set", True, "how?", "```bash\n" + "echo x\n" * 20 + "```",
    {"CODE_FIRST_EXEMPT_LANGS": "text"})
chk("'paste' in the prompt lifts the guard", False, "give me a prompt to paste", FENCE6)
chk("'snippet' in the prompt lifts the guard", False, "show the config snippet inline", FENCE6)
chk("CODE_FIRST_ALLOW_PATTERN replaces the default", True, "give me a prompt to paste", FENCE6,
    {"CODE_FIRST_ALLOW_PATTERN": r"\bverbatim\b"})
chk("a bad CODE_FIRST_ALLOW_PATTERN falls back to the default", False, "paste it", FENCE6,
    {"CODE_FIRST_ALLOW_PATTERN": "("})
chk("CODE_FIRST_MAX_FENCE_LINES raises the limit", False, "how?", FENCE6, {"CODE_FIRST_MAX_FENCE_LINES": "10"})
chk("CODE_FIRST_MAX_FENCE_LINES=0 allows no counted fence", True, "how?", "```py\na\n```",
    {"CODE_FIRST_MAX_FENCE_LINES": "0"})
chk("no final message is no verdict", False, "how?", None)

tmp = os.path.realpath(tempfile.mkdtemp())
try:
    def transcript(*entries):
        path = os.path.join(tmp, f"t{len(os.listdir(tmp))}.jsonl")
        with open(path, "w") as fh:
            for kind, content in entries:
                fh.write(json.dumps({"type": kind, "message": {"content": content}}) + "\n")
        return path

    t = transcript(("user", "propose the cache layer"),
                   ("assistant", [{"type": "text", "text": "thinking"}]),
                   ("user", [{"type": "tool_result", "content": "paste this"}]),
                   ("assistant", [{"type": "text", "text": FENCE6}]))
    prompt, final = guard.cf.last_turn(t)
    check("last_turn skips tool results when finding the user's prompt", prompt == "propose the cache layer", prompt)
    check("last_turn returns the final assistant text", final == FENCE6)

    def stop(path, env=None, **extra):
        return invoke(GUARD, {"transcript_path": path, **extra}, env=env)[1]

    check("the Stop hook blocks an over-limit reply", '"decision": "block"' in stop(t))
    check("the block names the idea branch prefix", "idea/<topic>" in stop(t))
    check("stop_hook_active prevents a re-block loop", stop(t, stop_hook_active=True) == "")
    check("CODE_FIRST_GUARD_OFF=1 drops the Stop guard", stop(t, {"CODE_FIRST_GUARD_OFF": "1"}) == "")
    check("CODE_FIRST_OFF=1 drops the Stop guard too", stop(t, {"CODE_FIRST_OFF": "1"}) == "")
    check("a missing transcript fails open", stop(os.path.join(tmp, "nope.jsonl")) == "")

    # ── a fixture repo: base resolution, the injected text, idea branches ─────────
    repo = os.path.join(tmp, "repo")
    git = lambda *a, **kw: subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", *a],
                                          capture_output=True, text=True, check=True, **kw)
    subprocess.run(["git", "init", "-q", "-b", "main", repo], check=True)
    git("commit", "-q", "--allow-empty", "-m", "init")
    git("branch", "develop")

    def cli(*args, env=None):
        return run_cli(CLI, args, cwd=repo, env=env)

    rc, out, err = cli("base")
    check("a base that resolves to the protected default is refused", rc == 1 and "protected" in err, err)
    rc, out, _ = cli("base", env={"GIT_GUARD_INTEGRATION_BRANCH": "develop"})
    check("GIT_GUARD_INTEGRATION_BRANCH is the fallback base", rc == 0 and out.strip() == "develop", out)
    rc, out, _ = cli("base", env={"CODE_FIRST_BASE_BRANCH": "develop", "GIT_GUARD_INTEGRATION_BRANCH": "x"})
    check("CODE_FIRST_BASE_BRANCH wins", rc == 0 and out.strip() == "develop", out)
    rc, out, _ = cli("base", env={"CODE_FIRST_BASE_BRANCH": "main"})
    check("an explicit CODE_FIRST_BASE_BRANCH is trusted even when protected", rc == 0 and out.strip() == "main")
    rc, out, _ = cli("base", env={"GIT_GUARD_INTEGRATION_BRANCH": "main", "GIT_GUARD_PROTECTED_BRANCH": "main"})
    check("a derived protected base is refused", rc == 1)
    check("the prefix defaults to idea/", cli("prefix")[1].strip() == "idea/")
    check("CODE_FIRST_BRANCH_PREFIX overrides it", cli("prefix", env={"CODE_FIRST_BRANCH_PREFIX": "spike/"})[1].strip() == "spike/")
    check("the tag defaults to IDEA", cli("tag")[1].strip() == "IDEA")

    def inject(env=None):
        return invoke(INJECT, {"cwd": repo}, env={"CLAUDE_PROJECT_DIR": repo, **(env or {})})[1]

    out = inject({"CODE_FIRST_BASE_BRANCH": "develop", "CODE_FIRST_REVIEW_SURFACE": "the GitLab MR"})
    check("the shipped contract renders BASE / PREFIX / SURFACE",
          "`develop`" in out and "`idea/<topic>`" in out and "the GitLab MR" in out, out)
    check("the injected text stays at <= 10 lines", len(out.strip().splitlines()) <= 10, len(out.splitlines()))
    check("it doesn't repeat the reporting contract", "OUTPUT CONTRACT" not in out)
    check("no safe base renders an ask, not a guess", "ask the user" in inject())
    os.makedirs(os.path.join(repo, ".claude"))
    pathlib.Path(repo, ".claude", "code-first.md").write_text("claude {{BASE}}\n")
    check(".claude/code-first.md overrides the shipped text",
          inject({"CODE_FIRST_BASE_BRANCH": "develop"}).strip() == "claude develop")
    os.makedirs(os.path.join(repo, ".agent"))
    pathlib.Path(repo, ".agent", "code-first.md").write_text("agent {{PREFIX}}\n")
    check(".agent/code-first.md wins over .claude/", inject().strip() == "agent idea/")
    pathlib.Path(repo, "cf.md").write_text("explicit\n")
    check("CODE_FIRST_CONTRACT_FILE wins over both", inject({"CODE_FIRST_CONTRACT_FILE": "cf.md"}).strip() == "explicit")
    check("a missing CODE_FIRST_CONTRACT_FILE is a loud DISARM",
          "code-first DISARMED" in inject({"CODE_FIRST_CONTRACT_FILE": "nope.md"}))
    check("CODE_FIRST_OFF=1 silences the injection", inject({"CODE_FIRST_OFF": "1"}) == "")

    # idea branches: list + the stale nudge (ages are committer dates)
    old = {"GIT_COMMITTER_DATE": "2020-01-01T00:00:00", "GIT_AUTHOR_DATE": "2020-01-01T00:00:00"}
    git("switch", "-q", "-c", "idea/old", "develop")
    git("commit", "-q", "--allow-empty", "-m", "IDEA: old sketch", env={**os.environ, **old})
    git("switch", "-q", "-c", "idea/fresh", "develop")
    git("commit", "-q", "--allow-empty", "-m", "IDEA: fresh sketch")
    rc, out, _ = cli("list")
    check("list shows idea branches oldest first with age + subject",
          out.splitlines()[0].startswith("idea/old\t") and "IDEA: fresh sketch" in out, out)

    def stale(env=None):
        return invoke(STALE, {"cwd": repo}, env={"CLAUDE_PROJECT_DIR": repo, **(env or {})})[1]

    out = stale()
    check("the stale nudge names only branches past the threshold", "idea/old" in out and "idea/fresh" not in out, out)
    check("CODE_FIRST_STALE_DAYS empty turns the nudge off", stale({"CODE_FIRST_STALE_DAYS": ""}) == "")
    check("no stale branches → silent", stale({"CODE_FIRST_STALE_DAYS": "100000"}) == "")
    check("CODE_FIRST_OFF=1 silences the nudge", stale({"CODE_FIRST_OFF": "1"}) == "")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
