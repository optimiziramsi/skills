# Milestone ledger — ids, status tags, groups, requests

**This is the canonical format** for how an *umbrella* milestone tracks its work. A milestone that
runs many chats in parallel under one orchestrator keeps ONE machine-scannable file,
`<milestone>/ledger.md`, in place of `steps.md`; every task is a record with inline bracket tags;
groups say what may run at the same time; requests carry a chat's "I need X from group Y" to the
orchestrator. Prose explains, tags decide. The `planning:milestone` skill owns create / switch /
close of the folder; this file owns what lives inside `ledger.md`, the report shapes that feed it,
and the `ledger` reader. No markdown tables anywhere; hard-wrap at 100.

Only the orchestrator writes `ledger.md`: workers report (§ Reports) and the orchestrator folds the
reports in. The milestone's `README.md` stays the human narrative (prose tracker, Log, Blocked); the
ledger is the machine view. Reach for an umbrella + ledger only when work genuinely fans out across
parallel chats — a single-chat milestone keeps `steps.md` and needs none of this.

## One record = one bullet + indented fields

```
- [id:API3] [group:API] [status:ready] [wsd:0.5] [needs:-] [owner:user]
  what: add the public tier-catalogue endpoint the pricing page reads
  verify: `curl -s localhost:3000/api/tiers | jq .tiers` returns the seeded tiers; `bun test tiers`
  spec: plan/pricing.md § API; backlog.md § TIER
```

- The **first line** carries only tags, in this order: `id`, `group`, `status`, `wsd`, `needs`, then
  optional `owner` / `chat` / `sha` / `by` / `prio`. Tools parse the first line; humans read the
  fields.
- **`id`** — stable, unique in the milestone, tag-safe (no spaces: `API3`, `WEB-T2`, `DES-4`). New
  ids = group prefix + next free number (`ledger next API` prints it). An id is never reused or
  renumbered; a struck record keeps its id with `[status:dropped]`.
- **`group`** — exactly one, declared as a group header in the same file (§ Groups).
- **`status`** — one of `pending` (nobody holds it), `ready` (every `needs` landed; the orchestrator
  flips it at each land relay), `active` (a chat holds it — `[chat:<slug>]` required), `blocked` (a
  chat holds it and cannot continue — `[by:<id|walk:<pattern>>]`, or the project's own decision id
  (e.g. `OD-n`), required), `landed` (`[sha:<short>]` required), `dropped`, `post-v1` (moved to the
  parked backlog). Nothing else.
- **`wsd`** — worker-session-days, one number or `-`.
- **`needs`** — comma-separated ids, or `group:<NAME>` (= every record of that group landed), or
  `-`. This is the only place a dependency lives; prose repeats it, never defines it.
- **Fields** (2-space indent, continuation lines 4-space): `what:` one sentence; `verify:` the done
  check — a backticked command or path, a probe URL + expected status, `review:` by whom, or `user:
  <who> approves, logged README § Log <date>`. **`verify:` is mandatory and must be runnable**:
  `ledger check` ERRORs on a `verify:` that carries no backticked command/path and no `review:` /
  `user:` / `README § Log` token, or that runs under 25 characters — a vague `verify: works` is not
  land-ready, and a smaller model confirms completion by running `verify:`, never by judging prose.
  `spec:` where the body lives (plan §, backlog record, design file). Optional `note:`.
- Order inside a group = priority. Moving a record up IS the re-prioritisation; `[prio:now]` marks a
  pre-emption the orchestrator granted on a request (strike it when the record lands).

## Groups — who may run in parallel

```
## API — [group:API] [status:active] [chat:api-1]
entry: API0 landed · exit: every GATE-A record landed · files: apps/api/src/**, services/tiers.ts
```

- A group header is a `##` heading carrying `[group:<NAME>]`, `[status:pending|active|paused|done]`
  and `[chat:<slug>|-]`; one prose line below names entry, exit and the files it owns. Sub-groups
  are their own groups (`BE-a` … `BE-i`), one chat each.
- **Every active group runs in parallel with every other active group.** A chat works ONLY records
  of its own group, in order; anything outside the group — a missing op, a shape, a bug elsewhere —
  is a request or a blocker report, never a side edit. The orchestrator opens and closes groups
  (`status`), one chat per group at a time.
- Serialisation is a record, not a convention: a window where nothing else may land is a record with
  `[prio:now]` and `needs:` on it from every group that must wait.

## Requests — "I need X from group Y"

```
## Requests
- [req:R3] [from:WEB2] [to:API] [needs:API15] [impact:continue] [status:open]
  what: pricing page needs a public tier-catalogue op; WEB2 continues on static copy meanwhile
```

- A worker that discovers a dependency outside its group files ONE request line in its report
  (§ Reports) — `from` = its record, `to` = the group that can provide it, `needs` = an existing id
  or `new`, `impact` = what happens to the requester: `continue` (keeps working, lands without it),
  `wait` (pauses at a landed boundary), `blocked` (cannot land anything until it arrives).
- The orchestrator answers the same day: `needs:new` becomes a record in the `to` group (`ledger
  next`), the requester's record gains the edge in its `needs`, the provider record may move up or
  get `[prio:now]`, the request flips `[status:filed]`; when the provider lands, `[status:done]` and
  the requester is told. Done requests are struck at the next land relay (the Log keeps them).
- `impact:blocked` with no independent record left → the requester's record flips `blocked` with
  `[by:<id>]` and the chat pauses (`worktree` skill § Pause + resume).

## Reports — the shapes that feed the ledger

Workers never edit `ledger.md`; they report in these one-line shapes and the orchestrator writes the
ledger. Each line starts with its verb so a scan finds it.

- **Land report** = the `worktree` skill's land-report shape (Ready / Summary / Significant /
  Follow-ups) plus, when the milestone has a ledger: `Record: [id:API3]`; `Verify:` the record's
  `verify:` line as run, with its result; `Design:` design file + tab ↔ the slice's screenshot
  (screen slices only); `Deferred:` `[id:<new>]…` or `none`. These ledger lines are the minimum, not
  the whole report — a project may add its own (e.g. `Tests:` / `Patterns:` from its board header).
  The orchestrator flips the record to `[status:landed] [sha:…]` from this report.
- `REVIEW [id:API3] <branch>@<sha> — ready for review`
- `BLOCKED [id:WEB6] [by:walk:ui-resolver-pattern] [impact:wait] <file:line evidence, options>`
- `REQUEST [from:WEB2] [to:API] [needs:new] [impact:continue] <what, why>`
- `PAUSE [id:WEB6] <handoff path>`
- Orchestrator relay to every active chat after a land: `RELAY <integration>→<sha>
  [landed:API1,API2] [ready:WEB6,WEB10] touched: <shared files>`
- Vocabulary is scoped to `ledger.md`: the worktree board (`.agent/worktrees.md`) keeps
  `open / active / paused / done`, loop jobs keep `job-status:`; a word means one thing per file
  class.

## Complete — the one definition

A milestone is complete when `ledger open` prints nothing (no record outside `landed` / `dropped` /
`post-v1`, no open request) and `ledger check` exits 0. The acceptance gate is itself a group of
records (e.g. `GATE-A*` deploy contract, `GATE-B*` acceptance), each with a `verify:` line, so
"done" is never a prose judgment: every `landed` record's `verify:` ran at its land and the land
report says so. Items only a human can approve carry `verify: user: … approves, logged README § Log
<date>` — the grep for that Log line is the check.

## `ledger` — the reader

On PATH inside a Claude Code session with the `planning` plugin enabled
(`…/cache/<plugin>/<version>/bin`), so a chat calls it bare; a headless runner started outside the
session is not on that PATH — call it by its path, or have the repo wrap it as `bin/ledger`. Pure
bash + awk, read-only. `ledger <cmd> [-m <milestone-dir>]`; without `-m` it takes the single
`.agent/milestone/*/ledger.md` under the repo.

- `list [GROUP]` — one line per record: id, status, group, wsd, needs.
- `ready` — `[status:ready]` records, plus `pending` records whose needs all landed (flagged
  `should-be-ready`).
- `open` — every record not landed / dropped / post-v1 and every open request. Empty = complete.
- `blocked` / `active` — the records in that status with their `by` / `chat`.
- `id <ID>` — the record block. `why <ID>` — the transitive chain of unlanded `needs:` as an
  indented tree (group refs as `group:X (n/m landed)`, `group:PREFIX*` globs, depth-capped): the
  critical path for one record. `next <PREFIX>` — next free id number.
- `check` — unique ids, vocab, declared groups, `needs` resolve, `ready` ⇔ needs landed, required
  tags per status, `verify:` present **and runnable** (§ One record), request vocab; exit 1 on any
  error. `--test` runs the embedded fixture.

## Where the rest lives

- Folder create / switch / close, `README.md` shape, the `.agent/milestones.md` index: the
  `planning:milestone` skill. For an umbrella milestone `ledger.md` replaces `steps.md`.
- Prose status in `README.md` (tracker, Log, Blocked): the `milestone` / `plan` skills' "prose, no
  checkboxes" rule — the ledger's `[status:…]` tags are the machine view, the README the narrative.
- Who lands how (gate, FF-only, land-report mechanics): the `worktree` skill + `.agent/worktrees.md`
  header; the land-report lines above are the extra ledger fields on that shape.
- Where a dropped finding goes when no milestone owns it: the project's todo inbox (e.g.
  `.todo-inbox`, when the `todo` plugin is enabled); the orchestrator folds it into records at each
  land relay.
