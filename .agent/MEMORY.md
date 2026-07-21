# Agent memory — opsi skills marketplace

Durable facts, decisions, and gotchas for this repo. **This repo's own working memory**, not the
account/plugin memory store. One dated section per fact; delete what turns out wrong; keep volatile
"now/next" in [handoff.md](./handoff.md).

Convention note: the source projects name this file `.agent/MEMORY.md` (singular) and **commit** it
(portable memory). This repo does the same — `.agent/` is tracked like an ordinary project (only
runner scratch, machine-local settings, and OS junk stay gitignored), so this durable memory travels
with the repo.

Precedence on conflict (source `rules/sessions.md`): the user's live word > repo docs > this file /
handoff > auto-injected session memory (claude-mem observations). Injected memory records the PAST and
may predate a pivot — when it contradicts a repo file, the repo file wins.

---

## Conventions re-grounded against source — verified 2026-07-13

Re-read the source projects (`gitlab.com/{optimiziramsi,opsi-infra}/*`) after the maintainer flagged
that a prior session reconstructed conventions from memory instead of re-reading them. Result:

- **Shipped plugins are faithful.** Every `MEMOR` reference in `plugins/` points at `.agent/MEMORY.md`
  or the "in-repo, never account memory" principle. `triage-todo` correctly treats `.todo` as
  user-owned / LLM-readonly with a gated allow-phrase. No propagated drift found.
- **Canonical durable-memory file = `.agent/MEMORY.md` (singular)** — confirmed in kupimkuham's file,
  its `.claude/README.md` layer map, and `rules/sessions.md`. The prior session's `.agent/MEMORIES.md`
  (plural) was an unverified guess; renamed to match.
- **Two valid source memory models:** kupimkuham = single dated `.agent/MEMORY.md` merged via `/retro`;
  rabbit-run = `.agent/lessons/` (one file per lesson, indexed). This repo's *shipped* `instructions`
  plugin ships the `lessons/` model; this repo's *own* memory uses the single-file model (2 facts).
- **`.todo` is user-owned in source** (kupimkuham: never edit → `FEEDBACK.md`; rabbit-run: gated
  "ALLOW TODO"). This repo's agent-maintained `.todo` with `(done)` markers is a deliberate local
  choice the user established (below), not drift.

## `.todo` format — no checkboxes, `(done)` prefix (2026-07-13, user)

Never use `[ ]`/`[x]`/`[~]` checkbox syntax for status, anywhere — empty brackets make noisy/ambiguous
git diffs and LLMs mangle them.

- **`.todo` (this repo):** plain `- ...` bullets only — no checkboxes, no group headings, no status
  tags. Done → prepend `(done)` (`- (done) ...`); leave in place and remove done items only once the
  user confirms cleanup. (This repo opts into an agent-maintained `.todo`; consumer projects keep
  `.todo` user-owned per the shipped skills.)
- **Other status** (plans, milestones, job files): prose ("Step 1 — done (commit abc)") or a `status:`
  field — never brackets. The opsi toolkit already complies.

## flow@opsi dogfooded HERE — .todo writes need arming (2026-07-18, user)

This checkout registers itself as a **directory marketplace** in `.claude/settings.local.json`
(gitignored; absolute path) with `flow@opsi` enabled — user's call. Consequence: the
`todo-readonly-guard` hook is live in this repo, so **updating `.todo` requires the user to arm the
session with "ALLOW TODO"** (or prefix bash with `TODO_GUARD_SKIP=1`); unarmed deferrals go to
`.todo-inbox`. The `(done)`-prefix format itself is unchanged.

**Gotcha found 2026-07-18 (session 5):** `extraKnownMarketplaces` + `enabledPlugins` in settings
alone did **not** install the plugin — the marketplace registered but `flow@opsi` never loaded (no
flow skills in-session; guard canary passed through). Fix: `claude plugin install --scope local
flow@opsi` (now shows enabled, scope local, in `claude plugin list`). Plugins load at session start
→ **verify on next boot**: flow skills visible and/or a `.todo`-write canary gets denied.

## Flow runner not yet live-tested (2026-07-13; USER-only, confirmed 2026-07-18)

`plugins/flow/bin/{loop,grind}` were built + tested with a FAKE `CLAUDE_BIN`, never against a real
`claude -p`. Session 5 attempt from inside a session (`FLOW_ALLOW_NESTED=1`) was **blocked by the
permission classifier** — spawning an unattended nested `claude -p` is not something the agent can
(or should) do. It must be run by the USER from a plain terminal; `--dry-run`/`--status`/queue
detection verified live and work. A scratch repo + smoke job can be prepared under the session
scratchpad (any empty git repo works; the smoke-job recipe is in the looper skill's "First run"
section).
Run: `cd <scratch> && python3 <repo>/plugins/flow/bin/loop --model sonnet` → type `yes`. Confirm:
SMOKE.txt says "ok", job-status flipped to done, ## Report filled, new commit in `git log`.
Remove this note once the live test passes.
