# Orchestrator playbook — running an umbrella milestone

The one **parent chat** that owns an umbrella milestone, and how it operates. Workers never
read this file; they read the milestone's `README.md` § Notes for agents and their own group
in [`ledger.md`](ledger.md). The orchestrator writes exactly two things — the `README.md`
(prose: tracker, Log, Blocked, the open-decisions list) and `ledger.md` (tags) — and only
through its **own worktree + fast-forward land**: a dirty integration checkout refuses every
worker's push. Format and vocab for everything below live in [`ledger.md`](ledger.md); the
`README.md` scaffold in [`readme-template.md`](readme-template.md); who lands how (gate,
FF-only, land-report mechanics) in the `worktree:topic` skill + `.agent/worktrees.md`. Umbrella
milestones only — a single-chat milestone keeps `steps.md` and needs none of this.

## Opening a session (or a phase)

1. `ledger check` green, then `ledger ready` — the candidates. Pick by the critical path, not
   list order: `ledger why <gate-record>` prints the chain of unlanded `needs:` still blocking
   a gate record. A setup/bootstrap record that must land before any group opens runs first,
   alone.
2. Open a group: flip its header to `[status:active] [chat:<slug>]`, add the chat's row to the
   `worktree` board (`.agent/worktrees.md`), start the chat with the worker brief below (a
   fresh session, its own worktree cut off the integration branch), and tell it the integration
   sha.
3. One chat per group at a time; sub-groups are their own groups, one chat each. A record that
   needs a human architectural decision runs as its own child chat with the user in the loop,
   never inside a worker.

## Worker brief (the session-start text)

```
milestone: <slug> · group: <GROUP> · records (in order): <ledger list <GROUP>>
Worktree <path>, branch <feature/slug>. The integration branch is at <sha>.
Read ONLY: README.md § Decisions + § Notes for agents, ledger.md § <GROUP>, the worktree board
§ <GROUP>, and what each record's spec: cites. Nothing else unless I point you.
Rules: your group's records only, in order; anything outside the group is a REQUEST or a
BLOCKED report, never a side edit; every record's verify: runs before its land report and its
result goes on the Verify: line; report only in the fixed shapes — REVIEW / BLOCKED / REQUEST /
PAUSE and the land report (ledger.md § Reports). You never edit ledger.md or README.md. Pause
with a handoff in your plan file when context runs high.
```

## Every land (the loop)

1. **Read the land report.** `Record:` names an `active` record of that chat's group; `Verify:`
   shows the record's own `verify:` as run, with the result; `Deferred:` lists new ids or
   `none`; plus whatever land-report lines the project adds on top of the ledger minimum.
   Anything missing → back to the worker, no OK.
2. **Gate.** The project's land gate green on the rebased HEAD, and any pattern / isolation
   review the group demands clean (or a deferral agreed with the user) → OK; the worker lands
   fast-forward.
3. **Ledger.** The record → `[status:landed] [sha:<short>]`; every record whose `needs` are now
   all landed → `ready`; each `Deferred:` item → a new record (`ledger next <PREFIX>`, with a
   `verify:`) in a group or the parked backlog; the project's todo inbox folded into records;
   `ledger check` green.
4. **README.** One Log line per land (sha, record ids, what moved); tracker prose only when a
   group's state changed; Blocked / open-decisions list if the land raised one.
5. **Relay** to every active chat: `RELAY <integration>→<sha> [landed:<ids>] [ready:<ids>]
   touched: <shared files>` — workers rebase before their next land.
6. **Land the ledger.** Commit `ledger.md` + `README.md` in the orchestrator's own worktree,
   `ledger check` green, fast-forward into the integration branch. The ledger is never edited in
   the integration checkout.

## Requests and blockers (same day)

- `REQUEST [from:<id>] [to:<GROUP>] [needs:<id|new>] [impact:continue|wait|blocked] <what>` → a
  `[req:R<n>]` in `ledger.md` § Requests (`status:open`). `needs:new` → a new record in the
  `to` group with a `verify:`; the requester gains the edge in its `needs`; the provider moves
  up or gets `[prio:now]`, and the request flips `[status:filed]` — tell the provider. Provider
  lands → `[status:done]`, tell the requester; strike done requests at the next relay (the Log
  keeps them).
- `BLOCKED [id:<id>] [by:<what>] [impact:…]`: `by:walk:<pattern>` → an architecture/decision
  child chat, the record `[status:blocked] [by:walk:…]`; a project decision id → the user's
  open-decisions list (ONE list, in the README); `by:<id>` → make sure that id is `ready` /
  `active` somewhere, else open its group. The worker takes its next independent record or
  pauses.
- Nothing is parked in a chat, in a TODO without an id, or as "later".

## Phase boundaries

- A phase opens only once its entry records have landed; a serialization window (a record
  nothing else may land beside) runs alone, then a `RELAY` and every chat rebases.
- At each boundary: `ledger why` on every gate record, rewrite the README tracker prose, re-cut
  the critical path.

## The orchestrator's own context

- Its memory is the `README.md` (Log, Decisions, open-decisions list), `ledger.md` and the
  worktree board — nothing lives in the chat. When context runs high: refresh
  `.agent/handoff.md` (integration sha, active groups + their chats, open requests, pending
  decisions), commit + land, then a fresh orchestrator chat continues from `ledger active` /
  `open` / `blocked`. Children keep reporting through their land reports; the new chat re-reads
  the linked-sessions list and is the parent from then on.
- The user gets ONE numbered open-decisions list; a ruling becomes a dated line in README §
  Decisions and the record(s) it unblocks flip the same day.

## Complete

`ledger open` prints nothing and `ledger check` exits 0 — every record landed / dropped /
post-v1, every request done, every gate record's `verify:` ran at its land. Then the milestone
closes per the `planning:milestone` skill (README status `closed`, archive on the user's OK).
