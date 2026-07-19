# instructions — keep the agent instruction system alive

Part of the [`opsi`](../../README.md) marketplace.

The meta-system: capture what you learn, route it to the right store, and keep the instruction
system consistent over time — so you fix something once and every future session inherits it.

## Contents

| Kind | Name | Purpose |
|---|---|---|
| skill + command | `retro` | Session-end harvest — route learnings to lessons/rules/docs, merge-don't-append, compact at caps, **apply-safe / propose-risky**, changelog, commit. |
| skill + command | `lessons` | Capture + curate one durable lesson in `.agent/lessons/` — kebab-slug file, README index, two-axis surfacing (enforced-hook / routed-doc / indexed × High/Mid/Low caps), dedup, prune, fold-up. |
| skill + command | `instructions-audit` | De-rot sweep — broken pointers, dead/duplicate rules, truth-vs-reality drift, cap breaches, enforcement drift; safe fixes applied, risky ones proposed. |
| skill + command | `instructions-maintenance` | The **constitution** — design principles, ownership matrix, extension criteria, governance tiers, retention/caps. The model the other skills apply; load before editing any instruction file. |
| skill + command | `rules-change` | The sanctioned **T3-change door** — explicit approval, coherence + cap check, re-test enforcement, reality check, changelog. What retro/audit route approved changes through. |
| agent | `lesson-scout` | Prior-art lookup — searches `.agent/lessons/` before you re-debug something. Read-only. |
| agent | `instructions-auditor` | Read-only sweep of the instruction surface → severity-ranked findings with `file:line` evidence. Used by `instructions-audit`. |
| hook | `caps` | SessionStart — surface any instruction-surface **cap breaches** (file sizes + skill/agent/rule counts). Stop — after any session that wrote files, nudge once per distinct breach-set on ANY breach present (pre-existing included, not only what this session bloated). Makes the governance caps the skills *describe* mechanical. All caps env-overridable; fails open; escape hatch `CAPS_GUARD_OFF=1`; self-test `--test`. |
| hook | `file-guard` | PreToolUse — writes to **T3 enforcement surfaces** (`.claude/settings*.json`, `.claude/hooks/`) downgrade to an **ask**: a session must not silently rewrite its own guards. Extra prefixes via `FILE_GUARD_EXTRA` (colon-separated); escape hatch `FILE_GUARD_OFF=1`; self-test `--test`. |

The full knowledge system: **define** (`instructions-maintenance`) · **capture** (`lessons`) ·
**harvest** (`retro`) · **maintain** (`instructions-audit`) · **change** (`rules-change`).

## Model

- **House layout:** `.agent/lessons/` (durable knowledge) · `.claude/rules/` (binding rules) ·
  `.docs/` (architecture/recipes) · `.agent/handoff.md` (volatile next-session state) ·
  `.agent/instructions-changelog.md` (what changed, tier-tagged).
- **Governance:** *safe* changes (wording, broken pointers, dedup, compaction) apply directly;
  *risky* changes (add/remove rule, cap change, behavior change) are proposed for approval.
- **Mechanical checks:** the shipped `caps` hook enforces the size/count caps at session start + stop;
  run the project's linter for anything else, else spot-check inline.

## Enable

```json
{ "enabledPlugins": { "instructions@opsi": true } }
```

> **Note:** enabling this plugin activates the `caps` hook in every project that enables it. It's a
> no-op where the capped files don't exist, and every cap is env-overridable (`CAP_CLAUDE`,
> `CAP_HANDOFF`, `CAP_SKILL`, `MAX_SKILLS`, …). Set `CAPS_GUARD_OFF=1` to disable it entirely.

Defaults (chars unless noted): `CLAUDE.md`/`AGENTS.md` 6000 · `.agent/handoff.md` 4000 ·
`.agent/instructions-changelog.md` 8000 · per `SKILL.md` 9000 · per agent 4000 · per rule 2000 ·
per command 800 · per lesson 4000 · counts: ≤12 skills, ≤6 agents, ≤10 rules.
