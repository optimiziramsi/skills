# runners — unattended background work

The `runners@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

Run large batches of work autonomously in the background: **looper** queues independent jobs,
**grind** re-runs one mission until done, **collab** is the playbook for a chat that drives
decisions while the runners execute. The skills PREPARE files under `.agent/`; the shipped
runners EXECUTE them.

## Contents

- name: `looper`
  kind: skill + command
  purpose:
    Prepare `.agent/loop/` job files — a queue of independent tasks the runner executes as
    separate background sessions.

- name: `grind`
  kind: skill + command
  purpose:
    Prepare a `.agent/grind/` mission — the same prompt re-run N times, the model picking 1–3
    items per iteration until done.

- name: `collab`
  kind: skill + command
  purpose:
    The playbook for long "chat drives decisions, looper executes" sessions that keep the main
    context lean.

- name: `runner-link`
  kind: hook
  purpose:
    SessionStart: re-stamps `<claude-config>/plugins/data/optimiziramsi-runners/current` at the
    plugin version actually loaded, so every repo's `.agent/bin/{loop,grind}` links follow an
    update.
    Refreshes existing links only — never creates one. Off: `FLOW_LINK_OFF=1`.

- name: `bin/loop`
  kind: runner
  purpose:
    Executes the `.agent/loop/` queue: one fresh headless `claude` session per pending job, with
    `blocked-on` ordering, retries + backoff, crash-resume (`running` marker + resume prompt),
    `--watch`, `--status`, `--dry-run`.

- name: `bin/grind`
  kind: runner
  purpose:
    Executes one `.agent/grind/` mission repeatedly: cross-iteration log memory, `done-check`,
    `max-iterations` cap, per-iteration watchdog + dirty-tree guard + 4-attempt retry state +
    productivity gate + transient long backoff, enforced `YYMMDD_HHMMSS_{topic}.md` naming,
    `--once`/`--count`/`--reset`/`--status`.

## Directories

- dir: `.agent/loop/`
  holds: background job queue + logs
  naming: `YYMMDD_HHMMSS_{topic}.md`

- dir: `.agent/grind/`
  holds: grind missions + memory logs
  naming: `YYMMDD_HHMMSS_{topic}.md`

- dir: `.agent/bin/`
  holds: your own symlinks to the runners — machine-local, **gitignored**
  naming: `loop`, `grind`

## The runners (`loop`, `grind`)

The looper and grind skills PREPARE files; the shipped runners EXECUTE them. Each unit of work runs
as a **fresh, isolated headless `claude` session** that does the work, commits, and updates its own
status — the runner never commits.

- **Launched by you, in a separate terminal.** The runners refuse to start from inside a Claude
  session (nested sessions are blocked), so the skills hand you a copy-paste command.
- **Link them once and the command is just `.agent/bin/loop`.** Two symlinks, made by you (the
  `scaffold` / `looper` / `grind` skills do it on request), **gitignored, never committed** — they
  hold your `$HOME`, so they are yours, not the repo's:

  ```bash
  mkdir -p .agent/bin
  ptr="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/data/optimiziramsi-runners/current"
  ln -sfn "$ptr/bin/loop"  .agent/bin/loop
  ln -sfn "$ptr/bin/grind" .agent/bin/grind
  echo '.agent/bin/' >> .gitignore
  ```

  They point through `…/data/optimiziramsi-runners/current`, a single per-machine pointer the
  `runner-link` hook re-stamps at every session start to the plugin version actually loaded. So one
  link survives every plugin update, no path anywhere encodes a version, and a stale copy of the
  launcher cannot exist. Each worktree that wants the short command links its own (or launch from
  the checkout root with `--worktree`, which is the normal way).
- **Worktrees: `--worktree NAME`, launched from the checkout root.** The runners are cwd-relative
  (job/mission dir, the repo they commit into), so selecting a worktree is just picking the cwd.
  NAME is a branch, a worktree directory name, a path, a unique substring of either, or `root`;
  ambiguity is an error listing candidates, never a guess. `loop --worktree all` surveys every
  worktree, arms once, and runs a child runner per tree with a queue (not with `--watch`).
- **Worktree runs are confined, and the confinement is proven first — in two independent steps.**
  In a linked worktree the runners inject the [`worktree-guards`](../worktree-guards) PreToolUse guards
  (a copy vendored into this plugin, so it works without that plugin enabled) into every child
  (arming the opt-in bash guard, since a run guarded only on the file tools is confined on paper
  only). Then: (1) both guards are fired at **this worktree's real paths** with synthetic payloads —
  no model, deterministic — and must deny; (2) a one-off **leak-probe** session establishes the
  other half, which is a property of the CLI rather than of the guards: that a PreToolUse `deny`
  fires *and is honored* in a headless child under `--dangerously-skip-permissions`. The probe asks
  the model only for two ordinary writes inside its own worktree and injects a witness hook that
  denies them, so nothing in it reads as an escape attempt. Verdicts: `enforced` (witness deny seen,
  neither file exists) arms; `unenforced` (a denied call took effect anyway) **refuses**;
  `unconfirmed` (the session made no guarded tool call) **also refuses**, because unproven is not
  proven — `FLOW_PROBE_LENIENT=1` downgrades that one to a warning. Every
  non-green verdict keeps the probe transcript and prints its path. Main-checkout runs are
  unchanged. `FLOW_WORKTREE_UNSAFE=1` skips the lot, `FLOW_PROBE_MODEL` picks the probe model.
- **Full permissions, explicit arm.** Jobs run with `--dangerously-skip-permissions` (a headless
  session can't answer a prompt, so unattended edits/commits need it). The runner requires an
  interactive "yes" — or `-y` for cron/unattended.
- **Python 3, stdlib only.** No pip installs. (Chosen over bash because the full contract —
  frontmatter parsing, a status state machine, retries + backoff, watch polling, blocked-on
  ordering, grind's iteration memory — is fragile in bash; `python3` is already assumed by every
  hook in this marketplace.) Escape hatches via env: `CLAUDE_BIN`, `FLOW_ALLOW_NESTED`,
  `FLOW_CLAUDE_PERMISSION_MODE`, `FLOW_EXTRA_CLAUDE_ARGS`, `FLOW_BACKOFF_BASE`,
  `FLOW_LONG_BACKOFF_BASE`, `FLOW_ITER_TIMEOUT_SECS`, `FLOW_ITER_PAUSE_SECS`. Run
  `.agent/bin/loop --help` / `.agent/bin/grind --help` for the full flag list.
- **A runner lands its own logs, and ignores the other runner's.** Each runner commits the
  session logs it wrote (its job dir only, path-limited, `FLOW_NO_LOG_COMMIT=1` to opt out) at the
  end of a run — the files are worth keeping, and leaving them uncommitted hands the next run a
  dirty tree. `grind`'s dirty-tree gate judges runner-owned files by the **file's own directory**,
  so a `loop` session's logs in `.agent/loop/` never read as work in progress in `.agent/grind/`.
- **Resilient by default.** `grind` guards every iteration: a wall-clock watchdog
  (900s default) kills hung sessions; a dirty-tree guard refuses to start on uncommitted changes
  (auto-resuming a previously interrupted iteration); a productivity gate only advances on a clean
  tree with a tagged commit or status flip; unproductive iterations retry up to 4 attempts with a
  continuation prompt (finish / revert / skip the in-flight item); transient API errors get long
  10–60 min backoffs that don't burn the attempt budget. `loop` marks each job `running` at
  launch — a crashed runner leaves that marker, and the next run resumes the job with a prompt
  pointing at its Report.

## Enable

```bash
claude plugin install runners@optimiziramsi --scope project
```

Then `/looper`, `/grind`, `/collab` — or describe the work and the matching skill triggers.
