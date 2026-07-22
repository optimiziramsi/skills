# Instructions changelog

Changes to this repo's instruction system + the plugins it ships — newest first, tier-tagged
(**T2** apply-safe · **T3** via `rules-change`). Governance doors: the `retro` / `rules-change`
skills (shipped in `optimiziramsi-skills`; pre-consolidation `instructions@opsi`), which this repo dogfoods.

- **2026-07-21 · T3** — lessons: slug filename shape is a project choice — a permanent numeric
  `NN-` ordering prefix is blessed, pinnable via meta-lint `filenames.rules` for `.agent/lessons`
  (example rule added to `meta-lint.rabbit-run.json`); lessons skill note; instructions 0.3.4 →
  0.3.5. Trigger: hub pt2 — hub uses a permanent `NN-slug`. Approved in-session.
- **2026-07-21 · T3** — commit-nudge: opt-in `COMMIT_NUDGE_EXTRA_DIRS=<dirs>` folds dirty *sibling*
  trees into the nudge + one-shot state; added a self-test (previously untested); commit 0.1.0 →
  0.1.1. Trigger: hub pt5b — a dirty `../gitops` went unseen. Approved in-session.
- **2026-07-21 · T3** — git-guard: `GIT_GUARD_ALLOW_FETCH=<remotes>` permits `git fetch <remote>`
  for named remotes only (bare/`--all`/`--multiple` stay blocked); +8 self-test cases; git 0.1.1 →
  0.1.2. Trigger: hub pt3 — the all-or-nothing `GIT_GUARD_ALLOW=fetch` was too coarse. Approved
  in-session.
- **2026-07-21 · T2** — hub Phase-18 divergence intake (6 items) parked in `.todo-inbox` and routed
  here. Safe fixes already applied: `cap-gate.sh` example guard (pt4, instructions 0.3.3); retro
  notes the `.agent/`/`.docs/` layout is the default, not a requirement (pt1, 0.3.4); README install
  load-protocol caveats (pt6); ADOPTION per-remote-fetch workaround + hook-composition notes
  (pt3/pt5). T3 builds (pt2/pt3/pt5b) recorded below as they land.
