---
name: hotfix
description: |
  Test-first hotfix protocol for bugs on a deployed environment: reproduce as a failing test, diagnose, minimal fix, then land it on BOTH the mainline and the deployed/release branch via cherry-pick — with all remote git handed to the user. Use when the user reports a bug on prod/staging ("production is broken", "bug on prod", "emergency fix", "hot patch", "rollback and fix") or names a deployed build/tag with a problem. Deploy mechanics (tags, CI, dashboards) stay per-project — this skill ships the discipline, not the pipeline.
---

# Hotfix — test-first, both branches, local git only

The protocol that keeps an urgent fix from becoming a second incident. Three non-negotiables:

1. **Test first** — reproduce the bug as a failing test before touching the fix.
2. **Cherry-pick both ways** — the fix lands on the mainline AND the deployed branch, never one.
3. **Local git only** — the agent checks out, cherry-picks, and tags locally; every push is printed
   for the **user** to run (the `git` plugin's guard enforces this anyway).

## First: find the project's release shape

Read the project's own deploy docs (CLAUDE.md links, `docs/`, infra notes) for how deployments are
identified — release branches, deploy tags, build ids. Probe:

```bash
git branch -a | grep -iE 'release|hotfix' | sort -V
git tag -l | grep -iE 'deploy|prod|release' | head
```

**If the project has no release branches/tags** (nothing deployed from a frozen ref), a "bug on prod"
is a plain bugfix on the mainline — use the normal flow, not this protocol. Say so and proceed simply.

## Phase 0 — reproduce as a failing test

- Locate (or create) the test file for the affected unit, in the project's test convention.
- Write a test that fails in exactly the way the user reports. Run it; confirm red.
- Commit the failing test by itself: `test: reproduce <bug> from <env/build>` — this commit is the
  proof-of-bug and the permanent regression guard; it ships even if the fix takes iterations.
- **Can't reproduce it as a test** (race, environment-only)? STOP and tell the user — a bug that
  can't be tested usually can't be confidently fixed either. Don't skip phase 0 on vague grounds.

## Phase 1 — identify the deployed code

Pin down which ref the affected environment runs (release branch, deploy tag, or the build id the
user named). Check it out locally. Diagnose against **that** code, not the mainline — the bug may
already be fixed there, or look different.

## Phase 2 — diagnose the root cause

Read the code, check recent commits on the deployed ref (`git log --oneline -20 <ref>`), and read the
project's relevant docs for domain context. **Tell the user what you found before writing the fix** —
they may have context that changes the approach.

## Phase 3 — the minimal fix

- **Normal urgency**: fix on the mainline first, then cherry-pick to the deployed branch.
- **Emergency (prod is down)**: fix directly on the deployed branch, then cherry-pick back.
- Either way: minimal diff — no refactors, no cleanup, no drive-by improvements (those go to the
  mainline separately, later). Run the project's checks (lint/build/tests). The phase-0 test must go
  green and nothing else may regress — that's the gate for phase 4.
- **Check for siblings**: if the bug is an instance of pattern X, grep for other instances and fix
  them all, not just the reported one.

## Phase 4 — land both ways, hand over the remotes

```bash
COMMIT=$(git rev-parse HEAD)        # on the branch you fixed
git checkout <the-other-branch>
git cherry-pick "$COMMIT"
```

Then print a copy-paste block for the **user** — never run it:

```
git push origin <release-branch> <mainline>
# then your project's deploy step (tag move / CI trigger / redeploy)
```

Remind them of the project's own deploy/verify steps (from its docs) — git operations alone deploy
nothing. If the fix includes migrations, flag any maintenance-mode step the project documents.

## What NOT to do

- No fix without the failing test first; no claiming done while the test is red or unwritten.
- Never leave the fix on only one branch — both ways, always, in the same session.
- Never push, pull, or force-move refs — print remote commands for the user.
- Don't widen scope — an incident is the worst time for a refactor.
