# instructions — keep the agent instruction system alive

Part of the [`optimiziramsi-skills`](../README.md) plugin (the opsi toolkit).

The meta-system: capture what you learn, route it to the right store, and keep the instruction
system consistent over time — so you fix something once and every future session inherits it.

## Contents

- name: `retro`
  kind: skill + command
  purpose:
    Session-end harvest — route learnings to lessons/rules/docs, merge-don't-append, compact at
    caps, **apply-safe / propose-risky**, changelog, commit.

- name: `lessons`
  kind: skill + command
  purpose:
    Capture + curate one durable lesson in `.agent/lessons/` — kebab-slug file, README index,
    two-axis surfacing (enforced-hook / routed-doc / indexed × High/Mid/Low caps), dedup, prune,
    fold-up.

- name: `instructions-audit`
  kind: skill + command
  purpose:
    De-rot sweep — broken pointers, dead/duplicate rules, truth-vs-reality drift, cap breaches,
    enforcement drift; safe fixes applied, risky ones proposed.

- name: `instructions-maintenance`
  kind: skill + command
  purpose:
    The **constitution** — design principles, ownership matrix, extension criteria, governance
    tiers, retention/caps. The model the other skills apply; load before editing any instruction
    file.

- name: `rules-change`
  kind: skill + command
  purpose:
    The sanctioned **T3-change door** — explicit approval, coherence + cap check, re-test
    enforcement, reality check, changelog. What retro/audit route approved changes through.

- name: `lesson-scout`
  kind: agent
  purpose:
    Prior-art lookup — searches `.agent/lessons/` before you re-debug something. Read-only.

- name: `instructions-auditor`
  kind: agent
  purpose:
    Read-only sweep of the instruction surface → severity-ranked findings with `file:line`
    evidence. Used by `instructions-audit`.

- name: `caps`
  kind: hook
  purpose:
    SessionStart — surface any instruction-surface **cap breaches** (file sizes +
    skill/agent/rule counts). Stop — after any session that wrote files, nudge once per distinct
    breach-set on ANY breach present (pre-existing included, not only what this session bloated).
    Makes the governance caps the skills *describe* mechanical. All caps env-overridable; fails
    open; escape hatch `CAPS_GUARD_OFF=1`; self-test `--test`.

- name: `file-guard`
  kind: hook
  purpose:
    PreToolUse — writes to **T3 enforcement surfaces** (`.claude/settings*.json`,
    `.claude/hooks/`) downgrade to an **ask**: a session must not silently rewrite its own
    guards. Extra prefixes via `FILE_GUARD_EXTRA` (colon-separated); escape hatch
    `FILE_GUARD_OFF=1`; self-test `--test`.

- name: `bin/meta-lint`
  kind: engine
  purpose:
    Config-driven **instruction-system linter** — 19 mechanical checks (cross-refs, lessons
    index/priority, agents/skills/commands symmetry, pattern routes, filenames, dup tripwires,
    sizes in lines OR chars, counts, staleness, boards, audit stamp, 100-col `[wrap]`,
    `[no-tables]`). Activates only where a project ships `.agent/meta-lint.json`; pulsed advisory
    at SessionStart via `--fast` (loud-DISARM `|| echo` fallback), and **blocks at Stop** via
    `--stop` (exit 2) when a file-writing session leaves a size/count cap breached. Escape hatch
    `META_LINT_OFF=1`; self-test `--test`.

- name: `tripwire-guard`
  kind: hook, engine
  purpose:
    PreToolUse `Bash` — runs **project-owned command tripwires** from `.agent/guards.d/*.sh`
    against every Bash command: a guard exits 2 to block (first block wins, reason fed to the
    agent), 0 to allow, anything else becomes a loud non-blocking warning. No dir/guards → silent
    no-op. One-shot escape `TRIPWIRE_SKIP=1` command prefix; kill switch `TRIPWIRE_GUARD_OFF=1`;
    jq-missing loud-DISARM; self-test `--test` (runs each guard's `tripwire_test` too).

The full knowledge system: **define** (`instructions-maintenance`) · **capture** (`lessons`) ·
**harvest** (`retro`) · **maintain** (`instructions-audit`) · **change** (`rules-change`).

## Model

- **House layout:** `.agent/lessons/` (durable knowledge) · `.claude/rules/` (binding rules) ·
  `.docs/` (architecture/recipes) · `.agent/handoff.md` (volatile next-session state) ·
  `.agent/instructions-changelog.md` (what changed, tier-tagged).
- **Governance:** *safe* changes (wording, broken pointers, dedup, compaction) apply directly;
  *risky* changes (add/remove rule, cap change, behavior change) are proposed for approval.
- **Mechanical checks:** the shipped `caps` hook enforces the size/count caps at session start +
  stop; projects that want the full structural sweep opt into the `meta-lint` engine below.

## meta-lint — the config-driven instruction-system linter

The ENGINE ships in this plugin (`bin/meta-lint`, python3 stdlib only); each project supplies the
POLICY via **`.agent/meta-lint.json`**. No config file → silent no-op (projects opt IN). A minimal
`{}` config lints the opsi house layout with the default caps; everything is overridable: enabled
`checks`, cap numbers **and units** (`lines` vs `chars`, most-specific entry wins per unit),
directory `layout`, `filenames` conventions, `dup` tripwire pairs, `boards`, the `audit` stamp
file+regex, `generated` file globs, and the `allow_marker` opt-out (repo-wide allows capped).

- **Modes:** full run (findings listed, exit 1 — advisory), `--fast` (one-line summary, exit 0 —
  the SessionStart pulse), `--stop` (Stop-hook **BLOCK** — exit 2 when the session wrote files and a
  size/count cap is breached, one-shot per breach-set), `--test` (self-test), `--config P` /
  `--root D` overrides.
- **Format checks:** `[wrap]` flags prose lines over `wrap.width` (default 100) — code fences,
  single-unsplittable-token lines (long URLs/paths), and GENERATED files exempt; frontmatter is
  not (use folded scalars). `[no-tables]` flags markdown tables in governed files — convert to
  record lists (one dash per record, fields as 2-space-indented `field: value` lines); the
  repo-root `README.md` is excluded by default, both checks take extra `exclude` globs.
  `extra_governed_files` pulls extensionless agent-written files (e.g. `.todo-inbox`) under both
  format checks — governed markdown is otherwise `*.md` under the crossref roots.
- **Wiring:** SessionStart runs `meta-lint --fast || echo "⚠️ meta-lint DISARMED …"` — fail-open
  but **loud**: the fallback fires only when the engine itself can't run, never on findings. Stop
  runs `meta-lint --stop` bare (no `|| echo`, so its exit 2 actually blocks); only the size/count
  caps run there, and only a file-writing session over a cap is stopped.
- **Coexistence:** where `.agent/meta-lint.json` exists, **meta-lint supersedes `caps.sh`** —
  caps.sh detects the config and skips itself at BOTH SessionStart and Stop, so exactly one engine
  surfaces caps and nothing double-reports or double-blocks.
- **Example policy:** [`examples/meta-lint.rabbit-run.json`](examples/meta-lint.rabbit-run.json) —
  a full-strength real-project config (line caps per file class, 4 dup tripwires, RR counts,
  board + audit + routes checks all armed). Copy and trim for your project.

## tripwire-guard — project-owned command tripwires

The ENGINE is a PreToolUse `Bash` hook (`hooks/tripwire-guard.sh`); the PROJECT supplies the
guards as **`.agent/guards.d/*.sh`** scripts (no dir → silent no-op). Each guard is executed in
sorted order with the Bash command in `$TRIPWIRE_COMMAND` and the full tool-input JSON in
`$TRIPWIRE_INPUT` + on stdin: **exit 2 + printed reason = block** (first block wins), exit 0 =
allow, anything else = loud non-blocking warning. A guard that also defines `tripwire_test` (and
gates its dispatch with `[ "${BASH_SOURCE[0]}" = "$0" ]`) gets its self-test run by the engine's
`--test`.

Shipped, ready-to-copy examples in [`examples/guards.d/`](examples/guards.d/) (integration branch
via `TRIPWIRE_INTEGRATION_BRANCH`, default `develop`):

- **`land-check.sh`** — blocks a landing push (`git push . HEAD:<integration>`) when HEAD isn't
  rebased onto the branch's *current* tip, and when the land would resurrect a board-file line
  (`TRIPWIRE_BOARD_FILE`, default `.agent/worktrees.md`) that the integration branch deleted.
- **`docs-drift-warn.sh`** — warn-only: a landing push that changes source
  (`TRIPWIRE_SRC_RX`) without touching docs (`TRIPWIRE_DOCS_RX`).
- **`cap-gate.sh`** — blocking: refuses a `git commit` while the instruction surface is over cap —
  the enforcement complement to the nudge-only `caps` hook. Caps env-overridable (`CAP_CLAUDE` …);
  `CAP_GATE_OFF=1` to bypass.

Escape hatches: prefix the ONE false-positiving command with `TRIPWIRE_SKIP=1` (one-shot, visible
in the transcript); `TRIPWIRE_GUARD_OFF=1` kill switch; `TRIPWIRE_GUARDS_DIR` overrides the
discovery dir. Missing jq disarms LOUDLY (systemMessage), never silently.

## Enable

```json
{ "enabledPlugins": { "optimiziramsi-skills@optimiziramsi": true } }
```

> **Note:** enabling this plugin activates the `caps` hook in every project that enables it. It's a
> no-op where the capped files don't exist, and every cap is env-overridable (`CAP_CLAUDE`,
> `CAP_HANDOFF`, `CAP_SKILL`, `MAX_SKILLS`, …). Set `CAPS_GUARD_OFF=1` to disable it entirely.

Defaults (chars unless noted): `CLAUDE.md`/`AGENTS.md` 6000 · `.agent/handoff.md` 4000 ·
`.agent/instructions-changelog.md` 8000 · per `SKILL.md` 9000 · per agent 4000 · per rule 2000 ·
per command 800 · per lesson 4000 · counts: ≤12 skills, ≤6 agents, ≤10 rules.
