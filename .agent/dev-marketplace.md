# The local marketplace is this folder — whatever branch is checked out is what ships locally

One marketplace registration on this machine, sourced from **this checkout's path**. No swapping,
no second name: `git checkout main` and every project on this computer runs the released plugin;
`git checkout develop` (or a feature branch) and they all run that instead, for as long as you
leave it there.

## Register it (once, yours to run)

```bash
claude plugin marketplace remove optimiziramsi && claude plugin marketplace add "$(git rev-parse --show-toplevel)"
```

Restart CCD. Projects that already have `optimiziramsi-skills@optimiziramsi` installed now resolve
it from disk. The github registration is gone — `main` in this checkout is the production copy.

## What makes the branch switch actually take

- **Marketplaces are keyed by NAME globally** (`~/.claude/plugins/known_marketplaces.json`), and
  the name comes from `.claude-plugin/marketplace.json`. There is exactly one `optimiziramsi`;
  pointing it at a path is what makes it follow your branch.
- **The install cache is version-keyed**:
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` holds a real copy, verified
  byte-identical for a directory source — it is not a symlink to your tree
  ([lesson](lessons/plugin-version-bump-on-edit.md)). So **`develop`'s version must never equal
  `main`'s**, or switching branches would be invisible. `release.sh` enforces this from both ends:
  it refuses to publish a `-dev`/`-rc` version, and after landing a release it opens the next
  `0.0.N-dev.1` on `develop`.
- **Iterating within `develop`** bumps the dev counter — `0.0.12-dev.1` → `-dev.2` → … Treat "same
  version, new content rebinds" as unproven until you have watched it happen. The proven cycle
  (verified 2026-08-19 across `-dev.1` → `-dev.2` → `-dev.3`): bump + commit → `claude plugin
  update` → restart CCD. `claude plugin marketplace update` was verified NOT to move the install
  at all — it validates the source and rewrites `lastUpdated`, nothing more.
- **Plugins bind at session start.** Restart CCD after a branch switch; a resumed session keeps the
  old binding.

## Consequences worth knowing before you leave `develop` checked out for days

- **The working tree is what the marketplace reads — but not what an installed plugin runs.**
  The branch you leave checked out decides which `marketplace.json` and which version the
  marketplace advertises; the installed plugin runs from its version-keyed cache copy. So
  uncommitted edits here are *not* live anywhere until you bump + `claude plugin update` + restart.
- **`main` has no workbench.** Checking it out removes `.agent/`, `.todo*`, `CLAUDE.md`,
  `.claude/`, `tests.sh`, `release.sh` from disk — they are simply not tracked there. They come
  back on `git checkout develop`. Gitignored things (`.agent/loop/`, `.claude/worktrees/`,
  `.idea/`) survive the switch untouched.
- **No agent does the switching.** `main` is the protected branch; `git checkout main` is yours.

## The loop

1. Edit on `develop` (or a feature branch off it), bump the `-dev` counter, commit.
2. Update the install, then restart CCD — a **marketplace** update alone never moves the pin
   (`installed_plugins.json` keeps the old version and CCD keeps binding it):

   ```bash
   claude plugin update optimiziramsi-skills@optimiziramsi --scope user
   ```

   CCD equivalent: Manage plugins → the plugin page → Update. Mechanics and the per-scope pin rules
   live in [ADOPTION.md](../ADOPTION.md) § "Updating the plugin".
3. Exercise it in the test project. Leave it for as long as you want.
4. When it holds up: bump to the final `0.0.N`, write the `CHANGELOG.md` section, and cut the
   release ([`release` skill](../.claude/skills/release/SKILL.md)).
5. `git checkout main` when you want the machine back on production.
