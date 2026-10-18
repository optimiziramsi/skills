# The local marketplace is this folder — whatever branch is checked out is what ships locally

One marketplace registration on this machine, sourced from **this checkout's path**. No swapping,
no second name: `git checkout main` and every project on this computer runs the released plugin;
`git checkout develop` (or a feature branch) and they all run that instead, for as long as you
leave it there.

## Register it (once, yours to run)

```bash
claude plugin marketplace remove optimiziramsi && claude plugin marketplace add "$(git rev-parse --show-toplevel)"
```

Restart CCD. Projects that already have one of its plugins installed (`<plugin>@optimiziramsi`)
now resolve it from disk. The github registration is gone — `main` in this checkout is the
production copy.

## What makes the branch switch actually take

- **Marketplaces are keyed by NAME globally** (`~/.claude/plugins/known_marketplaces.json`), and
  the name comes from `.claude-plugin/marketplace.json`. There is exactly one `optimiziramsi`;
  pointing it at a path is what makes it follow your branch.
- **The install cache is version-keyed**:
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` holds a real copy, verified
  byte-identical for a directory source — it is not a symlink to your tree
  ([lesson](lessons/plugin-version-bump-on-edit.md)). So **a plugin whose tree differs from
  `main`'s must never carry `main`'s version**, or switching branches would be invisible. Each
  plugin versions on its own: `tests.sh` § 8 forces a bump in the same commit as any edit under
  `<plugin>/` (first edit after a release → `X.Y.(Z+1)-dev.1`), and `release.sh` refuses to
  publish a pre-release. An untouched plugin keeps `main`'s version — same tree, nothing to see.
- **Iterating within `develop`** bumps that plugin's dev counter — `0.1.1-dev.1` → `-dev.2` → … Treat "same
  version, new content rebinds" as unproven until you have watched it happen. The proven cycle
  (verified 2026-08-19 across `-dev.1` → `-dev.2` → `-dev.3`): bump + commit → `claude plugin
  update` → restart CCD. `claude plugin marketplace update` was verified NOT to move the install
  at all — it validates the source and rewrites `lastUpdated`, nothing more.
- **Plugins bind at session start.** Restart CCD after a branch switch; a resumed session keeps the
  old binding.
- **`autoUpdate` is on for this registration** (`known_marketplaces.json`), so a version bump in
  the checked-out **working tree — committed or not** — reaches every install on the machine
  within minutes, no `claude plugin update` needed, and binds at the next session start. It updates installed
  plugins only: a plugin the update newly depends on is not installed (observed 2026-10-18).

## Consequences worth knowing before you leave `develop` checked out for days

- **The working tree is what the marketplace reads — but not what an installed plugin runs.**
  The branch you leave checked out decides which `marketplace.json` and which version the
  marketplace advertises; the installed plugin runs from its version-keyed cache copy. So
  an edit here is live nowhere until its plugin's version moves — and then auto-update installs
  the working tree as-is, committed or not; it binds at the next session start.
- **`main` has no workbench.** Checking it out removes `.agent/`, `.todo*`, `CLAUDE.md`,
  `.claude/`, `tests.sh`, `release.sh`, `vendor.sh`, root `lib/` from disk — they are simply not tracked there. They come
  back on `git checkout develop`. Gitignored things (`.agent/loop/`, `.claude/worktrees/`,
  `.idea/`) survive the switch untouched.
- **No agent does the switching.** `main` is the protected branch; `git checkout main` is yours.

## Feature branches carry their own series

`tests.sh` § 8 enforces it: on any branch other than `develop` / `main`, every plugin the branch
changes must be on `X.Y.Z-<branch-slug>.N` — `feat/abc-branch` → `0.1.1-feat-abc-branch.1`, then
`.2`, `.3`. Same
reason the `-dev` counter exists: the install cache is version-keyed, so a branch sharing
`develop`'s version would switch invisibly, and reverting would look like nothing happened. Drop
back to the `-dev` series when you return to `develop`. `release.sh` refuses to publish ANY
pre-release, so a branch series can never reach `main`.

## The loop

1. Edit on `develop` (or a feature branch off it), bump the edited plugin's `-dev` counter,
   commit. `tests.sh` § 8 fails the gate if a plugin's content moved and its version did not.
2. Update the install, then restart CCD — a **marketplace** update alone never moves the pin
   (`installed_plugins.json` keeps the old version and CCD keeps binding it):

   ```bash
   claude plugin update <plugin>@optimiziramsi --scope project
   ```

   CCD equivalent: Manage plugins → the plugin page → Update. Mechanics and the per-scope pin rules
   live in [ADOPTION.md](../ADOPTION.md) § "Updating the plugin".
3. Exercise it in the test project. Leave it for as long as you want.
4. When it holds up: bump each changed plugin to its final `X.Y.Z`, write its
   `<plugin>/CHANGELOG.md` section, and cut the release
   ([`release` skill](../.claude/skills/release/SKILL.md)).
5. `git checkout main` when you want the machine back on production.
