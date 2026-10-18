# todo — the .todo parking lot

The `todo@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

Drain the parking lot (**triage-todo** routes items, **feedback** works them now), remove a feature
cleanly (**scope-cut**), and keep `.todo` yours (**todo-readonly-guard**).

## Contents

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

- name: `scope-cut`
  kind: skill + command
  purpose:
    Remove/defer a feature *and everything that trails it* — code, docs, cron, tests, migrations,
    todo.

- name: `todo-readonly-guard`
  kind: hook
  purpose:
    `.todo` is the **user's** parking lot — denies agent writes to it (Edit/Write/Bash
    redirects/`sed -i`/`mv`…); deferrals go to `.todo-inbox`. The user arms a session by replying
    **"ALLOW TODO"** (needed for triage sessions); `TODO_GUARD_SKIP=1` one-off bypass,
    `TODO_GUARD_DISABLE=1` off. Self-test: `--test`.

## Directories

- dir: `.todo`, `.todo-inbox`
  holds: parking lot + agent deferrals (yours, at the repo root)
  naming: free-form

`triage-todo` routes into [`planning`](../planning)'s plans and milestones when that plugin is enabled.

## Enable

```bash
claude plugin install todo@optimiziramsi --scope project
```
