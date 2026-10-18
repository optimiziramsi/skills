# context — changelog

Versions of the `context@optimiziramsi` plugin.

## 0.1.0 — unreleased

- New: context-window nudges read from the transcript's usage — 30% / 50% / 60% of a 1M window by
  default, the last one saying plainly that a handoff is needed; "remind me later" / "keep going"
  / "topic done" answers are honored for the session. `/repack` writes the handoff for a
  `/clear` → `/continue` refresh.
