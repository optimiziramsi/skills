# flow — work-management for Claude

Part of the [`optimiziramsi-skills`](../README.md) plugin.

How work gets shaped, tracked, and executed across a project — one topic at a time (**plan**), one
strategic initiative across many sessions (**milestone**), removing something cleanly
(**scope-cut**), draining the parking lot (**triage-todo**), and running large batches of work
autonomously in the background (**looper** / **grind**, driven from a **collab** session). All of it
runs on a shared directory convention any project can adopt.

## Contents

- name: `plan`
  kind: skill + command
  purpose:
    Single-topic implementation plans in `.agent/plan/`. One plan = one topic = its source of
    truth.

- name: `milestone`
  kind: skill + command
  purpose:
    Multi-session strategic initiatives in `.agent/milestone/{date}_{slug}/`, each its own
    scope/steps/progress.

- name: `scope-cut`
  kind: skill + command
  purpose:
    Remove/defer a feature *and everything that trails it* — code, docs, cron, tests, migrations,
    todo.

- name: `triage-todo`
  kind: skill + command
  purpose:
    Walk `.todo` / `.todo-inbox` and route each item to a plan, milestone, scope-cut, scheduled
    task, or the bin.

- name: `feedback`
  kind: skill + command
  purpose:
    Process `.todo` items **now**: mirror them into the agent-owned `.agent/FEEDBACK.md` ledger
    (Open → In Progress → Done/Wont Do, 2-round retention) and work them one at a time. The "work
    it" sibling of triage-todo's "route it".

- name: `todo-readonly-guard`
  kind: hook
  purpose:
    `.todo` is the **user's** parking lot — denies agent writes to it (Edit/Write/Bash
    redirects/`sed -i`/`mv`…); deferrals go to `.todo-inbox`. The user arms a session by replying
    **"ALLOW TODO"** (needed for triage sessions); `TODO_GUARD_SKIP=1` one-off bypass,
    `TODO_GUARD_DISABLE=1` off. Self-test: `--test`.

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
    SessionStart: re-stamps `<claude-config>/plugins/data/optimiziramsi-skills/current` at the
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

## The directory convention

These skills read and write a small set of dirs, kept **under `.agent/`** (the agent's working
namespace) so they don't clutter your repo root. Adopt the ones you use; each degrades gracefully if
a dir is absent.

- dir: `.agent/plan/`
  holds: single-topic plans
  naming: `YYMMDD_HHMMSS_{topic}.md`

- dir: `.agent/milestone/{date}_{slug}/`
  holds: strategic initiatives (folder each)
  naming: `YYMMDD_{slug}/`

- dir: `.agent/milestones.md`
  holds: active-milestones index (what's in flight)
  naming: —

- dir: `.agent/loop/`
  holds: background job queue + logs
  naming: `YYMMDD_HHMMSS_{topic}.md`

- dir: `.agent/grind/`
  holds: grind missions + memory logs
  naming: `YYMMDD_HHMMSS_{topic}.md`

- dir: `.agent/bin/`
  holds: your own symlinks to the runners — machine-local, **gitignored**
  naming: `loop`, `grind`

- dir: `.todo`, `.todo-inbox`
  holds: parking lot + agent deferrals (yours, at the repo root)
  naming: free-form

- dir: `.docs/`
  holds: your architecture/specs — project-owned; skills *link* here, never write it
  naming: —

Timestamps come from `date '+%y%m%d_%H%M%S'` (or `+%y%m%d` for milestones). Closed plans/milestones
move to an `archive/` subdir — never edited again, never referenced by a live file.

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
  ptr="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/data/optimiziramsi-skills/current"
  ln -sfn "$ptr/flow/bin/loop"  .agent/bin/loop
  ln -sfn "$ptr/flow/bin/grind" .agent/bin/grind
  echo '.agent/bin/' >> .gitignore
  ```

  They point through `…/data/optimiziramsi-skills/current`, a single per-machine pointer the
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
  In a linked worktree the runners inject the `worktree` topic's PreToolUse guards into every child
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
  ordering, grind's iteration memory — is fragile in bash; `python3` is already assumed by the
  `git` plugin's hook.) Escape hatches via env: `CLAUDE_BIN`, `FLOW_ALLOW_NESTED`,
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

```json
{
  "extraKnownMarketplaces": {
    "optimiziramsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "optimiziramsi-skills@optimiziramsi": true }
}
```

Then `/plan`, `/milestone`, `/scope-cut`, `/triage-todo`, `/looper`, `/grind`, `/collab` — or just
describe the work and the matching skill triggers on its own.
