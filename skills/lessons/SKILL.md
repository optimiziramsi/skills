---
name: lessons
description: >-
  Capture and curate durable lessons in `.agent/lessons/` — one file per lesson, indexed in its
  README, surfaced by tier (enforced hook / routed doc / indexed). Use whenever the user corrects a
  repeatable mistake ('don't do that anymore', 'I already told you', 'remember this'), asks to save
  a lesson, right after a hard debugging session, or when curating/pruning the lessons index.
  Project knowledge lives in-repo here, never in account memory.
---

# Lessons

Captures and curates hard-won lessons so the same mistake never has to be corrected twice. The
**content** lives in `.agent/lessons/` (one file per lesson + a `README.md` index); this skill is
the **how-to** for writing and maintaining it.

## When invoked

Fires whenever the user signals you are repeating a mistake or re-stating something they've already
established — capture the lesson so it sticks.

Explicit triggers (phrases): "don't do that anymore" · "I already told you" · "we agreed (not) to" ·
"you keep doing X" / "every time" · "remember (not) to X" / "from now on" · "add this as a lesson" /
"/lessons".

**Proactive trigger (no phrase needed):** the moment you notice you're being corrected on something
*repeatable* — a mistake any future session could repeat, or a preference the user just stated —
capture it WITHOUT being asked. A repeated correction that isn't written down is a process bug.

When in doubt: if a future session repeating this mistake would annoy the user, it's a lesson.

## The model — where durable knowledge lives

- artifact: `.agent/lessons/`
  holds:
    Durable cross-session knowledge: engineering lessons, working-style preferences,
    operational/harness gotchas
  lifecycle: Permanent — additive + pruned

- artifact: `.agent/handoff.md`
  holds: ONLY ephemeral next-session continuity. Capped ~4k chars
  lifecycle: Refreshed each session

- artifact: `.agent/patterns/<topic>.md` (if the project keeps a patterns registry)
  holds: Canonical code-shape recipes
  lifecycle: Per-topic registry

**Lessons is the durable home; handoff is the ephemeral brief.** If a fact is useful beyond the next
session, it's a lesson, not a handoff entry.

**In-repo, never account memory.** All project knowledge that would otherwise go to a
personal/account memory store lives here instead, so anyone who clones the repo inherits it.

**Fold-up:** when a lesson hardens into enforced policy with a code-shape recipe, graduate it into a
patterns doc or a skill and replace the lesson with a one-line pointer (or remove it). Lessons are
friction-reducers; once enforced by tooling a lesson has graduated out.

## Surfacing tiers — when must this lesson be discovered?

The index is passive — nothing guarantees a session reads a lesson *before* the moment it's needed.
So every lesson carries exactly one **surfacing tier** (default: indexed):

- tier: 3
  name: **enforced**
  mechanism:
    a guard hook (e.g. a `lesson-guards` PreToolUse hook) blocks the bad tool call outright and
    cites the lesson
  use-when: the violation is mechanically detectable (a greppable bad command)

- tier: 2
  name: **routed**
  mechanism:
    a read-before pointer wired into the activity's **home doc** — the file already guaranteed
    loaded when that work happens (a skill, a CLAUDE.md §)
  use-when: the lesson is tied to a specific risky *moment*

- tier: 1
  name: **indexed**
  mechanism: README index line only (the default)
  use-when: reference/browsing knowledge; no single moment of risk

Tier-2/3 lessons are additionally listed in the README's **⚡ Read-before tripwires** registry
(moment → lesson → where it's wired), so wiring stays auditable. A tier-3 hook does not retire its
lesson — the lesson remains the *why* the guard cites.

When adding a guard rule: extend the guard hook, add a matching `--test` case, and run its
self-test. Guards should fail open (unparsable input → allow) and match only at command positions;
keep rules narrow — a false block interrupts every session.

## Priority router — how prominently a lesson surfaces

Orthogonal to the surfacing tier (the *mechanism*), every lesson holds one **priority**, expressed
purely by its position in the README index (no per-file field — the index is the single source):

- priority: 🔴 **High**
  read-when: every session start
  cap: **10**
  belongs-there-when: applies to every session AND isn't mechanically enforced

- priority: 🟡 **Mid**
  read-when: entering the matching activity (grouped)
  cap: **35**
  belongs-there-when: activity-scoped; reading it on entry prevents the mistake

- priority: ⚪ **Low**
  read-when: lookup only (grep when relevant)
  cap: (within the total)
  belongs-there-when: enforced-by-hook rationale, narrow facts, rare references

Caps are ratchets. **Promotion requires demotion when a level is full** — that forced trade IS the
reordering-by-importance mechanism; never grow a level to avoid choosing. If the project has a
mechanical linter it enforces the caps; otherwise enforce them by hand at each curation pass.

**Usage-driven reordering:** end every 🔴 High line with `↑YYMMDD` — the date the lesson last proved
itself (fired, prevented a mistake, or was re-confirmed). Bump it when that happens; promote a Mid
lesson that keeps biting session-wide; demote a High unconfirmed for >90 days. The cascade runs all
the way down: Mid lessons that stop biting sink to Low at curation passes; Low lessons whose
mechanic is gone get pruned. A tier-3 (enforced) lesson is at most ⚪ Low in the index — the hook
does the surfacing, the file keeps the why.

## Groups

The 🟡 Mid section of the index is grouped by **activity** — the work you're doing when the lesson
bites — so a session scans only the group matching its current work. Tailor the groups to what your
project actually does; a sensible default set:

- **Git & landing** — commits, staging, squashes, remotes.
- **Docs & instructions** — doc conventions, instruction-system discipline.
- **Code shapes** — language/framework conventions, imports, config.
- **Verification** — gates, checks, post-change sweeps.
- **Runners & sub-agents** — background jobs, delegation.
- **Collaboration & session flow** — how to work with this user.
- **Bookkeeping** — todo / plan / milestone discipline.
- **Environment & tooling** — shell / OS / runtime traps.

## Adding a lesson

1. **Dedup first.** Scan `.agent/lessons/README.md` for an existing lesson covering this. If one
   exists, UPDATE it (add the new origin/nuance) — don't create a near-duplicate.
2. **Pick the priority** (and, for Mid, the group). If the target level is at its cap, promotion
   requires demoting something — make the trade explicit.
3. **Create `.agent/lessons/<slug>.md`** — `<slug>` is kebab-case, short, describes the rule
   (e.g. `never-launch-runners`, `fix-source-schema-first`). One lesson per file. The exact filename
   shape is a project choice: a permanent numeric ordering prefix (`01-never-launch-runners.md`) is
   fine — pin whatever convention you want by adding a `.agent/lessons` rule to meta-lint's
   `filenames.rules` (see `examples/meta-lint.rabbit-run.json`); nothing enforces bare kebab.
4. **Write the file** (format below).
5. **Pick the surfacing tier.** Default **indexed**; if the mistake happens at a specific risky
   moment, **route** it (pointer in the home doc + a ⚡ registry row); if it's a greppable bad
   command, **enforce** it (guard rule + `--test` case + ⚡ registry row).
6. **Add one line to the README index** under the right priority section (High lines end `↑YYMMDD`).

## Updating / pruning

- **Update before append** — always extend an existing lesson before adding a new one.
- **One lesson = one rule, one file.** If a file grows several distinct rules, split it.
- **Prune when the mechanic is gone** — a lesson comes out when its underlying cause no longer
  exists (file renamed, system replaced, rule reversed). Not because of age; the `**Origin:**` date
  helps judge this.
- **Fold-up** canonical lessons into a patterns doc or a skill, then remove the lesson.

## Lesson file format

```markdown
# <Title — the rule, stated as an imperative or a claim>

<Body: the rule, why it matters, concrete examples. For a debugging lesson the fastest shape is:
what bit us → root cause → the fix → how to verify. Prose or terse bullets, not a story.>

**Origin:** <date + the incident that produced this lesson — keep it; future-you needs the context to
judge edge cases. Append "Generalized <date> — …" lines when the lesson is extended.>
```

Rules: title is `#` (H1, the file owns the title). Keep the `**Origin:**` line — it's the lesson's
provenance. If a lesson contradicts a doc or another skill, the lesson wins — update the other (and
note it).

## README index format

`README.md` is the index loaded as the entry point — one bullet per lesson (`[Title](file.md) —
hook`), routed by priority (🔴 High flat list · 🟡 Mid grouped by activity · ⚪ Low flat list), never
the lesson content itself. The **⚡ Read-before tripwires** section at the top is the wiring registry
for enforced + routed lessons; a tier-2/3 lesson appears both there and in its priority home. Keep
index entries to ONE bullet each — an entry may wrap physically at the project's wrap width; the
index is scanned every session; compactness is a feature.
