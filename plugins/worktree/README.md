# worktree — Claude Code git-worktree safety

Part of the [`opsi`](../../README.md) marketplace.

Guards that keep file edits inside the **active git worktree** so they don't silently leak into the
main checkout or a sibling worktree — mitigating [claude-code
#36182](https://github.com/anthropics/claude-code/issues/36182).
No-ops entirely when you're not in a linked worktree.

## Contents

- `worktree` (skill + command; `/worktree`, or worktree-mode triggers): The **parallel-work
  protocol**: drive one topic on its own worktree as small reviewed slices, landing to the
  integration branch only on the human's explicit OK. No captain — the human coordinates;
  `.agent/worktrees.md` is the board. Covers reserve → plan+example → execute → close, plus
  pause/resume, recycle, and the self-serializing land loop.
- `worktree-write-guard` (hook; PreToolUse `Edit|Write|MultiEdit|NotebookEdit`): Deny a file
  write whose absolute path escapes the worktree into the main checkout.
- `worktree-bash-guard` (hook; PreToolUse `Bash`): Deny a shell write (`>`, `sed -i`, `tee`…)
  into the main checkout from a worktree. **Opt-in** (false-positive-prone):
  `WORKTREE_BASH_GUARD_ENABLE=1`.
- `worktree-leak-detector` (hook; PostToolUse `Edit|Write|…`): After an in-worktree edit, warn
  loudly if the same path went dirty in the main checkout (a leak already happened).
- `worktree-detect` (hook; SessionStart): Flag a session rooted in a linked worktree and nudge
  toward the `/worktree` protocol. Silent in the main checkout.

The skill and the guards are complementary: the guards make leaks *mechanically impossible*; the
skill is the *workflow* on top (who takes what, how slices get reviewed and landed). The skill
relies on the write-guard for its leak protection.

Env toggles (hooks): `WORKTREE_GUARD_DISABLE=1`, `WORKTREE_LEAK_DETECT_DISABLE=1`,
`WORKTREE_GUARD_MODE=json|exit2` (default `json`).

## The integration branch

The skill lands work into a configurable **integration branch** — substitute your repo's day-to-day
merge target (`main`, `develop`, or `trunk`) for `<integration>` wherever it appears. Worktree
branches are cut off it; nothing reaches it except through the human-gated review→land flow. It
assumes the `.agent/` house layout for its board (`.agent/worktrees.md`) and per-topic plans
(`.agent/plan/<slug>.md`).

## Enable

```json
{ "enabledPlugins": { "worktree@opsi": true } }
```

> **Migration note:** these guards may already be wired directly in your
> `~/.claude/settings.json` **and/or the project's `.claude/settings.json`**. If you enable this
> plugin, **remove the duplicate hook entries from BOTH files** to avoid running each guard twice.
