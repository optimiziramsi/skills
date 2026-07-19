# git — Claude Code git safety net

Part of the [`opsi`](../../README.md) marketplace.

A single PreToolUse guard that stops Claude from doing the git things you almost never want an agent
to do on its own — regardless of how you write commits. Commit *style* is deliberately **not** here;
it's the separate opt-in [`commit`](../commit) plugin.

## Contents

| Kind | Name | Purpose |
|---|---|---|
| hook | `git-guard` | PreToolUse `Bash` — blocks push/pull (you own remote sync; local `git push .` ref updates pass), `commit --amend`, rebase/`filter-branch`, `reset --hard`, `--no-verify`, and discards of uncommitted work (`clean -f`, `stash drop`, `checkout --`, `restore`). Fails open; escape hatches `GIT_GUARD_OFF=1` and `GIT_GUARD_ALLOW`. |
| skill + command | `hotfix` | Test-first hotfix for a deployed bug: reproduce as a **failing test** (committed as proof-of-bug), diagnose on the deployed ref, minimal fix, **cherry-pick both ways** (mainline ↔ release branch), all remote ops printed for the user. Deploy mechanics stay per-project. |

## Pairs with `commit`

- **This plugin** = the git *safety net* (destructive/remote/history ops). Enable it anywhere.
- **[`commit`](../commit)** = the opinionated house *commit style* (bare single-line messages, cadence,
  a format guard, and an end-of-session nudge). Opt in only if you want that convention.

Enable `git` alone to get the guardrails while keeping your own commit format.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "opsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "git@opsi": true }
}
```

> **Note:** enabling this plugin activates `git-guard` in every project that enables it. It blocks
> `git push`/`pull` to any remote (the user owns remote sync); pushing to the local-dot remote
> (`git push . HEAD:<branch>`) is a local ref update and passes.
>
> **Escape hatches** (the hook reads its **own process env** — an inline `GIT_GUARD_OFF=1 git …`
> prefix does NOT disarm it; set these in your settings' `env` block or in the shell that launches
> `claude`):
>
> - `GIT_GUARD_OFF=1` — disable the guard entirely.
> - `GIT_GUARD_ALLOW=rebase,amend,checkout-file` — comma-separated tokens that suppress individual
>   blocks: `rebase` (`git rebase` — needed by rebase-based landing flows, e.g. the worktree
>   plugin), `amend` (`git commit --amend`), `checkout-file` (`git checkout <ref> -- <path>`).
