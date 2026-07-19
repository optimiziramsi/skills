---
name: rename
description: |
  Rename a file with full reference cascade — `git mv` the file, then update every non-archive reference across the project. Use when the user says: "rename X to Y", "move X to Y", "X should be called Y", "the file should be Z instead", or signals a path/name change. Catches the dozen-references-cascade problem (renames that work in one place but leave stale pointers everywhere else).
---

# Rename

Renaming a file is rarely just a `mv`. There are usually 5-15 references across docs, skills,
scripts, and config that all need updating. This skill handles the cascade.

## When invoked

The user wants to rename or move a file. The flow:

1. **Confirm source and target paths** if not 100% clear from context.
2. **Pre-scan** — grep all non-archive text files for the source path. Show the count by file type.
3. **Show the user the impact** — "Renaming X → Y will update N references across M files. Proceed?"
   Skip if obvious.
4. **Execute**:
   - `git mv <source> <target>` — preserves history.
   - For each non-archive reference, update the path. Use `sed -i '' 's|<old>|<new>|g'` for bulk
     replacement; verify with grep after.
   - Don't touch archive/frozen folders (e.g. `*/archive/`) or archive FILES (names matching
     `*archive*.md`, e.g. `worktrees-archive.md`) — they're historical record.
5. **Verify** — re-grep for the old path; only archive matches should remain.
6. **Single commit**: `rename {old} → {new}; update N references across M files`.

## Reference scan locations (don't miss any)

Scan all non-archive text files for the old path — Markdown, JSON, shell, YAML, and source
(`.md .json .sh .yml .yaml .ts .tsx .js .jsx`). The usual reference homes:

- `CLAUDE.md`, root `README.md`
- `.agent/*.md`, `.docs/**/*.md`
- `.claude/**/*.md` (skills, commands, agents)
- `.todo` and any planning dirs the project keeps (`.agent/plan/`, `.agent/milestone/`, …)
- `bin/*.sh`, scripts, and config (`package.json`, `tsconfig.json`, …) when relevant
- Source code (`packages/`, `apps/`, `src/`) — only if the rename involves a code path

Skip archive/frozen folders (`*/archive/`) AND archive files (names matching `*archive*.md`, e.g.
`worktrees-archive.md`) — they're a frozen historical record, not live references.

## Reference update strategies

- **Bare filename** (`status.md` → `README.md`): bulk replace, verify each occurrence is in the
  right context (could match unrelated text).
- **Full path** (`.docs/status.md` → `.docs/README.md`): bulk replace, simpler — path is more specific.
- **Directory rename**: `git mv` the directory; update path references; check imports/aliases.

## When to NOT use this skill

- Renaming a code symbol (variable, function, class) — that's a refactor, not a file rename. Use
  editor/LSP refactoring.
- Reorganizing many files at once — chain individual renames, or use a custom script. This skill is
  for one source → one target.

## Common gotchas

- **Bare-name collisions**: renaming `status.md` to `README.md` when a root `README.md` already
  exists makes `` `README.md` `` references ambiguous. Use full paths in that case.
- **Old name in HTML comments / hidden text**: grep is sufficient as long as you don't restrict to
  `.md` only. Include `.html` if relevant.
- **Symlinks**: rare; if found, follow them (they're usually obsolete and should be removed).
- **`<!-- source: foo.md -->` markers**: from old file consolidation. Remove if the source file no
  longer exists.

## What NOT to do

- Don't touch archive folders or archive-named files (`*archive*.md`). Ever.
- Don't rewrite commit messages from history.
- Don't auto-update if grep returns >50 matches — that's an unusual rename, surface to the user first.
- Don't rename without `git mv` (loses history).
