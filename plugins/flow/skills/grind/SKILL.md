---
name: grind
description: |
  Prepare a grind mission file and hand off to the flow grind runner (bin/grind). Grind runs the SAME mission N times — each iteration a fresh Claude session that picks 1–3 new items per the mission's picking rules, commits them, and appends to a log. Use grind for large incremental backlogs the user can't enumerate upfront: "add tests across the app", "implement missing features", "sweep style violations", "backfill docstrings". Triggers: "/grind", "prepare a grind", "grind through X", "incrementally implement X". Do NOT use for one-off tasks (do it directly) or enumerable multi-step plans (use looper).
---

# Grind — preparing grind missions

Grind is for **long incremental work the human can't enumerate upfront** and each iteration discovers. One mission file (`.agent/grind/<topic>.md`) runs N times via the shipped runner (`bin/grind`); the model picks what to do each run and remembers via a log.

You do **not** run the grind yourself — the runner refuses to launch inside a Claude session. Prepare the mission file and hand off the command.

## When to use grind vs looper vs direct work

| Situation | Use |
| --- | --- |
| Single focused task done in this session | direct |
| N distinct pre-defined jobs, each different | looper |
| "Keep chipping away at X" — items unknown, same mission shape | grind |
| Mission where "done" is observable (tests pass, no TODOs) | grind |
| Rewrite with hard ordering dependencies | looper |

Grind's unique traits: one mission file, many iterations (no enumeration); the model scans and picks each run; cross-iteration memory via a log file (the only state between fresh sessions); a mission-level stop signal (`status:`).

## Mission file format

Filename: `.agent/grind/YYMMDD_HHMMSS_{topic}.md` — 6+6 datetime prefix from `date '+%y%m%d_%H%M%S'`. The topic slug is short kebab-case (`web-tests`, `docstrings`, `style-sweep`).

```markdown
---
status: active             # active | done | paused — runner only runs `active`
title: Human-readable mission title
model: opus                # default opus; sonnet ONLY for fully mechanical missions
max-turns: 40              # advisory (see note) — a forcing function on per-iteration scope
effort: xhigh              # xhigh or max
scope-hint: 1-3 items      # how much to pick per iteration; runner passes it into each prompt
max-iterations: 40         # mission-level cap; the runner clamps anything over 500
done-check: ""             # optional shell command; exit 0 = mission complete → runner stops
---

## Mission

One paragraph: what are we grinding through, and what does success look like at the end?

## How to pick work each iteration

The core of the mission. MUST include:
- "Read the log first" — it's the model's memory.
- How to find candidates (grep/glob/read a file/run a command — be concrete).
- How to rank them (simple-first, high-impact-first…).
- When to stop picking (hit scope-hint, scope balloons…).

## Rules per iteration

Invariants: commit-per-item, the log-block format, scope discipline, when to flip `status: done`.

## References

Paths to docs, example files, patterns to follow.

## Out of scope

Explicit negative list — what this mission must NOT touch. Keeps every iteration honest.
```

> **`max-turns` is advisory** — the current Claude CLI has no `--max-turns` flag, so the runner can't hard-cap turns. Keep it as a scope forcing-function: if iterations balloon, tighten `scope-hint` and the picking rules.

The Mission and "How to pick" sections are where your effort goes. Bad picking rules make every iteration a coin flip; good ones make grind feel like the model has intent.

## Writing good picking rules — the core skill

**Do:**
- Make "read the log first" step 1 — nothing else matters if the model redoes yesterday's work.
- Be concrete about finding candidates — shell commands (`grep`, `rg`, `glob`) or file-level instructions.
- Rank items — prefer simple/high-impact/well-scoped first, else it picks randomly.
- Cap scope — 1–3 items, not "as many as fit".
- Give a deferred-bucket escape hatch — "if an item needs heavy setup (mocks, new helpers), defer it with a reason in the log".

**Don't:**
- Pre-enumerate items ("do Foo, Bar, Baz") — that's looper.
- Write step-by-step procedures — the model is a senior engineer.
- Forget the out-of-scope list — without it, scope creeps across dozens of sessions.
- Rely on git log for memory — the log file is the memory.

## How iterations communicate — the log is everything

Each iteration appends a structured block to the mission's memory log (`.agent/grind/{stem}.log`, same stem as the mission), e.g.:

```
## iter 5 — 2026-07-13 21:15
done: src/foo/Bar.test.ts; src/foo/Bar.ts (bug fix: handles empty array)
scanned: src/settings/ (all already covered); src/wizard/Step1.tsx
deferred: src/control/ScoringPanel.tsx — heavy store mocking; revisit after helpers land
notes: vi.mock pattern from src/page.test.ts works for simple components
```

The next iteration reads all prior blocks, then **skips** anything under `done` / fully-`scanned` dirs, **may pick up** `deferred` items whose blocker is resolved, and **applies** `notes`. Without the log, every iteration starts blind. (The runner keeps its own transcript in `.agent/grind/{stem}.run.log`, separate from this memory log.)

## Commit tagging

The runner exports `GRIND_ITERATION` and `GRIND_TOPIC` to each session. Every commit inside iteration N should end with `(grind: {topic} #{N})`. Later: `git log --grep "grind: {topic}"` shows the full mission trail. Write this rule into the mission's Rules section.

## Lifecycle and stop conditions

`status:` is authoritative and re-read between iterations (edit mid-run → next iteration respects it):

- `active` — runner processes iterations.
- `done` — runner stops; won't launch again until `--reset` or you re-activate.
- `paused` — same as done for the runner; a semantic "will resume" signal.

Three paths to `done`: the model flips it (no candidates left — trusted path), the runner flips it (`done-check` passed, or `max-iterations`/hard-cap 500 reached — fallback), or the user flips it. Ctrl+C aborts without touching status; the next launch resumes from the saved iteration counter (`--reset` restarts from zero).

## Handing off to the user

Resolve the shipped runner's absolute path and hand the user a command for a **separate terminal**:

```bash
echo "$CLAUDE_PLUGIN_ROOT/bin/grind"   # resolve <abs>
```

```
<abs>/bin/grind .agent/grind/{mission}.md            # run until done or max-iterations
<abs>/bin/grind .agent/grind/{mission}.md --once      # exactly one iteration
<abs>/bin/grind .agent/grind/{mission}.md --dry-run    # preview, run nothing
<abs>/bin/grind .agent/grind/{mission}.md --status     # progress + iteration count
<abs>/bin/grind .agent/grind/{mission}.md --reset      # restart from iteration zero
<abs>/bin/grind .agent/grind/{mission}.md -y           # skip the arm-confirmation
```

**Pre-flight the mission's tools** (its find-candidate commands, build/test) before handing off — a bad command makes every iteration thrash. The runner writes `.agent/grind/.gitignore` on first run: committed = the mission `.md`, its `.log` memory, and `runner_*.log`; ignored = `*.iter`, `*.attempt`, `*.jsonl`, `*.run.log`.

### Permissions

Jobs run with full tool permissions (`--dangerously-skip-permissions`) so the unattended loop can edit + commit; the runner requires an explicit arm ("yes" or `-y`). Say so plainly.

### First run — smoke-test it before trusting real work

Prove the loop once on a throwaway mission before pointing grind at a real backlog. In a scratch repo/branch, write a tiny bounded mission and run it `--once`:

```markdown
.agent/grind/000000_000000_smoke.md
---
status: active
title: Smoke test
max-iterations: 2
---
## Mission
Append one line "iter <N>" to `SMOKE.txt` and commit it.
## How to pick work each iteration
Read the log first. Add exactly one line, then log what you did.
## Out of scope
Anything other than SMOKE.txt.
```

From a **separate terminal**: `"$CLAUDE_PLUGIN_ROOT/bin/grind" .agent/grind/000000_000000_smoke.md --once`. **Confirm:** `SMOKE.txt` grew by a line, a commit landed tagged `(grind: smoke #1)`, the memory log `.agent/grind/000000_000000_smoke.log` has an iteration block, and the iteration counter advanced (`--status`). Then let it run unbounded to see it stop at `max-iterations`. `--dry-run`/`--status`/`--reset` never call the model. If sessions hang on permission prompts or it refuses as "nested", see the same notes as the `looper` skill (check `bin/grind --help`, `FLOW_CLAUDE_PERMISSION_MODE`, separate terminal).

## Quality defaults

**opus (4.8) + `xhigh`/`max` by default.** Sonnet only for fully mechanical missions (find-replace sweeps), still at `xhigh`/`max` — each iteration picks its own work, which takes judgment. Never declare a mission done off cached test passes; cold-rebuild first.

## Troubleshooting

- **Iterations do nothing useful** — picking rules too vague; add concrete find-candidate commands.
- **Iterations touch the same thing** — the log isn't being read/written; tighten the log-block format in Rules.
- **Iterations balloon past scope** — `scope-hint` too big; drop to "1-2 items", prefer simpler candidates.
- **Mission never flips to done** — add a `done-check`, or tighten "how to pick" so the model can confidently say "nothing left".

## What NOT to do

- **Never start the runner yourself.** Prepare the file, print the command, stop.
- **Don't pre-enumerate items** — if you're listing specific files, you want looper.
- **Don't skip the out-of-scope section** — it's what keeps the mission focused across dozens of sessions.
- **Don't write a mission that needs chat context** — each iteration reads only the project's CLAUDE.md + the mission + the log.
