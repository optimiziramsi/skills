# Lessons — index

Durable, hard-won lessons for **this** repo (the opsi marketplace) — one file per lesson, this
README the entry-point index. Content lives in the linked files; this list is scanned every session.
Priority: 🔴 High (read every session) · 🟡 Mid (grouped by activity, read on entry) · ⚪ Low (lookup).
Curation rules: the `lessons` skill (instructions@opsi), which this repo dogfoods.

## ⚡ Read-before tripwires

Wiring registry for enforced + routed lessons (moment → lesson → where it's wired):

- **Editing / committing a `plugins/<name>/` change** → [Bump plugin.json version on edit](plugin-version-bump-on-edit.md) → routed via CLAUDE.md § Authoring conventions (mechanization proposed, not yet enforced).

## 🔴 High — read every session

_(none yet)_

## 🟡 Mid — read when entering the activity

### Plugin authoring & versioning

- [Bump the plugin's `plugin.json` version on any `plugins/<name>/` change](plugin-version-bump-on-edit.md) — same-version edits never reach installed consumers; CCD binds by installed version and only re-materializes on a version change.

## ⚪ Low — lookup only

_(none yet)_
