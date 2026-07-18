# flow — work-management for Claude

Part of the [`opsi`](../../README.md) marketplace.

How work gets shaped, tracked, and executed across a project — one topic at a time (**plan**), one
strategic initiative across many sessions (**milestone**), removing something cleanly (**scope-cut**),
draining the parking lot (**triage-todo**), and running large batches of work autonomously in the
background (**looper** / **grind**, driven from a **collab** session). All of it runs on a shared
directory convention any project can adopt.

## Contents

| Kind | Name | Purpose |
|---|---|---|
| skill + command | `plan` | Single-topic implementation plans in `.agent/plan/`. One plan = one topic = its source of truth. |
| skill + command | `milestone` | Multi-session strategic initiatives in `.agent/milestone/{date}_{slug}/`, each its own scope/steps/progress. |
| skill + command | `scope-cut` | Remove/defer a feature *and everything that trails it* — code, docs, cron, tests, migrations, todo. |
| skill + command | `triage-todo` | Walk `.todo` / `.todo-inbox` and route each item to a plan, milestone, scope-cut, scheduled task, or the bin. |
| skill + command | `feedback` | Process `.todo` items **now**: mirror them into the agent-owned `.agent/FEEDBACK.md` ledger (Open → In Progress → Done/Wont Do, 2-round retention) and work them one at a time. The "work it" sibling of triage-todo's "route it". |
| hook | `todo-readonly-guard` | `.todo` is the **user's** parking lot — denies agent writes to it (Edit/Write/Bash redirects/`sed -i`/`mv`…); deferrals go to `.todo-inbox`. The user arms a session by replying **"ALLOW TODO"** (needed for triage sessions); `TODO_GUARD_SKIP=1` one-off bypass, `TODO_GUARD_DISABLE=1` off. Self-test: `--test`. |
| skill + command | `looper` | Prepare `.agent/loop/` job files — a queue of independent tasks the runner executes as separate background sessions. |
| skill + command | `grind` | Prepare a `.agent/grind/` mission — the same prompt re-run N times, the model picking 1–3 items per iteration until done. |
| skill + command | `collab` | The playbook for long "chat drives decisions, looper executes" sessions that keep the main context lean. |
| runner | `bin/loop` | Executes the `.agent/loop/` queue: one fresh headless `claude` session per pending job, with `blocked-on` ordering, retries + backoff, `--watch`, `--status`, `--dry-run`. |
| runner | `bin/grind` | Executes one `.agent/grind/` mission repeatedly: cross-iteration log memory, `done-check`, `max-iterations` cap, `--once`/`--reset`/`--status`. |

## The directory convention

These skills read and write a small set of dirs, kept **under `.agent/`** (the agent's working
namespace) so they don't clutter your repo root. Adopt the ones you use; each degrades gracefully if a
dir is absent.

| Dir | Holds | Naming |
|---|---|---|
| `.agent/plan/` | single-topic plans | `YYMMDD_HHMMSS_{topic}.md` |
| `.agent/milestone/{date}_{slug}/` | strategic initiatives (folder each) | `YYMMDD_{slug}/` |
| `.agent/milestones.md` | active-milestones index (what's in flight) | — |
| `.agent/loop/` | background job queue + logs | `YYMMDD_HHMMSS_{topic}.md` |
| `.agent/grind/` | grind missions + memory logs | `YYMMDD_HHMMSS_{topic}.md` |
| `.todo`, `.todo-inbox` | parking lot + agent deferrals (yours, at the repo root) | free-form |
| `.docs/` | your architecture/specs — project-owned; skills *link* here, never write it | — |

Timestamps come from `date '+%y%m%d_%H%M%S'` (or `+%y%m%d` for milestones). Closed plans/milestones
move to an `archive/` subdir — never edited again, never referenced by a live file.

## The runner (`bin/loop`, `bin/grind`)

The looper and grind skills PREPARE files; the shipped runners EXECUTE them. Each unit of work runs
as a **fresh, isolated headless `claude` session** that does the work, commits, and updates its own
status — the runner never commits.

- **Launched by you, in a separate terminal.** The runners refuse to start from inside a Claude
  session (nested sessions are blocked), so the skills hand you a copy-paste command. `$CLAUDE_PLUGIN_ROOT`
  isn't set in your shell, so the skill resolves the absolute path for you — or symlink it once:
  `ln -sf "$CLAUDE_PLUGIN_ROOT/bin/loop" bin/loop`.
- **Full permissions, explicit arm.** Jobs run with `--dangerously-skip-permissions` (a headless
  session can't answer a prompt, so unattended edits/commits need it). The runner requires an
  interactive "yes" — or `-y` for cron/unattended.
- **Python 3, stdlib only.** No pip installs. (Chosen over bash because the full contract —
  frontmatter parsing, a status state machine, retries + backoff, watch polling, blocked-on
  ordering, grind's iteration memory — is fragile in bash; `python3` is already assumed by the
  `git` plugin's hook.) Escape hatches via env: `CLAUDE_BIN`, `FLOW_ALLOW_NESTED`,
  `FLOW_CLAUDE_PERMISSION_MODE`, `FLOW_BACKOFF_BASE`. Run `bin/loop --help` / `bin/grind --help` for
  the full flag list.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "opsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "flow@opsi": true }
}
```

Then `/plan`, `/milestone`, `/scope-cut`, `/triage-todo`, `/looper`, `/grind`, `/collab` — or just
describe the work and the matching skill triggers on its own.
