# Lessons — index

Durable, hard-won lessons for **this** repo (the optimiziramsi-skills marketplace) — one file per
lesson, this README the entry-point index. Content lives in the linked files; this list is scanned every session.
Priority: 🔴 High (read every session) · 🟡 Mid (grouped by activity, read on entry) · ⚪ Low (lookup).
Curation rules: the `lessons` skill (shipped in `optimiziramsi-skills`), which this repo dogfoods.

## ⚡ Read-before tripwires

Wiring registry for enforced + routed lessons (moment → lesson → where it's wired):

- **Editing / committing a `plugins/<name>/` change** → [Bump plugin.json version on edit](plugin-version-bump-on-edit.md) → routed via CLAUDE.md § Authoring conventions (mechanization proposed, not yet enforced).
- **Fixing a guard bug, or hardening a channel** → [A doc that documents a bug becomes a bypass](doc-fixes-must-not-become-bypasses.md) → sweep the docs for the *workaround*, not just the claim (unwired; honored by hand).

## 🔴 High — read every session

_(none yet)_

## 🟡 Mid — read when entering the activity

### Plugin authoring & versioning

- [Bump the plugin's `plugin.json` version on any `plugins/<name>/` change](plugin-version-bump-on-edit.md) — same-version edits never reach installed consumers; CCD binds by installed version and only re-materializes on a version change.

### Authoring skill / guard documentation

- [A doc that documents a bug becomes a bypass the moment the bug is fixed](doc-fixes-must-not-become-bypasses.md) — the workaround outlives the defect; never ship "work around the guard" as guidance, ship "verify" instead.

## ⚪ Low — lookup only

_(none yet)_
