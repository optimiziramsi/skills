---
name: qa-gate
description: >-
  Run the full done-gate — typecheck, unit, integration/e2e, and visual verification — before
  claiming work is done. Use before any "done"/"fixed"/"works" claim, before handoff after code
  changes, or when the user says "verify", "run the gate", "is it green".
---

# QA gate — what "done" means

You are the QA loop, not the user. Run the project's checks in order and fix as you go — a claim of
"done" means the gate is green and verified, not assumed.

1. **Environment up.** Start/refresh whatever the checks run against (dev server, Docker stack, test
   DB). Note any port/URL the project prints.
2. **Static + unit.** Run the project's typecheck and unit/smoke checks. Fix failures before
   proceeding — don't stack more checks on a red base.
3. **Integration / e2e.** Run the project's end-to-end suite. Name flakes as flakes (a known
   cold-start retry is not a real failure) — but never wave away a real red as "probably flaky".
4. **Visual — if the UI changed, verify with your own eyes.** Capture screenshots of the affected
   screens, **Read the images**, and confirm each one actually looks and behaves as intended. Extend
   the screenshot/e2e coverage when screens were added or changed. Code that typechecks can still
   render broken.
5. **Project cross-checks.** Run whatever the project gates on before "green" (a version bump on
   changed web files, doc/contract sync on deploy-affecting changes, size bounds on new
   user-writable content, …). These live in the project's own rules/skills — check them.
6. **Report honestly.** Exact command results, failures with their output, flakes named as flakes. A
   red gate reported red is a good result; **a red gate reported green is the one unforgivable
   sin.**
