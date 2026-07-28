#!/bin/sh
# bin/loop — thin wrapper around the optimiziramsi-skills flow runner. IDENTICAL to bin/grind:
# it dispatches on its own filename, so both copies are the same file.
#
# This file is COMMITTED on purpose. A symlink into the plugin cache would encode a machine
# path and could not be tracked, so it would never travel to a fresh worktree — the very place
# you want to run the runner from. This wrapper carries no local paths: it resolves the
# installed plugin at run time, so it keeps working across worktrees.
#
# Resolution order:
#   1. $FLOW_RUNNER_ROOT      — explicit override (a dev checkout of the plugin repo)
#   2. $CLAUDE_PLUGIN_ROOT    — set when something inside a Claude Code session invokes it
#   3. newest version in the plugin cache (~/.claude/plugins/cache/*/optimiziramsi-skills/*)
#
# VERSION LOCK: this wrapper is stamped with the plugin version it was generated from and
# REFUSES TO RUN against a different one — a wrapper and a runner that disagree is exactly the
# drift this file exists to prevent. Refresh it after a plugin update (the error prints the
# command); regenerate from scratch with the `scaffold` skill.
#
# Usage: same flags as the runner it fronts, e.g.
#   bin/loop --status
#   bin/loop --worktree feature/thing        # run against a worktree, from the checkout root
#   bin/loop --worktree all                  # every worktree that has pending jobs
set -eu

WRAPPER_VERSION=0.0.5          # kept in lockstep with .claude-plugin/plugin.json by tests.sh

tool=$(basename "$0")
case "$tool" in
  loop|grind) ;;
  *) echo "runner wrapper: expected to be named 'loop' or 'grind', not '$tool'" >&2; exit 2 ;;
esac

runner=""
for root in "${FLOW_RUNNER_ROOT:-}" "${CLAUDE_PLUGIN_ROOT:-}"; do
  [ -n "$root" ] || continue
  # accept either the plugin root (…/flow/bin/x) or a bare bin dir (…/bin/x)
  for candidate in "$root/flow/bin/$tool" "$root/bin/$tool"; do
    if [ -x "$candidate" ]; then runner=$candidate; break 2; fi
  done
done

if [ -z "$runner" ]; then
  cached=$(ls -d "$HOME"/.claude/plugins/cache/*/optimiziramsi-skills/*/flow/bin/"$tool" 2>/dev/null \
           | sort -V | tail -n 1) || cached=""
  [ -n "$cached" ] && [ -x "$cached" ] && runner=$cached
fi

if [ -z "$runner" ]; then
  cat >&2 <<EOF
$tool: could not find the optimiziramsi-skills flow runner.

Looked in:
  \$FLOW_RUNNER_ROOT   (${FLOW_RUNNER_ROOT:-unset})
  \$CLAUDE_PLUGIN_ROOT (${CLAUDE_PLUGIN_ROOT:-unset})
  $HOME/.claude/plugins/cache/*/optimiziramsi-skills/*/flow/bin/$tool

Install it:  claude plugin install optimiziramsi-skills@optimiziramsi
Or point at a checkout:  FLOW_RUNNER_ROOT=/path/to/skills bin/$tool
EOF
  exit 127
fi

# ── version lock ────────────────────────────────────────────────────────────
# …/<plugin-root>/flow/bin/<tool> → <plugin-root>; a bare bin/ layout resolves one level up.
plugin_root=$(dirname "$(dirname "$runner")")
[ "$(basename "$plugin_root")" = "flow" ] && plugin_root=$(dirname "$plugin_root")
manifest="$plugin_root/.claude-plugin/plugin.json"
runner_version=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$manifest" 2>/dev/null \
                 | head -n 1) || runner_version=""

if [ "${FLOW_WRAPPER_ALLOW_DRIFT:-0}" != "1" ] && [ "$runner_version" != "$WRAPPER_VERSION" ]; then
  cat >&2 <<EOF
$tool: VERSION DRIFT — refusing to run.

  this wrapper (bin/$tool):  $WRAPPER_VERSION
  installed runner:          ${runner_version:-unknown}  ($runner)

The wrapper and the runner it fronts must be the same plugin version — a stale wrapper can
pass flags a newer runner renamed, or miss a gate a newer runner requires.

If the installed runner is OLDER, update the plugin first:
  claude plugin marketplace update optimiziramsi && claude plugin update optimiziramsi-skills@optimiziramsi

Then refresh the wrapper from the version you ended up with, and commit it:
  cp "$plugin_root/flow/examples/runner-wrapper.sh" bin/loop
  cp "$plugin_root/flow/examples/runner-wrapper.sh" bin/grind
  chmod +x bin/loop bin/grind

Override for one run (you own the risk):  FLOW_WRAPPER_ALLOW_DRIFT=1 bin/$tool …
EOF
  exit 3
fi

exec "$runner" "$@"
