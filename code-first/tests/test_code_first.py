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
for var in [v for v in os.environ if v.startswith(("CODE_FIRST_", "GIT_GUARD_", "CLAUDE_PLUGIN_OPTION_", "NUDGES_IN_WORKTREE"))]:
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
IDEA_TURN = ("<command-message>code-first:idea</command-message>\n"
             "<command-name>/code-first:idea</command-name>\n<command-args>{}</command-args>")
chk("the /idea turn itself is guarded (the command wrapper is not the user's words)", True,
    IDEA_TURN.format("cache layer"), FENCE6)
chk("'paste' in the /idea arguments still lifts the guard", False,
    IDEA_TURN.format("a prompt to paste"), FENCE6)
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
        return invoke(GUARD, {"transcript_path": path, **extra}, env={"TMPDIR": tmp, **(env or {})})[1]

    plain = transcript(("user", "add a retry to the client"), ("assistant", [{"type": "text", "text": FENCE6}]))
    check("the Stop hook is silent in a turn that is not code-first", stop(plain) == "")
    check("…and blocks there under CODE_FIRST_INJECT=always",
          '"decision": "block"' in stop(plain, {"CODE_FIRST_INJECT": "always"}))
    check("the idea command is recognized as the transcript records it", guard.cf.code_first_turn(
        None, "<command-message>code-first:idea</command-message>\n<command-name>/code-first:idea</command-name>"))
    check("the Stop hook blocks an over-limit reply to a 'propose' prompt", '"decision": "block"' in stop(t))
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

    sessions = [0]

    def inject(env=None, prompt="/idea cache", session=None):
        """One UserPromptSubmit call — a fresh session id unless one is named."""
        if session is None:
            sessions[0] += 1
            session = f"cf-{os.getpid()}-{sessions[0]}"
        return invoke(INJECT, {"cwd": repo, "session_id": session, "prompt": prompt},
                      env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": repo, **(env or {})})[1]

    # ── when the contract is injected: opt-in per session, or per prompt ──────────
    on = lambda out: "CODE-FIRST" in out
    check("a plain prompt injects nothing", inject(prompt="add a retry to the client") == "")
    check("design talk injects nothing", inject(prompt="brainstorm: how would you split it, what if we merge them?") == "")
    check("a path that ends in /idea is not the command", inject(prompt="look at src/idea and /ideas/x") == "")
    check("a prompt that only mentions /idea does not opt the session in",
          inject(prompt="do not use /idea here, write the decision down", session="s-mention") == ""
          and inject(prompt="go on", session="s-mention") == "")
    check("/idea <topic> injects the contract", on(inject(prompt="/idea cache", session="s-idea")))
    check("…and it stays on for a later plain prompt in that session",
          on(inject(prompt="now add the tests", session="s-idea")))
    check("…but not in another session", inject(prompt="now add the tests", session="s-other") == "")
    check("/code-first:idea <topic> turns it on too", on(inject(prompt="/code-first:idea cache", session="s-qual"))
          and on(inject(prompt="go on", session="s-qual")))
    check("a 'propose' prompt injects for that prompt", on(inject(prompt="Propose a cache layer", session="s-once")))
    check("…and the next plain prompt does not", inject(prompt="thanks, go on", session="s-once") == "")
    check("CODE_FIRST_TRIGGER_PATTERN replaces the default",
          on(inject({"CODE_FIRST_TRIGGER_PATTERN": r"\bdraft\b"}, prompt="draft the cache layer"))
          and inject({"CODE_FIRST_TRIGGER_PATTERN": r"\bdraft\b"}, prompt="propose a cache layer") == "")
    check("a bad CODE_FIRST_TRIGGER_PATTERN falls back to the default",
          on(inject({"CODE_FIRST_TRIGGER_PATTERN": "("}, prompt="sketch the cache layer")))
    check("CODE_FIRST_INJECT=always injects on a plain prompt",
          on(inject({"CODE_FIRST_INJECT": "always"}, prompt="add a retry to the client")))
    check("the Stop hook blocks a plain turn once the session opted in",
          '"decision": "block"' in stop(plain, session_id="s-idea") and stop(plain, session_id="s-other") == "")

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

    def stale(env=None, project=repo, session=None, **extra):
        """One stale-ideas call (Stop unless `hook_event_name` says otherwise) — a fresh session by default."""
        if session is None:
            sessions[0] += 1
            session = f"cf-{os.getpid()}-{sessions[0]}"
        return invoke(STALE, {"cwd": project, "session_id": session, "hook_event_name": "Stop", **extra},
                      env={"TMPDIR": tmp, "CLAUDE_PROJECT_DIR": project, **(env or {})})[1]

    events = json.loads(pathlib.Path(hook("hooks/hooks.json")).read_text())["hooks"]
    check("the stale note is registered at Stop, not SessionStart",
          "SessionStart" not in events and "stale-ideas.py" in json.dumps(events["Stop"]))
    check("the stale note prints nothing at SessionStart", stale(hook_event_name="SessionStart") == "")
    out = stale(session="s-stale")
    check("at Stop it names only branches past the threshold", "idea/old" in out and "idea/fresh" not in out, out)
    check("…as a user-visible note that blocks nothing",
          list(json.loads(out)) == ["systemMessage"] and "/idea list" in out and "promote" not in out, out)
    check("…once per session", stale(session="s-stale") == "")
    check("stop_hook_active stays silent", stale(stop_hook_active=True) == "")
    check("CODE_FIRST_STALE_DAYS empty turns the note off", stale({"CODE_FIRST_STALE_DAYS": ""}) == "")
    check("no stale branches → silent", stale({"CODE_FIRST_STALE_DAYS": "100000"}) == "")
    check("CODE_FIRST_OFF=1 silences the note", stale({"CODE_FIRST_OFF": "1"}) == "")
    wt = os.path.join(tmp, "wt")
    git("worktree", "add", "-q", wt, "-b", "wtbranch", "develop")
    check("a linked worktree gets no stale note", stale(project=wt) == "")
    check("…unless NUDGES_IN_WORKTREE=1", "idea/old" in stale({"NUDGES_IN_WORKTREE": "1"}, project=wt))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
