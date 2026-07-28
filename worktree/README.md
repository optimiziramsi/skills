# worktree — Claude Code git-worktree safety

Part of the [`optimiziramsi-skills`](../README.md) plugin (the opsi toolkit).

Guards that keep file edits inside the **active git worktree** so they don't silently leak into the
main checkout or a sibling worktree — mitigating [claude-code
#36182](https://github.com/anthropics/claude-code/issues/36182).
No-ops entirely when you're not in a linked worktree.

## Contents

- name: `worktree`
  kind: skill + command
  event: `/worktree`, or worktree-mode triggers
  purpose:
    The **parallel-work protocol**: drive one topic on its own worktree as small reviewed
    slices, landing to the integration branch only on the human's explicit OK. No captain — the
    human coordinates; `.agent/worktrees.md` is the board. Covers reserve → plan+example →
    execute → close, plus pause/resume, recycle, and the self-serializing land loop.

- name: `worktree-write-guard`
  kind: hook
  event: PreToolUse `Edit|Write|MultiEdit|NotebookEdit`
  purpose: Deny a file write whose absolute path escapes the worktree into the main checkout.

- name: `worktree-bash-guard`
  kind: hook
  event: PreToolUse `Bash`
  purpose:
    Deny a shell write (`>`, `sed -i`, `tee`…) into the main checkout from a worktree. **Opt-in**
    (false-positive-prone): `WORKTREE_BASH_GUARD_ENABLE=1`.

- name: `worktree-leak-detector`
  kind: hook
  event: PostToolUse `Edit|Write|…`
  purpose:
    After an in-worktree edit, warn loudly if the same path went dirty in the main checkout (a
    leak already happened).

- name: `worktree-detect`
  kind: hook
  event: SessionStart
  purpose:
    Flag a session rooted in a linked worktree and nudge toward the `/worktree` protocol. Silent
    in the main checkout; honors `WORKTREE_GUARD_DISABLE=1`.

The skill and the guards are complementary: the guards make leaks *mechanically impossible*; the
skill is the *workflow* on top (who takes what, how slices get reviewed and landed). The skill
relies on the write-guard for its leak protection.

Env toggles (hooks): `WORKTREE_GUARD_DISABLE=1` (write-guard **and** the SessionStart nudge),
`WORKTREE_LEAK_DETECT_DISABLE=1`, `WORKTREE_BASH_GUARD_ENABLE=1` (opt-in),
`WORKTREE_GUARD_MODE=json|exit2` (default `json`).

## The integration branch

The skill lands work into a configurable **integration branch** — your repo's day-to-day merge
target, substituted for `<integration>` wherever it appears. Worktree branches are cut off it;
nothing reaches it except through the human-gated review→land flow. It assumes the `.agent/` house
layout for its board (`.agent/worktrees.md`) and per-topic plans (`.agent/plan/<slug>.md`).

Declare it in the project's `.claude/settings.json` `env` so the skill and the `git` guard agree:

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

## Enable

```json
{ "enabledPlugins": { "optimiziramsi-skills@optimiziramsi": true } }
```

> **Migration note:** these guards may already be wired directly in your
> `~/.claude/settings.json` **and/or the project's `.claude/settings.json`**. If you enable this
> plugin, **remove the duplicate hook entries from BOTH files** to avoid running each guard twice.
