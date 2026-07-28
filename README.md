# opsi — Claude Code toolkit

A personal [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins)
shipping **one plugin**: reusable **skills, commands, agents, and hooks** shared across all my
projects — so I solve something once and get it everywhere, and update it in one place. The repo
root *is* the plugin, organized **topic-first**: `.claude-plugin/{marketplace,plugin}.json` at
root, then one folder per concern (`git/ commit/ flow/ …`), each owning its own
`skills/ commands/ agents/ hooks/` — so everything for a topic is in one place. `plugin.json`
declares the component paths, so the type dirs don't need to sit at the repo root.

## Install

From a `claude` session in the project you want it in:

```bash
claude plugin marketplace add optimiziramsi/skills
```

```bash
claude plugin install optimiziramsi-skills@optimiziramsi
```

Then **restart** — plugins bind at session start. (`/plugin` does the same from inside a session;
in CCD use Browse → the plugin page → **"Install for project (shared)"** so the enable travels with
the repo.)

Declaring it in settings instead — marketplace global, enablement in the project's
`.claude/settings.json`:

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
plugins. Full adoption protocol and gotchas: **[ADOPTION.md](ADOPTION.md)**.

## Concerns

One plugin, eleven concerns. Each concern is a top-level folder with its own `README.md`.

| Concern | Provides |
|---|---|
| [`git`](git/README.md) | Git **safety net** — a `git-guard` hook that blocks push/pull/fetch, bulk adds, non-FF merges, protected-branch moves, soft-resets to moving refs, `reset --hard`, `--no-verify`, and discards (rebase/amend/checkout-file pass by default for FF landing flows) — plus the **hotfix** skill (test-first, cherry-pick both ways, remotes handed to you). |
| [`commit`](commit/README.md) | The opinionated house **commit** style — bare single-line messages, topic-close + pause-for-review cadence, safe staging, a `commit-format` guard, and a `commit-nudge`. |
| [`setup`](setup/README.md) | One-time bootstrap — **scaffold** the `.agent/` workspace index and point CLAUDE.md/AGENTS.md at it, and **scaffold-claude-md** to write a house-style CLAUDE.md (a slim router of the hard rules). |
| [`reporting`](reporting/README.md) | The **lean-reporting output contract**, enforced — contract injected per prompt (`brevity-reminder`), re-pulsed every Nth tool call (`contract-pulse`), and a Stop `report-guard` that blocks a narrating/over-long final message. |
| [`session`](session/README.md) | Session continuity — **handoff** (write next-session notes, ≤4k), **continue** (boot from them), **session-summary** + a `session-start` hook. |
| [`instructions`](instructions/README.md) | Keep the agent-instruction system alive — **retro**, **lessons**, **instructions-audit**, **instructions-maintenance**, **rules-change** skills + `lesson-scout` / `instructions-auditor` agents + `caps` and `file-guard` hooks + two config-driven engines: **meta-lint** (behind `.agent/meta-lint.json`) and **tripwire-guard** (project-owned `.agent/guards.d/*.sh` asserts). |
| [`review`](review/README.md) | Structured review — **review** (P0/HIGH/MED/LOW → `.agent/reviews/`) and **qa-gate** skills + `semantic-reviewer`, `spec-cross-checker`, `wireframe-vs-code`, `doc-auditor`, `isolation-reviewer` agents. |
| [`repo`](repo/README.md) | **rename** — move a file and cascade every reference across docs/skills/config. |
| [`flow`](flow/README.md) | Work management — **plan**, **milestone**, **scope-cut**, **triage-todo**, **feedback**, plus autonomous background execution: **looper** / **grind** / **collab** driven by a shipped Python-3 runner (`bin/loop`, `bin/grind`). Ships the `todo-readonly-guard` — `.todo` stays user-owned (arm with "ALLOW TODO"). |
| [`patterns`](patterns/README.md) | A per-topic **pattern registry** (`.agent/patterns/`) — **manage-patterns** + `pattern-compliance`/`pattern-verifier` agents + hooks that gate edits governed only by non-blessed patterns. Ships the system, not any project's conventions. |
| [`worktree`](worktree/README.md) | Parallel isolated work — the **worktree** skill (reserve → plan → review-gated slices → land) + guards that keep edits inside the active worktree (mitigates [claude-code #36182](https://github.com/anthropics/claude-code/issues/36182)) + a SessionStart `worktree-detect` nudge. |

## Per-concern opt-out (env kill-switches)

Guards self-gate on project config (patterns fire only with a registry, meta-lint only with
`.agent/meta-lint.json`, worktree guards only in a linked worktree, the `.todo` and handoff nudges
only where those files exist). **Everything else has a switch** — every shipped hook honors one, so
no concern is stuck on:

| Switch | Silences |
|---|---|
| `GIT_GUARD_OFF=1` | the git safety net (see also `GIT_GUARD_ALLOW`, `GIT_GUARD_ALLOW_FETCH`, `GIT_GUARD_STRICT`, `GIT_GUARD_PROTECTED_BRANCH`) |
| `COMMIT_FORMAT_OFF=1` | the single-line commit-message guard |
| `STOP_NUDGE_OFF=1` | the end-of-session commit nudge (`COMMIT_NUDGE_EXTRA_DIRS` widens it) |
| `REPORT_GUARD_OFF=1` | the whole reporting contract (inject + pulse + Stop guard); `REPORT_PULSE_EVERY`, `REPORT_GUARD_MAX_LINES` tune it |
| `SESSION_START_OFF=1` | the SessionStart state snapshot + freshness nudges |
| `TODO_GUARD_DISABLE=1` | the `.todo` readonly guard (`TODO_GUARD_SKIP=1` = one-shot) |
| `FILE_GUARD_OFF=1` | the T3 enforcement-surface write guard (`FILE_GUARD_EXTRA` adds prefixes) |
| `CAPS_GUARD_OFF=1` | instruction-surface size caps |
| `META_LINT_OFF=1` | the meta-lint engine (already inert without `.agent/meta-lint.json`) |
| `TRIPWIRE_GUARD_OFF=1` | project tripwires (`TRIPWIRE_SKIP=1` = one-shot) |
| `PATTERN_GUARDS_OFF=1` | the pattern-registry edit gate |
| `WORKTREE_GUARD_DISABLE=1` | worktree edit containment **and** the SessionStart worktree nudge |
| `WORKTREE_LEAK_DETECT_DISABLE=1` | the post-edit worktree leak detector |

Opt-**in**, off by default: `WORKTREE_BASH_GUARD_ENABLE=1` (shell-channel worktree containment —
false-positive-prone). The flow runners take `FLOW_*` env; see [`flow`](flow/README.md).

**Runtime: python3 (stdlib only), nothing else.** Every hook is python over the shared
[`lib/hookio.py`](lib/hookio.py); their tests live in `<topic>/tests/`, not inside the guards.
There is deliberately no `jq` dependency — a guard that disarms itself when a tool is missing is
worse than no guard, and `python3` is the one interpreter a Claude Code host already needs.

**No branch name is hardcoded.** `main` is not assumed anywhere: the git guard detects the repo's
own default branch (override with `GIT_GUARD_PROTECTED_BRANCH`), the `worktree` skill takes
`<integration>` / `<protected>` from the project, `scaffold-claude-md` reads the branch layout out
of the repo before writing a rule about it, and the tripwire examples take
`TRIPWIRE_INTEGRATION_BRANCH`. `develop`-, `trunk`-, and `master`-based projects need no config.
**Single-branch repos need one line:** where the integration branch *is* the protected branch, set
`GIT_GUARD_INTEGRATION_BRANCH` so the `worktree` protocol's fast-forward land is permitted while
force/delete refspecs and `checkout` onto it stay blocked.

## Conventions

- **One plugin, topic-first.** Each concern is a folder (`<topic>/skills|commands|agents|hooks/`)
  with its own `README.md` and its own `hooks/hooks.json`; `plugin.json` lists the component paths.
  A **command** (`/x`) is a thin shim that invokes a same-named **skill** which holds the actual
  logic (single source of truth). Commands are `disable-model-invocation: true` — they exist so you
  can *type* `/x`; the skill's own description is what Claude auto-triggers on, so nothing is
  duplicated. Invocation names come from frontmatter/filename, so the folder grouping is
  organizational only — no `<topic>:` prefix appears in a skill/command/agent name. Claude Code
  namespaces plugin components as `optimiziramsi-skills:<name>` in menus and autocomplete; the bare
  `/<name>` invokes them too (CC ≥ 2.1.216).
- **House layout.** Everything the toolkit creates lives under **`.agent/`** — `handoff.md`,
  `lessons/`, `worktrees.md`, `milestones.md`, `plan/`, `milestone/`, `loop/`, `grind/`,
  `patterns/`, `reviews/` — so it never clutters your repo root. Your `.docs/` and root `.todo`
  stay yours; skills *link* to `.docs/` but never write it. Each concern degrades gracefully when
  a project doesn't use it.
- **Commits:** bare imperative single line; default cadence is commit at **topic close, then pause
  for review** (opt into commit-as-you-go per session).
- **Versioning:** any consumer-visible change bumps the single `.claude-plugin/plugin.json`
  `version` in the same commit — CCD only re-materializes on a version change. Release notes:
  [CHANGELOG.md](CHANGELOG.md).

`other/` is not part of the plugin — it holds standalone recipes (currently a machine-agnostic
guide to anchoring the Claude usage window on a schedule).

---

_Consolidated from per-project `.claude/` setups. Migration staging + notes live in `_review/`
(git-ignored — not part of the published marketplace)._
