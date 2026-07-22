# commit — the opsi house commit style

Part of the [`optimiziramsi-skills`](../README.md) plugin (the opsi toolkit).

An **opinionated** commit convention: bare imperative single-line messages, topic-close +
pause-for-review cadence, and stage-by-name discipline. Split out from the `git` plugin on purpose —
commit style is personal, so this is a separate opt-in. Want the git *safety net* (block
push/pull/fetch, bulk adds, non-FF merges, protected-branch moves, discards) but keep your own
commit format? Enable [`git`](../git) and skip this.

## Contents

- name: `commit`
  kind: skill + command
  purpose:
    Commit **cadence** (one topic = one commit at topic close, then pause for the user's review;
    commit-as-you-go is an explicit opt-in), **format** (single line, imperative, no
    body/trailers), and safe **staging** (stage by name).

- name: `commit-format`
  kind: hook
  purpose:
    PreToolUse `Bash` — blocks a model `git commit` whose message isn't a bare single line:
    `Co-Authored-By`, a heredoc body, or multiple `-m`. Fails open; escape hatch
    `COMMIT_FORMAT_OFF=1`.

- name: `commit-nudge`
  kind: hook
  purpose:
    Stop — if the session wrote files and the tree is dirty, nudges once to close the topic with
    a commit (or say why not). One-shot per dirty state; escape hatch `STOP_NUDGE_OFF=1`. Opt-in
    `COMMIT_NUDGE_EXTRA_DIRS=../gitops,../infra` also flags dirty *sibling* trees the current repo
    can't see.

## The split

- **This plugin** owns the *commit message format + cadence* — the opinionated house style.
- **The [`git`](../git) plugin** owns *git safety* — blocking destructive/remote/history operations
  (push, pull, fetch, bulk adds, non-FF merges, `reset --hard`, `clean -f`, `--no-verify`, …),
  regardless of commit style.

They're complementary but independent. The `commit` skill describes the safety rules too (as
guidance), but enabling `git` is what enforces them.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "optimiziramsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "optimiziramsi-skills@optimiziramsi": true }
}
```

Then `/commit`, or just let it commit at each topic close and pause for your review.
