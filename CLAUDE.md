# CLAUDE.md — opsi toolkit (this marketplace)

This repo **is** the [`opsi` toolkit](README.md) — the `optimiziramsi` Claude Code plugin
marketplace, shipping ONE plugin (`optimiziramsi-skills`) whose root is this repo
(mattpocock/skills layout): reusable skills, commands, agents, and hooks shared across projects.
It *ships* the house conventions — so it must **exemplify** them. Written in the house
slim-router style: routing + the hard rules that bind every session; everything else is linked,
not restated.

## Session bootstrap — before any work
1. Read [`.agent/handoff.md`](.agent/handoff.md) — current state + next up. "lets continue" means:
   resume at its **Next up**.
2. Read [`.agent/MEMORY.md`](.agent/MEMORY.md) — durable facts, decisions, gotchas.
3. This repo tracks its own working continuity like an ordinary project: `.agent/` (memory,
   handoff, lessons) and the root `.todo` / `.todo-inbox` are versioned. Only machine-local or
   path-bearing artifacts stay gitignored — runner scratch (`.agent/loop/`, `.agent/grind/`),
   `.claude/settings.local.json`, `_review/` migration staging, and OS/build junk. Keep committed
   `.agent/` content free of real local paths and personal data.

## Hard rules — every session, no exceptions

- **Git remotes are the user's.** Never `git push` / `pull` (`git fetch` is fine). The user reviews
  and pushes from their own client. History is append-only (no `--amend` / `rebase` / `reset` to a
  commit); never discard uncommitted work. `main` carries the marketplace (squash-landed
  2026-07-18); `init-marketplace` is the retained build history. *(The `git` plugin dogfoods its
  own guard.)*
- **Commit as you go.** Small, focused commits, terse imperative single-line subject — the
  `commit` plugin's own house style, dogfooded here. Don't batch into one final commit; don't wait
  to be asked.
- **"Done" means validated**, not just written: run **`./tests.sh`** (JSON validity, marketplace ↔
  plugin manifests agree, every hook self-test) and check **no project-specific content leaked
  in** — the plugin ships the *system*, never any one project's conventions.
- **Lean reporting.** No narration, no tool-output dumps. Report once at the end: outcome → a few
  terse bullets → questions grouped by topic. Assume an expert reader.
- **Minimum, surgical change.** Every changed line traces to the request; nothing speculative.
  State assumptions and ask when interpretations diverge.

## Authoring conventions (marketplace-specific)

Full overview + rationale: [README.md](README.md). The load-bearing rules:

- **One plugin, one concern per module.** The repo root is the plugin: `.claude-plugin/
  {marketplace,plugin}.json` + root `skills/ commands/ agents/ hooks/ bin/ docs/ examples/`.
  Concerns stay cleanly separated *inside* it (one skill dir per concern piece, one
  `docs/<concern>.md`, per-concern env kill-switches — see README) — merged for one-install /
  one-version updates, not blended.
- **`/command` = a thin shim → the same-named `skill`.** The skill's `SKILL.md` is the single
  source of the logic; the command wrapper carries none. Never duplicate steps into the command.
- **Opinionated behavior must be switchable.** Every hook either self-gates on project config or
  honors an env kill-switch (README table); a new hook ships with one or the other.
- **Bump the version on any consumer-visible change.** Any edit to shipped content (skill,
  command, agent, hook, bin, manifest) bumps [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)
  `version` in the **same commit** — CCD only re-materializes an installed plugin on a version
  *change*, so a same-version edit never reaches consumers
  ([why](.agent/lessons/plugin-version-bump-on-edit.md)). Repo-meta files (CLAUDE.md, `.agent/`,
  `.todo*`, tests.sh) don't require a bump.
- **Runtime output lives under the consumer's `.agent/`** — the plugin never clutters a project's
  root.
- **Ships the system, not conventions.** No product, stack, or deploy specifics baked in; a
  project's own rules stay in that project.
- **Status writeups are prose or a `status:` field — never `[ ]` / `[x]` checkboxes.** This
  repo's `.todo` is an agent-maintained list using a `(done)` prefix (a deliberate local choice;
  consumer projects keep `.todo` user-owned — see the shipped `triage-todo` / feedback skills).
  **When `optimiziramsi-skills@optimiziramsi` is installed here (dogfooding), its `todo-readonly-guard` is live**: to
  update `.todo`, ask the user to arm the session with **"ALLOW TODO"**; unarmed deferrals go to
  `.todo-inbox`.
