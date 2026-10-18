# CLAUDE.md — optimiziramsi-skills (this marketplace)

This repo **is** [`optimiziramsi-skills`](README.md) — the `optimiziramsi` Claude Code plugin
marketplace, shipping **one plugin per concern** (one `<plugin>/` folder each, id
`<plugin>@optimiziramsi`): reusable skills, commands, agents, and hooks that each project enables
à la carte. Active plan: [`.agent/plan/261018_135850_plugin-split.md`](.agent/plan/261018_135850_plugin-split.md).
It *ships* the house conventions — so it must **exemplify** them. Written in the house
slim-router style: routing + the hard rules that bind every session; everything else is linked,
not restated.

## Session bootstrap — before any work
1. Read [`.agent/handoff.md`](.agent/handoff.md) — current state + next up. "lets continue" means:
   resume at its **Next up**.
2. Read [`.agent/MEMORY.md`](.agent/MEMORY.md) — durable facts, decisions, gotchas.
3. This repo tracks its own working continuity like an ordinary project: `.agent/` (memory,
   handoff, lessons) and the root `.todo` / `.todo-inbox` are versioned on `develop` (the release
   filter keeps them off `main`). Only machine-local or path-bearing artifacts stay gitignored —
   runner scratch (`.agent/loop/`, `.agent/grind/`), `.claude/settings.local.json`, `_review/`
   migration staging, and OS/build junk. Keep committed `.agent/` content free of real local paths
   and personal data.

## Hard rules — every session, no exceptions

- **Git remotes are the user's.** Never `git push` / `pull` (`git fetch` is fine). The user reviews
  and pushes from their own client. History is append-only (no `--amend` / `rebase` / `reset` to a
  commit); never discard uncommitted work. *(The `git` plugin dogfoods its own guard.)*
- **Work on `develop`, publish to `main`.** `main` is the **published plugin only**, written
  **only** by `./release.sh` as a filtered tree-copy — never by hand, by merge, or after
  `git checkout main`. Cut one with the [`release` skill](.claude/skills/release/SKILL.md); to try
  unreleased code use [`.agent/dev-marketplace.md`](.agent/dev-marketplace.md), never a release.
  `init-marketplace` is the retained build history.
- **Commit as you go.** Small, focused commits, terse imperative single-line subject — the
  `commit` plugin's own house style, dogfooded here. Don't batch into one final commit; don't wait
  to be asked.
- **"Done" means validated**, not just written: run **`./tests.sh`** (JSON validity, marketplace ↔
  plugin dirs agree, declared paths + dependencies resolve, every `${CLAUDE_PLUGIN_ROOT}` hook
  target exists inside its plugin, every `/command` has its same-named skill, `claude plugin
  validate --strict` on the marketplace and each plugin, test suites + self-tests, vendored copies
  in sync, per-plugin version discipline) and check **no project-specific content leaked in** —
  the plugins ship the *system*, never any one project's conventions.
- **Lean reporting.** No narration, no tool-output dumps. Report once at the end: outcome → a few
  terse bullets → questions grouped by topic. Assume an expert reader.
- **Minimum, surgical change.** Every changed line traces to the request; nothing speculative.
  State assumptions and ask when interpretations diverge.

## Authoring conventions (marketplace-specific)

Full overview + rationale: [README.md](README.md). The load-bearing rules:

- **One plugin per concern, self-contained.** The repo root is the marketplace only
  (`.claude-plugin/marketplace.json`). Each `<plugin>/` (dir name = plugin name) has its own
  `.claude-plugin/plugin.json`, `README.md`, `CHANGELOG.md`, and the default layout `skills/
  commands/ agents/ hooks/hooks.json` (+ `bin/ examples/ tests/` where used). A plugin reaches
  **nothing outside its own folder** at runtime — shared code lives once in root `lib/` and
  `./vendor.sh` copies it into each plugin that imports it (`flow/vendor/worktree/` likewise
  mirrors `worktree`'s guards); edit the source, re-run, commit the copies. No `dependencies`
  between plugins — a project must be able to drop any one. Adding/removing a plugin = its folder
  **and** its `marketplace.json` entry (tests.sh checks both). `optimiziramsi-skills/` is the
  deprecated all-in bundle kept for migration.
- **`/command` = a thin shim → the same-named `skill`.** The skill's `SKILL.md` is the single
  source of the logic; the command wrapper carries none — not steps, and **not a duplicated
  description**. Every command carries `disable-model-invocation: true`: inside a plugin a command
  shadows its same-named skill in the model's listing, and that flag keeps the *command* out of
  context so the *skill's* description (with its trigger phrases) is what drives auto-triggering.
  The command's own terse description is for the `/` menu only. New command → ship the flag.
- **Opinionated behavior must be switchable.** Every hook either self-gates on project config or
  honors an env kill-switch (README table); a new hook ships with one or the other.
- **Bump the plugin's version on any consumer-visible change.** Any edit under `<plugin>/`
  bumps that plugin's `<plugin>/.claude-plugin/plugin.json` `version` in the **same commit** (`-dev.N`
  → `-dev.N+1`; first edit after a release → `X.Y.(Z+1)-dev.1`) — CCD only re-materializes an
  installed plugin on a version *change*, so a same-version edit never reaches consumers
  ([why](.agent/lessons/plugin-version-bump-on-edit.md)). Repo-meta files (CLAUDE.md, `.agent/`,
  `.todo*`, tests.sh, release.sh, vendor.sh, root `lib/` until vendored) don't require a bump.
- **Runtime output lives under the consumer's `.agent/`** — no plugin clutters a project's root.
- **Ships the system, not conventions.** No product, stack, or deploy specifics baked in; a
  project's own rules stay in that project.
- **Status writeups are prose or a `status:` field — never `[ ]` / `[x]` checkboxes.** This
  repo's `.todo` is an agent-maintained list using a `(done)` prefix (a deliberate local choice;
  consumer projects keep `.todo` user-owned — see the shipped `triage-todo` / feedback skills).
  **When `flow@optimiziramsi` (or the bundle) is installed here (dogfooding), its `todo-readonly-guard` is live**: to
  update `.todo`, ask the user to arm the session with **"ALLOW TODO"**; unarmed deferrals go to
  `.todo-inbox`.
