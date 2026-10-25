# relay-model-guard-tail-knob

Make model-guard's transcript tail size a project knob instead of a hard-coded constant.

## Scope

`MODEL_GUARD_TAIL_KB` (in KB, default 512, via `hookio.setting_int`) controls how far back
`transcript_model` seeks when reading the session's last assistant `model`. Read at call time, not
import, so tests can flip the env between checks.

Touches: `guards/` only + root `README.md` switches row. `guards/lib/hookio.py` is a vendored copy —
not edited; `setting_int` already exists there.

## Slices

One coherent slice (the knob + its tests + docs + version bump are atomic):

- `guards/hooks/model-guard.py` — `TAIL_BYTES` const → `tail_bytes()` helper reading
  `MODEL_GUARD_TAIL_KB`; docstring Config line names the knob.
- `guards/tests/test_model_guard.py` — knob added to the env-pop tuple; 4 checks against
  `transcript_model` directly: default 512 KB reads a model past 1 KB; a 1 KB tail hides a model
  beyond the window; a model inside the 1 KB tail is still read; a malformed value falls back.
- Docs name the knob: `guards/README.md` model-guard entry, root `README.md` switches row,
  `guards/CHANGELOG.md` (## 0.1.1 — unreleased).
- `guards/.claude-plugin/plugin.json` 0.1.1-dev.2 → 0.1.1-dev.3 (same commit).

## Progress

- Landed: claim row → `develop@5cba308`.
- Committed on branch, not landed: the knob slice (one commit, prefix `relay-model-guard-tail-knob ┃`).
- `python3 guards/tests/test_model_guard.py` → 21/21 green (4 new).
- Next: `./tests.sh` ALL GREEN, then ping the human for review.

## Open questions

None — the task is fully specified; delivered as one slice.
