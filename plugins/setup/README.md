# setup — bootstrap a project for the opsi toolkit

Part of the [`opsi`](../../README.md) marketplace.

A **one-time** scaffold. The opsi plugins keep everything they create under `.agent/`; this makes
that layout legible in a project, wires the entrypoint to it, and can write the entrypoint itself in
the house style — once, with no ongoing machinery.

## Contents

- name: `scaffold`
  kind: skill + command
  purpose:
    Create a static `.agent/README.md` index of the workspace layout, and add **one** pointer to
    it from `CLAUDE.md`/`AGENTS.md` (idempotent, asks before editing).

- name: `scaffold-claude-md`
  kind: skill + command
  purpose:
    Write a house-style **`CLAUDE.md`** — a slim router of routing + the hard rules that bind
    every session (never-push/never-main git, commit-as-you-go, verified done-gate, in-repo
    memory, lean reporting; optional roles + governance + caps). Never overwrites an existing
    entrypoint — reconciles into it.

## Why one-time, not automatic

Claude Code **auto-triggers skills** on their descriptions when a plugin is enabled — a skill does
not need to be listed in CLAUDE.md to work. So the toolkit deliberately avoids two
tempting-but-wrong patterns: **per-skill self-registration** ("you don't mention X, add it?" —
naggy, and drifts from the manifests) and **continuous index generation** (a sync burden for info
each plugin's README already owns). Instead: a single static index + one entrypoint pointer, created
once. After that, skills discover themselves and the `session-start` hook keeps live state fresh.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "opsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "setup@opsi": true }
}
```

Then, once in the project: `/scaffold-claude-md` to write the house-style entrypoint (if the repo
has none), and `/scaffold` to create the `.agent/` index and point the entrypoint at it.
