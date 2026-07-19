---
name: manage-patterns
description: |
  Author and curate a per-topic pattern registry under `.agent/patterns/`. Use when: adding a new pattern topic, modifying one (status flip TODO → decided → blessed, body rewrite, anti-pattern addition, cross-reference update), splitting/merging topics, or when the user says "bless a pattern", "decide a pattern", "walk a topic", "promote pattern X to blessed", or names ".agent/patterns". Covers the phased authoring workflow — brainstorm → plan → build the code → human review → write the pattern — with an explicit pause-for-human at each phase. Patterns are NEVER written from imagination or an architecture sketch alone; they are derived from real, compiling, human-reviewed reference code.
---

# Manage Patterns — author + curate the pattern registry

The pattern registry lives at **`.agent/patterns/`** — one markdown file per topic, plus a `README.md` index. **This folder IS the registry.** Every blessed code shape in the project is documented here with a full prose body + GOOD / BAD / anti-patterns / edge cases. Reference files in the codebase are SOFT examples; the bodies here govern.

The registry is machine-enforced by this plugin's hooks: `generate-pattern-routes.py` compiles every pattern's governance globs into `.agent/patterns/pattern-routes.tsv`, and the `pattern-guards` hook reads that table to **hard-block edits in areas governed only by non-blessed patterns** and to **remind** which checklists govern a file you just edited. (Override the registry dir with `PATTERN_REGISTRY_DIR`; disable the hook with `PATTERN_GUARDS_OFF=1`.)

## Foundational principles

**Forward-state.** Pattern files describe how the code SHOULD be, not how it currently is. Newly authored code MUST follow the blessed patterns; existing non-conforming code is migrated later via background/cascade work. When a topic's reference is a greenfield scaffold (no pre-existing equivalent), say so in the body so readers don't hunt for a current-state implementation.

**Single source of truth.** Each topic file IS the canonical body for its pattern — full prose, full GOOD + BAD examples, full anti-patterns, edge cases. Reference files are SOFT examples; if one drifts from the body, the **reference file is wrong** — the body governs. Default toward fuller examples even if they duplicate the reference.

**File-first, doc-second.** Patterns are **never** written from imagination or a sketch. A topic body is the *distillation* of a working reference file — the rules + WHY + BAD-shapes + edge cases learned while building/refactoring real, compiling, wired code under human review. If the code doesn't exist yet, **the code is the first work.** Writing the pattern first produces a "complete" doc over an empty file that the next reader has to rebuild from scratch.

**Soft-reference.** Every blessed topic carries a `Reference:` line citing the canonical file(s). Always a SOFT pointer ("see `src/lib/cache/cache.service.ts` for the canonical shape"), never a contract — the file can be refactored/renamed/deleted as the codebase evolves; the body remains the SSOT. If the file is renamed, update the `Reference:` line; the body usually stays.

## Status legend + the gating rule

- **`blessed`** — reference shape exists and is human-confirmed; agents may pattern-match against it.
- **`decided`** — shape decided in chat; reference not yet shipped. Autonomous jobs MUST NOT apply it yet.
- **`TODO`** — not yet discussed. STOP and walk the pattern via this skill before any code in the area lands.

**The gate** (mechanized by `pattern-guards`): before code in a governed area, its pattern must be `blessed`. A path governed only by `decided`/`TODO` patterns is hard-blocked at edit time. If a `blessed` pattern also governs the path, editing proceeds (there's a shape to follow) and the non-blessed overlap is surfaced as a STOP-warning to escalate to a human.

## Topic file structure

```markdown
---
topic: Service class + lazy binding      # exact human-readable title
section: server                          # your area prefix (see Filename conventions)
status: blessed                          # blessed | decided | TODO
paths:                                   # governance globs — which files this pattern governs
  - "src/lib/**/*.service.ts"
  - "src/services/*.ts"
route: edit                              # edit (remind at edit-time) | land (codebase-wide; review at land)
last-updated: 2026-07-13
---

### Service class + lazy binding

Status: `blessed`
Reference: `src/lib/cache/cache.service.ts` (soft — the body governs)
Wiring: `src/services/cache.ts`

#### Rules — write-time checklist

Every line is one diff-checkable imperative — the write-time contract an agent consumes in seconds
and a compliance pass diff-checks against. 5–12 lines (a short body still gets 2–4).

- [one-line imperatives distilled from GOOD/BAD/Anti-patterns]

[rule prose — the pattern, the WHY, the variants]

#### GOOD
[canonical form — concrete enough to copy-paste-adapt]

#### BAD
[wrong forms, each block captioned with the one-line why]

#### Anti-patterns
- Specific mistake — one-line WHY it's wrong.

#### Edge cases / notes
- Caveats, when-it-doesn't-apply, and `Pairs with [Other Topic](./other.md)` cross-links.
```

The five `####` sub-sections appear in that exact order. The checklist heading is the **exact greppable string** `#### Rules — write-time checklist` — the hook and the `pattern-verifier`/`pattern-compliance` agents key on it; don't vary it. Every **blessed** topic also carries a `## Discovery` section (scope · how to detect the pattern in code · confidence) so autonomous scans can find instances.

## Frontmatter shape

- `topic` — exact human-readable title.
- `section` — your area prefix (see below).
- `status` — `blessed` | `decided` | `TODO`.
- `paths` — governance globs (which files the pattern governs); **required for `blessed`**, omit on TODO skeletons. Factual (derived from the pattern's scope), not routing policy.
- `route` — `edit` (default; remind at edit-time) or `land` (the pattern's globs are effectively codebase-wide, so a per-edit reminder would fire everywhere — review it at land-time via `pattern-compliance` instead).
- `last-updated` — ISO date.

`paths` + `route` are what `generate-pattern-routes.py` compiles into the routes table; `Pairs with` cross-links live in the Edge-cases body, not frontmatter (one source of truth for the pairing graph).

## Filename conventions

```
{section-prefix}-{kebab-topic-name}.md
```

**Section prefix** — a short tag derived from your project's top-level layout (e.g. `server-`, `api-`, `web-`, `shared-`, `worker-`), plus **`universal-`** for cross-cutting patterns that apply across areas (a pattern's *scope* drives the prefix, not where its reference file happens to live). Pick a small, consistent prefix set for your repo and index each section in the README.

**Kebab rules:** lowercase alphanumeric + dashes; drop everything after the first em-dash (commentary) or opening paren (clarifier); drop backticks; replace `+`/`/`/`:`/`,` with dashes; collapse repeats; strip ends. E.g. `### Service class + lazy binding` → `server-service-class-lazy-binding.md`.

## The routes table + enforcement

`generate-pattern-routes.py` reads every pattern's `paths:`/`route:`/`status:` frontmatter and writes `.agent/patterns/pattern-routes.tsv` (one row per glob). The `pattern-guards` hook reads that table on every Write/Edit. You rarely run the generator by hand: the hook **auto-regenerates the TSV** whenever you write a registry `*.md`, and reminds you to **commit the regenerated TSV in the same commit as the pattern change**. If you edit patterns outside the Write/Edit tools (bash, sed), the simplest manual regen is to touch any registry file **via the Write/Edit tools** (append/remove a trailing newline) so the hook's auto-regen fires. Alternatively run the generator directly — `$CLAUDE_PLUGIN_ROOT` is not reliably an exported shell variable in Bash tool sessions, so locate the plugin's `hooks/` dir first (e.g. from the hook's own output/config, or the plugin cache under `~/.claude/plugins/`) and run its `generate-pattern-routes.py` with `python3`.

## Self-questions before blessing a topic

Apply in order; if you can't answer all, keep status at `TODO`/`decided` — don't bless prematurely.

1. **What does "good" look like?** One paragraph in your head first.
2. **Is there a file already doing it well?** Yes → bless it as the reference. No → build it FIRST as a real working example; no placeholder reference files.
3. **What does this depend on?** Other blessed patterns, libs, conventions — record as `Pairs with` bullets.
4. **What's the anti-pattern?** 2–3 specific things a verifier should flag, each with a one-line WHY.
5. **What edge cases?** Concurrency, idempotency, empty input, shutdown, retry — whatever applies.
6. **Per-area or universal?** If universal, use the `universal-` prefix.
7. **Smallest viable reference?** Trim to canonical shape; comments explain WHY-not-HOW.
8. **Can every rule be a one-line, diff-checkable imperative?** Those become the checklist. A rule you can't state in one line is usually two rules — or not yet decided.

## Adding a new topic — the phased workflow

**Don't hurry.** Five phases, each with a pause point where you check in with the human. Skipping phases produces empty templates nobody can use.

| # | Phase | What happens | Pause? |
|---|---|---|---|
| 1 | **Brainstorm** | Discuss the shape in chat. No code, no doc. Walk the self-questions. | YES |
| 2 | **Plan** | Identify the reference file(s) to build/refactor + what cascades. Use the `plan` skill for big walks. | YES |
| 3 | **Build the code** | Build/refactor the reference file(s) — real, compiling, wired. No placeholder bodies. | YES |
| 4 | **Human review of the code** | Human reads + iterates until they sign off. The pattern is derived from CONFIRMED code. | YES |
| 5 | **Write the pattern** | NOW author the topic file — distilling rules from the just-blessed reference. | YES |

**Phase 1 (Brainstorm)** is the conversation — don't open files or pre-empt. Red flags that mean it isn't done: multiple undecided approaches; the human said "let me think"; a dependency is itself `TODO`/`decided` (walk that first); a fuzzy "what does this depend on". Stay in phase 1 until resolved.

**Phase 3 (Build)** the file must compile and be wired; TODOs allowed only for genuine downstream gaps, never for the shape itself. If building surfaces a shape problem, return to phase 1/2 — don't paper over it.

**Phase 4 (Review)** is the phase you're most tempted to skip ("the code compiles, let me write the pattern"). Don't — the reference file is the pattern's foundation; if it's wrong, the pattern is wrong. Iterate until the human signs off.

**Phase 5 (Write)** author the topic file per § Topic file structure: frontmatter → `### Topic` → Status/Reference/Wiring lines → write the `#### Rules — write-time checklist` LAST (after GOOD/BAD/anti-patterns exist) → README entry. Present the draft; the human signs off. Then commit (with the auto-regenerated routes TSV), and if the new pattern implies a codebase-wide cascade, track it for background/cascade work (the flow plugin's `looper`/`grind`) in the project's todo — the cascade is NOT part of this walk.

## Modifying an existing topic

Same human-in-the-loop discipline. **Substantive changes** (status flip to `blessed`, body rewrite, new real-code anti-pattern) walk the full 5-phase flow — reference file first (1–4), then body (5). A flip to `blessed` specifically requires a real, working, human-confirmed reference. **Minor edits** (typo, broken link, an added `Pairs with` cross-link) are a single exchange + edit — still bump `last-updated` and get review. Always read the topic file in full first; preserve structure; flip `decided → blessed` only after phase-4 review of the reference code.

## Legacy sentinel

When a file is legacy / not-yet-compliant, add a top-of-file sentinel so readers + autonomous jobs skip it as a blessed example and don't extend the old shape:

```ts
/**
 * LEGACY — does not yet comply with <path-to-topic-file>. Needs refactor before further changes.
 */
```

## Splits / merges

**Split** an over-long or multi-concern topic: decide boundaries → create new file(s) → move body chunks verbatim → cross-link via `Pairs with` → update README. **Merge** duplicates: pick the survivor → fold in unique content → delete the redundant file → update README → `grep -r` fix cross-references. Log either in the milestone/plan record.

## When tempted to shortcut

The phases exist because shortcutting produces bad output: writing from an architecture doc (empty reference files) → phase 3 fixes it; skipping the brainstorm (missed anti-patterns) → phase 1; "it compiles, I'll write the pattern" (skips review) → phase 4. If a session feels rushed, **stop and ask which phase we're in** — better to realign than ship a pattern that has to be re-walked.

## Out of scope for this skill

- The project's architecture docs (patterns reference them; they live separately).
- The actual coding-style / conventions guide (patterns are per-topic shapes; a style guide is standing rules).
- Per-feature plans (`.agent/plan/`) — they reference patterns but aren't patterns.
