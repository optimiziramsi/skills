# opsi — Claude Code toolkit

A personal [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins):
reusable **skills, commands, agents, and hooks** shared across all my projects — so I solve something
once and get it everywhere, and update it in one place.

## Install

In your `settings.json` (user-level or a project's `.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "opsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": {
    "git@opsi": true,
    "commit@opsi": true,
    "setup@opsi": true,
    "reporting@opsi": true,
    "session@opsi": true,
    "instructions@opsi": true,
    "review@opsi": true,
    "repo@opsi": true,
    "flow@opsi": true,
    "patterns@opsi": true,
    "worktree@opsi": true
  }
}
```

The snippet lists every plugin the marketplace ships — enable only the ones a given project needs
(delete the rest); a plugin's hooks activate wherever it's enabled.

## Plugins

| Plugin | Provides |
|---|---|
| [`git`](plugins/git) | Git **safety net** — a `git-guard` hook that blocks push/pull/fetch, bulk adds, non-FF merges, protected-branch moves, soft-resets to moving refs, `reset --hard`, `--no-verify`, and discards (rebase/amend/checkout-file pass by default for FF landing flows), regardless of commit style — plus the **hotfix** skill (test-first, cherry-pick both ways, remotes handed to you). |
| [`commit`](plugins/commit) | The opinionated house **commit** style — bare single-line messages, topic-close + pause-for-review cadence, safe staging, a `commit-format` guard, and a `commit-nudge`. Opt-in; pairs with `git`. |
| [`setup`](plugins/setup) | One-time bootstrap — **scaffold** the `.agent/` workspace index (`.agent/README.md`) and point CLAUDE.md/AGENTS.md at it, and **scaffold-claude-md** to write a house-style CLAUDE.md (a slim router of the hard rules that bind every session). No per-skill registration, no ongoing generation. |
| [`reporting`](plugins/reporting) | The **lean-reporting output contract**, enforced — contract injected per prompt (`brevity-reminder`), re-pulsed every Nth tool call (`contract-pulse`), and a Stop `report-guard` that blocks a narrating/over-long final message and forces a compact rewrite. Opt-in, like `commit`. |
| [`session`](plugins/session) | Session continuity — **handoff** (write next-session notes, ≤4k), **continue** (boot from them), **session-summary** + a `session-start` hook. |
| [`instructions`](plugins/instructions) | Keep the agent-instruction system alive — **retro**, **lessons**, **instructions-audit**, **instructions-maintenance**, **rules-change** skills + `lesson-scout` and `instructions-auditor` agents + `caps` and `file-guard` hooks (size caps enforced mechanically; guard/settings edits ask the user) + two config-driven engines: **meta-lint** (project instruction-system linter behind `.agent/meta-lint.json`, pulsed at SessionStart) and **tripwire-guard** (project-owned `.agent/guards.d/*.sh` asserts on Bash commands). Apply-safe / propose-risky governance. |
| [`review`](plugins/review) | Structured review — **review** (P0/HIGH/MED/LOW → `.agent/reviews/`) and **qa-gate** skills + `semantic-reviewer`, `spec-cross-checker`, `wireframe-vs-code`, `doc-auditor` (docs-vs-code drift), `isolation-reviewer` (multi-tenant isolation) agents. |
| [`repo`](plugins/repo) | **rename** — move a file and cascade every reference across docs/skills/config. |
| [`flow`](plugins/flow) | Work management — **plan**, **milestone**, **scope-cut**, **triage-todo**, **feedback** (`.agent/FEEDBACK.md` ledger), plus autonomous background execution: **looper** / **grind** / **collab** skills driven by a shipped resilient Python-3 runner (`bin/loop`, `bin/grind`) that runs jobs as headless `claude` sessions — per-iteration watchdog, dirty-tree guard, attempt continuation across retries, and a productivity gate. Ships a `todo-readonly-guard` hook — `.todo` stays user-owned (arm with "ALLOW TODO"). |
| [`patterns`](plugins/patterns) | A per-topic **pattern registry** (`.agent/patterns/`) — **manage-patterns** (author/curate blessed code shapes via a 5-phase, human-reviewed workflow) + `pattern-compliance`/`pattern-verifier` agents + hooks that mechanically **gate** edits in areas governed only by non-blessed patterns. Ships the system, not any project's conventions. |
| [`worktree`](plugins/worktree) | Parallel isolated work — the **worktree** skill (reserve → plan → review-gated slices → land to an integration branch; pause/resume/recycle) + three guards that keep edits inside the active worktree (mitigates [claude-code #36182](https://github.com/anthropics/claude-code/issues/36182)) + a SessionStart `worktree-detect` hook that flags a worktree-rooted session and routes it into the protocol. |

## Conventions

- **One concern per plugin.** A **command** (`/x`) is a thin shim that invokes a same-named
  **skill** which holds the actual logic (single source of truth).
- **House layout.** Everything the plugins create lives under **`.agent/`** — `handoff.md`, `lessons/`,
  `worktrees.md`, `milestones.md`, `plan/`, `milestone/`, `loop/`, `grind/`, `patterns/`, `reviews/` — so
  the toolkit never clutters your repo root. Your `.docs/` (architecture/specs) and root `.todo` stay
  yours; skills *link* to `.docs/` but never write it. Each skill degrades gracefully when a project
  doesn't use a given piece.
- **Commits:** bare imperative single line; the default cadence is commit at **topic close, then
  pause for review** before the next topic (opt into commit-as-you-go per session).

---

_Consolidated from per-project `.claude/` setups. Migration staging + notes live in `_review/`
(git-ignored — not part of the published marketplace)._
