---
name: scaffold-claude-md
description: >-
  Write a house-style `CLAUDE.md` for a project — a slim router carrying only routing + the hard
  rules that bind every session, in the opsi convention (session bootstrap, never-push/never-main
  git, commit-as-you-go, verified done-gate, in-repo memory, lean reporting; optional roles +
  governance + caps). Use when a repo has no entrypoint, or the user asks to "write a CLAUDE.md",
  "set up the agent entrypoint", "add house rules / conventions", "opsi CLAUDE.md". Never overwrites
  an existing CLAUDE.md — reconciles into it. Pairs with `scaffold` (the `.agent/` layout).
---

# Scaffold a house-style `CLAUDE.md`

Writes the opsi **slim-router** entrypoint: the only two things in it are **routing** (where to
look) and the **hard rules that bind every session**. Everything else has one canonical home and is
*linked, not restated* — so the file stays small and never drifts. This is the entrypoint the
`scaffold` skill points at; run both to set a project up (this one for the rules, `scaffold` for the
`.agent/` layout).

## Why it's shaped this way

- **A CLAUDE.md is a router, not a manual.** Skills auto-trigger on their descriptions;
  product/stack/ deploy truth lives in `docs/`; mechanics live in the plugins. The entrypoint only
  holds what must bind *every* session regardless of which skill fires — the hard rules — plus
  pointers.
- **Generic core + optional full system.** The core (git/commit/done-gate/memory/reporting) suits
  any repo. The fenced OPTIONAL block (roles + T1/T2/T3 governance + size caps) is for teams that
  adopt the `instructions` plugin's self-maintaining system — keep it or delete it as one unit.
- **It never clobbers.** An existing CLAUDE.md is a contract; this skill reconciles into it, never
  overwrites.

## Steps

1. **Check for an entrypoint** (`CLAUDE.md`, else `AGENTS.md`, at the repo root).
   - **None:** proceed to write one from the template below.
   - **Exists:** do NOT overwrite. Read it, diff it against the template's hard rules, and offer to
     *insert only the missing rules* (show the exact edit, confirm first). Leave the rest alone.

2. **Fill what you can infer, mark the rest.** Set the project name (repo dir) and, if a
   `package.json` / `Makefile` / `justfile` is present, the real build/test/run commands — **naming
   the done-gate explicitly**. Leave everything you can't verify as a visible `<!-- PLACEHOLDER
   -->`; never invent product scope, stack, or deploy facts.

3. **Prune to the project's plugins.** The template names the `git` / `commit` / `instructions`
   plugins that back each rule. Drop references to any plugin the project won't enable (ask if
   unsure), and delete the whole OPTIONAL block for a light setup.

4. **Show the full proposed file and confirm before writing.** It's the project's contract — the
   user approves it once.

5. **Point the way onward.** Mention that `scaffold` creates the `.agent/README.md` workspace index
   and adds the one pointer this file expects, and that `.agent/` can be committed (team-shared) or
   gitignored (private) — their call.

## The template

````markdown
# CLAUDE.md — <!-- PROJECT NAME --> agent guide

<!-- ONE-LINE INTRO: what this repo is, who it's for, and the single posture that colours every
     change (e.g. "public app for real users — multi-tenancy, security, privacy are baseline"). -->

Read this in 30 seconds. Only two kinds of content live here: **routing** (where to look) and the
**hard rules that bind every session**. Everything else has one canonical home and is *linked, not
restated* — fix drift at the source, never by copying it here.

## Session bootstrap — before any work
1. Read [`.agent/handoff.md`](.agent/handoff.md) — current state + next up. "lets continue" means:
   resume at its **Next up**.
2. Read durable memory — [`.agent/lessons/`](.agent/lessons/) (or `.agent/MEMORY.md`): decisions,
   gotchas, working agreements. **Project knowledge lives in-repo, never in account memory.**
3. <!-- OPTIONAL: declare your session role (see Roles below). Delete this line if you don't use roles. -->

## Hard rules — every session, no exceptions

- **Git remotes are the user's.** Never `git push` / `pull` (`git fetch` is fine). Don't commit on
  `main` — work on `develop` or a worktree; if you find yourself on `main`, STOP and ask. On protected
  branches history is append-only — no `--amend` / `rebase` / `reset` to a commit. Never discard
  uncommitted work (`clean -f`, `restore`, `checkout -- .`, `stash drop`) — it may hold the user's WIP.
  *(The `git` plugin's guard hook blocks the remote/destructive/history ops mechanically.)*
- **Commit as you go.** Small, focused commits with a terse imperative subject — don't batch into one
  final commit, don't wait to be asked. Message format: the `commit` plugin.
- **"Done" means verified by a real run**, not by reading code. Define the success check before coding
  and loop until it passes; report failures honestly, with output. For UI work, look at it.
- **Lean reporting.** No narration, no tool-output dumps. While working, stay quiet; report once at the
  end — outcome line → a few terse bullets → questions (grouped by topic). Assume an expert reader.
- **Minimum, surgical change.** Every changed line traces to the request; nothing speculative. State
  assumptions and ask when interpretations diverge. Fix at the source, or DEFER visibly (`// TODO` +
  the parking lot) — never a silent shim (`as` cast, `?? fallback`) that hides a real mismatch.

## Agent workspace
This repo uses the opsi toolkit's `.agent/` layout — see [`.agent/README.md`](.agent/README.md) for
what lives where. `.todo` at the repo root is the **user's** inbox: read it, don't edit it.

## Sources of truth (linked, not duplicated)
<!-- Point at the canonical docs; delete rows you don't have.
- Product / scope: docs/PRODUCT.md · Locked decisions: docs/DECISIONS.md
- Architecture / stack: docs/ARCHITECTURE.md
- Deploy contract the platform reads: <HUB.md / infra repo> -->

## Commands
<!-- The few commands an agent needs; mark the DONE-GATE.
- run / dev:  <...>
- test / verify (the done-gate):  <...> -->

<!-- =========================================================================
     OPTIONAL — the full self-maintaining instruction system (the `instructions`
     plugin: roles + governance tiers + size caps). Keep this block as one unit if
     you adopt it; delete it entirely for a light setup.
     ========================================================================= -->

## Roles — declare one at session start
- **Planner / architect** — owns the docs (`CLAUDE.md`, `docs/*`, rules); keeping them true IS the
  deliverable. STOP for user approval before structural / meta changes.
- **Coder / executor** — docs are frozen contracts. If reality contradicts a doc, **STOP** and get it
  fixed first; never patch docs to match code, never plow ahead against them. Default to coder.

## Instruction-system governance
- **Tiers:** T1 status (handoff, lessons) — update freely · T2 wording fixes of existing rules — apply
  + a changelog line · T3 new/removed rules, hooks, skills, caps — **user approval required**.
- **Size caps** on the instruction surface are checked at session start and on commit (the
  `instructions` plugin's caps hook). Resolve a tripped cap **merge → route → tighten → retire** —
  never by raising the cap. Every fact has ONE home.
- **Status writeups** are prose or a `status:` field — **never `[ ]` / `[x]` checkboxes** (noisy diffs;
  models mangle them). Learnings route through `/retro` — merge, date, prune.
````

## What NOT to do

- **Don't overwrite an existing entrypoint** — reconcile the missing hard rules into it, with
  consent.
- **Don't invent project facts** — leave product/stack/deploy/commands as visible placeholders until
  the user (or the actual files) supply them.
- **Don't enumerate skills** into the file — they auto-trigger; listing them duplicates the
  manifests.
- **Don't keep dangling plugin references** — prune the OPTIONAL block and any plugin the project
  isn't using, so every rule the file states is actually backed.
