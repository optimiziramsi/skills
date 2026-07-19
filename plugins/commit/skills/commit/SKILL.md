---
name: commit
description: How and when to make git commits. Use proactively — commit at topic close (one logical topic = one commit), then pause for the user's review before starting the next topic, UNLESS the user has opted into commit-as-you-go. Also use whenever explicitly committing or saving changes, or when a git commit is about to happen. Triggers: "commit", "save changes", "commit this", finishing a coherent chunk of work.
---

# Commit

How and when to commit. Two parts — **cadence** (when) and **format** (how). These rules are for
model-authored commits.

## Cadence — topic close, then pause for review

If the project defines its own commit cadence, the project's rule wins over this skill's
topic-close default.

The default: **one logical topic = one commit, made at topic close, followed by a pause for the
user's review** before the next topic starts.

- When a logical unit of work is done (a feature, a fix, a config change), commit it as **one
  commit**. Don't leave finished work uncommitted across topic boundaries.
- After the topic-close commit, **pause** — verify your own work first (build/lint/tests as
  appropriate), then present it and let the user review before starting the next topic. Batching
  several topic closes before pausing removes the user's control point.
- Within a topic, prefer one commit at the end over many partial commits — partial commits clutter
  history with intermediate states. If a topic genuinely spans independent stages, separate
  commits are fine.
- One logical change per commit; don't bundle unrelated changes.

**Opt-in alternative — commit-as-you-go.** If the user asks for it ("commit as you go", "don't
wait for my review", an autonomous/batch run where nobody is watching), commit each completed
logical unit automatically without pausing, and keep going. This is an explicit opt-in, not the
default — don't slide into it on your own.

**Opt-out.** If the user says "don't commit", "hold off on commits", or "I'll commit myself" —
for the task or the whole session — respect it until they say otherwise. (A session may open with
exactly that instruction.)

**Do NOT commit:**

- Mid-way through a multi-file change that would leave the tree broken.
- Scratch / temp / experimental files, or anything that looks like secrets (`.env`, `secrets/…`).
- Human-authored uncommitted work you didn't create — leave it, don't "tidy" it.

## Format — single line, imperative, describes the change

- **Single line. No body. No trailers. No `Co-Authored-By`.**
- Imperative mood: "add X", "fix Y", "remove Z", "refactor W".
- Describe **what the commit contains**, not the workflow around it.

```bash
# correct
git commit -m "add permission system with role-based access"
git commit -m "fix race condition in score reporting"
git commit -m "remove unused projection rebuild endpoint"

# wrong — has a body or trailers
git commit -m "add permissions" -m "implements role checks…"

# wrong — vague, meta, or a workflow prefix
git commit -m "wip"
git commit -m "phase 3: permissions"
git commit -m "updates"
git commit -m "commit for review"
```

If a commit unavoidably touches several things, summarize the dominant change:
`refactor server package into boot/services/utils structure`.

## Staging — stage by name

Stage specific files. Avoid `git add -A` / `git add .` unless you're certain the working tree holds
nothing unexpected.

```bash
# correct
git add src/permissions/index.ts src/permissions/types.ts

# risky — may pick up .env, debug files, scratch work
git add -A
```

## Never without explicit user permission

- **Never push, pull, or fetch** — the user owns remote sync. (Pushing to the local `.` remote,
  `git push . HEAD:<branch>`, is a local ref update, not a remote op.)
- **Never amend** an existing commit — create a new one. Amending rewrites history.
- **Never force-push** or `filter-branch` — published history is append-only. (Local `git rebase`
  as part of a rebase + `merge --ff-only` landing flow is fine.)
- **Never `git reset --hard`** (or `--merge`/`--keep`) — it clobbers the worktree. Plain
  `git reset <file>` to unstage is fine.
- **Never discard uncommitted work** — no `git clean -f`, `git stash drop/clear`,
  `git checkout -- <path>` / `checkout .`, or `git restore` (only `restore --staged` to unstage).
  The tree may hold the user's WIP.
- **Never skip hooks** (`--no-verify`). If a hook fails, fix the underlying cause.

If a workflow seems to require any of these, **stop and ask** the user.

> **Enforcement is split across two plugins.** The *message format* above (single line, no
> `Co-Authored-By`, no body) is enforced by this plugin's `commit-format` hook (escape hatch
> `COMMIT_FORMAT_OFF=1`). The *destructive git ops* (push/pull/fetch/bulk `git add`/non-FF merges/
> protected-branch moves/`reset --hard`/discards/`--no-verify`) are enforced by the separate `git`
> plugin's `git-guard` hook — enable the `git` plugin for that safety net (escape hatch
> `GIT_GUARD_OFF=1`; the amend guidance above is not hook-enforced by default — see that plugin's
> `GIT_GUARD_STRICT`). Both fail open.

## Human commits

Human commits may use `wip`, `tmp`, or other shorthand. That's fine — don't "fix" them or ask about
them. These rules apply to model-authored commits only.
