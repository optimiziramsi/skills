# git-guard — changelog

Versions of the `git-guard@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.1 — unreleased

- Block reasons no longer name an env switch or allow token (`GIT_GUARD_ALLOW`, `GIT_GUARD_ALLOW_FETCH`,
  `GIT_GUARD_PROTECTED_BRANCH`, `GIT_GUARD_INTEGRATION_BRANCH`, `GIT_GUARD_STRICT`): a model read the
  named switch as the next thing to try. A reason now says what was blocked, gives the allowed form
  when one exists, and otherwise ends with "Stop and tell the user what you wanted to do." The
  switches stay documented in the README. What is blocked or allowed is unchanged.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (the `git-guard` hook of its `git` topic). Enable it per project with `claude plugin install git-guard@optimiziramsi --scope project`.
- Branch detection (default / protected / integration) moved into the shared `lib/hookio.py`, so
  `code-first` resolves branches exactly as this guard does. No behavior change.
