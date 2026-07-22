# opsi — Claude Code toolkit

A personal [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins)
shipping **one plugin**: reusable **skills, commands, agents, and hooks** shared across all my
projects — so I solve something once and get it everywhere, and update it in one place. The repo
root *is* the plugin (mattpocock/skills layout): `.claude-plugin/{marketplace,plugin}.json` +
root `skills/ commands/ agents/ hooks/ bin/ docs/`.

## Install

In your `settings.json` (marketplace global, enablement in the project's `.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "optimiziramsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": {
    "optimiziramsi-skills@optimiziramsi": true
  }
}
```

That JSON registers and enables the plugin, but it does not by itself **load** it:

- **Keep enablement project-only.** Put `enabledPlugins` in the project's `.claude/settings.json`,
  not `~/.claude` — enables travel with the repo.
- **Install + full restart binds.** Enablement isn't installation: install the plugin (`/plugin`,
  or approve the first-load prompt) and **restart** — plugins bind at session start, never
  mid-session. Floor: CC / CCD **≥ 2.1.195**.

Everything ships enabled; **projects opt out per concern via env** (below) instead of picking
plugins. Full adoption protocol and gotchas: **[ADOPTION.md](ADOPTION.md)**. Migrating from the
old 11-plugin marketplace: **[MIGRATION.md](MIGRATION.md)**.

## Concerns

One plugin, eleven concerns. Each concern's full doc lives in `docs/`.

| Concern | Provides |
|---|---|
| [`git`](docs/git.md) | Git **safety net** — a `git-guard` hook that blocks push/pull/fetch, bulk adds, non-FF merges, protected-branch moves, soft-resets to moving refs, `reset --hard`, `--no-verify`, and discards (rebase/amend/checkout-file pass by default for FF landing flows) — plus the **hotfix** skill (test-first, cherry-pick both ways, remotes handed to you). |
| [`commit`](docs/commit.md) | The opinionated house **commit** style — bare single-line messages, topic-close + pause-for-review cadence, safe staging, a `commit-format` guard, and a `commit-nudge`. |
| [`setup`](docs/setup.md) | One-time bootstrap — **scaffold** the `.agent/` workspace index and point CLAUDE.md/AGENTS.md at it, and **scaffold-claude-md** to write a house-style CLAUDE.md (a slim router of the hard rules). |
| [`reporting`](docs/reporting.md) | The **lean-reporting output contract**, enforced — contract injected per prompt (`brevity-reminder`), re-pulsed every Nth tool call (`contract-pulse`), and a Stop `report-guard` that blocks a narrating/over-long final message. |
| [`session`](docs/session.md) | Session continuity — **handoff** (write next-session notes, ≤4k), **continue** (boot from them), **session-summary** + a `session-start` hook. |
| [`instructions`](docs/instructions.md) | Keep the agent-instruction system alive — **retro**, **lessons**, **instructions-audit**, **instructions-maintenance**, **rules-change** skills + `lesson-scout` / `instructions-auditor` agents + `caps` and `file-guard` hooks + two config-driven engines: **meta-lint** (behind `.agent/meta-lint.json`) and **tripwire-guard** (project-owned `.agent/guards.d/*.sh` asserts). |
| [`review`](docs/review.md) | Structured review — **review** (P0/HIGH/MED/LOW → `.agent/reviews/`) and **qa-gate** skills + `semantic-reviewer`, `spec-cross-checker`, `wireframe-vs-code`, `doc-auditor`, `isolation-reviewer` agents. |
| [`repo`](docs/repo.md) | **rename** — move a file and cascade every reference across docs/skills/config. |
| [`flow`](docs/flow.md) | Work management — **plan**, **milestone**, **scope-cut**, **triage-todo**, **feedback**, plus autonomous background execution: **looper** / **grind** / **collab** driven by a shipped Python-3 runner (`bin/loop`, `bin/grind`). Ships the `todo-readonly-guard` — `.todo` stays user-owned (arm with "ALLOW TODO"). |
| [`patterns`](docs/patterns.md) | A per-topic **pattern registry** (`.agent/patterns/`) — **manage-patterns** + `pattern-compliance`/`pattern-verifier` agents + hooks that gate edits governed only by non-blessed patterns. Ships the system, not any project's conventions. |
| [`worktree`](docs/worktree.md) | Parallel isolated work — the **worktree** skill (reserve → plan → review-gated slices → land) + guards that keep edits inside the active worktree (mitigates [claude-code #36182](https://github.com/anthropics/claude-code/issues/36182)) + a SessionStart `worktree-detect` nudge. |

## Per-concern opt-out (env kill-switches)

Guards self-gate on project config (patterns fire only with a registry, meta-lint only with
`.agent/meta-lint.json`, worktree guards only in a linked worktree, session hooks only where
`.agent/` exists). The opinionated concerns switch off per project in `.claude/settings.json`
`env`:

| Switch | Silences |
|---|---|
| `GIT_GUARD_OFF=1` | the git safety net (see also `GIT_GUARD_ALLOW`, `GIT_GUARD_ALLOW_FETCH`) |
| `COMMIT_FORMAT_OFF=1` | the single-line commit-message guard |
| `STOP_NUDGE_OFF=1` | the end-of-session commit nudge |
| `REPORT_GUARD_OFF=1` | the whole reporting contract (inject + pulse + Stop guard) |
| `TODO_GUARD_DISABLE=1` | the `.todo` readonly guard |
| `FILE_GUARD_OFF=1` | the T3 enforcement-surface write guard |
| `CAPS_GUARD_OFF=1` | instruction-surface size caps |
| `TRIPWIRE_GUARD_OFF=1` | project tripwires (`TRIPWIRE_SKIP=1` = one-shot) |
| `WORKTREE_GUARD_DISABLE=1` | worktree edit containment |

## Conventions

- **One plugin, one concern per module.** A **command** (`/x`) is a thin shim that invokes a
  same-named **skill** which holds the actual logic (single source of truth). Concern docs live in
  `docs/<concern>.md`.
- **House layout.** Everything the toolkit creates lives under **`.agent/`** — `handoff.md`,
  `lessons/`, `worktrees.md`, `milestones.md`, `plan/`, `milestone/`, `loop/`, `grind/`,
  `patterns/`, `reviews/` — so it never clutters your repo root. Your `.docs/` and root `.todo`
  stay yours; skills *link* to `.docs/` but never write it. Each concern degrades gracefully when
  a project doesn't use it.
- **Commits:** bare imperative single line; default cadence is commit at **topic close, then pause
  for review** (opt into commit-as-you-go per session).
- **Versioning:** any consumer-visible change bumps the single `.claude-plugin/plugin.json`
  `version` in the same commit — CCD only re-materializes on a version change.

---

_Consolidated from per-project `.claude/` setups. Migration staging + notes live in `_review/`
(git-ignored — not part of the published marketplace)._
