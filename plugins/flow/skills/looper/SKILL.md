---
name: looper
description: |
  Prepare and manage loop jobs — background tasks executed sequentially by the flow loop runner (bin/loop) using the Claude CLI. Use whenever the user mentions: loop jobs, looper, background jobs, overnight tasks, batch tasks, job queue, breaking work into pieces for automated sequential execution, or triaging/checking loop job status. This skill PREPARES `.agent/loop/` job files and hands the runner command to the user — it never launches the runner itself.
---

# Looper — preparing loop jobs

The loop runner (`bin/loop`, shipped with this plugin) executes a queue of `.agent/loop/*.md` job files. Each job runs as a **fresh, isolated headless Claude session** that reads the job, does the work, commits, and updates the job's own status. This skill is about **writing good job files and handing off** — the runner mechanics live in the shipped script.

You do **not** run the loop yourself. The runner refuses to launch from inside a Claude session (nested sessions are blocked), so your role is to prepare the queue and give the user the command.

## When to use the loop system vs doing it yourself

Use the loop system when:

- Total work is more than ~30 minutes of model time.
- Tasks are independent enough to be separate sessions (each job is a fresh session, no shared memory).
- The user wants to walk away and come back to results (overnight/batch runs).
- A clear audit trail matters (each job records a Report + its own commits).

Do it directly when:

- It's a single focused task you can finish in this session.
- Tasks have hard dependencies on each other's outputs (use `blocked-on:` if you still split).
- The user wants interactive back-and-forth during execution.

Use **grind** instead when the items aren't enumerable upfront — the same mission re-run N times, the model picking each iteration. See the `grind` skill.

## Job file format

Filename: `.agent/loop/YYMMDD_HHMMSS_short_description.md` — 6+6 datetime prefix from `date '+%y%m%d_%H%M%S'`. Space jobs 5–10 seconds apart so alphabetical order is unambiguous (the runner executes in filename order).

```markdown
---
job-status: draft          # draft while writing; flip to pending when ready
model: opus                # default opus; sonnet ONLY for fully mechanical jobs
effort: xhigh              # xhigh or max — the runner does NOT lower this
title: Short human-readable title
max-turns: 50              # advisory (see note); a forcing function on scope
max-retries: 2             # runner retries this many times on failure
blocked-on: 260713_100000_schema.md   # optional; runner waits until deps are `done`
---

## Task

[Focused instructions — the problem, the outcome, where to look. See "Writing good Task sections".]

## References

[Paths to docs/files the executing model should read before starting.]

## Report

<empty — the executing model fills this in>
```

> **`max-turns` is advisory.** The current Claude CLI has no `--max-turns` flag, so the runner can't hard-cap turns; keep the field as a scope forcing-function and as forward-compatible intent. Keep jobs small enough that turns aren't the limiter.

### Status enum

| `job-status` | Meaning | Who sets it |
| --- | --- | --- |
| `draft` | Being written — runner ignores it | you |
| `pending` | Ready to run | you (flip from draft) |
| `blocked` | A `blocked-on` dependency isn't `done` yet — self-heals | runner (computed) |
| `done` | Work complete and committed | executing model |
| `failed` | Tried but couldn't finish — read the Report | executing model (runner as fallback) |
| `skipped` | Not applicable / obsolete | executing model |
| `conflict` | Blocked on an undecided decision/pattern — needs a human | executing model |

## Writing good Task sections — the core skill

The executing model starts fresh with no context beyond the project's CLAUDE.md and this job file. Everything it needs is in Task or References.

**Golden rule: describe the problem and the outcome, not the implementation.** The executing model is a senior engineer. Tell it WHY something needs to change, WHAT "done" looks like, and WHERE to look — then let it choose HOW. Prescriptive step-by-step recipes remove its ability to handle edge cases.

Structure Task as:

1. **Goal** — one sentence: what changes and why.
2. **Context** — the problem/architectural reason driving the change. Enough "why" for judgment calls.
3. **Scope** — which area to work in (dirs, packages, layers). Define scope positively, not as an exception list.
4. **Success criteria** — observable outcomes (builds pass, endpoint returns X, dependency removed), not a checklist of code edits.

**Do:** point to reference files for patterns; explain the motivation; give implementation freedom; define scope positively.

**Don't:** paste code snippets to copy; list exact line numbers (they go stale — describe what to find); write numbered procedures; paste prior-session implementation detail; add long exception lists (if you need many, the scope is poorly defined or the job should split).

**Keep scope small.** Two 10-minute jobs beat one 30-minute job that fails partway.

## Draft → pending workflow

Write files as `job-status: draft` so the runner won't pick up half-written jobs if it's already running. Once all jobs are written and reviewed, flip each to `pending` (a batch flip is fine). Commit them — a running `--watch` loop picks up new pending files automatically.

## Shared state between jobs

Each job is its own session (no shared memory), but the runner executes sequentially and each job commits its work, so **later jobs can read what earlier jobs committed.** Order jobs via timestamp prefixes and state the dependency in Task ("assumes the schema from `260713_100000_schema.md` is committed"). For hard ordering, use `blocked-on:` — the runner enforces it (a job stays effectively blocked until its deps are `done`).

## Optionally append a verification job

A single job that implements *and* verifies its own work is unreliable. For an architectural or cross-cutting batch (refactor, sweep, "convert all", multi-file service change), append a **review job** after the implementation job(s):

- Its Task instructs the executing model to invoke the project's review tooling — e.g. the opsi `review` plugin's `semantic-reviewer` agent, a `code-reviewer` agent, or the project's own checks — and write findings to its Report. It does NOT fix.
- Then a **fix-pass job** reads the review job's Report and fixes the listed issues.

Name the trio with adjacent timestamps so they run in order:

```
260713_220500_fix_service_pattern.md
260713_220510_verify_service_pattern.md
260713_220520_fix_violations_from_verify.md
```

Skip the chain for single-file edits with obvious correctness, pure-doc jobs, or jobs with strong external verification (build/test catches it). Default toward including it for anything cross-cutting — failures cost more than the extra tokens.

## Handing off to the user

**You never launch the runner** (it refuses inside a Claude session anyway). Prepare the queue, then resolve the runner's absolute path and hand the user a copy-paste command they run in a **separate terminal**:

```bash
# Resolve the shipped runner's path (run this to fill in <abs>):
echo "$CLAUDE_PLUGIN_ROOT/bin/loop"
```

Then give them, e.g.:

```
<abs>/bin/loop              # run all pending jobs, then exit
<abs>/bin/loop --watch      # run, then keep polling for new pending jobs
<abs>/bin/loop --status     # show current job statuses
<abs>/bin/loop --dry-run    # preview what would run
<abs>/bin/loop -y           # skip the arm-confirmation (unattended/cron)
```

Optional convenience — symlink it to the short `bin/loop` form (re-run after a plugin update to refresh the path):

```bash
mkdir -p bin && ln -sf "$CLAUDE_PLUGIN_ROOT/bin/loop" bin/loop
```

Before handing off, **pre-flight the tools** the jobs rely on — confirm the build/test/lint commands actually run in this repo. A runner that fails every job on a broken command wastes a whole batch. The runner writes per-job logs to `.agent/loop/{stem}.log` (readable) + `.agent/loop/{stem}.jsonl` (raw) and a session overview to `.agent/loop/runner_*.log`.

### Permissions

The runner executes jobs with full tool permissions (`--dangerously-skip-permissions`) so unattended jobs can edit + commit without prompts — a headless session can't answer a prompt, so a denied tool means a failed job. It requires an explicit arm (interactive "yes", or `-y`) before running. Tell the user this plainly.

### First run — smoke-test it before trusting real work

The runner drives autonomous, committing sessions, so prove the whole chain once on a throwaway job before pointing it at anything real. In a scratch repo or a disposable branch, write one trivial job:

```markdown
.agent/loop/000000_000000_smoke.md
---
job-status: pending
title: Smoke test
---
## Task
Create a file `SMOKE.txt` containing the word "ok", then commit it with a one-line message.
## Report
```

Then, from a **separate terminal** (not inside a Claude session — the runner refuses that): `"$CLAUDE_PLUGIN_ROOT/bin/loop"` (resolve the path first with `echo`). It should ask you to confirm, then run one session. **Confirm all four:** `SMOKE.txt` exists with "ok", the job's `job-status` flipped to `done`, its `## Report` is filled in, and `git log` shows a new commit. Inspect the transcript at `.agent/loop/000000_000000_smoke.log`.

- `--dry-run` and `--status` never call the model — safe to run anytime to sanity-check parsing/queueing.
- If a session **hangs or every job fails on a denied tool**, this CLI's permission flags differ from what the runner assumes — check `bin/loop --help` and set `FLOW_CLAUDE_PERMISSION_MODE` (e.g. `acceptEdits`, or `dontAsk` with an `--allowed-tools` allowlist via `FLOW_EXTRA_CLAUDE_ARGS`).
- If it refuses with "inside a Claude Code session", you launched it from within Claude — open a plain terminal (or, only for testing with a stub, `FLOW_ALLOW_NESTED=1`).

## Triaging failed jobs

When a job is `failed`, read its Report — the executing model records what went wrong before failing. Common modes:

1. **Ran out of scope/turns** — split it, or raise `max-retries` and re-queue.
2. **Build/environment error** — fix the environment first, then re-queue.
3. **Ambiguous task** — rewrite Task more specifically, then re-queue.
4. **Genuine blocker** (`conflict`) — needs a human decision; resolve, then rewrite or mark `skipped`.

Re-queue by editing the file and setting `job-status: pending`.

## Quality defaults

- **opus (4.8) + `xhigh`/`max` by default.** Drop to `sonnet` only for fully mechanical jobs — still at `xhigh`/`max`. Cheap/shallow runs that need rework cost more than one strong run.
- **The `job-status` enum, never checkboxes** — checkboxes are fragile for orchestration.

## What NOT to do

- **Never launch the runner yourself.** Prepare files, print the command, stop.
- Don't pre-write implementation code in the job — describe the outcome.
- Don't create jobs before the user has aligned on the approach.
