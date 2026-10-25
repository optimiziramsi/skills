# worktree — the parallel-work protocol

The `worktree@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

Drive one topic on its own git worktree as small reviewed slices, landing to the integration
branch only on the human's explicit OK — and, with `relay`, pair-program by worktree: you comment
in one shared worktree, the primary chat spawns a worktree sub chat per topic. Usually enabled
together with [`worktree-guards`](../worktree-guards), which keeps the edits inside the worktree.

## Contents

- name: `worktree`
  kind: skill + command
  event: `/worktree`, or worktree-mode triggers
  purpose:
    The **parallel-work protocol**: drive one topic on its own worktree as small reviewed
    slices, landing to the integration branch only on the human's explicit OK. No captain — the
    human coordinates; `.agent/worktrees.md` is the board. Covers reserve → plan+example →
    execute → close, plus pause/resume, recycle, and the self-serializing land loop.

- name: `relay`
  kind: skill + command
  event: `/relay`, or relay-mode triggers ("relay mode", "pick up my comments", "start topic X")
  purpose:
    **Pair-programming by worktree.** The human and the primary chat share ONE worktree on a
    branch cut off the integration branch (any name the app gives it); the human edits and leaves comments
    there (staged, never committed — reference only, never landed). The primary turns comments
    into topics, spawns one `worktree`-skill sub chat per topic (fresh session, own worktree off
    the integration branch, title `Relay: <slug>`, self-contained brief with the project's hard
    rules verbatim and a `Done =` line), never codes a topic itself and never proxies the sub
    chat's questions — review, "merge?", "close?" are the human's, in the sub chat. After each
    land it rebases the shared branch (temp commit → rebase → soft reset, edits re-staged),
    strips the comments that landed, annotates files still in flight, reviews the land against
    `Done =` (parked work is reopened — "offloaded for later" is a failure), and tears the sub
    chat down (archive → branch delete → board strike).

- name: `bin/relay-watch`
  kind: cli
  purpose:
    The relay watcher (on PATH while the plugin is enabled; run via the Monitor tool). One line
    per new comment line that carries a handover phrase (`RELAY`, `READY`, `TAKE OVER`, `NOW YOU`,
    `DO IT`, `GO AHEAD`, `YOUR TURN`, `SCHEDULED`, `PICK IT UP`) → the primary proposes the topic
    as a session card; and one per comment file untouched for `RELAY_QUIET_SECS` → the primary
    asks "Address it? Yes / Not yet", never starts on its own. macOS + Linux; `--test` self-test.

The skill and [`worktree-guards`](../worktree-guards) are complementary: the guards are the *mechanism*; the skill is the
*workflow* on top (who takes what, how slices get reviewed and landed). The skill relies on the
write-guard for its leak protection — that one is exact (it resolves a tool's path). The bash
guard is best-effort: it resolves what a shell command would write, but it is not a shell, so
`eval`, a variable holding the path, or a command substitution defeat it. Write as if neither
existed.

## The integration branch

The skill lands work into a configurable **integration branch** — your repo's day-to-day merge
target, substituted for `<integration>` wherever it appears. Worktree branches are cut off it;
nothing reaches it except through the human-gated review→land flow. It assumes the `.agent/` house
layout for its board (`.agent/worktrees.md`) and per-topic plans (`.agent/plan/<slug>.md`).

Declare it in the project's `.claude/settings.json` `env` so the skill and [`git-guard`](../git-guard) agree:

```json
{ "env": { "GIT_GUARD_PROTECTED_BRANCH": "main", "GIT_GUARD_INTEGRATION_BRANCH": "develop" } }
```

A **two-tier** repo protects `main` and lands on `develop`. A **single-branch** repo sets both to
the same name — and there `GIT_GUARD_INTEGRATION_BRANCH` is load-bearing: without it the protected-
branch rule blocks the skill's own `git push . HEAD:<integration>` and no slice can ever land.

## Landing wiring (one-time, per repo)

Git refuses a push to a branch checked out in **any** worktree, so the human's own checkout must
never be what holds `<integration>` — otherwise their branch switches and uncommitted work break
every worker's land. Pin it in a tree nobody edits:

```bash
git worktree add .claude/worktrees/_integration <integration>
```

```bash
git config receive.denyCurrentBranch updateInstead
```

That tree stays clean by construction (so lands are always accepted), locks `<integration>` against
accidental checkout elsewhere, and keeps the landed state materialized for builds. The config must
be **repo-level** — a `--worktree`-scoped `receive.denyCurrentBranch` is ignored. Gitignore
`.claude/worktrees/` so the worktree dirs don't show up as untracked in the main checkout (the land
loop treats a dirty main checkout as a leak signal). *Fallback: keep `<integration>` checked out
nowhere; the push then fast-forwards with no config at all.*

## Settings (relay)

| Env | Default | Meaning |
|---|---|---|
| `RELAY_SUB_MODELS` | `claude-opus-4-8@max,claude-opus-5-5@high,claude-opus-5-5@xhigh` | sub-chat `model@effort` preference list, first available wins |
| `RELAY_PRIMARY_MODELS` | `claude-opus-4-8@max,claude-fable-5-1@high,claude-opus-5-5@xhigh,claude-opus-5-5@max` | the primary's preference list (reported; the human picks the model) |
| `RELAY_QUIET_SECS` | `600` | seconds a comment file must stay untouched before the primary asks about it |

A sub chat can only be started at or below the primary's own model and effort — run the primary
at the top of its list.

## Enable

```bash
claude plugin install worktree@optimiziramsi --scope project
```
