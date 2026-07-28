#!/bin/sh
# bin/loop — thin wrapper around the optimiziramsi-skills flow runner. IDENTICAL to bin/grind:
# it dispatches on its own filename, so both copies are the same file.
#
# COMMITTED on purpose. A symlink into the plugin cache would encode a machine path and could not
# be tracked, so it would never travel to a fresh worktree — the very place you want to run from.
# This file carries no local paths: it resolves the installed plugin at run time, execs it, and
# gets out of the way. The runners are cwd-relative, so exec alone puts the work in the right repo.
#
# Resolution order:  $FLOW_RUNNER_ROOT (a dev checkout) → $CLAUDE_PLUGIN_ROOT (set inside a
# session) → the newest version in the plugin cache.
#
# Usage: whatever flags the runner takes, e.g.
#   bin/loop --status
#   bin/loop --worktree feature/thing        # run against a worktree, from the checkout root
set -eu

tool=$(basename "$0")
cache=$(ls -d "$HOME"/.claude/plugins/cache/*/optimiziramsi-skills/*/flow/bin 2>/dev/null \
        | sort -V | tail -n 1) || cache=""

for dir in "${FLOW_RUNNER_ROOT:-}/flow/bin" "${CLAUDE_PLUGIN_ROOT:-}/flow/bin" "$cache"; do
  [ -x "$dir/$tool" ] && exec "$dir/$tool" "$@"
done

echo "$tool: optimiziramsi-skills flow runner not found." >&2
echo "  install:  claude plugin install optimiziramsi-skills@optimiziramsi" >&2
echo "  or:       FLOW_RUNNER_ROOT=/path/to/skills bin/$tool ..." >&2
exit 127
