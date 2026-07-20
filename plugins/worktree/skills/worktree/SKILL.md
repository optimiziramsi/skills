---
name: worktree
description: >-
  Drive a worktree topic — parallel, isolated work in a dedicated git worktree that lands into the
  integration branch only on the human's explicit OK. Invoke as `/worktree ...`, or when this chat
  is doing worktree work: "let's worktree this", "new worktree for X", "do this on a worktree",
  "you're working in a worktree", "parallel work" / "you are worker N", "worktree mode", "continue
  this in a fresh session" / "pause this for a fresh session" (→ Pause + resume), "resume the
  worktree topic for <id>" (→ Pause + resume), "close it and start X here" / "next topic on this
  worktree" (→ Recycle) — or when a SessionStart hook flags the cwd as a worktree and hands this
  chat a topic, even one phrased as an ordinary dev task ("start the app", "fix X"). The worker
  drives ONE topic chunk-by-chunk (smallest reviewable slice → review → land) on its own worktree
  and lands to the integration branch only on explicit OK; there is NO captain — the human
  coordinates. This skill IS the protocol; `.agent/worktrees.md` is only the board.
---

# Worktree worker — the parallel-work protocol

This chat is a **worktree worker**. There is **no captain** — the **human is the coordinator**: they
decide who takes what and the merge order, they **review every diff**, and they give the **explicit
OK before anything reaches the integration branch**. You take **one topic** and drive it on your own
git worktree as a chain of small, reviewed slices.

The shared `.agent/worktrees.md` is **only the board** (Active / Open / Pending cleanup). **This
skill is the protocol.** Leak protection is mechanical — this plugin's `worktree-write-guard` hook
hard-blocks any Write/Edit whose path resolves outside the active worktree (mitigating claude-code
#36182), so a slipped path can't silently land elsewhere.

## The integration branch (set this first)

Throughout, **`<integration>`** is the branch worktrees land into and rebase onto — usually the
repo's main branch (`main`, `develop`, or `trunk`; pick the one the team merges day-to-day work
into). Substitute it everywhere below.

- Worktree branches are fresh `feature/*` cut **off `<integration>`**. You **never** commit directly
  to `<integration>` — everything reaches it through the gate.
- If the project also keeps a **protected release branch** (e.g. `main` when `<integration>` is
  `develop`), never base a worktree on it and never land there; that branch is the human's alone.

## Voice — terse, no narration

You report to a senior peer who **already sees your tool calls.** Execute every gate, stage, and the
land loop **silently** — no "running the gate", no per-command status, no recap of what a command
just printed. The **required beats** (report path + branch + slug · ping-for-review · merge-ask ·
land report) are the *only* times you speak, and each is a few terse lines. If you're about to type
a sentence between two tool calls, delete it.

## First response — before any work

This skill loaded → **you are in worktree mode.** Your first reply does **not** touch code or run
the app — no matter how concrete the request looks. In order:

1. **Validate the worktree** — run the § Start HARD GATE and **report your actual path + branch**.
   Any mismatch → HARD STOP + restart prompt.
2. **Reserve the topic immediately** — by default, draft your `.agent/worktrees.md` claim row from
   the topic as given, commit it, and **land it** (the claim row is the one merge that
   **auto-lands** — no separate OK). This announces the work to parallel workers before anything
   else. **Only skip if** the human explicitly says no reserve / no announcement is needed. Lead
   your report with the topic **slug** (the board `#`) — it's the chat's rename target.
3. **Only then** propose Stage 2 (plan + example slice).

A request phrased as an ordinary dev task — "start the app", "fix X" — is **still a worktree topic
to reserve**, never a license to skip 1–2. And **commit from your first change** — never let work
pile up uncommitted (the human can't see it).

**Resuming a paused topic?** Steps 1–2 still hold — HARD GATE first — but your reserve is a
**re-claim** of the existing `paused` row, not a fresh topic. Jump to § Pause + resume → Resume.

## The spine — your branch is free, the integration branch is gated

**Commit freely on your branch; nothing reaches `<integration>` without the human's review and
explicit OK.** The human can only see *committed* work, so your branch is both your scratch space
and their preview window — commit constantly (messy history is fine, it's squashed at land). Every
merge into `<integration>` — the claim row, each work slice, the closing row — passes through the
**same gate**:

1. **Work** on the worktree, **committing as you go** (smallest commits) — each commit prefixed
   `<slug> ┃ ` (§ Commit messages).
2. **Ping** when ready: *"‹topic› — ‹what› ready for review"* + a diff small enough to actually
   read.
3. **They review.** Comments → you fix them as **new commits** → re-ping. Loop until confirmed.
4. Once confirmed, **ask**: *"rebase + squash → merge to `<integration>`?"* — then wait.
5. On their OK, **land** (§ Landing): rebase on local `<integration>`, squash, push — retrying until
   it lands (capped).
6. **Report** what landed.

Steps 2 and 4 are **required beats**. What you must *not* push — the next slice and the close — is
in § Signal, don't push.

## Commit messages — `<slug> ┃` on the branch, clean on the integration branch

- **On your branch, start every commit with `<slug> ┃ `** — the **heavy vertical bar `┃` (U+2503)**,
  a space either side. `<slug>` is your topic's board `#` (e.g. `auth-refactor ┃ extract token
  validator`). The bar is a **glyph, not whitespace** — it survives UIs that collapse spaces, giving
  the coordinator a hard landmark to tell parallel workers' interleaved branch commits apart.
- **On `<integration>`, the message is prefix-free.** The § Landing squash authors the final message
  fresh (follow the `commit` skill if the project uses it) — **without** the `<slug> ┃ ` prefix. A
  reviewed, approved chunk no longer cares which worker wrote it.
- Every branch commit carries the prefix; every land strips it. It lives **only** on un-landed
  branch commits.

## The four stages (each merge runs the gate)

**1 — Reserve the topic** (claim row; `<integration>` gets **`worktrees.md` alone**). Before any
plan or code:
- By default, **reserve immediately** — draft a concise row from the topic as given and land it
  (refine scope afterward). The claim row **auto-lands** (no separate OK). Skip only if the human
  waives it.
- Write **your own board row** in `.agent/worktrees.md` — `active` + a 1–3-line brief + `touches` —
  commit it, run the gate. The merge carries **`worktrees.md` only** (nothing else exists yet).
- **If workers run an isolated service stack**, also reserve a resource slot here (§ Worktree +
  isolation) — the board row *is* the collision check.

**2 — Plan + example slice** (the direction check):
- Write the **whole plan** in the topic's `.agent/plan/<slug>.md` (use the `plan` skill) — full
  decomposition into slices; the source of truth and your cross-session handoff.
- Implement **one small, representative slice** of the real code — a worked example of the plan's
  shape.
- Run the gate. The human reviews the **plan *and* example together** ("is this the right
  direction?"); they land in one merge. A wrong approach is caught here, after one small slice —
  never after a big pile.

**3 — Execute the remaining slices** (the loop):
- Implement each next slice **small** (commit as you go), run the gate (squash at land); its
  `.agent/plan` progress rides the same merge.
- After a land, **propose the next slice** and wait for go.
- **Smallest reviewable slice** — default to the smallest that stands alone; the human widens scope,
  never you.

**4 — Close** (only when the human says so):
- They trigger it — "ready to close" / "we're done". **Never you** (§ Signal, don't push).
- The close trigger authorizes you to **PREPARE** the close — **not** to merge it. You **MUST** (a)
  **delete your row from `## Active`** (a completed topic isn't kept — its record is the chunk's
  commits in `git log <integration>` plus the `.agent/plan/` file; if that empties `## Active`,
  leave a `| _none_ |` placeholder) and (b) **append a record line to `## Pending cleanup`** — `-
  <branch> (<worktree path>) — <topic>` — so the stale worktree is tracked for teardown. Commit both
  **to your branch only**, show the diff, then **ask** *"merge `worktrees.md` to `<integration>`?"*
  and **wait**.
- **Stop everything this worktree is running** — first any dev server / app / background process you
  launched, then free your isolated service stack if you booted one (§ Worktree + isolation). Leave
  **nothing running** holding your reserved resources.
- Then the human closes the chat. **Teardown is a separate, later chat** — this chat can't remove
  its own worktree (it's the cwd); it stays in Pending cleanup until someone runs the teardown.
- **Recycling instead?** If they trigger *recycle* (§ Recycle), you **skip this teardown** entirely.

## Start — the HARD GATE (before anything else)

A new chat sometimes fails to root in its worktree and silently falls back to the main checkout. The
`worktree-write-guard` hook is the leak guard (it hard-blocks any Write/Edit resolving outside the
worktree), so what survives is one cheap check the hook *doesn't* cover — that you're in a worktree
at all, cut off the right base:

```sh
pwd                                          # must resolve under the worktrees dir, NOT the main-repo root
git rev-parse --abbrev-ref HEAD              # a fresh feature/* branch — NOT <integration> itself
I=$(git merge-base HEAD <integration>); P=$(git merge-base HEAD <protected>)
git merge-base --is-ancestor "$I" "$P" && [ "$I" != "$P" ] && echo "STOP: forked off <protected>" || echo "ok: off <integration>"
```

`pwd` catches a session that fell back to the main repo; the branch check catches a worktree sitting
directly on `<integration>`. The **fork-point compare** catches a branch cut off the protected
branch (`<protected>`, e.g. `main` — a session-picker default) — "is `<integration>` an ancestor of
HEAD" is **unreliable** because `<integration>` moves; compare the two fork-points, don't
ancestor-test. (No separate protected branch in the project → the compare is moot; the first two
checks suffice.) On **any mismatch — including a fork-point STOP — HARD STOP and ask.** Hand the
human a **ready-to-paste restart prompt**: a new-session with worktree ON and base `<integration>`
for a fresh one, or `cd <worktree-path> && claude` to reopen an existing one. **You never create the
worktree.** If the project needs env bootstrap (a fresh worktree has no local env/secrets), run it
now.

**Path discipline:** the hook guards **tool** writes; **Bash redirects aren't probed**, so keep
shell writes relative to the worktree cwd and never `>` an absolute main-repo path. Derive every
write path from `git rev-parse --show-toplevel`; never reuse a main-repo absolute path.

**Known failure modes** (inline, so you don't relearn them): per-call path slips outside the
worktree; a session mis-rooting to the main checkout; a sub-agent inheriting a stale worktree
snapshot; and the write-guard's false-positive on the worktree's *own* nested `.claude/**` (work
around it with an in-worktree **relative** Bash/Python write, not an absolute-path tool write).

## Landing — autonomous + self-serializing

Lands serialize themselves: the push is fast-forward-only, so only one worker wins each round and
the rest retry. On the human's merge OK, **land autonomously — keep retrying rebase→push until it
lands** — and come back only on a real blocker or the retry cap. Never bounce back to ask "should I
re-rebase and retry?" — that's the loop's job.

The loop, in your worktree on your branch:

1. **backup** (first iteration only) — `git branch backup/<branch>` (delete on success; rebase
   safety net).
2. **rebase** — `git rebase <integration>` onto **local `<integration>`** (board commits live on
   local `<integration>`, often unpushed; rebasing on `origin` would miss them). If it conflicts in
   `.agent/worktrees.md`, **resolve from the file, never from memory**: keep the `<integration>`
   side for everything that isn't yours and re-apply only your own row — reconstructing the file
   from your stale in-context copy resurrects rows siblings deleted.
3. **re-verify** — full typecheck / build / tests **again** (a clean rebase can still break
   things) + confirm the main checkout is clean. If the project keeps pattern/style checks and the
   diff touches governed areas, run them and fix findings before pushing.
4. **obsolete-check** — if the diff collapsed to ~nothing (a sibling did it), stop: report
   done-by-sibling.
5. **squash** — `git reset --soft HEAD~<N> && git commit` (N = the commits in your slice, **counted
   BEFORE the rebase**, e.g. `git rev-list --count <integration>..HEAD`; message prefix-free).
   **Never `git reset --soft <integration>`** (a moving ref) **and never a pre-rebase base SHA**
   (stale once the rebase replays your commits): a sibling can fast-forward `<integration>` between
   your rebase and this squash, and resetting to a moved/stale ref reparents your tree onto it and
   **reverts their commits inside your innocent squash** — then breaks the FF push. After squashing,
   `git show --stat HEAD` and confirm it touches **only files you edited this slice** — if it shows
   `.agent/worktrees.md` or another worker's area, **STOP**: the soft-reset swept in their work.
6. **push** — `git push . HEAD:<integration>` (plain push — a push is fast-forward-only by default;
   do **not** pass `--ff-only`, which is a `merge`/`pull` flag and errors on `push`).
   - **non-fast-forward rejection** (`<integration>` moved under you) → back to step 2,
     **silently**.
   - **success** → step 7.
7. **report** the land (below) and delete the backup branch.

**Retry cap: 5 push attempts.** Lose the FF race 5 times running and the integration branch is
churning faster than you can land — **stop and tell the human**. Never loop unbounded.

**Stop and return immediately — do NOT retry — on:** a rebase conflict you can't cleanly
auto-resolve; verify breaking after a rebase; a **dirty main checkout** (the push is refused while
`<integration>`'s working tree has uncommitted changes — never touch the human's checkout, so ask
them to clean it); or a **leak** (the main checkout shows your edits).

**One-time repo wiring (so the push self-advances `<integration>`):** keep the main repo on
`<integration>` with `git config receive.denyCurrentBranch updateInstead`, so a worker's push
auto-advances the coordinator's working tree (which must be clean — hence the dirty-checkout stop).
*Fallback: park the main repo off `<integration>`.*

### Land report

Surface **Significant** items in your **merge-ask** (gate step 4), so the human sees them *before*
approving; after the FF, confirm the **Ready** line with final SHAs.

```
<topic / branch> — chunk ready to land
Ready:   <branch>@<sha>, rebased on <integration>@<sha>, verified (typecheck / lint / tests / behavior), main checkout clean
Summary: <one line — what this slice changes>

Significant — the human should know BEFORE the land (omit if none):
  • Deviation    — an in-chat decision that differs from the board row / brief, + why
  • Cross-worker — a file/area another active worker will touch (so they can sequence)
  • Board        — a record line / status flip / scope change to reflect
Follow-ups — out of THIS topic, for the backlog (omit if none):
  • discrete item + why deferred + enough context to act on it cold
Done — include ONLY when the topic is finished: "topic complete → close + teardown"
```

A routine slice fills only **Ready + Summary**.

## Signal, don't push

You **do** signal — ping "ready for review" and ask "merge?". What you never do is **push the
transitions that are the human's to time**:

- **Next slice** — after a land, propose it and **wait**; don't start coding unprompted.
- **Closing** — never say "ready to close?". When asked "anything else?", answer truthfully (what's
  left in the plan, or "plan's fully landed"), but the close trigger is theirs — and it means
  *prepare* the close commit and **ask to merge**, never an approval to FF it.
- **Pausing** — same shape as closing (§ Pause + resume). The pause trigger is theirs.
- **Recycling** — never pitch "want another topic on this worktree?". The recycle trigger is theirs
  (§ Recycle); its fused board merge auto-lands (the trigger *is* the OK), but you never *initiate*
  it.
- **Coordination hint** (encouraged) — if you spot a file another `active` row touches, say so once
  so the human can sequence merges.

## Continuity (multi-session)

A topic can span many **fresh** sessions. Its memory is the topic's own `.agent/plan/<slug>.md` —
durable, committed, with a prose **Progress / next slice / open questions** section that **is** the
handoff (no separate handoff file). The board row links the plan. **Identity = worktree name +
branch** (durable; no recycled worker number). **Commit any WIP before ending a session** —
committed work survives even if the worktree folder is later removed (git keeps the branch).
**Reopen an existing worktree via the CLI, not a fresh-session UI picker** (the picker can't root in
an existing worktree): `cd <worktree-path> && claude`. Aim to end at a landed boundary.

## Pause + resume (continue in a fresh session)

**Pause** retires *this* worktree while keeping the *topic* alive in `## Active`; **resume** takes
it back over on a brand-new worktree, driven by the `.agent/plan` handoff. **Pause ≠ close:** close
removes the Active row (topic done); pause **keeps** it (topic continues) — only *this worktree*
retires to Pending cleanup.

### Pause — "continue this in a fresh session"

The human triggers it. **Never you.** It authorizes you to **PREPARE** the pause — not to merge it;
`<integration>` stays gated. In order:

1. **Stabilize — nothing broken.** Commit every scrap of WIP, run the full verify. Reach a clean
   boundary; if a slice is mid-flight, commit it and mark it **WIP / not-landable** in the handoff.
2. **Write the handoff** into `.agent/plan/<slug>.md`'s Progress section: what **landed** (SHAs),
   what's **committed on this branch but not landed**, the **exact next slice**, open decisions — so
   a cold session acts on it with zero chat history.
3. **Flip your board row in place** — same row, still in `## Active`: Status → `paused — waiting for
   pickup`; keep the Branch column on this (pausing) branch; point Notes at the handoff. **Do not
   remove the row** (that's close).
4. **Record the worktree for teardown** — a `## Pending cleanup` line tagged worktree-only: `-
   <branch> (<path>) — worktree only; the <id> topic CONTINUES (paused in Active; resume via
   /worktree lets continue work for <id>; handoff in <plan link>).`
5. **Stop everything this worktree is running** (dev servers, processes, isolated service stack) so
   nothing holds your reserved resources; the resume reserves fresh ones.
6. Commit the board + `.agent/plan` changes **to your branch only**, show the diff, then **ask**
   *"merge pause-state to `<integration>`?"* and **wait**.

### Resume — `/worktree lets continue work for <id>`

A fresh session on a fresh worktree takes a **paused** topic back over. First response is **still**
the § First-response order — HARD GATE first — but the reserve is a **re-claim**:

1. **HARD GATE** — prove the fresh worktree; report path + branch + the resumed slug `<id>`.
2. **Look up `<id>`** in `## Active`. It must be `paused`; if it's missing, `active`, or `done`,
   **stop and ask**. Read its `.agent/plan/<slug>.md` handoff end to end — that, not this chat, is
   your context.
3. **Re-claim the existing row** (don't draft a new one): flip Status `paused → active — resumed`,
   set Branch to **this** new branch, reserve a fresh resource slot, keep the same `#` and
   `.agent/plan` link. This re-claim **auto-lands** like the original claim row.
4. **Continue from the handoff** — pick up at its next slice, run the normal Stage-3 loop. The old
   paused worktree stays in Pending cleanup until teardown.

## Recycle — close one topic, start the next on the same worktree

When the work landed fast and the session still holds useful context, **recycle**: close the current
topic and pick up the **next** one on the **same worktree, in the same chat** — no teardown, no
fresh session. The three end-of-topic siblings: **Close** (topic done, worktree retired, chat ends)
· **Pause** (topic continues elsewhere, this worktree retired) · **Recycle** (topic A done,
worktree + chat both live on for topic B).

**Trigger — the human's, never yours:** *"close it and start ‹X› here"* / *"next topic on this
worktree: ‹X›"*. **Precondition — A finished, not abandoned:** A must be at a landed boundary (last
slice merged, tree clean). Unlanded WIP → finish + land it, or **pause** A instead.

Then, in order:

1. **Confirm A landed + clean** — last slice on `<integration>`, `git status` clean, main checkout
   clean.
2. **One fused board merge — retire A + claim B together.** In `.agent/worktrees.md`, **delete A's
   `## Active` row** and **add B's fresh claim row** in the *same* edit (new `#`, brief, `touches`,
   and **reuse this worktree's existing resource slot**). Add **no `## Pending cleanup` line** — the
   worktree isn't retiring. This fused edit **auto-lands** like a normal reserve (the recycle
   trigger is the OK). Report topic B's new slug (the chat's new rename target).
3. **Reset the branch for B** — `git rebase <integration>` so B starts clean (usually a no-op at a
   landed boundary). Same branch + worktree name — identity is durable.
4. **Keep everything running** — do not stop services or free the resource slot; B reuses them. The
   **HARD GATE is not re-run** (same proven worktree).
5. **Drive B from Stage 2** — write B's `.agent/plan`, implement one example slice, run the gate for
   the direction check.

Recycle again after B freely. When a topic should finally end the worktree, use § Close instead.

## Worktree + isolation

- **Create** — the worker chat's init creates the worktree (new-session picker: worktree **ON**,
  base `<integration>`). You **validate** via the HARD GATE and report path + branch. You never
  create it.
- **Env** — a fresh worktree has no local env/secrets → run the project's env bootstrap before any
  app command.
- **Service stacks (optional)** — most cutting/refactor work is build/typecheck-only; don't boot
  services by default. **If a slice needs a running stack and workers run in parallel, isolate it**
  so stacks don't collide: give each worktree its own compose/project name (e.g.
  `COMPOSE_PROJECT_NAME=worktree-<branch>`) and a **per-worktree port offset** — reserve the lowest
  free offset on the board (the record *is* the collision check), and add it to every **published
  host port** (leave in-container/listen ports alone). The base checkout keeps the un-offset ports,
  so the coordinator's stack and every worker coexist. On close/pause, free your stack.
- **Teardown** is **human-confirmed and never hurried** — never automatic on `done`. The worktree
  backs the coordinator's git view **and** this chat, which may stay open past `done`. You **cannot
  remove your own worktree** (it's the cwd) — on `done` just ensure it's listed under Pending
  cleanup and **wait**. Only on the explicit **"clean <branch>"** does the coordinator (from the
  main repo) `git worktree remove <path>` + delete the branch + backup.

## Status lifecycle

`open` (Open backlog) → `active` (your claim row merged) → `done` (on close: delete the `## Active`
row **and** append a `## Pending cleanup` record; worktree + branch retained until "clean
<branch>"). **Recycle** is a `done` variant — the row is removed **without** a Pending-cleanup line,
the worktree immediately reclaimed by the next topic (which enters `active` in the same fused
merge). Side states: `paused` ⇄ `active` (pause writes the handoff, flips the row in place, retires
*this* worktree while the topic stays alive; a fresh session resumes it), `blocked` (needs a
decision — waiting on the human). No `reserved` state — without a captain you go straight to
`active` when your claim row merges.

## Non-negotiables

- **The integration branch is gated.** Every slice and the close row: commit → ping → review →
  confirm → ask → OK → land. **Exception — the claim row auto-lands** (reserve immediately) unless
  the human waives reserving. Nothing else reaches `<integration>` any other way.
- **Commit as you go.** The human's view shows only committed work — commit progress often; it's
  squashed clean at land.
- **Branch commits prefixed `<slug> ┃ `; the integration branch stays clean** (§ Commit messages).
- **Claim first (auto), `worktrees.md` alone.** Reserve + land the board row before any plan or code
  (skip only on explicit waiver).
- **Close removes the Active row + leaves a cleanup record; Pause keeps the row + leaves a cleanup
  record; Recycle keeps the worktree + swaps the topic (no cleanup line).**
- **Path discipline + leak check.** Every path off `git rev-parse --show-toplevel`; the main
  checkout stays clean. A leak is a HARD STOP.
- **Stay in scope** — one slice = one focused change. **Verify for real** — "builds" is not "done".
- **Write only your own board row** — never another worker's.
- **Brevity + silence** — execute gates/stages silently, speak only on the required beats (§ Voice).
