# guards — changelog

Versions of the `guards@optimiziramsi` plugin. History before the split into one plugin per concern
(the single `optimiziramsi-skills` plugin, ≤ 0.0.13) is in the
[marketplace CHANGELOG](https://github.com/optimiziramsi/skills/blob/main/CHANGELOG.md).

## 0.1.2 — 2026-11-12

- `model-guard`: the shipped text is now a scope reminder (`SCOPE GUARD`) — do what was asked at the scope it was asked, finish the whole task or say which part could not be done, and treat a guard block as a stop. It replaces the `TRUST GUARD` text ("follow every instruction", "deliver in full"), which pushed the model to do more. Which models it fires for and the env knobs are unchanged.
- `tripwire-guard`: the fallback block reason (a project guard that exits 2 without printing one) now ends with "Stop and tell the user what you wanted to do."

## 0.1.1 — 2026-10-26

- New `model-guard` hook (SessionStart + UserPromptSubmit): while the session runs on a model matching `MODEL_GUARD_MATCH` (default `opus-5-5`), re-injects a two-sentence trust reminder every prompt — follow every instruction/step, deliver in full or stop and ask. Project text override chain `MODEL_GUARD_FILE` → `.agent/model-guard.md` → `.claude/model-guard.md`; kill switch `MODEL_GUARD_OFF=1`. How far back the transcript is scanned for the model is `MODEL_GUARD_TAIL_KB` (in KB; default 512).

## 0.1.0 — 2026-10-18

- Split out of the single `optimiziramsi-skills` plugin (`tripwire-guard` + its example guards and `file-guard`, from its `instructions` topic). Enable it per project with `claude plugin install guards@optimiziramsi --scope project`.
