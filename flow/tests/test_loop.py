#!/usr/bin/env python3
"""Self-tests for the loop runner. Run: python3 flow/tests/test_loop.py

Two layers: the pure selection logic imported directly, then end-to-end runs against a fake
`claude` CLI (lib/selftest.CLAUDE_STUB) so the real control flow is exercised without a model.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
from selftest import Check, hook, load_module, run_cli, write_claude_stub  # noqa: E402

check = Check()
LOOP = hook("flow/bin/loop")
loop = load_module(LOOP, "flow_loop")


def job(status, title="t", **extra):
    fields = "".join(f"{k.replace('_', '-')}: {v}\n" for k, v in extra.items())
    return f"---\njob-status: {status}\ntitle: {title}\n{fields}---\n\nDo the thing.\n"


tmp = os.path.realpath(tempfile.mkdtemp())
try:
    # ── argument parsing ───────────────────────────────────────────────────
    opts = loop.parse_args([])
    check("defaults: no watch, opus, .agent/loop",
          not opts["watch"] and opts["model"] == "opus" and opts["dir"] == ".agent/loop")
    opts = loop.parse_args(["--watch", "--model", "sonnet", "--retries", "5", "--dir", "d",
                            "--worktree", "w", "-y", "--dry-run", "--status"])
    check("every flag parses", (opts["watch"] and opts["model"] == "sonnet"
                                and opts["retries"] == 5 and opts["dir"] == "d"
                                and opts["worktree"] == "w" and opts["yes"]
                                and opts["dry_run"] and opts["status"]))
    check("--worktree is stripped for a child runner",
          loop._child_argv(["--worktree", "all", "-y", "--dir", "d"]) == ["-y", "--dir", "d"])

    # ── job loading and dependency ordering ────────────────────────────────
    jobs_dir = os.path.join(tmp, "jobs")
    os.makedirs(jobs_dir)
    files = {"01-a.md": job("done"), "02-b.md": job("pending", blocked_on="01-a.md"),
             "03-c.md": job("pending", blocked_on="09-missing.md"),
             "04-d.md": job("draft"), "05-e.md": job("running"),
             "06-f.md": job("failed"), "README.md": "not a job\n",
             "runner_x.log.md": job("pending")}
    for name, text in files.items():
        pathlib.Path(jobs_dir, name).write_text(text)

    jobs = loop.load_jobs(jobs_dir)
    names = [j["base"] for j in jobs]
    check("README.md and runner_* are not jobs",
          "README.md" not in names and "runner_x.log.md" not in names, names)
    check("statuses are parsed from frontmatter",
          {j["base"]: j["status"] for j in jobs}["05-e.md"] == "running")

    by_key = {j["stem"]: j for j in jobs}
    check("a satisfied dependency is runnable", loop.deps_satisfied(by_key["02-b"], by_key)[0])
    check("a missing dependency is not satisfied",
          loop.deps_satisfied(by_key["03-c"], by_key) == (False, ["09-missing"]))
    check("no blocked-on means satisfied", loop.deps_satisfied(by_key["04-d"], by_key)[0])

    queue = loop.runnable_queue(jobs)
    check("the queue is pending + running with deps met",
          [j["base"] for j in queue] == ["02-b.md", "05-e.md"], [j["base"] for j in queue])
    check("a crash-leftover job is flagged for resume",
          {j["base"]: j["resume"] for j in queue} == {"02-b.md": False, "05-e.md": True})
    check("draft and failed are never queued",
          not {"04-d.md", "06-f.md"} & {j["base"] for j in queue})

    check("the prompt carries the job body and path",
          "Do the thing." in loop.compose_prompt(by_key["02-b"])
          and by_key["02-b"]["path"] in loop.compose_prompt(by_key["02-b"]))

    # ── end to end against the stub CLI ────────────────────────────────────
    repo = os.path.join(tmp, "repo")
    subprocess.run(["git", "init", "-q", "-b", "main", repo], capture_output=True, check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "init"], capture_output=True, check=True)
    live = os.path.join(repo, ".agent", "loop")
    os.makedirs(live)
    job_path = os.path.join(live, "01-work.md")
    pathlib.Path(job_path).write_text(job("pending", title="the work"))
    stub = write_claude_stub(tmp)
    # FLOW_BACKOFF_BASE=0: a stub session finishes instantly, which the runner reads as a
    # fast/transient failure and would answer with real 30s+ sleeps.
    base_env = {"CLAUDE_BIN": stub, "FLOW_ALLOW_NESTED": "1", "FLOW_BACKOFF_BASE": "0"}

    def run(args, action="noop"):
        return run_cli(LOOP, args, cwd=repo, env={**base_env, "STUB_ACTION": action,
                                                  "STUB_JOB": job_path})

    rc, _, err = run(["--status"])
    check("--status lists the job", rc == 0 and "the work" in err and "pending" in err, err)
    rc, _, err = run(["--dry-run"])
    check("--dry-run names the job and runs nothing",
          rc == 0 and "01-work.md" in err and "dry run" in err, err)
    check("--dry-run left the status alone", "job-status: pending" in pathlib.Path(job_path).read_text())

    rc, _, err = run(["-y"], action="finish-job")
    check("a job runs and reaches done", rc == 0 and "done" in err, err)
    check("the job file ends up done", "job-status: done" in pathlib.Path(job_path).read_text())
    check("a transcript log was written", os.path.isfile(os.path.join(live, "01-work.log")))
    check("the jsonl gitignore was seeded",
          "*.jsonl" in pathlib.Path(live, ".gitignore").read_text())
    rc, _, err = run(["-y"])
    check("a drained queue is a no-op", rc == 0 and "nothing pending" in err, err)

    # a job that never reaches a terminal status is left `failed` for triage, not looped on
    stuck = os.path.join(live, "02-stuck.md")
    pathlib.Path(stuck).write_text(job("pending", title="stuck"))
    rc, _, err = run(["-y", "--retries", "0"])
    check("an unproductive job is given up on", rc == 0 and "giving up" in err, err[-400:])
    check("the stuck job is marked failed", "job-status: failed" in pathlib.Path(stuck).read_text())

    rc, _, err = run(["--nonsense"])
    check("an unknown flag is rejected", rc != 0 and "unknown argument" in err, err)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

sys.exit(check.done())
