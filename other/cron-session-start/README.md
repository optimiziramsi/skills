# cron-session-start — pin your Claude usage window to a fixed daily grid

A small technique: fire a tiny scheduled **warmup** message so your Claude **5-hour usage
window** resets at clock times *you* choose, instead of wherever your first message of the
day happens to land. Keeps the dead time (when you're rate-limited) out of your focus hours.

"cron" loosely — on macOS you'll use **launchd**; on an always-on Linux box, real cron;
off-machine, CI.

> Not a plugin — just reusable know-how. Ships the *technique*, not any one machine's config.

## Why bother

Claude's limit is a **rolling 5-hour window**: it starts on your first message and resets 5h
later. Start work at a random time and your resets are at random times — hit the cap and you
wait for a reset that might be hours away, mid-task. Anchor the window on a schedule and the
resets land where they help (a fresh cap at the start of each work block) while the waits
fall when you're away.

It doesn't give you *more* budget — the cap is the cap — it **aligns the boundaries** so more
of your fresh-cap moments and fewer of your walls happen during the hours you actually work.

## How the window really works (3 rules)

1. A window **starts on your first message** and lasts exactly 5h.
2. A message starts a **new** window only if **no window is currently active** (the previous
   5h has elapsed). Sent inside an active window, it just adds usage — no new anchor.
3. Hit the cap and you're blocked until the **current** window resets.

## Two traps most "warmup cron" guides miss

**Trap 1 — a single morning warmup drifts.** By rule 2, one 09:00 ping sets the phase only
*if* you then stay continuously active. Step away when a window expires and your next message
re-anchors the phase to whenever you return. **Fix:** fire at *every* boundary, so each
re-anchors on schedule whether or not you're at the keyboard.

**Trap 2 — an API key doesn't touch your subscription window.** `ANTHROPIC_API_KEY` bills a
separate pay-per-use pool. Only a Claude Code **login** (interactive) or an **OAuth token**
(`claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN`) consumes — and therefore anchors — your
Pro/Max 5-hour window. Any headless/off-machine trigger must use the token.

## Designing the grid

Two facts shape it:

- **24h ÷ 5h isn't whole** — you can't tile a day with 5h windows on a fixed daily clock. One
  gap is always the odd one out. **Park that seam in your deadest hours** (asleep).
- **Windows drift slightly late.** The warmup call takes a moment (sometimes a minute or two)
  to land, so each 5h window ends a little *after* its nominal boundary. If the next trigger
  fires *exactly* at the boundary it can land *inside* the not-quite-closed window and fail to
  re-anchor. **Fire each re-anchor with a margin** — a **5h10m cadence** — so the previous
  window has definitely closed.

**Recipe:** pick the hour you want your first fresh cap (start of your day). Step forward by
**5h + ~10 min** three times; stop before your wake-up hour, leaving the long seam overnight.

Worked example (first cap ~08:50):

    08:50 ─5h10m─▶ 14:00 ─5h10m─▶ 19:10 ─5h10m─▶ 00:20      then a ~8h30m seam back to 08:50

Fresh 5h caps at ~08:50, 14:00, 19:10, 00:20. Aim to put a fresh cap just before each heavy
work block and let the wall fall in a lull.

*Trade-off of the margin:* each hop has a ~10-min gap with no active window; a message sent
*in* that gap re-anchors a few minutes off-grid — harmless, and the next day's fixed schedule
resets it. Firing early (no margin) is worse: it can miss the re-anchor entirely.

## See your own usage (to place the grid)

Point the grid at your data. This stdlib-only scan prints your token burn by hour and where
your 5h blocks currently start (local time) — put a fresh cap just before your heavy hours,
and the seam in your deadest ones:

```python
#!/usr/bin/env python3
import os, glob, json, time, datetime as dt
from collections import Counter
cut = time.time() - 45*86400                       # last 45 days
burn, ep = Counter(), []
for f in glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'), recursive=True):
    if os.path.getmtime(f) < cut:
        continue
    for line in open(f, errors='ignore'):
        if '"timestamp"' not in line:
            continue
        try:
            o = json.loads(line)
            d = dt.datetime.fromisoformat(o['timestamp'].replace('Z', '+00:00'))
        except Exception:
            continue
        h = d.astimezone().hour
        u = (o.get('message') or {}).get('usage') or {}
        burn[h] += sum(u.get(k, 0) or 0 for k in
                       ('input_tokens', 'output_tokens',
                        'cache_read_input_tokens', 'cache_creation_input_tokens'))
        ep.append(d.timestamp())
mx = max(burn.values() or [1])
print("token burn by hour:")
for h in range(24):
    if burn[h]:
        print(f"  {h:02d}  {'#' * int(40 * burn[h] / mx)}")
ep.sort(); anchors, cur = [], None
for e in ep:                                        # a new 5h block starts after a >5h gap
    if cur is None or e >= cur + 5 * 3600:
        cur = e; anchors.append(e)
ah = Counter(dt.datetime.fromtimestamp(a).astimezone().hour for a in anchors)
print("your 5h blocks currently start at:")
for h in range(24):
    if ah[h]:
        print(f"  {h:02d}  {'#' * ah[h]}")
```

## Recipe A — macOS (launchd)   ← recommended on a Mac

launchd beats cron on a Mac: cron runs with a bare `PATH` and **silently skips** jobs missed
during sleep. This setup uses **no wake-from-sleep** (fires only when the Mac is already
awake); swap in `pmset repeat wakeorpoweron` if you'd rather guarantee the wake.

**1. Wrapper** — `~/claude-warmup/warmup.sh` (`chmod +x`):

```bash
#!/bin/bash
set -u
FIRE_HOURS="00 08 14 19"                 # the grid's hours; keep in sync with the plist
export HOME="${HOME:?}"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOG="$HOME/claude-warmup/warmup.log"
log(){ echo "$(date '+%F %T %Z')  $*" >>"$LOG"; }

# guard: only on a grid hour (a late wake-from-sleep catch-up then no-ops)
[ "${WARMUP_FORCE:-0}" = 1 ] || case " $FIRE_HOURS " in
  *" $(date +%H) "*) : ;; *) log "skip: off-grid $(date +%H)"; exit 0 ;; esac
# guard: AC power only
[ "${WARMUP_FORCE:-0}" = 1 ] || pmset -g batt | grep -q "AC Power" || { log "skip: battery"; exit 0; }

CLAUDE="$(command -v claude || echo "$HOME/.local/bin/claude")"
cd "$HOME"
if out="$("$CLAUDE" -p "Reply with only: ok" --model haiku 2>&1)"; then
  log "ok: anchored $(date +%H:%M) (reply='$(printf %s "$out" | tr -d '\n' | cut -c1-40)')"
else
  log "FAIL rc=$? ($(printf %s "$out" | tr -d '\n' | cut -c1-80))"
fi
```

**2. LaunchAgent** — `~/Library/LaunchAgents/com.<you>.claude-warmup.plist` (absolute paths
required; replace `<you>` and the home path):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.&lt;you&gt;.claude-warmup</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>/Users/&lt;you&gt;/claude-warmup/warmup.sh</string></array>
  <key>StartCalendarInterval</key><array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>50</integer></dict>
    <dict><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>19</integer><key>Minute</key><integer>10</integer></dict>
    <dict><key>Hour</key><integer>0</integer><key>Minute</key><integer>20</integer></dict></array>
  <key>RunAtLoad</key><false/>
  <key>ProcessType</key><string>Background</string>
</dict></plist>
```

**3. Load & verify:**

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.<you>.claude-warmup.plist
launchctl print gui/$(id -u)/com.<you>.claude-warmup | head    # loaded + next fire
WARMUP_FORCE=1 bash ~/claude-warmup/warmup.sh                   # test now; check warmup.log
```

Unload with `launchctl bootout gui/$(id -u)/com.<you>.claude-warmup`. Loading into the
`gui/<uid>` domain lets the ping reach your login Keychain, so **no token is needed locally**.
(Add a portable timeout around the `claude` call if you like — stock macOS has no `timeout`;
`gtimeout` ships with coreutils, or use `perl -e 'alarm shift; exec @ARGV' 120 …`.)

## Recipe B — Linux / always-on box (cron)

On a machine that never sleeps, plain cron is ideal and exact. Headless, so you need the OAuth
token (Trap 2). Keep the crontab/file `600`:

```cron
CLAUDE_CODE_OAUTH_TOKEN=...              # from `claude setup-token`
50 8  * * *  claude -p "Reply with only: ok" --model haiku >>~/warmup.log 2>&1
0  14 * * *  claude -p "Reply with only: ok" --model haiku >>~/warmup.log 2>&1
10 19 * * *  claude -p "Reply with only: ok" --model haiku >>~/warmup.log 2>&1
20 0  * * *  claude -p "Reply with only: ok" --model haiku >>~/warmup.log 2>&1
```

## Recipe C — off-machine (GitLab CI)

Runs 24/7 regardless of your machine. Needs the OAuth token as a **masked + protected** CI
variable `CLAUDE_CODE_OAUTH_TOKEN` (full account access — treat as a password; private repo,
ideally your own runner). Schedules are best-effort (±a few→~20 min) — fine here.

`.gitlab-ci.yml`:
```yaml
warmup:
  image: node:22-slim
  rules:
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
    - if: '$CI_PIPELINE_SOURCE == "web"'     # lets you click Run pipeline to test
  variables: { GIT_STRATEGY: none }
  script:
    - npm install -g @anthropic-ai/claude-code
    - claude -p "Reply with only: ok" --model haiku
```
Then **Build → Pipeline schedules**: one schedule per grid time (cron `50 8 * * *`,
`0 14 * * *`, `10 19 * * *`, `20 0 * * *`) with your timezone. GitLab beats GitHub here —
GitHub's `on: schedule` is delayed far more often, sometimes dropped.

## The ping

`claude -p "Reply with only: ok" --model haiku` — the 5h window is **account-level and shared
across models**, so any authenticated call anchors it; the model only affects cost. Haiku plus
a ~1-token reply is about as cheap as it gets, in both dollars and the slice of your 5h budget
it uses.

## Verify

- `tail ~/claude-warmup/warmup.log` — one line per grid time.
- `npx ccusage blocks` (third-party) or a scan of `~/.claude/projects/**/*.jsonl` — confirm
  your 5h blocks now start on the grid.

## Gotchas

- **Don't run two triggers at the same grid** (e.g. Mac + CI) — redundant pings.
- **No-wake means missed-if-asleep**: a Mac asleep at a grid time skips that anchor (by
  design). Use `pmset repeat wakeorpoweron` to guarantee it.
- **All-night sessions won't re-phase** in the morning (no idle gap before the first grid
  time) — expected; the grid resumes once a window expires.
- **It consumes your window** — that's the point (a real, counted call), just a tiny one.

---
*A concrete single-machine instance of Recipe A — real paths, a usage scanner, and a
`gitlab/` variant — is the kind of thing that lives outside a repo like this, e.g. in
`~/claude-warmup/`.*
