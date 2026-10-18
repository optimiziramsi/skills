# Two marketplaces: `optimiziramsi` (released) and `optimiziramsi-dev` (this checkout)

The same plugins, published under two marketplace names so a machine can carry both:

- **`optimiziramsi`** — GitHub, `main` only: the released plugins. What projects normally enable
  (`<plugin>@optimiziramsi`).
- **`optimiziramsi-dev`** — this checkout's **working tree**, whatever branch is checked out. A
  project opts in by enabling `<plugin>@optimiziramsi-dev` instead — this repo does, to dogfood.

The name comes from `.claude-plugin/marketplace.json`: the working tree always says
`optimiziramsi-dev` (tests.sh § 2 checks it), and `release.sh` renames it to `optimiziramsi` in the
published tree. Marketplaces are keyed by NAME globally (`~/.claude/plugins/known_marketplaces.json`),
which is why one name per source is the whole trick.

## Register them (once per machine, yours to run)

```bash
claude plugin marketplace add optimiziramsi/skills
```

```bash
claude plugin marketplace add "$(git rev-parse --show-toplevel)"
```

The second registers as `optimiziramsi-dev` because that is what the checkout's manifest says. If
an older registration named `optimiziramsi` still points at this checkout, remove it first
(`claude plugin marketplace remove optimiziramsi`) — that drops the install records of every
plugin installed from it, in every scope, so re-install afterwards.

## What makes a change reach a dev install

- **`autoUpdate` reads the working tree** — committed or not. A version bump under `<plugin>/`
  reaches every `@optimiziramsi-dev` install on the machine within minutes, no
  `claude plugin update` needed, and binds at the next session start (observed 2026-10-18).
  Auto-update installs nothing new: a plugin a project hasn't installed stays uninstalled.
- **The install cache is version-keyed**: `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
  is a real copy ([lesson](lessons/plugin-version-bump-on-edit.md)). An edit with no version
  bump reaches nobody — `tests.sh` § 8 forces the bump in the same commit (first edit after a
  release → `X.Y.(Z+1)-dev.1`, then `-dev.N+1`). Without `autoUpdate`, the proven manual cycle is
  bump → `claude plugin update <plugin>@optimiziramsi-dev --scope project` → restart.
- **Plugins bind at session start.** Restart CCD (or `/reload-plugins`) after an update or a
  branch switch; a resumed session keeps the old binding.
- **Never enable one plugin from both marketplaces in one project** — both load, and every hook
  fires twice.

## Consequences worth knowing

- **Leaving a feature branch checked out** switches every `@optimiziramsi-dev` install on the
  machine to it — and only those; `@optimiziramsi` projects stay on the release.
- **`main` has no workbench.** Checking it out removes `.agent/`, `.todo*`, `CLAUDE.md`,
  `.claude/`, `tests.sh`, `release.sh`, `vendor.sh`, root `lib/` from disk, and its manifest says
  `optimiziramsi` — so the dev registration breaks until you are back on `develop`. No agent does
  that switch; `main` is the protected branch.

## Feature branches carry their own series

`tests.sh` § 8 enforces it: on any branch other than `develop` / `main`, every plugin the branch
changes must be on `X.Y.Z-<branch-slug>.N` — `feat/abc-branch` → `0.1.1-feat-abc-branch.1`, then
`.2`, `.3`. The install cache is version-keyed, so a branch sharing `develop`'s version would switch
invisibly. Drop back to the `-dev` series on `develop`; `release.sh` refuses any pre-release.

## The loop

1. Edit on `develop` (or a feature branch off it), bump the edited plugin's `-dev` counter, commit.
2. Let auto-update move the dev installs (or `claude plugin update <plugin>@optimiziramsi-dev`),
   then restart / `/reload-plugins` in the test project.
3. When it holds up: bump each changed plugin to its final `X.Y.Z`, write its
   `<plugin>/CHANGELOG.md` section, and cut the release
   ([`release` skill](../.claude/skills/release/SKILL.md)). Pushing `main` is what reaches
   `@optimiziramsi` projects.
