# code-first — the idea is a branch diff you review

The `code-first@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

The working style is opt-in per session: it starts when you run `/idea`, or for one prompt when
you ask for a proposal (see [When the contract applies](#when-the-contract-applies)). A design or
architecture session that never does either is left alone.

In a code-first turn, the proposal IS code. Claude brainstorms as `IDEA:` commits on an
`idea/<topic>` branch cut from the integration branch (never the protected one), and you read it
in your IDE as a code review — not chat prose, not inline snippets, not the chat diff view. Chat
carries only the branch name, the key decisions, and open questions with a recommendation on each.
Rough or maybe-wrong is fine: a diff gets a reaction faster than prose. It is still a brainstorm,
so nothing lands without the project's normal gate.

Cadence: (1) the idea is committed on `idea/<topic>`; (2) you review the diff and endorse or push
back; (3) on endorse, `/idea promote` replays it as real commits on a topic branch, which go
through the normal gate.

## Contents

- name: `idea`
  kind: skill + command
  purpose:
    `/idea <topic>` cuts `idea/<topic>` off the resolved base and commits the idea; `/idea list`
    shows open idea branches with their age; `/idea promote` replays an endorsed idea onto a real
    topic branch (cherry-pick per commit, tag dropped — no merge commit, no interactive rebase);
    `/idea drop <topic>` deletes the branch locally after confirming. Every command passes
    [`git-guard`](../git-guard) as shipped and [`commit`](../commit)'s single-line format. Also
    auto-triggers on technical proposals ("sketch this", "how would you do X").

- name: `inject`
  kind: hook
  purpose:
    UserPromptSubmit — injects the code-first contract (≤ 10 lines) when the turn is code-first:
    the session ran `/idea`, or the prompt asks for a proposal. Any other prompt gets nothing.
    Only the code-first part: the output contract itself is [`reporting`](../reporting)'s, so the
    two compose.

- name: `idea-guard`
  kind: hook
  purpose:
    Stop — acts only in a code-first turn (same test as `inject`; silent otherwise). Blocks once
    (`stop_hook_active`-guarded) when the final message's fenced code exceeds
    `CODE_FIRST_MAX_FENCE_LINES` non-empty lines, summed over fences, and asks for a rewrite:
    commit it to an idea branch, chat only the branch name + questions. Fails open.

- name: `stale-ideas`
  kind: hook
  purpose:
    Stop — one line for you (not for the model) naming `idea/*` branches older than
    `CODE_FIRST_STALE_DAYS`, so ideas don't rot. Shown once per session, never blocks. Silent
    when there are none, and in a linked git worktree unless `NUDGES_IN_WORKTREE=1`.

- name: `bin/code-first`
  kind: cli
  purpose:
    `code-first base | list | prefix | tag` — the deterministic half of `/idea` (on PATH while
    the plugin is enabled), so the skill and the hooks resolve the same branch, prefix and tag.

## When the contract applies

- **The session opted in.** A prompt that invokes the idea command — `/idea …` or
  `/code-first:idea …` — turns code-first on for the rest of that session.
- **One prompt asks for a proposal.** A prompt matching `CODE_FIRST_TRIGGER_PATTERN` (default:
  the words propose, proposal, sketch) gets the contract for that prompt only. "Brainstorm",
  "how would you" and "what if we" are left out of the default on purpose: they are design talk.
- **`CODE_FIRST_INJECT=always`** applies it to every prompt.

In any other turn the plugin injects nothing and its Stop guard stays silent.

## The contract text — where it is read from

First hit wins, relative to the project root:

1. `$CODE_FIRST_CONTRACT_FILE`
2. `.agent/code-first.md` (repos on the `.agent/` layout)
3. `.claude/code-first.md` (generic repos)
4. the shipped [`hooks/code-first-reminder.txt`](hooks/code-first-reminder.txt)

`{{BASE}}`, `{{PREFIX}}`, `{{SURFACE}}` and `{{TAG}}` are substituted from the settings below, so most
repos only set env and never write an override file. An override that exists but can't be read —
or a `CODE_FIRST_CONTRACT_FILE` that doesn't exist — prints "⚠️ code-first DISARMED", never a
silent skip.

## Settings

All in a settings.json `env` block (project `.claude/settings.json` to share, `.claude/settings.local.json`
or `~/.claude/settings.json` for yourself), read from the hook's own process env like `git-guard`.

- `CODE_FIRST_BASE_BRANCH` — the branch ideas are cut from. Unset → `GIT_GUARD_INTEGRATION_BRANCH`,
  then the repo's detected default branch (the same detection `git-guard` uses — shared code, not a
  fork). A *derived* base that is a `GIT_GUARD_PROTECTED_BRANCH` entry is refused and `/idea` stops
  to ask; an *explicit* `CODE_FIRST_BASE_BRANCH` is trusted as given.
- `CODE_FIRST_BRANCH_PREFIX` — default `idea/`.
- `CODE_FIRST_COMMIT_TAG` — default `IDEA`; idea commits read `IDEA: <summary>`. That is one line,
  so `commit-format` passes it. The `commit` skill's "no workflow prefix" rule is about landed
  history, and the tag never lands: `/idea promote` drops it.
- `CODE_FIRST_REVIEW_SURFACE` — wording only (`my IDE`, `the GitLab MR`), templated into the text.
- `CODE_FIRST_MAX_FENCE_LINES` — Stop-guard limit, default `5`; `0` = no counted fence at all.
- `CODE_FIRST_EXEMPT_LANGS` — fence languages the guard doesn't count, default
  `bash,sh,zsh,shell,console` (commands for you to run).
- `CODE_FIRST_ALLOW_PATTERN` — regex on your last prompt that lifts the guard for that turn,
  default `\b(prompt|paste|inline|snippet|command)s?\b`.
- `CODE_FIRST_TRIGGER_PATTERN` — regex (case-insensitive) on your prompt that applies the contract
  to that one prompt, default `\b(propose|proposal|sketch)\b`. A bad regex falls back to the default.
- `CODE_FIRST_INJECT` — `always` applies the contract to every prompt; unset = opt-in as above.
- `CODE_FIRST_STALE_DAYS` — stale-idea note threshold, default `7`; empty = no note.
- `NUDGES_IN_WORKTREE` — `1` shows the stale-idea note in a linked git worktree too (off there by
  default).
- `CODE_FIRST_CONTRACT_FILE` — explicit contract override (see above).

## Escape hatches

- `CODE_FIRST_OFF=1` — everything: injection, Stop guard, stale-idea note.
- `CODE_FIRST_GUARD_OFF=1` — keep the injected reminder, drop only the Stop enforcement.
- A turn where you need inline text: say so ("paste-ready prompt", "inline snippet") and the
  allow-pattern lifts the guard for that turn.

## Decisions

- **Fence-guard exemption: both.** A prompt allow-pattern covers what you explicitly asked for
  inline (a prompt to paste, a config snippet); a language allowlist covers shell commands, which
  the house style puts in `bash` fences for you to run. Neither alone was enough: a language list
  can't tell "here's the 60-line module" in `text` from a requested paste.
- **`/idea promote` hands off to the gate, it doesn't run it.** Gates are per project (`qa-gate`
  where enabled, CI, a manual check); promote ends by naming it, and lands nothing.
- **Its own plugin, not a `reporting` sub-mode.** It depends on git conventions (branches, base
  resolution, the commit tag) that `reporting` doesn't — and a project may want either alone.
  `reporting`'s Stop guard still exempts fences from its shape checks; limiting them is this
  plugin's job.

## Enable

```bash
claude plugin install code-first@optimiziramsi --scope project
```

A typical project's settings: `{"env": {"CODE_FIRST_BASE_BRANCH": "develop", "CODE_FIRST_REVIEW_SURFACE": "my IDE"}}`.
