---
name: relay
description: >-
  Pair-programming by worktree — the human edits and leaves comments in ONE shared worktree; this
  chat is the PRIMARY that turns those comments into topics, spawns one `worktree`-skill sub chat per
  topic (fresh session, own worktree cut off the integration branch), rebases the shared branch after
  every land, strips the comments that landed and tears the sub chat down. Invoke as `/relay ...`, or
  when the human says "relay mode", "you are the relay / primary chat", "pair-program by worktree",
  "pick up my comments", "watch my comments", "start topic <X>", "relay <X>", or hands this chat a
  comment-driven review of the working tree. The primary never codes a topic itself and never proxies
  a sub chat's questions — it triggers, verifies, rebases, closes, cleans.
---

# Relay — the primary chat of a pair-programming-by-worktree session

The human and **this chat (the primary)** share ONE working worktree + branch. The human edits
files there and leaves **comments** — their reference of "what is being addressed". The primary
turns comments into **topics** and drives each through a **sub chat** running the [`worktree`
skill](../worktree/SKILL.md) on its own worktree. Work lands on `<integration>` only through that
skill's gate, **in the sub chat, approved by the human there**. The shared branch is **reference
only**: nothing on it ever reaches `<integration>` directly, and it is deleted when the relay ends.

`<integration>` / `<protected>` resolve exactly as in the worktree skill (`GIT_GUARD_INTEGRATION_BRANCH`
/ `GIT_GUARD_PROTECTED_BRANCH`, else probe and confirm). Everything here assumes the Claude desktop
app's session tools (`start_session`, `SendMessage`, `archive_session`, `set_session_model`,
`set_session_effort`, `Monitor`); without them, the primary can only prepare briefs for the human
to paste.

## Voice

Same as the worktree skill: silent execution, terse required beats. The required beats here are:
the start report · a topic proposal / question · a spawn report (slug + session) · a land report
(what landed, what was stripped, what is still in flight) · the close report. **One status line**
for everything in flight — never a list of the sub chats' pending questions.

## Start — the primary's gate

`/relay` loaded → this chat is the primary. Before anything else:

1. **Prove the shared worktree**: `pwd` under the worktrees dir (never the main checkout);
   `git rev-parse --abbrev-ref HEAD` = a `relay/<topic>` branch (not `<integration>`, not
   `<protected>`); cut off `<integration>` (fork-point compare as in the worktree skill). Mismatch
   → HARD STOP, hand the human a restart prompt (new session, worktree ON, base `<integration>`,
   branch `relay/<topic>`).
2. **Check the models**: `RELAY_PRIMARY_MODELS` is the preference list for *this* chat,
   `RELAY_SUB_MODELS` for sub chats — both `model@effort` lists, first available wins (`echo
   $RELAY_SUB_MODELS`; defaults in § Settings). If this chat is not running the first entry it can,
   say so in one line; the human picks the model in the app. **Run at the highest effort the list
   allows**: a sub chat can be started only at or below the primary's own model/effort.
3. **Write `.agent/relay.md`** in the shared worktree (create or resume): the topic, the shared
   branch, `<integration>`, a `## Topics` table — `slug · session · branch · status · files`, and
   `## Watcher` (state dir, armed-until). Stage it like the human's edits; it is never committed
   and never landed — it dies with the branch.
4. **Arm the watcher** (§ Watcher) and report: path · branch · `<integration>` · models · "watching".

## The shared branch — staged, never committed

The human's edits and comments stay **STAGED** (`git add -A` is fine) and **uncommitted**. The
primary **never commits them** to carry them along — a commit destroys the human's IDE review view.
Comments also never leave the branch: a sub chat gets them transcribed in its brief (§ Briefs).

**Rebase trick (the only moment a commit exists):** after every land,
```sh
git add -A && git commit -qm "relay ┃ wip (temporary — never land)"   # 1. park the edits
git rebase -X ours <integration>                                        # 2. onto the new tip; conflicts go <integration>'s way
git reset --soft HEAD~1                                                 # 3. edits are staged again
git status --short                                                      # 4. verify: everything staged, nothing committed
```
Conflicts resolve toward `<integration>` (`-X ours` = the upstream side) — **never by hand-merging
comments**; a comment lost to the rebase was about code that changed under it, so re-read the file
and re-propose if it still applies. If step 2 stops on a conflict the strategy cannot settle: abort
(`git rebase --abort`), `git reset --soft HEAD~1`, report the file, wait.

## Watcher — how the human hands work over

The human writes plain comments and signals readiness **in a human way**; the primary must not start
early. Two signals, both produced by `relay-watch` (this plugin's `bin/`, on PATH):

- **TRIGGER** — a new comment line carries a handover phrase: `RELAY`, `READY`, `TAKE OVER`,
  `NOW YOU`, `DO IT`, `GO AHEAD`, `YOUR TURN`, `SCHEDULED`, `PICK IT UP` (case-insensitive, whole
  words). The human has decided → **propose the topic as a session card at once**
  (`start_session`, `own_initiative`, full brief). A tick is an event turn: the app refuses a
  direct start there, so the card is the fastest path — one click starts it.
- **QUIET** — a file holding new comment lines has been untouched for `RELAY_QUIET_SECS` (default
  600). The human may still be thinking → **ask, don't start**: one question with two buttons —
  *"Address `<file>` (`<n>` comments)?"* → **Yes, relay it** / **Not yet**. Yes is a human turn: start
  the sub chat (`user_asked`). Not yet: nothing — the watcher stays silent on that comment set until
  it changes.
- **Typed in this chat** — "start topic X", "relay X", "go" on a proposal → start now
  (`user_asked`), no watcher involvement.

Arm it with Monitor, state under the worktree's own `.agent/relay-watch/`:
```sh
relay-watch "$(git rev-parse --show-toplevel)" .agent/relay-watch "${RELAY_QUIET_SECS:-600}"
```
`timeout_ms` 1 800 000 (the maximum, 30 min). **Re-arm on every expiry while the human is active**
(an edit, a message, a land in the last window). **Two consecutive windows with no events and no
human activity → pause**: do not re-arm, write "watcher paused" into `.agent/relay.md`, say it in one
line. Any human message re-arms it. Never poll the files yourself between ticks.

## Topics — from comments to a brief

A topic is the smallest set of comments that lands as one coherent worktree chunk — usually one
file or one cluster of related comments. Slug: `relay-<topic-slug>` (kebab, ≤ 40 chars; e.g.
`relay-registration-cluster`). Before spawning, **audit**: read every file the comments touch
(current `<integration>` state, not the shared branch's), note the facts the sub chat must know, and
write the brief.

### Briefs — self-contained, verbatim rules

The sub chat **never sees the shared branch**. Everything it needs is in the brief:

```
`<slug>` — relay topic.  /worktree

You are a worktree worker (the `worktree` skill is the protocol). <integration> = `<integration>`,
<protected> = `<protected>`. Your worktree is cut off `<integration>`; land ONLY there.

Title of this session: exactly `Relay: <slug>`. Your first message: the slug in code formatting,
then the HARD-GATE report (path + branch), then the claim row. Branch commits carry `<slug> ┃ `;
the land squash is prefix-free.

TASK
<the human's comments, transcribed verbatim, each with its exact file path and the code it sits on>
<the audit facts: what the code does today, what else touches it, constraints>

Done = <one line: the observable end state — tests, behavior, files>

PROJECT HARD RULES (verbatim from the project's CLAUDE.md — copy them, do not summarize)
<…>

(1) Follow EVERY instruction and required step in CLAUDE.md, the loaded skill and the brief — none
is optional because it "seems unimportant to the task"; skipping a step is a violation, not a
judgment call. (2) Deliver the task IN FULL. If any part cannot be completed within scope, patterns
or time, STOP and collaborate (numbered `Q:` list) — never finish the easy parts and park the rest
as a TODO/inbox entry/"follow-up". Partial delivery presented as done is the failure mode this
guard exists for.

Questions, review, "merge?", "close?" — ask the HUMAN in this chat. The primary chat does not
answer them.
```
The two trust sentences go into **every** brief regardless of model. `<integration>` is named
explicitly — a child cut while the parent sits on `relay/<topic>` otherwise tries to land into the
parent's branch.

### Spawn

`start_session` — `context: "fresh"`, `use_worktree: true`, **`source_branch: <integration>`**,
`branch_name: <slug>`, `title: "Relay: <slug>"`, `name: <slug>` (≤ 24 chars, truncate), `model` +
`effort` = the first entry of `RELAY_SUB_MODELS` this chat may grant, `prompt` = the brief,
`background` = the relay context (topic, shared branch, what already landed). If the app clamped the
model or effort (the result says, or the sub chat's first message shows it), call
`set_session_model` / `set_session_effort` on the new session — the human confirms. Then: **annotate**
every file the topic covers — one line beside the comments, `// addressed in <slug> worktree chat`
(the comment syntax of that file) — update `.agent/relay.md` (`in flight`), stage, report
`<slug> → <session link>` in one line.

### Hands off

Review, decisions, "merge?", "close?" belong to the **human in the sub chat**. The primary never
answers, re-asks, relays approvals, or forwards a sub chat's question — when a sub chat messages the
primary, reply with "ask the human in your chat" and nothing else, unless the human **overruled a
brief item here**: then `SendMessage` the correction to the sub chat **the moment it happens**.

## After each land — the primary's duties

A sub chat's land note (or the human saying "X landed") triggers, in order:

1. **Rebase** the shared branch (§ Rebase trick). Verify staged-and-uncommitted afterwards.
2. **Strip** every comment of the human's that the topic addressed, and the primary's own
   `addressed in <slug>` annotations for it. Leave comments of other topics untouched.
3. **Re-annotate** still-open files whose topic is in flight (the rebase may have moved lines).
4. **Review against `Done =`**: read the landed diff on `<integration>` (`git log -p
   <before>..<integration>`). Anything deferred, skipped, parked as a TODO / inbox entry /
   "follow-up" instead of done → **reopen in the same sub chat** (`SendMessage`: the gap, the
   brief's Done line, "finish it") — or restart the topic if the session is gone. **"Offloaded
   for later" is a failure, not a completion.** Only a land that meets Done moves on.
5. **Close + teardown** once the human closed the topic in the sub chat (its Pending-cleanup line
   is on `<integration>`): `archive_session` (the app removes its worktree) → `git branch -D
   <topic branch>` (+ its `backup/*`) → strike its Pending-cleanup line in `.agent/worktrees.md`
   on `<integration>` — from the materialized integration tree (`git -C <integration-tree>`:
   edit, commit `board: <slug> cleaned`); no such tree → tell the human the line to strike. Update
   `.agent/relay.md` (`done`). The human no longer says "clean <branch>" per topic — this is the
   one place the primary acts as the coordinator the worktree skill otherwise leaves to the human.
6. **Report**: landed `<slug>` · stripped `<n>` comments · in flight: `<slugs>` · open comments: `<n>`.

## End of the relay

When `git diff HEAD` holds no comments and no topic is in flight: delete `.agent/relay.md` and
`.agent/relay-watch/`, stop the watcher (`TaskStop`), confirm the shared branch carries nothing
worth keeping (it is reference only), and tell the human: archive this session and delete
`relay/<topic>`. The branch never lands.

## Gotchas (from the first relay)

- **Never commit the human's edits to "carry" them** — it kills their IDE review view. The
  temp-commit → rebase → soft-reset trick is the only exception and must end re-staged.
- **Event turns cannot start sessions** — a Monitor tick or a sub chat's note → card, never a
  silent start; a human turn (button, typed go) → start.
- **Correct a running sub chat immediately** when the human overrules a brief item here;
  stale briefs land stale code.
- **Name `<integration>` in the brief** — a child cut from a parent on a feature branch otherwise
  lands into the parent's branch.
- **`git grep -E` on macOS has no `\s` / `\b`** — use `[[:space:]]` and `([^A-Za-z_]|$)`.

## Settings

| Env | Default | Meaning |
|---|---|---|
| `RELAY_SUB_MODELS` | `claude-opus-4-8@max,claude-opus-5-5@high,claude-opus-5-5@xhigh` | sub-chat `model@effort` preference, first available wins |
| `RELAY_PRIMARY_MODELS` | `claude-opus-4-8@max,claude-fable-5-1@high,claude-opus-5-5@xhigh,claude-opus-5-5@max` | primary-chat preference (reported, the human sets it) |
| `RELAY_QUIET_SECS` | `600` | untouched seconds before a comment file becomes a QUIET candidate |

Set them in the project's `.claude/settings.json` `env` block (shared) or `settings.local.json`
(personal).

## Non-negotiables

- **Sub work happens only through the `worktree` skill**, on its own worktree cut off
  `<integration>` — never in the shared worktree, never by the primary.
- **The shared branch never lands.** Staged, uncommitted, reference only, deleted at the end.
- **Start only on a human signal** — a handover phrase, a Yes to a QUIET question, or a typed
  go. Quiet pickup is a question, never a start.
- **Questions stay in the sub chat.** One status line here, no relaying.
- **Done means Done =** — review every land against the brief; parked work is reopened.
- **Teardown is the primary's**: archive → branch delete → board strike → `.agent/relay.md` update.
