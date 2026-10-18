# lessons — learn once, keep it

The `lessons@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

Capture what a session learned and route it where every future session finds it: **retro**
harvests, **lessons** curates `.agent/lessons/` (one file per lesson, indexed), **lesson-scout**
looks up prior art before you re-debug something.

## Contents

- name: `retro`
  kind: skill + command
  purpose:
    Session-end harvest — route learnings to lessons/rules/docs, merge-don't-append, compact at
    caps, **apply-safe / propose-risky**, changelog, commit.

- name: `lessons`
  kind: skill + command
  purpose:
    Capture + curate one durable lesson in `.agent/lessons/` — kebab-slug file, README index,
    two-axis surfacing (enforced-hook / routed-doc / indexed × High/Mid/Low caps), dedup, prune,
    fold-up.

- name: `lesson-scout`
  kind: agent
  purpose:
    Prior-art lookup — searches `.agent/lessons/` before you re-debug something. Read-only.

Rule and cap changes that `retro` proposes go through [`instructions`](../instructions)'
`rules-change` when that plugin is enabled.

## Enable

```bash
claude plugin install lessons@optimiziramsi --scope project
```
