---
name: upkeep
description: >-
  Keep a project's plugins current — refresh the marketplaces, update installed plugins that have
  a newer version, and offer plugins new to the marketplaces the project uses, then hand over
  /reload-plugins. Use on /upkeep, when the upkeep notice says updates or new plugins exist, or
  when the user says "update the plugins", "any plugin updates?", "refresh plugins", "what's new
  in the marketplace".
---

# upkeep — plugins current, in one pass

The user invoked this, so updating already-installed plugins is in scope. Installing a NEW plugin
is not — those are offered, and installed only on the user's pick.

## Steps

1. **Refresh** each watched marketplace (`upkeep marketplaces` lists them; the CLI is on PATH
   while the plugin is enabled): `claude plugin marketplace update <marketplace>`.
2. **Read the state**: `upkeep status --json` → `updates` (`[id, scope, installed, available]`)
   and `new` (`[marketplace, name, description]`).
3. **Update** each outdated plugin at its own scope, from the project root:
   `claude plugin update <id> --scope <scope>`. A `user`-scope update moves that plugin in every
   project on the machine — say so in the report.
4. **Offer the new ones**: list name + description, recommend at most one, and install only what
   the user picks: `claude plugin install <name>@<marketplace> --scope project`. Nothing picked →
   nothing installed.
5. **Hand over**: updates bind at the next session start — tell the user to run `/reload-plugins`
   (or restart). Report what moved (`id old → new`), what was installed, what was skipped and why.

## Rules

- Never `marketplace remove` / `uninstall` / disable anything here — that's the user's call, asked
  for explicitly.
- A plugin whose installed version reads `unknown` (git-sourced, no declared version) can't be
  compared; mention it instead of guessing.
- Errors from the CLI go into the report verbatim; don't retry in a loop.
