---
name: idea
description: >-
  Code-first brainstorming — the proposal IS code, committed on an `idea/<topic>` branch the user
  reviews as a diff in their IDE; chat carries only the branch name, key decisions and open
  questions. Use for any technical proposal ("how would you do X", "sketch this", "propose an
  approach", "brainstorm", "what if we"), and on /idea <topic> | list | promote | drop. Not for a
  prose plan the user explicitly asked for, or for paste-ready text they asked for inline.
---

# idea — the proposal is a branch diff

For anything technical, write the idea as code. The user reads it in their review surface as a
code review — not chat prose, not inline snippets, not the chat diff view. Rough, first-cut or
maybe-wrong is fine: a diff gets a reaction faster than prose. It is still a brainstorm, so
nothing lands without the project's normal gate.

**Cadence:** (1) write the idea as commits on the idea branch; chat holds only the branch name,
the key decisions, and the open questions with a recommendation on each. (2) The user reviews the
diff and endorses or pushes back — push-back means more idea commits, not a prose rebuttal.
(3) On endorse, `promote` turns it into real commits on a topic branch, which go through the
normal gate. No prose-only "here's the plan" turn unless the user asked for one.

Every value below comes from the `code-first` CLI on PATH (the plugin's `bin/`), so this skill and
the plugin's hooks agree. Every git command here passes `git-guard` as shipped (no push, no
non-FF merge, nothing onto the protected branch) and `commit`'s single-line format.

## `/idea <topic>` — start one

1. `code-first base` → the branch ideas are cut from. Exit 1 means no safe base (it resolved to a
   protected branch, or nothing resolved): **stop and ask** which branch to cut from; suggest
   setting `CODE_FIRST_BASE_BRANCH` in the project's settings `env`.
2. `git status --porcelain` — if the tree is dirty, stop and ask: commit, stash, or leave it.
   Never carry someone's uncommitted work onto an idea branch.
3. `git switch -c "$(code-first prefix)<topic>" <base>` — `<topic>` is short kebab-case.
4. Write the idea as code: real files where they would live, stubs and `TODO(idea):` markers are
   fine, tests if they make the shape clearer. Stage by name.
5. Commit, one per coherent piece: `git commit -m "$(code-first tag): <imperative summary>"` —
   one line, no body (the tag is how idea commits read at a glance; promote drops it).
6. Reply with: the branch name, a `git log --oneline <base>..` count, the 1–3 key decisions, and
   the open questions — each with your recommendation. No code in chat.

On push-back: switch back to the idea branch, add commits (don't rewrite history the user already
reviewed), reply the same way.

## `/idea list`

`code-first list` → branch, age in days, last subject, oldest first. Show it as-is; flag any older
than `CODE_FIRST_STALE_DAYS` (default 7) and ask whether to promote, drop, or keep each.

## `/idea promote [<topic>]` — the user endorsed it

Default `<topic>` is the current branch's suffix. Ask for the real topic branch name if the
project names branches differently (else use `<topic>`).

1. `base=$(code-first base)` (stop and ask on exit 1) and `git status --porcelain` clean.
2. `git switch -c <topic-branch> <base>`
3. Replay the idea commits oldest-first, dropping the tag — a rebase that rewords, with no merge
   commit and no interactive rebase:
   - `git rev-list --reverse <base>..<idea-branch>` → each `<sha>`:
   - `git cherry-pick --no-commit <sha>` then
     `git commit -m "<that commit's subject without the leading TAG:>"`.
   If the user wants it squashed instead, cherry-pick them all `--no-commit` and make one commit.
4. Show `git log --oneline <base>..` and hand off to the project's gate (e.g. `qa-gate` when that
   plugin is enabled) — promote does not run the gate itself, and does not land anything.
5. Offer `/idea drop <topic>` for the now-replayed idea branch; don't delete it unasked.

## `/idea drop <topic>`

Confirm first — it discards the branch's commits (they stay in the reflog only). Then
`git switch <base>` if it is the current branch, and `git branch -D "$(code-first prefix)<topic>"`.
Local only: a pushed copy is the user's to delete.

## Rules

- **Never commit ideas on the protected or integration branch**, and never land or push one.
- **Chat stays short**: branch name + decisions + questions. Inline code only when the user
  asked for paste-ready text (a prompt, a shell command to run, a config snippet) — the Stop
  guard lets that through when their prompt says so.
- **The idea branch is disposable.** Promote replays it; it never merges into anything.
