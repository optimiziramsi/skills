# code-first — changelog

Versions of the `code-first@optimiziramsi` plugin.

## 0.2.0 — 2026-11-12

- The contract is opt-in: it is injected, and the Stop guard acts, only once a session ran `/idea`
  (for the rest of that session) or for a prompt matching `CODE_FIRST_TRIGGER_PATTERN` (default
  propose / proposal / sketch). `CODE_FIRST_INJECT=always` restores every-prompt injection.
- The `idea` skill's description no longer triggers on design talk ("brainstorm", "how would you do
  X", "what if we"): in a design session the user wants decisions written down, not code.
- The Stop guard now acts on the `/idea` turn itself. The transcript records a slash command as
  `<command-name>/idea</command-name>`, and the word "command" in that wrapper matched the allow
  pattern, so the turn that opens an idea was never guarded. Only what the user typed after the
  command is read now.
- The stale-idea line moved from SessionStart to Stop: a note for the user only, once per session,
  silent in a linked worktree unless `NUDGES_IN_WORKTREE=1`.

## 0.1.0 — 2026-10-18

- New: the code-first working style as its own plugin — an injected contract with a per-repo
  override chain, a Stop guard on inline fenced code, `/idea` (start / list / promote / drop), a
  stale-idea SessionStart nudge, and the `code-first` CLI. Extracted from one consumer repo's
  CLAUDE.md rule + lesson.
