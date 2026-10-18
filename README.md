# optimiziramsi-skills — Claude Code toolkit

A personal [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins),
`optimiziramsi`, shipping **one plugin per concern**: reusable **skills, commands, agents, and
hooks** shared across my projects — solve something once, get it everywhere, update it in one
place. Each project enables only the plugins that suit it. The repo root is the marketplace
(`.claude-plugin/marketplace.json`); every top-level concern folder (`git-guard/ commit/ runners/ …`) is a
self-contained plugin with its own `.claude-plugin/plugin.json`, `skills/ commands/ agents/
hooks/`, `README.md` and `CHANGELOG.md`.

## Install — per project

Register the marketplace once per machine, then pick plugins in each project. From a `claude`
session in the project:

```bash
claude plugin marketplace add optimiziramsi/skills
```

```bash
claude plugin install git-guard@optimiziramsi --scope project
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
    "git-guard@optimiziramsi": true,
    "commit@optimiziramsi": true,
    "session@optimiziramsi": true
  }
}
```

- **Opt out personally** without touching the shared file: `"<plugin>@optimiziramsi": false` in
  the project's `.claude/settings.local.json`.
- **Tune a plugin** with the env switches below — shared in `.claude/settings.json` `env`,
  personal in `.claude/settings.local.json` `env`.
- **Coming from the single plugin?** `optimiziramsi-skills@optimiziramsi` no longer exists —
  install the plugins the project wants, then uninstall it (ADOPTION.md § Migrating). Floor: CC / CCD **≥ 2.1.195**.

Full adoption protocol and gotchas: **[ADOPTION.md](ADOPTION.md)**.

## Plugins

Eighteen plugins, each a top-level folder; the id is `<folder>@optimiziramsi`. Usually enabled
together: `worktree` + `worktree-guards`; `todo` + `planning`.

| Plugin | Provides |
|---|---|
| [`git-guard`](git-guard/README.md) | Git safety net — a hook that blocks push/pull/fetch, bulk adds, non-FF merges, protected-branch moves, hard resets, --no-verify and discards of uncommitted work. |
| [`hotfix`](hotfix/README.md) | Test-first hotfix for a deployed bug — reproduce as a failing test, minimal fix, land it on both the mainline and the release branch. |
| [`commit`](commit/README.md) | House commit style — bare single-line messages, topic-close + pause-for-review cadence, safe staging; a commit-format guard and an end-of-session commit nudge. |
| [`rename`](rename/README.md) | Move a file and cascade every reference to it across docs, skills and config. |
| [`reporting`](reporting/README.md) | Lean-reporting output contract, enforced — injected per prompt, re-pulsed every Nth tool call, and a Stop guard that blocks a narrating or over-long final message. |
| [`session`](session/README.md) | Session continuity — handoff (next-session notes, ≤4k), continue, session-summary, and a SessionStart state snapshot. |
| [`lessons`](lessons/README.md) | Learn once, keep it — retro harvests a session's learnings, lessons curates them in .agent/lessons/, and the lesson-scout agent finds prior art before you re-debug. |
| [`instructions`](instructions/README.md) | Keep the agent instruction system small and true — its rules (instructions-maintenance, rules-change), the instructions-audit sweep + auditor agent, and the caps / meta-lint size and structure checks. |
| [`guards`](guards/README.md) | Project-owned enforcement — run your own .agent/guards.d checks on every shell command (tripwire-guard), and ask before the agent edits Claude settings or hook scripts (file-guard). |
| [`review`](review/README.md) | Structured review — the review skill (P0/HIGH/MED/LOW → .agent/reviews/) plus semantic-bug, spec, doc-drift, multi-tenant isolation and wireframe reviewer agents. |
| [`qa-gate`](qa-gate/README.md) | The done-gate — typecheck, unit, e2e and visual verification before any claim of done. |
| [`planning`](planning/README.md) | Plans and milestones — single-topic implementation plans in .agent/plan/, multi-session initiatives in .agent/milestone/. |
| [`todo`](todo/README.md) | The .todo parking lot — triage-todo, feedback and scope-cut, plus a guard that keeps .todo the user's (arm with "ALLOW TODO"). |
| [`runners`](runners/README.md) | Unattended background work — looper / grind / collab prepare jobs that the shipped loop and grind runners execute as headless claude sessions, confined when run in a worktree. |
| [`patterns`](patterns/README.md) | Per-topic pattern registry under .agent/patterns/ — manage-patterns, pattern-compliance / pattern-verifier agents, and hooks that gate edits governed only by non-blessed patterns. |
| [`worktree`](worktree/README.md) | The parallel-work protocol — drive one topic on its own git worktree as review-gated slices, landing only on the human's OK. Pairs with worktree-guards. |
| [`worktree-guards`](worktree-guards/README.md) | Guards that keep edits inside the active git worktree — write and shell guards, a leak detector, and a SessionStart worktree notice. No-ops outside a linked worktree. |
| [`setup`](setup/README.md) | One-time bootstrap — scaffold the .agent/ workspace and write a house-style slim-router CLAUDE.md. |

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
false-positive-prone; the runners arm it for their own children in worktree mode). The runners take `FLOW_*` env; see [`runners`](runners/README.md).

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
  dead mention when that plugin isn't enabled, and `runners` carries its own copy of
  `worktree-guards`' guards for runner confinement. A **command** (`/x`) is a thin shim that invokes a same-named **skill** which holds the actual
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
