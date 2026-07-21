# CLAUDE.md — opsi toolkit (this marketplace)

This repo **is** the [`opsi`](README.md) Claude Code plugin marketplace: reusable skills, commands,
agents, and hooks shared across projects. It *ships* the house conventions — so it must
**exemplify** them. Written in the house slim-router style: routing + the hard rules that bind
every session; everything else is linked, not restated.

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
  `plugins/` sync, every hook self-test) and check **no project-specific content leaked in** —
  plugins ship the *system*, never any one project's conventions.
- **Lean reporting.** No narration, no tool-output dumps. Report once at the end: outcome → a few
  terse bullets → questions grouped by topic. Assume an expert reader.
- **Minimum, surgical change.** Every changed line traces to the request; nothing speculative.
  State assumptions and ask when interpretations diverge.

## Authoring conventions (marketplace-specific)

Full overview + rationale: [README.md](README.md). The load-bearing rules:

- **One concern per plugin.** Each plugin under `plugins/` is enabled independently; keep
  concerns split (the `git` safety net vs the `commit` style is the reference example).
- **`/command` = a thin shim → the same-named `skill`.** The skill's `SKILL.md` is the single
  source of the logic; the command wrapper carries none. Never duplicate steps into the command.
- **Plugin shape:** `.claude-plugin/plugin.json` + `skills/<name>/SKILL.md` (+ optional
  `commands/`, `agents/`, `hooks/`, `README.md`). Register every plugin in
  [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json); keep plugin.json /
  marketplace / README descriptions in sync.
- **Bump the plugin's version on any change to it.** Any edit under `plugins/<name>/`
  (hook/skill/command/agent/config) bumps `plugins/<name>/.claude-plugin/plugin.json` `version` in
  the **same commit** — CCD only re-materializes an installed plugin on a version *change*, so a
  same-version edit never reaches consumers ([why](.agent/lessons/plugin-version-bump-on-edit.md)).
- **Runtime output lives under the consumer's `.agent/`** — plugins never clutter a project's
  root.
- **Ships the system, not conventions.** No product, stack, or deploy specifics baked into a
  plugin; a project's own rules stay in that project.
- **Status writeups are prose or a `status:` field — never `[ ]` / `[x]` checkboxes.** This
  repo's `.todo` is an agent-maintained list using a `(done)` prefix (a deliberate local choice;
  consumer projects keep `.todo` user-owned — see the shipped `triage-todo` / feedback skills).
  **We dogfood `flow@opsi` here** (via `.claude/settings.local.json`, gitignored), so its
  `todo-readonly-guard` is live: to update `.todo`, ask the user to arm the session with
  **"ALLOW TODO"**; unarmed deferrals go to `.todo-inbox`.
