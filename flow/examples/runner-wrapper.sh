#!/bin/sh
# bin/loop — thin wrapper around the optimiziramsi-skills flow runner. IDENTICAL to bin/grind:
# it dispatches on its own filename, so both copies are the same file.
#
# This file is COMMITTED on purpose. A symlink into the plugin cache would encode a machine
# path and could not be tracked, so it would never travel to a fresh worktree — the very place
# you want to run the runner from. This wrapper carries no local paths: it resolves the
# installed plugin at run time, so it keeps working after a plugin update and in every worktree.
#
# Resolution order:
#   1. $FLOW_RUNNER_ROOT      — explicit override (a dev checkout of the plugin repo)
#   2. $CLAUDE_PLUGIN_ROOT    — set when something inside a Claude Code session invokes it
#   3. newest version in the plugin cache (~/.claude/plugins/cache/*/optimiziramsi-skills/*)
#
# Regenerate with the `scaffold` skill. Usage: same flags as the runner it fronts, e.g.
#   bin/loop --status
#   bin/loop --worktree feature/thing        # run against a worktree, from the checkout root
#   bin/loop --worktree all                  # every worktree that has pending jobs
set -eu

tool=$(basename "$0")
case "$tool" in
  loop|grind) ;;
  *) echo "runner wrapper: expected to be named 'loop' or 'grind', not '$tool'" >&2; exit 2 ;;
esac

try() { [ -n "${1:-}" ] && [ -x "$1" ]; }

for root in "${FLOW_RUNNER_ROOT:-}" "${CLAUDE_PLUGIN_ROOT:-}"; do
  [ -n "$root" ] || continue
  # accept either the plugin root (…/flow/bin/x) or a bare bin dir (…/bin/x)
  for candidate in "$root/flow/bin/$tool" "$root/bin/$tool"; do
    if try "$candidate"; then exec "$candidate" "$@"; fi
  done
done

cached=$(ls -d "$HOME"/.claude/plugins/cache/*/optimiziramsi-skills/*/flow/bin/"$tool" 2>/dev/null \
         | sort -V | tail -n 1) || cached=""
if try "$cached"; then exec "$cached" "$@"; fi

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
