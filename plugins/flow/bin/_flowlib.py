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
"""

import json
import os
import shlex
import shutil
import subprocess
import sys
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
def build_claude_argv(prompt: str, model: str, permission_mode: str, effort=None, max_turns=None):
    """Construct the claude argv using only flags the installed CLI supports."""
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
                   effort=None, max_turns=None):
    """Run one headless claude session. Streams events to a readable .log and a raw
    .jsonl. Returns (exit_code, elapsed_secs, saw_rate_limit).
    """
    argv = build_claude_argv(prompt, model, permission_mode, effort=effort, max_turns=max_turns)
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    start = time.time()
    saw_rate_limit = False

    with open(log_path, "a", encoding="utf-8") as logf, \
            open(jsonl_path, "a", encoding="utf-8") as jf:
        logf.write(f"\n===== run @ {human_now()} =====\n")
        logf.write(dim(f"$ {' '.join(shlex.quote(a) for a in argv[:-1])} <prompt>\n"))
        logf.flush()
        try:
            proc = subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env,
            )
        except OSError as e:
            logf.write(red(f"could not launch claude: {e}\n"))
            return 127, time.time() - start, False

        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                jf.write(line)
                jf.flush()
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    logf.write(line + "\n")
                    logf.flush()
                    continue
                if isinstance(obj, dict):
                    if obj.get("type") == "system" and obj.get("subtype") == "api_retry":
                        saw_rate_limit = True
                    if obj.get("type") == "result" and obj.get("is_error"):
                        sub = str(obj.get("subtype", "")) + str(obj.get("result", ""))
                        if "rate" in sub.lower() or "limit" in sub.lower():
                            saw_rate_limit = True
                    summary = _summarize_event(obj)
                    if summary:
                        logf.write(summary + "\n")
                        logf.flush()
            code = proc.wait()
        except Exception as e:  # noqa: BLE001 — one job's crash must never kill the batch
            logf.write(red(f"runner error while streaming: {e}\n"))
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass
            code = proc.poll()
            if code is None:
                code = 1
        elapsed = time.time() - start
        logf.write(dim(f"----- exit {code} after {int(elapsed)}s -----\n"))
    return code, elapsed, saw_rate_limit


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
