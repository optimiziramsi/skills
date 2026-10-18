# planning — plans and milestones

The `planning@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

How work gets shaped across a project — one topic at a time (**plan**), one strategic initiative
across many sessions (**milestone**).

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

## Directories

Kept **under `.agent/`** so they don't clutter your repo root; each degrades gracefully if absent.

- dir: `.agent/plan/`
  holds: single-topic plans
  naming: `YYMMDD_HHMMSS_{topic}.md`

- dir: `.agent/milestone/{date}_{slug}/`
  holds: strategic initiatives (folder each)
  naming: `YYMMDD_{slug}/`

- dir: `.agent/milestones.md`
  holds: active-milestones index (what's in flight)
  naming: —

- dir: `.docs/`
  holds: your architecture/specs — project-owned; skills *link* here, never write it
  naming: —

Timestamps come from `date '+%y%m%d_%H%M%S'` (or `+%y%m%d` for milestones). Closed plans/milestones
move to an `archive/` subdir — never edited again, never referenced by a live file.

## Enable

```bash
claude plugin install planning@optimiziramsi --scope project
```

Then `/plan`, `/milestone` — or describe the work and the matching skill triggers.
