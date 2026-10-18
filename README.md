# optimiziramsi-skills — Claude Code toolkit

A personal [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins),
`optimiziramsi`, shipping **one plugin per concern**: reusable **skills, commands, agents, and
hooks** shared across my projects — solve something once, get it everywhere, update it in one
place. Each project enables only the plugins that suit it. The repo root is the marketplace
(`.claude-plugin/marketplace.json`); every top-level concern folder (`git/ commit/ flow/ …`) is a
self-contained plugin with its own `.claude-plugin/plugin.json`, `skills/ commands/ agents/
hooks/`, `README.md` and `CHANGELOG.md`.

## Install — per project

Register the marketplace once per machine, then pick plugins in each project. From a `claude`
session in the project:

```bash
claude plugin marketplace add optimiziramsi/skills
```

```bash
claude plugin install git@optimiziramsi --scope project
```

Repeat the install for each plugin the project wants, then **restart** — plugins bind at session
start. `--scope project` writes the enable into the project's committed `.claude/settings.json`,
so it travels with the repo. (`/plugin` does the same from inside a session; in CCD use Browse →
the plugin page → **"Install for project (shared)"**.)

The resulting `.claude/settings.json` carries just the enables (the marketplace registration stays
machine-global — ADOPTION.md says why). Teammates run the same `install --scope project` once on
their machine, since an enable alone installs nothing:

```json
{
  "enabledPlugins": {
    "git@optimiziramsi": true,
    "commit@optimiziramsi": true,
    "session@optimiziramsi": true
  }
}
```

- **Opt out personally** without touching the shared file: `"<plugin>@optimiziramsi": false` in
  the project's `.claude/settings.local.json`.
- **Tune a plugin** with the env switches below — shared in `.claude/settings.json` `env`,
  personal in `.claude/settings.local.json` `env`.
- **Coming from the single plugin?** `optimiziramsi-skills@optimiziramsi` is now a deprecated
  bundle that pulls in all eleven — while it is enabled none of them can be disabled. Install the
  plugins the project wants, then uninstall the bundle. Floor: CC / CCD **≥ 2.1.195**.

Full adoption protocol and gotchas: **[ADOPTION.md](ADOPTION.md)**.

## Plugins

Eleven plugins, each a top-level folder; the id is `<folder>@optimiziramsi`.

| Plugin | Provides |
|---|---|
| [`git`](git/README.md) | Git **safety net** — a `git-guard` hook that blocks push/pull/fetch, bulk adds, non-FF merges, protected-branch moves, soft-resets to moving refs, `reset --hard`, `--no-verify`, and discards (rebase/amend/checkout-file pass by default for FF landing flows) — plus the **hotfix** skill (test-first, cherry-pick both ways, remotes handed to you). |
| [`commit`](commit/README.md) | The opinionated house **commit** style — bare single-line messages, topic-close + pause-for-review cadence, safe staging, a `commit-format` guard, and a `commit-nudge`. |
| [`setup`](setup/README.md) | One-time bootstrap — **scaffold** the `.agent/` workspace index and point CLAUDE.md/AGENTS.md at it, and **scaffold-claude-md** to write a house-style CLAUDE.md (a slim router of the hard rules). |
| [`reporting`](reporting/README.md) | The **lean-reporting output contract**, enforced — contract injected per prompt (`brevity-reminder`), re-pulsed every Nth tool call (`contract-pulse`), and a Stop `report-guard` that blocks a narrating/over-long final message. |
| [`session`](session/README.md) | Session continuity — **handoff** (write next-session notes, ≤4k), **continue** (boot from them), **session-summary** + a `session-start` hook. |
| [`instructions`](instructions/README.md) | Keep the agent-instruction system alive — **retro**, **lessons**, **instructions-audit**, **instructions-maintenance**, **rules-change** skills + `lesson-scout` / `instructions-auditor` agents + `caps` and `file-guard` hooks + two config-driven engines: **meta-lint** (behind `.agent/meta-lint.json`) and **tripwire-guard** (project-owned `.agent/guards.d/` asserts, any language). |
| [`review`](review/README.md) | Structured review — **review** (P0/HIGH/MED/LOW → `.agent/reviews/`) and **qa-gate** skills + `semantic-reviewer`, `spec-cross-checker`, `wireframe-vs-code`, `doc-auditor`, `isolation-reviewer` agents. |
| [`repo`](repo/README.md) | **rename** — move a file and cascade every reference across docs/skills/config. |
| [`flow`](flow/README.md) | Work management — **plan**, **milestone**, **scope-cut**, **triage-todo**, **feedback**, plus autonomous background execution: **looper** / **grind** / **collab** driven by shipped Python-3 runners, launched via gitignored `.agent/bin/{loop,grind}` symlinks. Ships the `todo-readonly-guard` — `.todo` stays user-owned (arm with "ALLOW TODO"). |
| [`patterns`](patterns/README.md) | A per-topic **pattern registry** (`.agent/patterns/`) — **manage-patterns** + `pattern-compliance`/`pattern-verifier` agents + hooks that gate edits governed only by non-blessed patterns. Ships the system, not any project's conventions. |
| [`worktree`](worktree/README.md) | Parallel isolated work — the **worktree** skill (reserve → plan → review-gated slices → land) + guards that keep edits inside the active worktree (mitigates [claude-code #36182](https://github.com/anthropics/claude-code/issues/36182)) + a SessionStart `worktree-detect` nudge. |

## Per-concern switches (env)

Picking plugins is the coarse control; these are the fine one. Guards self-gate on project config (patterns fire only with a registry, meta-lint only with
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
| `FLOW_LINK_OFF=1` | re-stamping the runner-link pointer (`.agent/bin/{loop,grind}` then keep their current target) |
| `FILE_GUARD_OFF=1` | the T3 enforcement-surface write guard (`FILE_GUARD_EXTRA` adds prefixes) |
| `CAPS_GUARD_OFF=1` | instruction-surface size caps |
| `META_LINT_OFF=1` | the meta-lint engine (already inert without `.agent/meta-lint.json`) |
| `TRIPWIRE_GUARD_OFF=1` | project tripwires (`TRIPWIRE_SKIP=1` = one-shot) |
| `PATTERN_GUARDS_OFF=1` | the pattern-registry edit gate |
| `WORKTREE_GUARD_DISABLE=1` | worktree edit containment **and** the SessionStart worktree nudge |
| `WORKTREE_LEAK_DETECT_DISABLE=1` | the post-edit worktree leak detector |

Opt-**in**, off by default: `WORKTREE_BASH_GUARD_ENABLE=1` (shell-channel worktree containment —
false-positive-prone; the flow runners arm it for their own children in worktree mode). The flow runners take `FLOW_*` env; see [`flow`](flow/README.md).

**Runtime: python3 (stdlib only), nothing else.** Every hook is python over a shared
`lib/hookio.py`, vendored into each plugin that uses it (a plugin can reach nothing outside its own
folder); their tests live in `<plugin>/tests/`, not inside the guards.
There is deliberately no `jq` dependency — a guard that disarms itself when a tool is missing is
worse than no guard, and `python3` is the one interpreter a Claude Code host already needs.
**That choice binds these plugins' own code, not yours:** the one place a project supplies
executable code — `.agent/guards.d/` tripwires — takes `*.sh`, `*.py`, or any executable file with
a shebang, so your guards are written in whatever your repo already speaks.

**No branch name is hardcoded.** `main` is not assumed anywhere: the git guard detects the repo's
own default branch (override with `GIT_GUARD_PROTECTED_BRANCH`), the `worktree` skill takes
`<integration>` / `<protected>` from the project, `scaffold-claude-md` reads the branch layout out
of the repo before writing a rule about it, and the tripwire examples take
`TRIPWIRE_INTEGRATION_BRANCH`. `develop`-, `trunk`-, and `master`-based projects need no config.
**Single-branch repos need one line:** where the integration branch *is* the protected branch, set
`GIT_GUARD_INTEGRATION_BRANCH` so the `worktree` protocol's fast-forward land is permitted while
force/delete refspecs and `checkout` onto it stay blocked.

## Conventions

- **One plugin per concern.** Each is a folder (`<plugin>/skills|commands|agents|hooks/`) in
  Claude Code's default plugin layout, with its own `README.md`, `CHANGELOG.md` and version.
  Plugins don't depend on each other: a skill that mentions another plugin's skill degrades to a
  dead mention when that plugin isn't enabled, and `flow` carries its own copy of `worktree`'s
  guards for runner confinement. A **command** (`/x`) is a thin shim that invokes a same-named **skill** which holds the actual
  logic (single source of truth). Commands are `disable-model-invocation: true` — they exist so you
  can *type* `/x`; the skill's own description is what Claude auto-triggers on, so nothing is
  duplicated. Claude Code namespaces plugin components as `<plugin>:<name>` in menus and
  autocomplete (`git:hotfix`, `review:doc-auditor`); the bare `/<name>` invokes them too
  (CC ≥ 2.1.216).
- **House layout.** Everything the toolkit creates lives under **`.agent/`** — `handoff.md`,
  `lessons/`, `worktrees.md`, `milestones.md`, `plan/`, `milestone/`, `loop/`, `grind/`,
  `patterns/`, `reviews/` — so it never clutters your repo root. Your `.docs/` and root `.todo`
  stay yours; skills *link* to `.docs/` but never write it. Each concern degrades gracefully when
  a project doesn't use it.
- **Commits:** bare imperative single line; default cadence is commit at **topic close, then pause
  for review** (opt into commit-as-you-go per session).
- **Versioning:** per plugin — any consumer-visible change to a plugin bumps its own
  `<plugin>/.claude-plugin/plugin.json` `version` in the same commit (CCD only re-materializes on
  a version change). Release notes: `<plugin>/CHANGELOG.md`; history before the split:
  [CHANGELOG.md](CHANGELOG.md).

`other/` is not a plugin — it holds standalone recipes (currently a machine-agnostic
guide to anchoring the Claude usage window on a schedule).

---

_Consolidated from per-project `.claude/` setups. Migration staging + notes live in `_review/`
(git-ignored — not part of the published marketplace)._
