# Dev marketplace — test `develop` in real projects without cutting a release

Goal: run unreleased plugin code in other repos (loopers, guards, skills) so a bug costs a commit,
not a public version.

## How the plumbing actually works

- **Marketplaces are keyed by NAME, globally.** `~/.claude/plugins/known_marketplaces.json` holds
  one entry per name; the name comes from `.claude-plugin/marketplace.json` (`optimiziramsi`).
  There is no way to have a github-sourced and a directory-sourced `optimiziramsi` at the same
  time — you **swap the source**, you don't run both.
- **A directory source is a real source, not a symlink to your tree.** `installLocation` points at
  your path, but the *plugin* still materializes into
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` — verified as a byte-identical copy
  for a directory-sourced plugin, exactly like a github one.
- **That cache is version-keyed**, which is why a same-version edit can stay invisible
  ([lesson](lessons/plugin-version-bump-on-edit.md)). Treat "a local path is always fresh" as
  **unproven** until you've watched an edit land with the version unchanged. Until then, iterate on
  a `0.0.N-dev.M` version series — `release.sh` refuses to release any `-dev`/`-rc` version, so the
  series cannot escape by accident.
- **Plugins bind at session start.** Restart CCD after any marketplace/install/version change; a
  resumed session keeps the old binding.

## Switching this machine to the dev source

Remotes and install records are the user's — run these yourself, from a plain terminal:

```bash
claude plugin marketplace remove optimiziramsi && claude plugin marketplace add /Users/YOU/PROJECTS/git/github.com/optimiziramsi/skills
```

The path is this checkout, which sits on `develop`. Every project that already has
`optimiziramsi-skills@optimiziramsi` installed now resolves it from local disk. Restart CCD.

Prefer a fixed path that doesn't move with your branch? Add a worktree and point at that instead:

```bash
git worktree add .claude/worktrees/dev develop
```

## Switching back to the public source

```bash
claude plugin marketplace remove optimiziramsi && claude plugin marketplace add optimiziramsi/skills
```

Do this before validating a release the way consumers will get it — the shallow clone tracks
`main`, so it is the only way to see the *filtered* tree in situ.

## The loop

1. Edit on `develop`, bump to `0.0.N-dev.M`, commit.
2. `claude plugin update optimiziramsi-skills@optimiziramsi` in the test project, restart, exercise it.
3. Repeat until it holds up in the field.
4. Collapse the `-dev` series to the real `0.0.N` and cut the release (`.claude/skills/release/`).
