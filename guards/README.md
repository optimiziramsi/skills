# guards — project-owned enforcement

The `guards@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

Three hooks that enforce the PROJECT's rules rather than this marketplace's: **tripwire-guard** runs
your own checks before every shell command, **file-guard** asks you before the agent edits the files
that enforce your rules, **model-guard** re-injects a trust reminder while the session runs on a
model you do not trust to follow instructions in full.

## Contents

- name: `tripwire-guard`
  kind: hook, engine
  purpose:
    PreToolUse `Bash` — runs **project-owned command tripwires** from `.agent/guards.d/`
    against every Bash command: a guard exits 2 to block (first block wins, reason fed to the
    agent), 0 to allow, anything else becomes a loud non-blocking warning. Guards are written in
    any language (`*.sh`, `*.py`, or any `+x` file with a shebang). No dir/guards → silent
    no-op. One-shot escape `TRIPWIRE_SKIP=1` command prefix; kill switch `TRIPWIRE_GUARD_OFF=1`.
    Engine tests: `python3 tests/test_tripwire.py`.

- name: `file-guard`
  kind: hook
  purpose:
    PreToolUse — writes to **T3 enforcement surfaces** (`.claude/settings*.json`,
    `.claude/hooks/`) downgrade to an **ask**: a session must not silently rewrite its own
    guards. Extra prefixes via `FILE_GUARD_EXTRA` (colon-separated); escape hatch
    `FILE_GUARD_OFF=1`; self-test `--test`.

- name: `model-guard`
  kind: hook
  purpose:
    SessionStart + UserPromptSubmit — while the session model matches `MODEL_GUARD_MATCH`
    (comma-separated substrings of the model id; default `opus-5-5`), injects a two-sentence
    **trust reminder** on every prompt: follow every instruction and step (skipping is a violation,
    not a judgment call), and deliver in full — stop and ask rather than park the rest as a
    TODO / follow-up. The model comes from the SessionStart payload, then the transcript's last
    assistant `model` (so a `/model` switch is honored). Text override: `MODEL_GUARD_FILE` →
    `.agent/model-guard.md` → `.claude/model-guard.md` → the shipped `hooks/model-guard.txt`
    (`{{MODEL}}` = the matched id). How far back the transcript is read for the model is
    `MODEL_GUARD_TAIL_KB` (in KB; default 512). Kill switch `MODEL_GUARD_OFF=1`. Tests:
    `python3 tests/test_model_guard.py`.

## tripwire-guard — project-owned command tripwires

The ENGINE is a PreToolUse `Bash` hook (`hooks/tripwire-guard.py`); the PROJECT supplies the
guards in **`.agent/guards.d/`** (no dir → silent no-op). Each guard is executed in sorted order
with the Bash command in `$TRIPWIRE_COMMAND` and the full tool-input JSON in `$TRIPWIRE_INPUT` +
on stdin: **exit 2 + printed reason = block** (first block wins), exit 0 = allow, anything else =
loud non-blocking warning.

**Your guards, your language.** `*.sh` runs under `bash` and `*.py` under `python3` (no executable
bit needed); anything else in the dir runs directly when it is `+x`, so its own shebang picks the
interpreter — node, ruby, a compiled binary. Non-runnable files (a README, a config, a guard you
disabled by dropping its `+x`) are ignored. The engine is python because *this plugin* is python;
that is not a contract on the projects that install it. Self-tests are the guard's business too —
the bash examples below define a `tripwire_test` function and gate their dispatch with
`[ "${BASH_SOURCE[0]}" = "$0" ]` so they can be sourced and tested.

Shipped, ready-to-copy examples in [`examples/guards.d/`](examples/guards.d/) — bash because
these three are mostly `git` plumbing, not because guards must be (integration branch via
`TRIPWIRE_INTEGRATION_BRANCH`, default `develop`):

- **`land-check.sh`** — blocks a landing push (`git push . HEAD:<integration>`) when HEAD isn't
  rebased onto the branch's *current* tip, and when the land would resurrect a board-file line
  (`TRIPWIRE_BOARD_FILE`, default `.agent/worktrees.md`) that the integration branch deleted.
- **`docs-drift-warn.sh`** — warn-only: a landing push that changes source
  (`TRIPWIRE_SRC_RX`) without touching docs (`TRIPWIRE_DOCS_RX`).
- **`cap-gate.sh`** — blocking: refuses a `git commit` while the instruction surface is over cap —
  the enforcement complement to the nudge-only `caps` hook. Caps env-overridable (`CAP_CLAUDE` …);
  `CAP_GATE_OFF=1` to bypass.

Escape hatches: prefix the ONE false-positiving command with `TRIPWIRE_SKIP=1` (one-shot, visible
in the transcript); `TRIPWIRE_GUARD_OFF=1` kill switch; `TRIPWIRE_GUARDS_DIR` overrides the
discovery dir. The engine is python3 (stdlib only) — no `jq`, so it has no way to disarm itself.

## Enable

```bash
claude plugin install guards@optimiziramsi --scope project
```
