---
name: collab
description: |
  Long collaborative sessions where the human drives architectural decisions and the AI executes via looper. Use when the user wants to review and improve a codebase across multiple topics, says "let's go through the code", "I want to address things", "long session", "keep context clean", or signals an iterative review-and-fix workflow — or mentions looper / background execution / "work while I sleep".
---

# Collaborative architecture sessions

How to run long, productive sessions where the human drives decisions and the AI executes via the loop system (see the `looper` skill).

## Core principle

**Chat is for decisions. Looper is for execution.**

The main conversation context is precious — reserve it for discussion, alignment, and decision-making. Heavy implementation (reading many files, writing code, refactoring) goes to `.agent/loop/` jobs that run in the background. This keeps the main session lean, which is the #1 factor in session longevity.

## Session flow

### 1. Human raises a topic

They describe something they noticed or want changed — often a brief observation.

### 2. AI researches via subagent

Never read large files in the main chat — dispatch a read-only agent and get back a summary. Use `Explore` for codebase research; if the project (or an installed plugin) offers specialized agents, use them — e.g. the opsi `review` plugin's `semantic-reviewer` (lifecycle/error/cleanup review), `spec-cross-checker` (one feature's docs↔code drift), or `wireframe-vs-code` (UI vs spec). A code-architect style agent is good for design exploration.

### 3. Present findings concisely

Summarize what exists, what's wrong, and the options. Short — the human needs the diagnosis and the trade-offs, not every file path.

### 4. Discuss and align

Where decisions happen. Don't rush to implementation. Present trade-offs honestly — if the human says "fight me", give real counterarguments. Use a scratch location (e.g. `.scratches/`) for design iteration (v1 → v2 → v3). Use `.agent/plan/` files (the `plan` skill) for anything that touches multiple systems, before any loop jobs.

### 5. Create loop jobs

Once aligned, write loop jobs per the `looper` skill:

- **Outcome-focused prompts** — WHY and WHAT, not HOW. No code snippets; the executing model figures out implementation.
- **Reference the plan/scratches** if a design was iterated there.
- **Create as `draft`, flip to `pending` in one batch**, then commit — a `--watch` loop picks up new pending jobs automatically.

### 5a. Jobs with unresolved questions stay `draft`

If a job needs a decision the human hasn't made, do NOT flip it to `pending`. Leave it `draft` and:

1. List the blocking questions at the top of the job under `## Open questions (blocking)`.
2. Surface them to the human — in chat, and (if the project keeps one) mirrored into a `.todo-inbox` section named for the batch so they can answer inline. If `.todo` is guarded read-only, ask the user to arm the session first.
3. Tell the human: "parked N questions — answer them and I'll flip the jobs to pending."
4. Do NOT guess and execute. A job that runs, hits the blocker, and reports back with a question list is a failure mode to prevent upstream — not a feature.

Only flip `draft → pending` once every blocking question is answered and the job prompt is updated to fold in the decisions (remove the Open-questions block).

### 6. Move to the next topic

Don't wait for jobs to finish — the looper handles execution. Keep discussing. Check progress at natural pauses.

### 7. Check results between topics

Read the latest `.agent/loop/runner_*.log` (session overview) and per-job `.agent/loop/{stem}.log`; check job statuses and the `## Report` of done jobs. Create follow-up jobs for issues found — a natural triage cycle.

## What makes it work

- **Subagents for research** — never bloat the main chat with file contents; summarize back.
- **Scratches for design, plans for architecture** — decisions live in files, not just chat.
- **Don't agree too fast** — real counterarguments; progressive alignment (discuss → refine → confirm → execute), never hear → execute. The human drives architecture; the AI researches and proposes.
- **Update project docs immediately** — when a decision lands, write it into the project's own docs/conventions (and `.agent/handoff.md` for continuity). Project rules go in project files, never in account-level memory — that won't carry across machines or collaborators. "Use this everywhere" = update the convention doc AND queue a job to fix existing violations.
- **Quality execution** — opus + `xhigh`/`max` for loop jobs; outcome-focused prompts; order jobs by dependency; end a cross-cutting batch with a verification job (see the `looper` skill).
- **One commit per loop job** — keeps the tree clean for the next job.

## Running the looper

The looper runs in a **separate terminal** — you never launch it (nested Claude sessions are blocked, and the runner refuses anyway). Resolve its path and hand the user the command:

```bash
echo "$CLAUDE_PLUGIN_ROOT/bin/loop"   # → <abs>
# then, in a separate terminal:
<abs>/bin/loop --watch -y
```

Monitor via the log files and job statuses; create follow-up jobs directly — a watching loop picks them up.

## Anti-patterns

- ❌ Reading large files in the main chat (use a subagent)
- ❌ Writing implementation code in the main chat (use looper)
- ❌ Creating loop jobs before aligning with the human
- ❌ Prescriptive job prompts with code snippets
- ❌ Waiting for the looper to finish before discussing the next topic
- ❌ Forgetting to update project docs after decisions
- ❌ Agreeing with everything without pushback
