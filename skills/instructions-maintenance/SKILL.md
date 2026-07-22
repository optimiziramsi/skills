---
name: instructions-maintenance
description: >-
  The constitution of the agent instruction system — the rules for how CLAUDE.md, .claude/ (skills,
  rules, hooks, settings, agents), and .agent/ evolve. Load this BEFORE creating or modifying any
  instruction file, when adding a skill/rule/hook/agent, changing a convention, or capturing a
  lesson. Owns the design principles, extension criteria, governance tiers, retention policy, and
  caps that the other instructions skills apply.
---

# Instruction system — constitution & maintenance

This skill owns the rules for how the instruction system itself evolves. If it conflicts with
another instruction file, this file wins — then fix the other. Assumes the `.agent/` house layout.

The other `instructions` skills apply what this defines: `retro` harvests into it, `lessons`
captures into it, `instructions-audit` repairs it, `rules-change` changes it. This is the shared
model.

## Design principles

1. **One fact, one owner.** Every convention/invariant/table lives in exactly one file; everything
   else links to it. Duplication is how instructions rot.
2. **Enforce mechanically what must never happen.** Hard rules become hooks or permission denies,
   not prose. Prose is for judgment.
3. **By convention, not enumeration.** Never document what `ls`, `git log`, or the filesystem can
   answer — document the naming convention and point at the source. Enumerated lists are drift
   bombs.
4. **Rules guard, skills teach.** `.claude/rules/*.md` = path-scoped MUST/NEVER invariants (≤ ~20
   lines, auto-loaded). Skills = full procedures, loaded per task.
5. **Lessons remember.** `.agent/lessons/` is the single sink for recurring mistakes and intentional
   designs. Skills cite lessons; they don't restate them.

## One fact, one owner — the ownership matrix

Keep an authoritative record list (in this file, or a CLAUDE.md section) of which file owns which
class of fact, so nothing is documented twice. A typical house layout:

- fact-class: Session workflow / routing summary
  owner: `CLAUDE.md`

- fact-class: Path-scoped invariants
  owner: `.claude/rules/<domain>.md`

- fact-class: Full procedures
  owner: `.claude/skills/<name>/SKILL.md`

- fact-class: Recurring mistakes, intentional designs
  owner: `.agent/lessons/`

- fact-class: Architecture / code-shape / recipes
  owner: `.docs/`

- fact-class: Mechanical enforcement
  owner: `.claude/settings.json` + `.claude/hooks/`

- fact-class: Applied T2/T3 changes + `Last audit:` stamp
  owner: `.agent/instructions-changelog.md`

- fact-class: This constitution (tiers, caps, doc-sync gate)
  owner: this file

## The doc-sync gate

> Any change that alters a convention, invariant, entity pattern, or layout MUST update the owning
> file **in the same commit.**

When you and a doc disagree about reality, reality wins — fix the doc; if the misread caused a wrong
action, also write a lesson (`lessons` skill).

## File format — 100-col wrap + record lists

All governed instruction markdown follows one mechanical format, enforced by meta-lint's `[wrap]` +
`[no-tables]` checks where the project runs the engine:

- **Hard-wrap prose at 100 columns.** Mechanical exemptions ONLY: lines inside code fences; lines
  whose content is a single unsplittable token (a long URL or path — use reference-style link
  definitions); files with a GENERATED header. YAML frontmatter is NOT exempt — a long
  `description:` uses a folded scalar (`>-`) and wraps like prose. Agent-written extensionless
  files (e.g. a `.todo-inbox` deferral queue) belong under the same rule — projects running the
  meta-lint engine list them in `extra_governed_files`.
- **Tables are banned — use record lists**: YAML array-of-objects shape. The rules: (1) **one
  dash per RECORD** — never one dash per field; (2) the record's remaining fields sit under the
  dash as 2-space-indented `field: value` lines; (3) a long or multi-line value gets the bare
  key on its own line, the value following on lines indented 4 spaces (2 beyond the field keys),
  so ownership is unambiguous; (4) ONE blank line between records. The shape mirrors a YAML list
  of objects (strict YAML parseability is NOT required — values may open with markdown markers).
  Field-level diffs beat row-level diffs, and source view stays readable. When converting a
  table, each row becomes one record led by its key field, the remaining cells folded in as
  `field: value` pairs — never drop a cell. The record shape is the
  TABLE replacement only: an ordinary bullet list stays an ordinary bullet list — never convert
  one into the other in either direction. Sole exception: the repository-root `README.md`
  (GitHub-rendered, human-facing) may keep tables.

  ```markdown
  | foo   | bar          | baz   |
  | ----- | ------------ | ----- |
  | val 1 | a long value | val 3 |
  | val 4 | val 5        | val 6 |

  becomes

  - foo: val 1
    bar:
      long lorem ipsum wrapped at the 100-col limit
      continuing lines clearly belong to bar
    baz: val 3

  - foo: val 4
    bar: val 5
    baz: val 6
  ```

- **Index files stay one bullet per entry** — an entry may wrap physically at the wrap width, but
  never grows into a second bullet or a paragraph.

## Extension criteria — when to add each mechanism

- **Skill** (`.claude/skills/<name>/SKILL.md`): a task type recurred ≥2× with a repo-specific
  procedure. Frontmatter `name` + a trigger-rich `description`; body = reads, procedure, validation.
- **Rule** (`.claude/rules/<name>.md`): an invariant keeps being violated when touching certain
  paths. Path globs in frontmatter; ≤ ~20 lines of MUST/NEVER, each derived from a skill or lesson.
- **Hook** (`.claude/hooks/*` + wiring): a rule is non-negotiable AND mechanically checkable.
  Fail-open on parse errors (a broken hook must never brick sessions). Every block/pass rule gets a
  self-test case; run it before committing. PreToolUse: exit 2 + stderr (or a deny JSON) blocks;
  PostToolUse: `additionalContext` nudges.
- **Agent** (`.claude/agents/<name>.md`): a delegated task needed a restricted tool set or isolated
  context ≥2×. Don't pre-create.
- **Command wrapper** (`.claude/commands/<name>.md`): exists only so the slash picker lists it.
  Every skill gets one; a wrapper is a `description:` + a pointer to its skill + `$ARGUMENTS` —
  never any logic. Creating/renaming/retiring a skill updates its wrapper in the SAME commit (1:1
  parity).
- **Settings** (`.claude/settings.json`): shared/tracked; machine overrides go in
  `settings.local.json` (gitignored). Deny rules beat allows — never remove a deny without a user
  decision.

## Growth control & retention

Context bloat degrades every future session, so the system must not overgrow.

**Caps.** Give each always-loaded / per-file surface a character cap (CLAUDE.md, each SKILL.md, each
rule, the lessons index, the changelog…). If the project has a mechanical `caps`/`meta-lint` checker
it owns the numbers and enforces them; any table here only mirrors it. **Never raise a cap to fit
content** — that's a T3 change.

**Retention test** — every statement in a live instruction file must pass all four; the first
failure decides the action:

1. **Still true?** No → delete or amend; reality wins.
2. **Still actionable?** Would a future session act differently without it (judged against the last
   ~3 months of real commits, not hypotheticals)? No → delete; git keeps the nostalgia.
3. **Not derivable?** (`ls` / `git log` / one obvious read answers it) Derivable → delete; document
   the convention instead.
4. **In its owner file?** No → move it there, leave a link.

**Compaction precedence** (over cap, or failing the test): **merge** → **route** to the one owner
(leave a link) → **tighten** wording → **retire** (delete the body, leave a `Supersedes …` note or a
`[retired YYYY-MM-DD: reason]` one-liner). Full text stays in git — meaning is never silently
deleted, and live files never keep "(kept for history)" content.

## Governance tiers

- **T1 — status/journal**: plan/status updates, new lessons entries, changelog lines → update
  freely.
- **T2 — safe**: wording clarifications of an existing rule, reality-syncs, broken-pointer fixes,
  mechanical compaction that passes the retention test → apply directly + ONE changelog line.
- **T3 — risky**: new/removed rules, cap changes, ANY change to enforcement/automation (hooks,
  settings, guards), workflow changes, judgment deletions → **never without explicit user approval**
  (via the `rules-change` skill). Audits/retros batch all T3 findings into ONE proposal.

## Commit scope

Instruction changes commit single-line per the `commit` skill; keep an instruction change and its
owner-file sync in the same commit (the doc-sync gate).
