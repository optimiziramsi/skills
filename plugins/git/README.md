# git — Claude Code git safety net

Part of the [`opsi`](../../README.md) marketplace.

A single PreToolUse guard that stops Claude from doing the git things you almost never want an agent
to do on its own — regardless of how you write commits. Commit *style* is deliberately **not** here;
it's the separate opt-in [`commit`](../commit) plugin.

## Contents

- `git-guard` (hook): PreToolUse `Bash` — blocks push/pull/fetch (you own remote sync; local
  `git push .` ref updates pass), bulk staging (`add -A`/`--all`/`.`), non-FF `git merge`
  (`--ff-only` passes), protected-branch ops (`checkout`/`switch`/push-refspec onto `main` by
  default), `reset --soft <moving-ref>`, `filter-branch`, `reset --hard`, `--no-verify`, and
  discards of uncommitted work (`clean -f`, `stash drop`, `checkout --`, `restore`). `rebase`,
  `commit --amend`, and `checkout <ref> -- <path>` are **allowed** by default (rebase + FF
  landing flows need them) — re-block via `GIT_GUARD_STRICT`. Fails open; escape hatches
  `GIT_GUARD_OFF=1`, `GIT_GUARD_ALLOW`, `GIT_GUARD_STRICT`, `GIT_GUARD_PROTECTED_BRANCH`.
- `hotfix` (skill + command): Test-first hotfix for a deployed bug: reproduce as a **failing
  test** (committed as proof-of-bug), diagnose on the deployed ref, minimal fix, **cherry-pick
  both ways** (mainline ↔ release branch), all remote ops printed for the user. Deploy mechanics
  stay per-project.

## Pairs with `commit`

- **This plugin** = the git *safety net* (destructive/remote/history ops). Enable it anywhere.
- **[`commit`](../commit)** = the opinionated house *commit style* (bare single-line messages,
  cadence, a format guard, and an end-of-session nudge). Opt in only if you want that convention.

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
> `git push`/`pull`/`fetch` to any remote (the user owns remote sync); pushing to the local-dot
> remote (`git push . HEAD:<branch>`) is a local ref update and passes — unless the refspec targets
> the protected branch.
>
> **Defaults assume a rebase + FF-only landing flow** (rebase onto the mainline, then
> `git merge --ff-only` / `git push . HEAD:<branch>`): `git rebase`, `git commit --amend`, and
> `git checkout <ref> -- <path>` (fix-forward file restore) pass by default. What does NOT pass:
> plain `git merge` (merge commits), bulk staging, remote sync, protected-branch moves,
> soft-resets to a moving ref, and every destructive/discard operation.
>
> **Escape hatches** (the hook reads its **own process env** — an inline `GIT_GUARD_OFF=1 git …`
> prefix does NOT disarm it; set these in your settings' `env` block or in the shell that launches
> `claude`):
>
> - `GIT_GUARD_OFF=1` — disable the guard entirely.
> - `GIT_GUARD_STRICT=rebase,amend,checkout-file` — comma-separated tokens that **re-enable**
>   blocks the default leaves off, for repos that want append-only history: `rebase`
>   (block `git rebase`), `amend` (block `git commit --amend`), `checkout-file`
>   (block `git checkout <ref> -- <path>`).
> - `GIT_GUARD_ALLOW=fetch,bulk-add,merge,protected-branch,soft-reset` — comma-separated tokens
>   that **relax** individual workflow blocks: `fetch` (read-only `git fetch`), `bulk-add`
>   (`git add -A`/`--all`/`.`), `merge` (non-FF `git merge`), `protected-branch` (checkout/switch/
>   push-refspec onto the protected branch), `soft-reset` (`git reset --soft <ref>` beyond
>   `HEAD~N`/sha). The destructive core (push/pull, `reset --hard`, discards, `--no-verify`) has
>   no allow token — that's what `GIT_GUARD_OFF` is for.
> - `GIT_GUARD_PROTECTED_BRANCH=main` — comma-separated protected branch name(s); default `main`
>   (e.g. `main,master`, or your deploy branch).
