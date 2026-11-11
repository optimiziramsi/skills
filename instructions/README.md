# instructions — keep the agent instruction system small and true

The `instructions@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

The rules for how CLAUDE.md, `.claude/` and `.agent/` evolve, the sweep that de-rots them, and the
checks that keep them inside their size caps.

## Contents

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

- name: `instructions-audit`
  kind: skill + command
  purpose:
    De-rot sweep — broken pointers, dead/duplicate rules, truth-vs-reality drift, cap breaches,
    enforcement drift; safe fixes applied, risky ones proposed.

- name: `instructions-auditor`
  kind: agent
  purpose:
    Read-only sweep of the instruction surface → severity-ranked findings with `file:line`
    evidence. Used by `instructions-audit`.

- name: `caps`
  kind: hook
  purpose:
    Stop — a note for the **user** listing any instruction-surface **cap breaches** (file sizes
    + skill/agent/rule counts): a `systemMessage`, so it is not model context and never blocks
    the stop; shown once per session per distinct breach-set, whether or not the session wrote
    files. Nothing is printed at session start. Makes the governance caps the skills *describe*
    visible. All caps env-overridable; fails open; escape hatch `CAPS_GUARD_OFF=1`; tests:
    `python3 tests/test_caps.py`.

- name: `bin/meta-lint`
  kind: engine
  purpose:
    Config-driven **instruction-system linter** — 19 mechanical checks (cross-refs, lessons
    index/priority, agents/skills/commands symmetry, pattern routes, filenames, dup tripwires,
    sizes in lines OR chars, counts, staleness, boards, audit stamp, 100-col `[wrap]`,
    `[no-tables]`). Activates only where a project ships `.agent/meta-lint.json`. At Stop it
    does two things: `--end-note` shows the user the findings count (a `systemMessage`, once per
    session per distinct text, never blocking; loud-DISARM `|| echo` fallback), and `--stop`
    **blocks** (exit 2) when a file-writing session leaves a size/count cap breached. Nothing
    runs at session start. Escape hatch `META_LINT_OFF=1`; self-test `--test`, plus
    `python3 tests/test_meta_lint_note.py`.

Capturing and harvesting lessons is the separate [`lessons`](../lessons) plugin; project-owned
command checks and the settings/hooks edit guard are [`guards`](../guards).

## Model

- **House layout:** `.agent/lessons/` (durable knowledge) · `.claude/rules/` (binding rules) ·
  `.docs/` (architecture/recipes) · `.agent/handoff.md` (volatile next-session state) ·
  `.agent/instructions-changelog.md` (what changed, tier-tagged).
- **Governance:** *safe* changes (wording, broken pointers, dedup, compaction) apply directly;
  *risky* changes (add/remove rule, cap change, behavior change) are proposed for approval.
- **Mechanical checks:** the shipped `caps` hook reports size/count cap breaches to the user at
  Stop; projects that want the full structural sweep, and a Stop gate on the caps, opt into the
  `meta-lint` engine below.
- **Timing:** nothing here speaks at session start — a chat does the work it was opened for.
  Housekeeping facts go to the user at Stop, and not at all in a linked git worktree (see
  Settings).

## meta-lint — the config-driven instruction-system linter

The ENGINE ships in this plugin (`bin/meta-lint`, python3 stdlib only); each project supplies the
POLICY via **`.agent/meta-lint.json`**. No config file → silent no-op (projects opt IN). A minimal
`{}` config lints the house layout with the default caps; everything is overridable: enabled
`checks`, cap numbers **and units** (`lines` vs `chars`, most-specific entry wins per unit),
directory `layout`, `filenames` conventions, `dup` tripwire pairs, `boards`, the `audit` stamp
file+regex, `generated` file globs, and the `allow_marker` opt-out (repo-wide allows capped).

- **Modes:** full run (findings listed, exit 1 — advisory), `--fast` (one-line summary, exit 0 —
  for running by hand), `--end-note` (Stop-hook **NOTE** — the findings count as a
  `systemMessage` for the user, exit 0, one-shot per session per distinct text, silent when
  clean), `--stop` (Stop-hook **BLOCK** — exit 2 when the session wrote files and a size/count
  cap is breached, one-shot per breach-set), `--test` (self-test), `--config P` / `--root D`
  overrides.
- **Format checks:** `[wrap]` flags prose lines over `wrap.width` (default 100) — code fences,
  single-unsplittable-token lines (long URLs/paths), and GENERATED files exempt; frontmatter is
  not (use folded scalars). `[no-tables]` flags markdown tables in governed files — convert to
  record lists (one dash per record, fields as 2-space-indented `field: value` lines); the
  repo-root `README.md` is excluded by default, both checks take extra `exclude` globs.
  `extra_governed_files` pulls extensionless agent-written files (e.g. `.todo-inbox`) under both
  format checks — governed markdown is otherwise `*.md` under the crossref roots.
- **Wiring:** Stop runs `meta-lint --end-note || echo '{"systemMessage":"⚠️ … DISARMED …"}'` —
  fail-open but **loud**: the fallback fires only when the engine itself can't run, never on
  findings. Stop also runs `meta-lint --stop` bare (no `|| echo`, so its exit 2 actually blocks);
  only the size/count caps run there, and only a file-writing session over a cap is stopped. The
  note is information for the user; the block is a gate on what the session wrote.
- **Coexistence:** where `.agent/meta-lint.json` exists, **meta-lint supersedes `caps`** —
  caps detects the config and skips itself, so exactly one engine reports caps and nothing
  double-reports.
- **Example policy:** [`examples/meta-lint.rabbit-run.json`](examples/meta-lint.rabbit-run.json) —
  a full-strength real-project config (line caps per file class, 4 dup tripwires, RR counts,
  board + audit + routes checks all armed). Copy and trim for your project.

## Enable

```bash
claude plugin install instructions@optimiziramsi --scope project
```

> **Note:** enabling this plugin activates the `caps` hook in every project that enables it. It's a
> no-op where the capped files don't exist, and every cap is env-overridable (`CAP_CLAUDE`,
> `CAP_HANDOFF`, `CAP_SKILL`, `MAX_SKILLS`, …). Set `CAPS_GUARD_OFF=1` to disable it entirely.

## Settings

In a settings.json `env` block (any scope):

- `CAPS_GUARD_OFF=1` — the `caps` note off.
- `META_LINT_OFF=1` — the `meta-lint` engine off (note and Stop gate).
- `NUDGES_IN_WORKTREE=1` — show the `caps` and `meta-lint --end-note` notes in a linked git
  worktree too. Off by default: a worktree is for one topic, and cleanup belongs to the main
  checkout's chat. The same switch is read by every plugin that ships such notes. It does not
  affect the `meta-lint --stop` gate, which runs everywhere.
- `CAP_*` / `MAX_*` — the `caps` numbers (defaults below).

Defaults (chars unless noted): `CLAUDE.md`/`AGENTS.md` 6000 · `.agent/handoff.md` 4000 ·
`.agent/instructions-changelog.md` 8000 · per `SKILL.md` 9000 · per agent 4000 · per rule 2000 ·
per command 800 · per lesson 4000 · counts: ≤12 skills, ≤6 agents, ≤10 rules.
