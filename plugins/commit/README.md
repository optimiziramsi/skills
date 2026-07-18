# commit — the opsi house commit style

Part of the [`opsi`](../../README.md) marketplace.

An **opinionated** commit convention: bare imperative single-line messages, commit-as-you-go cadence,
and stage-by-name discipline. Split out from the `git` plugin on purpose — commit style is personal,
so this is a separate opt-in. Want the git *safety net* (block push/pull/amend/force/discard) but keep
your own commit format? Enable [`git`](../git) and skip this.

## Contents

| Kind | Name | Purpose |
|---|---|---|
| skill + command | `commit` | Commit **cadence** (auto by default, opt out with "don't commit"), **format** (single line, imperative, no body/trailers), and safe **staging** (stage by name). |
| hook | `commit-format` | PreToolUse `Bash` — blocks a model `git commit` whose message isn't a bare single line: `Co-Authored-By`, a heredoc body, or multiple `-m`. Fails open; escape hatch `COMMIT_FORMAT_OFF=1`. |
| hook | `commit-nudge` | Stop — if the session wrote files and the tree is dirty, nudges once to commit as you go (or say why not). One-shot per dirty state; escape hatch `STOP_NUDGE_OFF=1`. |

## The split

- **This plugin** owns the *commit message format + cadence* — the opinionated house style.
- **The [`git`](../git) plugin** owns *git safety* — blocking destructive/remote/history operations
  (push, pull, rebase, `reset --hard`, `clean -f`, `--no-verify`, …), regardless of commit style.

They're complementary but independent. The `commit` skill describes the safety rules too (as guidance),
but enabling `git` is what enforces them.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "opsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "commit@opsi": true }
}
```

Then `/commit`, or just let it commit as you work.
