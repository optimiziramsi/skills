# guards — changelog

Versions of the `guards@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.1 — unreleased

- New `model-guard` hook (SessionStart + UserPromptSubmit): while the session runs on a model matching `MODEL_GUARD_MATCH` (default `opus-5-5`), re-injects a two-sentence trust reminder every prompt — follow every instruction/step, deliver in full or stop and ask. Project text override chain `MODEL_GUARD_FILE` → `.agent/model-guard.md` → `.claude/model-guard.md`; kill switch `MODEL_GUARD_OFF=1`.

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (`tripwire-guard` + its example guards and `file-guard`, from its `instructions` topic). Enable it per project with `claude plugin install guards@optimiziramsi --scope project`.
