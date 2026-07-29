# A doc that documents a bug becomes a bypass the moment the bug is fixed

Guidance written *around* a defect — "the guard false-positives here, work around it with X" —
has a shelf life the fix silently ends. The workaround outlives the defect, and once the
neighbouring channel gets hardened, that same sentence is now an instruction to **route around a
guard**. Deleting the fixed-defect claim is not enough; the workaround it justified is the part
that does the damage.

## What bit us (2026-07-29)

The `worktree` skill's "Known failure modes" list carried: *the write-guard's false-positive on
the worktree's own nested `.claude/**` (work around it with an in-worktree relative Bash/Python
write, not an absolute-path tool write)*.

- The false-positive was fixed in **0.0.6** — the rewritten write-guard tests "inside the
  worktree" **before** "inside the main checkout", so a nested `.claude/**` target is allowed in
  both layouts. The sentence was stale for three releases.
- **0.0.9 hardened the shell channel** (`worktree-bash-guard` gained path resolution + `cd`
  tracking). At that moment the workaround stopped being a workaround and became "switch to the
  Bash channel to get past the tool guard" — in direct contradiction of § Path discipline three
  lines above it, which the *same release* had just rewritten to say "write as if neither
  guard existed".
- Neither the 0.0.6 release that fixed the bug nor the 0.0.9 release that rewrote the paragraph
  directly above it noticed. A consumer repo field-testing 0.0.9 found it.

## The rule

- **When a guard/defect gets fixed, grep the docs for the workaround, not just the claim.** The
  claim is findable (`grep "false-positive"`); the workaround is prose and usually isn't.
- **Never ship "work around the guard" as guidance.** The honest replacement is *verify* — confirm
  the write landed where you meant. A guard denial is a real escape; re-issue the path, don't
  switch channels. If a guard is genuinely wrong, fix the guard or use its kill-switch; both are
  visible, and a prose bypass is not.
- **Attribute a residual to the component that owns it.** What replaced this item is a *host*
  path-resolver quirk, not a guard defect — labelling it correctly stops the next reader from
  concluding the guard is broken and reaching for a bypass again.
- **Hardening a channel invalidates advice that assumed it was open.** Any release that closes a
  hole should sweep for text written while it was open. Cross-reference
  [[plugin-version-bump-on-edit]]: shipping the fix is only half of it.

**Origin:** 2026-07-29 — rabbit-run, running 0.0.9 for real, reported the stale item; verified
here (the false-positive is unreproducible in both worktree layouts) and fixed doc-only in 0.0.10.
