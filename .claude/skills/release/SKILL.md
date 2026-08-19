---
name: release
description: Cut a public release of this marketplace — bump the version, write the CHANGELOG entry, validate, and land a filtered plugin-only tree on `main` via ./release.sh. Use when the user says "cut a release", "make a release", "publish", "ship it", "release vX.Y.Z", or when develop has consumer-visible changes ready to go public. Repo-local — this is NOT shipped to consumers.
---

# Release this marketplace

Two branches, one repo:

- **`develop`** — the working branch. Everything: plugin content, `.agent/`, `.todo`, `CLAUDE.md`,
  `tests.sh`, `release.sh`. All work happens here (or on feature branches off it).
- **`main`** — what the world installs. The plugin and its public docs, nothing else. Written
  **only** by `./release.sh`, never by hand, never by merge.

A consumer's marketplace clone is shallow and tracks `main` alone, so `develop` is invisible to
them — the filter exists so nobody browsing or grepping their plugin cache has to guess which
files are the plugin and which are this repo's own workbench.

## Cutting one

1. **Confirm the scope.** `git log main..develop --oneline` — everything there ships. If any of it
   isn't ready, it doesn't get released; land it later.
2. **Bump `.claude-plugin/plugin.json` `version`.** Consumers only re-materialize on a version
   *change* ([lesson](../../../.agent/lessons/plugin-version-bump-on-edit.md)). Patch for fixes,
   minor for new components. A release that trims or moves shipped files **is** consumer-visible —
   bump for it.
3. **Write the `CHANGELOG.md` section.** `## <version> — <date>` at the top, in the existing
   voice: what changed, and *why it mattered*. `release.sh` refuses to run without this heading.
4. **`./tests.sh`** — must be ALL GREEN. `release.sh` re-runs it and refuses on red.
5. **Commit** the bump + changelog on `develop` (house style: terse imperative subject).
6. **`./release.sh --dry-run`** — read the top-level entry list it prints. Anything on it that
   isn't plugin content or public docs means `DEV_ONLY` in `release.sh` needs a new entry.
7. **`./release.sh`** — lands the filtered tree on `main` and tags `vX.Y.Z`, locally.
8. **Hand the push to the user.** Remotes are theirs; print the two commands and stop.

## Rules

- **Never `git checkout main`** — it's the protected branch, and `release.sh` does its work in a
  throwaway worktree precisely so nothing has to.
- **Never merge `develop` into `main`.** The filter makes every such merge conflict on the
  stripped paths forever. Tree-copy or nothing.
- **A hotfix is just a release.** Fix on `develop` (or a branch off it), then cut. There is no
  cherry-pick path back from `main` and none is wanted.
- **`main` is and stays GitHub's default branch** — the `github` marketplace source resolves the
  default branch, so making `develop` default would ship the working tree to every consumer.

## Testing before you release

Don't cut a release to try something. Point a **directory** marketplace at a local `develop`
worktree instead and install from that — see `.agent/dev-marketplace.md`.
