# reporting — the lean-reporting output contract, enforced

The `reporting@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

The house **output contract**: total silence while working (zero text between tool calls), then
exactly one report — **1 outcome line + ≤5 terse fact bullets + a numbered `Q:` list** (omitted if
empty). No narration, headers, tables, or "next steps". Blocked on a decision mid-task → send only
the `Q:` list and wait.

**Opt-in and opinionated** (like the `commit` plugin): enable it only if you want this specific
convention. It's aggressive by design — the Stop guard *blocks* a violating final message and forces
a rewrite.

## Contents

- name: `contract`
  kind: hook
  purpose:
    UserPromptSubmit — injects the full contract text with every prompt. The text is the
    project's own when it has one — first hit wins, project-relative: `$REPORT_CONTRACT_FILE` →
    `.agent/output-contract.md` → `.claude/output-contract.md` → the shipped
    `hooks/brevity-reminder.txt`. An override that exists but can't be read (or a
    `REPORT_CONTRACT_FILE` that doesn't exist) prints a visible "⚠️ brevity-reminder DISARMED" line
    instead of silently falling back.

- name: `contract-pulse`
  kind: hook
  purpose:
    PostToolUse — re-injects a one-line reminder every Nth tool call (default 10,
    `REPORT_PULSE_EVERY`), so the contract doesn't decay over a long agentic turn.
    `REPORT_PULSE_TEXT` replaces the one-liner (keep it matching a custom contract).

- name: `report-guard`
  kind: hook
  purpose:
    Stop — reads the turn's final assistant message from the transcript; **blocks** it (one
    rewrite, `stop_hook_active`-guarded) on process narration, headers, tables, or gross
    over-length (`REPORT_GUARD_MAX_LINES`, default 18). Fenced code blocks are exempt from shape
    checks — limiting inline code is the [`code-first`](../code-first) plugin's job. Self-test:
    `--test`.

Escape hatch for all three: `REPORT_GUARD_OFF=1` (user-set). Fail-open: a missing dependency or
unreadable transcript never bricks a session.

## Why three hooks, not one

A single injection decays: models drift back to narrating over a 50-tool-call turn. The trio covers
the whole lifecycle — contract stated at prompt time, kept warm mid-turn, and *verified* at stop.
The Stop guard is what gives the convention teeth; the injections are what keep the guard from
firing often.

## Enable

```json
{
  "extraKnownMarketplaces": {
    "optimiziramsi": { "source": { "source": "github", "repo": "optimiziramsi/skills" } }
  },
  "enabledPlugins": { "reporting@optimiziramsi": true }
}
```

No skills or commands — this plugin is pure enforcement of a reporting style.
