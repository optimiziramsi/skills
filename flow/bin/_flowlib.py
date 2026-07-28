"""Shared library for the flow runners (`loop` and `grind`).

These are user-launched autonomous runners: they iterate over markdown job/mission
files and invoke the Claude Code CLI in headless mode (`claude --print`) once per
unit of work. Each invocation is a FRESH, isolated Claude session — the executing
agent reads the job, does the work, commits, and updates the job's status. The
runner never commits; it only selects work, launches the agent, and records logs.

Stdlib only — no third-party deps. Python 3.8+.

Escape hatches / overrides (env vars):
  CLAUDE_BIN                 path to the claude binary (default: `claude` on PATH)
  FLOW_ALLOW_NESTED=1        allow running from inside a Claude Code session (testing)
  FLOW_CLAUDE_PERMISSION_MODE  override the permission mode passed to claude
  FLOW_EXTRA_CLAUDE_ARGS     extra args appended to every claude invocation (shlex-split)
  FLOW_BACKOFF_BASE          base seconds for the short exponential backoff (default 30)
  FLOW_LONG_BACKOFF_BASE     seconds per step of the long transient-API backoff
                             (default 600 → 10/20/…/60 min; lower it for testing)
  FLOW_ITER_TIMEOUT_SECS     grind wall-clock watchdog per iteration (default 900; 0 = off)
  FLOW_WORKTREE_UNSAFE=1     skip worktree confinement + its leak-probe (you own the risk)
  FLOW_PROBE_MODEL           model for the one-off leak-probe session (default sonnet)
"""

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime

# ── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "opus"          # opus 4.8 by default; sonnet only for mechanical work
# A trusted local batch runner must edit files and run git/build commands with no
# interactive prompts (a headless `-p` session cannot answer a prompt, so a denied
# tool = a failed job). bypassPermissions is the pragmatic default; override with
# FLOW_CLAUDE_PERMISSION_MODE, and the runners still require an explicit arm (-y or
# an interactive "yes") before executing.
DEFAULT_PERMISSION_MODE = "bypassPermissions"
RATE_LIMIT_FAST_FAIL_SECS = 120  # a run that fails faster than this looks like a rate limit

# Transient API error signatures in the CLI's output — server-side capacity /
# rate-limit / quota / network failures that deserve a long backoff instead of
# burning a retry. Content-based, so it also catches errors that surface only
# after the CLI's internal retries have pushed the wall clock past any
# duration heuristic.
TRANSIENT_OUTPUT_RE = re.compile(
    r"API Error.*(429|500|502|503|504|529)|\b(429|529) [A-Z]|overloaded"
    r"|rate[ _-]?limit|usage limit|daily limit|monthly limit|quota exceeded"
    r"|plan limit|too many requests|temporarily unavailable|service unavailable"
    r"|gateway timeout|conversation.{0,40}too long|context.{0,40}exceeded"
    r"|stream timeout|anthropic api error|ETIMEDOUT|ECONNRESET|ENETUNREACH|fetch failed",
    re.IGNORECASE,
)


# ── Terminal styling (no deps) ──────────────────────────────────────────────
def _c(code: str, s: str) -> str:
    if not sys.stderr.isatty():
        return s
    return f"\033[{code}m{s}\033[0m"


def bold(s: str) -> str:
    return _c("1", s)


def red(s: str) -> str:
    return _c("31", s)


def green(s: str) -> str:
    return _c("32", s)


def yellow(s: str) -> str:
    return _c("33", s)


def dim(s: str) -> str:
    return _c("2", s)


def info(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def die(msg: str, code: int = 1) -> "NoReturn":  # type: ignore[name-defined]
    print(red(f"error: {msg}"), file=sys.stderr, flush=True)
    sys.exit(code)


# ── Environment guards ──────────────────────────────────────────────────────
def nested_guard() -> None:
    """Refuse to run from inside a Claude Code session (nested sessions are blocked).

    `CLAUDECODE=1` is set by Claude Code in every session's environment. The runner
    must be launched from a plain terminal so its `claude -p` children are top-level.
    """
    if os.environ.get("FLOW_ALLOW_NESTED") == "1":
        return
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE_SESSION_ID"):
        die(
            "this runner is launched from INSIDE a Claude Code session.\n"
            "  Run it from a separate, plain terminal instead — nested Claude sessions are blocked.\n"
            "  (Set FLOW_ALLOW_NESTED=1 to override, e.g. for testing with a fake CLAUDE_BIN.)",
            code=2,
        )


def claude_bin() -> str:
    return os.environ.get("CLAUDE_BIN") or "claude"


# ── Worktree selection ──────────────────────────────────────────────────────
# The runners are cwd-relative: the job dir, the repo they commit into, and the
# worktree-confinement detection all key off the current directory. So targeting a
# worktree is only ever a question of picking the cwd — `--worktree NAME` resolves a
# name to a path and chdirs, nothing downstream changes.
def list_worktrees(cwd: str = None):
    """Every worktree of the repo containing `cwd`, main checkout first.

    Returns [{"path", "branch", "name", "is_main"}]; `branch` is "" when detached.
    Returns [] when git is unavailable or `cwd` is not in a repo.
    """
    try:
        out = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=cwd or os.getcwd(), capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return []
    trees, cur = [], None
    for line in out.splitlines():
        if line.startswith("worktree "):
            cur = {"path": line[9:], "branch": "", "is_main": not trees}
            cur["name"] = os.path.basename(cur["path"].rstrip("/"))
            trees.append(cur)
        elif line.startswith("branch ") and cur is not None:
            # `branch refs/heads/feature/foo` → `feature/foo`
            cur["branch"] = line[7:].replace("refs/heads/", "", 1)
    return trees


def resolve_worktree(name: str, cwd: str = None):
    """Resolve a `--worktree` argument to one worktree dict, or die with the candidates.

    Match order (first non-empty wins, and a tie inside one tier is an error rather
    than a guess): reserved alias → filesystem path → exact branch → exact directory
    name → unique substring of either. `.` means "right here" and returns None.
    """
    raw = (name or "").strip()
    if raw in ("", "."):
        return None
    trees = list_worktrees(cwd)
    if not trees:
        die("--worktree needs a git repository (none found here).")

    def _fail(msg):
        listing = "\n".join(
            f"    {t['name']:<28} {t['branch'] or '(detached)'}"
            + ("  ← main checkout" if t["is_main"] else "")
            for t in trees
        )
        die(f"{msg}\n  worktrees:\n{listing}")

    if raw in ("root", "main-checkout", "checkout"):
        return trees[0]
    real = os.path.realpath(os.path.expanduser(raw))
    for t in trees:
        if os.path.realpath(t["path"]) == real:
            return t
    for tier in (lambda t: t["branch"] == raw, lambda t: t["name"] == raw):
        hits = [t for t in trees if tier(t)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            _fail(f"--worktree {raw!r} is ambiguous.")
    hits = [t for t in trees if raw in t["branch"] or raw in t["name"]]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        _fail(f"--worktree {raw!r} matches {len(hits)} worktrees — be more specific.")
    _fail(f"no worktree matches --worktree {raw!r}.")


def select_worktree(name: str) -> None:
    """Resolve `--worktree NAME` and chdir into it, announcing the move.

    Everything after this point is cwd-relative, so this is the whole mechanism: run
    the wrapper from the checkout root, name a worktree, work happens over there.
    """
    t = resolve_worktree(name)
    if t is None:
        return
    if not os.path.isdir(t["path"]):
        die(f"worktree {t['name']!r} is registered but its directory is gone: {t['path']}\n"
            "  (run `git worktree prune` in the main checkout)")
    os.chdir(t["path"])
    where = "main checkout" if t["is_main"] else "worktree"
    info(dim(f"→ {where} {t['path']}  [{t['branch'] or 'detached'}]"))


def ensure_claude_available() -> None:
    b = claude_bin()
    if os.path.sep in b:
        if not os.path.exists(b):
            die(f"CLAUDE_BIN points at a missing file: {b}")
        return
    if shutil.which(b) is None:
        die(f"the `{b}` CLI is not on PATH. Install Claude Code, or set CLAUDE_BIN.")


_SUPPORTED_FLAGS = None


def supported_flags() -> set:
    """Long flags this installed claude CLI understands (probed once from --help)."""
    global _SUPPORTED_FLAGS
    if _SUPPORTED_FLAGS is not None:
        return _SUPPORTED_FLAGS
    flags = set()
    try:
        out = subprocess.run(
            [claude_bin(), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        for tok in (out.stdout + " " + out.stderr).split():
            tok = tok.strip(",")
            if tok.startswith("--"):
                flags.add(tok.split("=", 1)[0])
    except Exception:
        pass
    _SUPPORTED_FLAGS = flags
    return flags


# ── Time / naming ───────────────────────────────────────────────────────────
def stamp() -> str:
    return datetime.now().strftime("%y%m%d_%H%M%S")


def human_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── Frontmatter parsing (minimal YAML, stdlib only) ─────────────────────────
def parse_frontmatter(text: str):
    """Return (meta: dict[str,str], body: str).

    Handles a leading `---` fenced block of simple `key: value` scalar lines. Not a
    full YAML parser — the job/mission formats only use scalar fields. Inline `#`
    comments and surrounding quotes are stripped from values.
    """
    meta = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return meta, text
    for raw in lines[1:end]:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        # strip a trailing inline comment only when the value isn't quoted
        if val and val[0] not in ("'", '"') and "#" in val:
            val = val.split("#", 1)[0].strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        meta[key] = val
    body = "\n".join(lines[end + 1:])
    return meta, body


def read_job(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    meta, body = parse_frontmatter(text)
    return meta, body, text


def set_frontmatter_field(path: str, key: str, value: str) -> None:
    """Update (or insert) a single frontmatter field in place. No git; bookkeeping only.

    Used as a fallback so a crashed job doesn't loop forever. The executing agent
    normally owns status writes — this only fires when the agent never reached a
    terminal status.
    """
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            end = i
            break
    if end is None:
        return
    replaced = False
    for i in range(1, end):
        stripped = lines[i].lstrip()
        if stripped.startswith(f"{key}:"):
            indent = lines[i][: len(lines[i]) - len(stripped)]
            lines[i] = f"{indent}{key}: {value}"
            replaced = True
            break
    if not replaced:
        lines.insert(end, f"{key}: {value}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + ("\n" if text.endswith("\n") else ""))


def coerce_int(meta: dict, key: str, default: int) -> int:
    try:
        return int(str(meta.get(key, default)).strip())
    except (ValueError, TypeError):
        return default


# ── Claude invocation ───────────────────────────────────────────────────────
def build_claude_argv(prompt: str, model: str, permission_mode: str, effort=None, max_turns=None,
                      settings_json=None):
    """Construct the claude argv using only flags the installed CLI supports.

    `settings_json` (a JSON string) rides in on `--settings`; the runners use it to inject
    the worktree-confinement guard into each headless child. Absent, the argv is
    byte-identical to the pre-confinement behavior.
    """
    flags = supported_flags()
    # When --help couldn't be probed (empty set, e.g. a stubbed CLAUDE_BIN), don't
    # gate on membership — pass the core flags and let the binary sort it out.
    def ok(flag):
        return (not flags) or (flag in flags)

    argv = [claude_bin(), "--print"]
    if model and ok("--model"):
        argv += ["--model", model]
    if effort and ok("--effort"):
        argv += ["--effort", effort]
    if max_turns and ok("--max-turns"):
        argv += ["--max-turns", str(max_turns)]
    if settings_json and ok("--settings"):
        argv += ["--settings", settings_json]
    pm = os.environ.get("FLOW_CLAUDE_PERMISSION_MODE", permission_mode)
    if pm:
        if pm == "bypassPermissions" and "--dangerously-skip-permissions" in flags:
            argv.append("--dangerously-skip-permissions")
        elif "--permission-mode" in flags:
            argv += ["--permission-mode", pm]
        elif "--dangerously-skip-permissions" in flags:
            argv.append("--dangerously-skip-permissions")
    # stream-json gives us tool/result/rate-limit events, but the CLI requires
    # --verbose alongside it in print mode. Only request it when both are available;
    # otherwise fall back to default text output (run_claude_job logs raw lines fine).
    if ok("--output-format") and ok("--verbose"):
        argv += ["--output-format", "stream-json", "--verbose"]
    extra = os.environ.get("FLOW_EXTRA_CLAUDE_ARGS")
    if extra:
        argv += shlex.split(extra)
    argv.append(prompt)
    return argv


def _summarize_event(obj: dict):
    """Turn one stream-json event into a short human-readable log line (or None).

    Total by design — the event schema is external and may drift, so any malformed
    shape degrades to None rather than raising (a raise here would kill the run).
    """
    try:
        t = obj.get("type")
        if t == "assistant":
            parts = []
            msg = obj.get("message")
            content = msg.get("content", []) if isinstance(msg, dict) else []
            for block in content or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and str(block.get("text", "")).strip():
                    parts.append(block["text"].strip())
                elif block.get("type") == "tool_use":
                    parts.append(dim(f"⚙ {block.get('name', 'tool')}"))
            return "  ".join(parts) if parts else None
        if t == "system" and obj.get("subtype") == "api_retry":
            return yellow(
                f"↻ api retry {obj.get('attempt', '?')}/{obj.get('max_retries', '?')} "
                f"({obj.get('error', '')} {obj.get('error_status', '')})"
            )
        if t == "result":
            tag = red("RESULT (error)") if obj.get("is_error") else green("RESULT")
            txt = str(obj.get("result") or "").strip()
            cost = obj.get("total_cost_usd")
            suffix = f"  ${cost:.4f}" if isinstance(cost, (int, float)) and not isinstance(cost, bool) else ""
            return f"{tag}{suffix}\n{txt}" if txt else f"{tag}{suffix}"
    except Exception:  # noqa: BLE001 — a logging summary must never break the run
        return None
    return None


def run_claude_job(prompt, model, permission_mode, log_path, jsonl_path, env_extra=None,
                   effort=None, max_turns=None, timeout_secs=None, settings_json=None):
    """Run one headless claude session. Streams events to a readable .log and a raw
    .jsonl. Returns (exit_code, elapsed_secs, saw_transient, timed_out).

    `saw_transient` is True when the output contained a transient-API-error signature
    (rate limit / 5xx / overloaded / quota / network) — callers should back off instead
    of burning a retry. `timeout_secs` arms a wall-clock watchdog: past the deadline the
    child gets SIGTERM, then SIGKILL after a 10s grace (`timed_out` reports it fired).
    `settings_json` (when set) is injected via `--settings` — the runners use it to confine a
    worktree run's children to the worktree (see `worktree_preflight`).
    """
    argv = build_claude_argv(prompt, model, permission_mode, effort=effort, max_turns=max_turns,
                             settings_json=settings_json)
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    start = time.time()
    saw_transient = False
    watchdog_fired = {"timed_out": False}
    done_evt = threading.Event()

    with open(log_path, "a", encoding="utf-8") as logf, \
            open(jsonl_path, "a", encoding="utf-8") as jf:
        logf.write(f"\n===== run @ {human_now()} =====\n")
        logf.write(dim(f"$ {' '.join(shlex.quote(a) for a in argv[:-1])} <prompt>\n"))
        logf.flush()
        try:
            # POSIX: own process group (start_new_session) so kills reach the whole
            # tree — the CLI's children inherit the stdout pipe, and an orphaned
            # grandchild would otherwise keep the read loop alive after a kill.
            proc = subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env,
                start_new_session=(os.name == "posix"),
            )
        except OSError as e:
            logf.write(red(f"could not launch claude: {e}\n"))
            return 127, time.time() - start, False, False

        def _kill_proc(sig):
            try:
                if os.name == "posix":
                    os.killpg(os.getpgid(proc.pid), sig)
                    return
            except Exception:  # noqa: BLE001 — group may be gone; fall through
                pass
            try:
                if sig == signal.SIGKILL:
                    proc.kill()
                else:
                    proc.terminate()
            except Exception:  # noqa: BLE001
                pass

        watchdog = None
        if timeout_secs and timeout_secs > 0:
            def _watchdog():
                # wall-clock cap: a hung network read has no native timeout in the
                # CLI (--max-turns caps turns, not time). SIGTERM past the deadline;
                # SIGKILL if it's ignored for 10s. Keep this thread side-effect-free
                # beyond the kill — the main thread does all logging.
                if done_evt.wait(timeout_secs):
                    return
                if proc.poll() is None:
                    watchdog_fired["timed_out"] = True
                    _kill_proc(signal.SIGTERM)
                    if not done_evt.wait(10) and proc.poll() is None:
                        _kill_proc(signal.SIGKILL)
            watchdog = threading.Thread(target=_watchdog, daemon=True)
            watchdog.start()

        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                jf.write(line)
                jf.flush()
                line = line.strip()
                if not line:
                    continue
                if TRANSIENT_OUTPUT_RE.search(line):
                    saw_transient = True
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    logf.write(line + "\n")
                    logf.flush()
                    continue
                if isinstance(obj, dict):
                    if obj.get("type") == "system" and obj.get("subtype") == "api_retry":
                        saw_transient = True
                    if obj.get("type") == "result" and obj.get("is_error"):
                        sub = str(obj.get("subtype", "")) + str(obj.get("result", ""))
                        if "rate" in sub.lower() or "limit" in sub.lower():
                            saw_transient = True
                    summary = _summarize_event(obj)
                    if summary:
                        logf.write(summary + "\n")
                        logf.flush()
            code = proc.wait()
        except KeyboardInterrupt:
            # the child runs in its own process group (see Popen above), so the
            # terminal's SIGINT does not reach it — kill the group before bubbling up
            _kill_proc(signal.SIGTERM)
            time.sleep(0.5)
            if proc.poll() is None:
                _kill_proc(signal.SIGKILL)
            raise
        except Exception as e:  # noqa: BLE001 — one job's crash must never kill the batch
            logf.write(red(f"runner error while streaming: {e}\n"))
            _kill_proc(signal.SIGKILL)
            code = proc.poll()
            if code is None:
                code = 1
        finally:
            done_evt.set()
            if watchdog is not None:
                watchdog.join(timeout=1)
        elapsed = time.time() - start
        timed_out = watchdog_fired["timed_out"]
        if timed_out:
            logf.write(red(f"⏱ watchdog: exceeded {int(timeout_secs)}s wall clock — killed\n"))
        logf.write(dim(f"----- exit {code} after {int(elapsed)}s -----\n"))
    return code, elapsed, saw_transient, timed_out


def backoff_sleep(attempt: int, base: float = 30.0, cap: float = 600.0) -> None:
    """Exponential backoff between retries (used after a fast/rate-limited failure).

    Base delay is overridable with FLOW_BACKOFF_BASE (seconds) for tuning/testing.
    """
    try:
        base = float(os.environ.get("FLOW_BACKOFF_BASE", base))
    except ValueError:
        pass
    delay = min(cap, base * (2 ** max(0, attempt - 1)))
    info(yellow(f"  backing off {int(delay)}s before retry…"))
    time.sleep(delay)


def long_backoff_sleep(step: int) -> None:
    """Long linear backoff for sustained transient-API failures (grind).

    Step N sleeps N × base, capped at 6 × base. Default base is 600s, so the ladder
    is 10/20/30/40/50/60 minutes (~3.5h total across 6 steps). Override the base with
    FLOW_LONG_BACKOFF_BASE (seconds) for tuning/testing.
    """
    base = 600.0
    try:
        base = float(os.environ.get("FLOW_LONG_BACKOFF_BASE", base))
    except ValueError:
        pass
    delay = min(6 * base, base * max(1, step))
    info(yellow(f"  transient-API backoff: sleeping {int(delay)}s (step {step}/6)…"))
    time.sleep(delay)


# ── Worktree confinement (engages only when cwd is a LINKED git worktree) ───
# The runners are cwd-relative: a child launched with cwd = a worktree does all its work there.
# The risk is an autonomous child slipping a write into the MAIN checkout or a sibling worktree
# (claude-code #36182). So when cwd is a linked worktree the runners (1) inject the `worktree`
# topic's PreToolUse guards into every child via --settings and (2) PROVE they block a
# main-checkout write with a live leak-probe before any real work runs — refusing to continue
# unless confinement is confirmed. In the main checkout (or outside a repo) none of this engages
# and behavior is byte-identical to a runner that never heard of worktrees.
#
# The guards are the `worktree` topic's, deliberately NOT a second copy living here: one
# implementation, one self-test, one set of edge cases. The cost is a cross-topic path
# dependency — flow/bin/ → worktree/hooks/ — which `confine_hooks()` fails loudly on.
def _git_out(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def worktree_context(cwd=None):
    """dict(is_linked, wt_root, main_root, branch) when cwd is in a git work tree, else None.

    `is_linked` is True only for a LINKED worktree (git-dir != git-common-dir). `wt_root` is the
    worktree root; `main_root` is the main checkout (the parent of the shared git-common-dir).
    All realpath-resolved, so downstream path comparisons are apples-to-apples.
    """
    cwd = cwd or os.getcwd()
    if _git_out(cwd, "rev-parse", "--is-inside-work-tree") != "true":
        return None
    wt = _git_out(cwd, "rev-parse", "--show-toplevel")
    gd = _git_out(cwd, "rev-parse", "--absolute-git-dir")
    common = _git_out(cwd, "rev-parse", "--git-common-dir")
    if not (wt and gd and common):
        return None
    if not os.path.isabs(common):
        common = os.path.abspath(os.path.join(cwd, common))
    return {
        "is_linked": os.path.realpath(gd) != os.path.realpath(common),
        "wt_root": os.path.realpath(wt),
        "main_root": os.path.realpath(os.path.dirname(common)),
        "branch": _git_out(cwd, "rev-parse", "--abbrev-ref", "HEAD") or "?",
    }


CONFINE_HOOKS = (  # (relative path from the plugin root, tool matcher)
    ("worktree/hooks/worktree-write-guard.sh", "Edit|Write|MultiEdit|NotebookEdit"),
    ("worktree/hooks/worktree-bash-guard.sh", "Bash"),
)


def confine_hooks():
    """[(absolute guard path, matcher)] — dies if the `worktree` topic isn't beside us."""
    # …/<plugin>/flow/bin/_flowlib.py → …/<plugin>
    plugin_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = []
    for rel, matcher in CONFINE_HOOKS:
        path = os.path.join(plugin_root, rel)
        if not os.path.exists(path):
            die(f"worktree confinement needs the `worktree` topic's guard, which is missing:\n"
                f"  {path}\n"
                "  Reinstall the plugin, or set FLOW_WORKTREE_UNSAFE=1 to run WITHOUT "
                "confinement (not recommended).")
        out.append((path, matcher))
    return out


def confine_settings_json(hooks):
    """`--settings` JSON registering the guards on PreToolUse for this run's children.

    The command carries an ABSOLUTE hook path: a relative command inside injected settings
    resolves against the child's cwd, not against this file. The guards are self-configuring —
    each reads the child's cwd from its hook input and derives the worktree/main roots per call,
    so no paths are baked into the settings blob.
    """
    return json.dumps({"hooks": {"PreToolUse": [
        {"matcher": matcher, "hooks": [{"type": "command", "command": f"bash {shlex.quote(path)}"}]}
        for path, matcher in hooks
    ]}})


PROBE_MODEL_DEFAULT = "sonnet"  # cheap; the model can't affect WHETHER a hook fires
_PROBE_PROMPT = """\
CONFINEMENT SELF-TEST — you are a disposable probe, NOT doing real work. Do EXACTLY these three
steps in order, then reply DONE. Do nothing else and explain nothing.
1. Use the Write tool to create the file `{ok}` with the exact content `OK`.
2. Use the Write tool to create the file `{leak_tool}` with the exact content `LEAK`.
3. Run this Bash command exactly: printf LEAK > {leak_bash}
Reply DONE.
"""


def run_leak_probe(ctx, model, settings_json):
    """One throwaway child (same bypass flags + injected guards) that tries to write into the
    main checkout by BOTH the Write tool and a bash redirect, plus a positive control inside the
    worktree. Returns:
      'confined'     — neither main-checkout write landed AND the control did (guards work),
      'leak'         — a main-checkout write landed (confinement is NOT effective),
      'inconclusive' — the control never landed, so cooperation couldn't be confirmed.
    Every probe file is cleaned up; on a leak the transcript is kept and its path surfaced.
    """
    ok = os.path.join(ctx["wt_root"], ".flow_probe_ok")
    leak_tool = os.path.join(ctx["main_root"], ".flow_probe_tool")
    leak_bash = os.path.join(ctx["main_root"], ".flow_probe_bash")

    def _clean():
        for p in (ok, leak_tool, leak_bash):
            try:
                os.unlink(p)
            except OSError:
                pass

    _clean()
    prompt = _PROBE_PROMPT.format(ok=ok, leak_tool=leak_tool, leak_bash=shlex.quote(leak_bash))
    fd1, plog = tempfile.mkstemp(prefix="flow_probe_", suffix=".log")
    fd2, pjsonl = tempfile.mkstemp(prefix="flow_probe_", suffix=".jsonl")
    os.close(fd1)
    os.close(fd2)
    try:
        run_claude_job(prompt, model, DEFAULT_PERMISSION_MODE, plog, pjsonl,
                       settings_json=settings_json, max_turns=6, timeout_secs=180)
        leaked = os.path.exists(leak_tool) or os.path.exists(leak_bash)
        cooperated = os.path.exists(ok)
    finally:
        _clean()
    if leaked:
        info(red(f"    probe transcript kept for inspection: {plog}"))
        return "leak"
    for p in (plog, pjsonl):
        try:
            os.unlink(p)
        except OSError:
            pass
    return "confined" if cooperated else "inconclusive"


def worktree_preflight():
    """Call once before arming. Returns the `--settings` JSON to inject into every child, or
    None for normal (main-checkout / non-repo) mode — where behavior is unchanged.

    In worktree mode it self-tests the guards (fast, no model call), then runs the live
    leak-probe and die()s unless confinement is proven. FLOW_WORKTREE_UNSAFE=1 skips the whole
    thing — the escape hatch; you own the risk.
    """
    ctx = worktree_context()
    if not ctx or not ctx["is_linked"]:
        return None
    info(bold("\n⚠ WORKTREE MODE — autonomous edits will be confined to this worktree"))
    info(f"    in scope (worktree):       {ctx['wt_root']}  [{ctx['branch']}]")
    info(f"    protected (main checkout): {ctx['main_root']}")
    if os.environ.get("FLOW_WORKTREE_UNSAFE") == "1":
        info(yellow("    FLOW_WORKTREE_UNSAFE=1 — confinement + leak-probe SKIPPED. You own the risk."))
        return None
    flags = supported_flags()
    if flags and "--settings" not in flags:
        die("this claude CLI has no --settings flag, so the runner can't inject worktree "
            "confinement into its children. Update the CLI, run from the main checkout, or set "
            "FLOW_WORKTREE_UNSAFE=1 to run WITHOUT confinement (not recommended).")
    hooks = confine_hooks()
    for path, _ in hooks:
        st = subprocess.run(["bash", path, "--test"], capture_output=True, text=True)
        if st.returncode != 0:
            die(f"guard self-test FAILED ({os.path.basename(path)}) — refusing to run:\n"
                f"{st.stdout}\n{st.stderr}")
    info(dim(f"    guard self-tests: ok ({len(hooks)})"))
    settings = confine_settings_json(hooks)
    probe_model = os.environ.get("FLOW_PROBE_MODEL", PROBE_MODEL_DEFAULT)
    info(dim(f"    verifying confinement with a live leak-probe ({probe_model}, one throwaway session)…"))
    verdict = run_leak_probe(ctx, probe_model, settings)
    if verdict == "confined":
        info(green("    ✓ leak-probe: writes into the main checkout are BLOCKED — confinement proven."))
        return settings
    if verdict == "leak":
        die("✘ leak-probe: a test write REACHED the main checkout — confinement is NOT effective "
            "under --dangerously-skip-permissions on this CLI (PreToolUse hooks likely don't fire "
            "under bypass here). REFUSING to run — a real job could leak into the main checkout. "
            "Run jobs from the main checkout instead, or pursue OS-sandbox confinement.")
    die("✘ leak-probe INCONCLUSIVE — the probe session never wrote its positive-control file, so "
        "confinement could not be confirmed. REFUSING to run. Re-try; if it persists, check the "
        "CLI / probe model (FLOW_PROBE_MODEL), or set FLOW_WORKTREE_UNSAFE=1 to override (not "
        "recommended).")


# ── The executing-model protocol (prepended to every job/mission prompt) ────
EXECUTING_PROTOCOL = """\
You are an autonomous executor launched by a batch runner. This is a fresh, isolated
session: your ONLY context is this project's CLAUDE.md/AGENTS.md (if present) and the
work item below. There is no human to answer questions mid-run.

Hard rules:
- Stay strictly in scope. Do only what the work item asks; do not refactor unrelated code.
- If the project documents patterns/conventions, follow them. If a decision the item
  needs was never made (ambiguous shape, undecided pattern), DO NOT guess — record the
  blocker and mark the terminal status accordingly (see below), then stop.
- Commit your own work with a single-line message (the runner never commits for you).
- Verify before you finish: run the project's build/tests if they exist and are relevant.

You MUST end by writing a terminal status into this work item's frontmatter and a short
note in its Report/Log section, then committing. {status_contract}
"""


# ── Self-test (`python3 _flowlib.py --test`; run by the repo's tests.sh) ─────
def _self_test() -> int:
    import contextlib
    import io
    fails = 0

    def contextlib_redirect_stderr():
        """Keep the expected banners/errors out of the --test output."""
        return contextlib.redirect_stderr(io.StringIO())

    def check(label, cond):
        nonlocal fails
        if cond:
            print(f"PASS  {label}")
        else:
            print(f"FAIL  {label}")
            fails += 1

    def resolves_to(name, expect_path, tmp):
        try:
            t = resolve_worktree(name, cwd=tmp)
        except SystemExit:
            return False
        return t is not None and os.path.realpath(t["path"]) == os.path.realpath(expect_path)

    def dies_on(name, tmp):
        import contextlib
        import io
        try:  # swallow the expected error banner so --test output stays readable
            with contextlib.redirect_stderr(io.StringIO()):
                resolve_worktree(name, cwd=tmp)
            return False
        except SystemExit:
            return True

    tmp = tempfile.mkdtemp()
    tmp = os.path.realpath(tmp)  # macOS /var → /private/var
    try:
        repo, wt_a, wt_b = f"{tmp}/repo", f"{tmp}/repo/.wt/alpha", f"{tmp}/repo/.wt/beta"
        q = {"capture_output": True, "check": True}
        subprocess.run(["git", "init", "-q", "-b", "trunk", repo], **q)
        subprocess.run(["git", "-C", repo, "commit", "-q", "--allow-empty", "-m", "i"], **q)
        for path, branch in ((wt_a, "feature/alpha-work"), (wt_b, "feature/beta-work")):
            subprocess.run(["git", "-C", repo, "worktree", "add", "-q", path, "-b", branch], **q)

        trees = list_worktrees(repo)
        check("lists every worktree", len(trees) == 3)
        check("main checkout is first", trees[0]["is_main"] and not trees[1]["is_main"])
        check("branch names are stripped of refs/heads/",
              sorted(t["branch"] for t in trees) == ["feature/alpha-work", "feature/beta-work", "trunk"])
        check("'.' means stay put", resolve_worktree(".", cwd=repo) is None)
        check("'' means stay put", resolve_worktree("", cwd=repo) is None)
        check("resolves a reserved root alias", resolves_to("root", repo, repo))
        check("resolves an exact branch", resolves_to("feature/alpha-work", wt_a, repo))
        check("resolves an exact directory name", resolves_to("beta", wt_b, repo))
        check("resolves a filesystem path", resolves_to(wt_a, wt_a, repo))
        check("resolves a unique substring", resolves_to("alpha", wt_a, repo))
        check("refuses an ambiguous substring", dies_on("work", repo))
        check("refuses an unknown name", dies_on("nope", repo))
        # A directory name must not be beaten by a substring hit elsewhere.
        check("exact name wins over substring", resolves_to("alpha", wt_a, repo))

        # ── worktree confinement ────────────────────────────────────────────
        main_ctx, wt_ctx = worktree_context(repo), worktree_context(wt_a)
        check("main checkout is not a linked worktree", not main_ctx["is_linked"])
        check("a worktree is linked", wt_ctx["is_linked"])
        check("worktree ctx points at the main checkout",
              wt_ctx["main_root"] == os.path.realpath(repo) and wt_ctx["wt_root"] == os.path.realpath(wt_a))
        settings = json.loads(confine_settings_json(confine_hooks()))
        entries = settings["hooks"]["PreToolUse"]
        check("settings register both guards on PreToolUse", len(entries) == 2)
        check("guard commands are absolute",
              all(e["hooks"][0]["command"].split()[-1].startswith("/") for e in entries))
        check("guards cover writes and Bash",
              {"Bash"} == {e["matcher"] for e in entries} - {"Edit|Write|MultiEdit|NotebookEdit"})
        check("--settings rides into the argv",
              "--settings" in build_claude_argv("p", "m", "", settings_json="{}"))
        check("no --settings without confinement",
              "--settings" not in build_claude_argv("p", "m", ""))

        # End-to-end preflight against a stubbed CLI: the stub plays the child session and
        # decides which probe files appear, so all three verdicts are exercised for real.
        stub = os.path.join(tmp, "claude_stub.py")
        with open(stub, "w") as fh:
            fh.write(
                "#!/usr/bin/env python3\n"
                "import os, re, sys\n"
                "if '--help' in sys.argv:\n"
                "    print('--print --model --effort --max-turns --settings --permission-mode '\n"
                "          '--dangerously-skip-permissions --output-format --verbose')\n"
                "    raise SystemExit(0)\n"
                "mode = os.environ.get('STUB_MODE', 'confined')\n"
                "paths = re.findall(r'`([^`]+)`', sys.argv[-1]) + re.findall(r'> (\\S+)', sys.argv[-1])\n"
                "ok = [p for p in paths if p.endswith('.flow_probe_ok')]\n"
                "leaks = [p for p in paths if '.flow_probe_' in p and not p.endswith('_ok')]\n"
                "if mode in ('confined', 'leak'):\n"
                "    open(ok[0], 'w').write('OK')\n"
                "if mode == 'leak':\n"
                "    open(leaks[0], 'w').write('LEAK')\n"
            )
        prev_cwd, prev_env = os.getcwd(), dict(os.environ)
        try:
            os.chdir(wt_a)
            os.chmod(stub, 0o755)
            os.environ["CLAUDE_BIN"] = stub
            for mode, expect_settings in (("confined", True), ("leak", False), ("silent", False)):
                os.environ["STUB_MODE"] = mode
                try:
                    with contextlib_redirect_stderr():
                        got = worktree_preflight()
                    died = False
                except SystemExit:
                    got, died = None, True
                if expect_settings:
                    check(f"preflight arms on a {mode} probe", got is not None and not died)
                else:
                    check(f"preflight REFUSES on a {mode} probe", died and got is None)
            os.chdir(repo)
            os.environ["STUB_MODE"] = "leak"  # would leak, but the main checkout never confines
            with contextlib_redirect_stderr():
                check("main checkout skips confinement entirely", worktree_preflight() is None)
        finally:
            os.chdir(prev_cwd)
            os.environ.clear()
            os.environ.update(prev_env)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("all tests passed" if not fails else f"{fails} FAILED")
    return fails


if __name__ == "__main__":
    if "--test" in sys.argv[1:]:
        sys.exit(_self_test())
    print(__doc__)
