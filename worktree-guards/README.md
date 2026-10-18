# worktree-guards — keep edits inside the active git worktree

The `worktree-guards@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

Guards that keep file edits inside the **active git worktree** so they don't silently leak into the
main checkout or a sibling worktree — mitigating [claude-code
#36182](https://github.com/anthropics/claude-code/issues/36182).
No-ops entirely when you're not in a linked worktree. The workflow on top is the
[`worktree`](../worktree) plugin.

## Contents

- name: `worktree-write-guard`
  kind: hook
  event: PreToolUse `Edit|Write|MultiEdit|NotebookEdit`
  purpose: Deny a file write whose absolute path escapes the worktree into the main checkout.

- name: `worktree-bash-guard`
  kind: hook
  event: PreToolUse `Bash`
  purpose:
    Deny a shell write (`>`, `sed -i`, `tee`…) into the main checkout from a worktree. **Opt-in**
    (false-positive-prone): `WORKTREE_BASH_GUARD_ENABLE=1` — which the [`runners`](../runners) set for the
    headless children they launch in a worktree, where there is no human to un-block a false
    positive and the shell is the widest way out.

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

Env toggles (hooks): `WORKTREE_GUARD_DISABLE=1` (write-guard **and** the SessionStart nudge),
`WORKTREE_LEAK_DETECT_DISABLE=1`, `WORKTREE_BASH_GUARD_ENABLE=1` (opt-in),
`WORKTREE_GUARD_MODE=json|exit2` (default `json`).

All four guards are python3 (stdlib only) over the shared [`lib/hookio.py`](lib/hookio.py) (vendored into each plugin that uses it), so
they have no `jq` dependency and cannot disarm themselves on a missing tool. Their tests live in
[`tests/test_worktree.py`](tests/test_worktree.py), not inside the guards — run them with
`python3 tests/test_worktree.py` (the [`runners`](../runners) plugin carries a vendored copy of
these guards and runs this suite before arming worktree confinement).

## Enable

```bash
claude plugin install worktree-guards@optimiziramsi --scope project
```

> **Migration note:** these guards may already be wired directly in your
> `~/.claude/settings.json` **and/or the project's `.claude/settings.json`**. If you enable this
> plugin, **remove the duplicate hook entries from BOTH files** to avoid running each guard twice.
