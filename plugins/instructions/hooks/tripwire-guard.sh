#!/usr/bin/env bash
# tripwire-guard — PreToolUse(Bash) ENGINE for project-owned command tripwires.
#
# The engine ships here (instructions@opsi); the PROJECT supplies the guards as
# `.agent/guards.d/*.sh` scripts. No dir / no guards → silent no-op (projects opt IN). This is
# the generic remainder of RR's lesson-guards.sh: project-defined asserts on the Bash tool's
# command, surfaced AT the moment of risk (its git/commit rules live in git-guard/commit-format).
#
# Guard contract (each *.sh, executed in sorted order, cwd = project dir):
#   - receives the Bash tool's command in $TRIPWIRE_COMMAND, and the full tool-input JSON both
#     in $TRIPWIRE_INPUT and on stdin
#   - print the reason to stdout and exit 2  → BLOCK (first block wins; reason fed to the agent)
#   - exit 0                                 → allow
#   - any other exit                         → LOUD non-blocking warning (systemMessage) carrying
#     whatever it printed — an advisory or a crash is surfaced, never silently swallowed,
#     never blocking
#   - optionally define a `tripwire_test` function (PASS/FAIL lines, return #fails) and gate the
#     top-level dispatch with `[ "${BASH_SOURCE[0]}" = "$0" ]` so the engine's --test can source
#     the file and run the self-test. See examples/guards.d/ in this plugin.
#
# Escape hatches (guards have no shell parser — false positives happen):
#   TRIPWIRE_SKIP=1 …        prefixed to the ONE command that false-positives (one-shot,
#                            visible in the transcript)
#   TRIPWIRE_GUARD_OFF=1     kill switch (user-set env)
#   TRIPWIRE_GUARDS_DIR      override the discovery dir (default .agent/guards.d)
#
# Fail-open but LOUD: missing jq prints a DISARMED systemMessage instead of silently unarming.
# Self-test: bash tripwire-guard.sh --test  (engine cases + every discoverable guard's
# tripwire_test — shipped examples included)
set -u

if [ "${1:-}" = "--test" ]; then
  command -v jq >/dev/null 2>&1 || { echo "FAIL  jq is required to run --test"; exit 1; }
  fails=0
  self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  tmp=$(mktemp -d)
  mkdir -p "$tmp/guards" "$tmp/empty" "$tmp/order"
  cat > "$tmp/guards/10-block.sh" <<'EOF'
#!/usr/bin/env bash
case "${TRIPWIRE_COMMAND:-}" in
  *forbidden*) echo "⛔ test-guard: forbidden command"; exit 2 ;;
esac
exit 0
EOF
  cat > "$tmp/guards/20-warn.sh" <<'EOF'
#!/usr/bin/env bash
case "${TRIPWIRE_COMMAND:-}" in
  *sketchy*) echo "heads-up: sketchy move"; exit 3 ;;
esac
exit 0
EOF
  cat > "$tmp/guards/30-stdin.sh" <<'EOF'
#!/usr/bin/env bash
in=$(cat)
[ "$in" = "${TRIPWIRE_INPUT:-}" ] || { echo "stdin/env tool-input mismatch"; exit 2; }
exit 0
EOF
  printf '#!/usr/bin/env bash\necho "first wins"; exit 2\n' > "$tmp/order/05-first.sh"
  cp "$tmp/guards/10-block.sh" "$tmp/order/10-block.sh"

  rc=0; out=""; err=""
  run() { # run <guards_dir> <command...>
    local dir="$1" cmd="$2" json
    json=$(printf '{"tool_input":{"command":"%s"}}' "$cmd")
    out=$(TRIPWIRE_GUARDS_DIR="$dir" CLAUDE_PROJECT_DIR="$tmp" bash "$self" <<<"$json" 2>"$tmp/stderr"); rc=$?
    err=$(cat "$tmp/stderr" 2>/dev/null)
  }
  t() { # t <name> <want> <got>
    if [ "$3" = "$2" ]; then echo "PASS  $1"; else echo "FAIL  $1 (want $2, got $3)"; fails=$((fails + 1)); fi
  }
  has() { case "$2" in *"$1"*) return 0 ;; *) return 1 ;; esac; }

  run "$tmp/missing" 'echo forbidden';   t "no guards dir → allow" 0 "$rc"
  run "$tmp/empty" 'echo forbidden';     t "empty guards dir → allow" 0 "$rc"
  run "$tmp/guards" 'echo harmless';     t "clean command → allow" 0 "$rc"
  t "stdin+env parity guard ran clean" 0 "$rc"
  run "$tmp/guards" 'echo forbidden';    t "guard block → exit 2" 2 "$rc"
  if has "forbidden command" "$err"; then echo "PASS  block reason on stderr"; else echo "FAIL  block reason on stderr: $err"; fails=$((fails + 1)); fi
  run "$tmp/guards" 'echo sketchy';      t "warn guard → allow" 0 "$rc"
  if has "systemMessage" "$out" && has "sketchy move" "$out"; then echo "PASS  warning surfaced as systemMessage"; else echo "FAIL  warning: $out"; fails=$((fails + 1)); fi
  run "$tmp/order" 'echo forbidden';     t "first block wins → exit 2" 2 "$rc"
  if has "first wins" "$err" && ! has "forbidden command" "$err"; then echo "PASS  first block's reason only"; else echo "FAIL  order: $err"; fails=$((fails + 1)); fi
  run "$tmp/guards" 'TRIPWIRE_SKIP=1 echo forbidden'; t "TRIPWIRE_SKIP=1 one-shot escape" 0 "$rc"
  json='{"tool_input":{"command":"echo forbidden"}}'
  out=$(TRIPWIRE_GUARD_OFF=1 TRIPWIRE_GUARDS_DIR="$tmp/guards" CLAUDE_PROJECT_DIR="$tmp" bash "$self" <<<"$json"); t "TRIPWIRE_GUARD_OFF=1 kill switch" 0 "$?"
  bashbin=$(command -v bash)
  out=$(PATH=/nonexistent TRIPWIRE_GUARDS_DIR="$tmp/guards" CLAUDE_PROJECT_DIR="$tmp" "$bashbin" "$self" <<<"$json"); rc=$?
  if [ "$rc" -eq 0 ] && has "DISARMED" "$out"; then echo "PASS  missing jq → loud DISARM, allow"; else echo "FAIL  disarm: rc=$rc out=$out"; fails=$((fails + 1)); fi

  echo
  echo "--- guard self-tests (tripwire_test) ---"
  seen=""
  for g in "$(dirname "$self")/../examples/guards.d"/*.sh "${CLAUDE_PROJECT_DIR:-$(pwd)}/${TRIPWIRE_GUARDS_DIR:-.agent/guards.d}"/*.sh; do
    [ -f "$g" ] || continue
    real="$(cd "$(dirname "$g")" && pwd)/$(basename "$g")"
    case "$seen" in *"|$real|"*) continue ;; esac
    seen="$seen|$real|"
    grep -q 'tripwire_test' "$g" || continue
    echo "· $(basename "$g")"
    bash -c 'source "$1"; declare -F tripwire_test >/dev/null && tripwire_test' _ "$real" || fails=$((fails + 1))
  done

  rm -rf "$tmp"
  echo
  if [ "$fails" -gt 0 ]; then echo "$fails FAILED"; exit 1; else echo "all tests passed"; exit 0; fi
fi

[ "${TRIPWIRE_GUARD_OFF:-0}" = "1" ] && exit 0

proj="${CLAUDE_PROJECT_DIR:-$(pwd)}"
dir="${TRIPWIRE_GUARDS_DIR:-.agent/guards.d}"
case "$dir" in /*) ;; *) dir="$proj/$dir" ;; esac
[ -d "$dir" ] || exit 0
n=0
for g in "$dir"/*.sh; do [ -f "$g" ] && n=$((n + 1)); done
[ "$n" -gt 0 ] || exit 0

# Fail-open but LOUD: a missing dependency must never disarm the tripwires silently.
if ! command -v jq >/dev/null 2>&1; then
  printf '{"systemMessage":"⚠️ tripwire-guard DISARMED — jq not found; project tripwires (guards.d) are NOT enforced this session."}\n'
  exit 0
fi
input=$(cat 2>/dev/null) || exit 0
cmd=$(jq -r '.tool_input.command // empty' <<<"$input" 2>/dev/null) || exit 0
[ -n "$cmd" ] || exit 0

# user-authorized one-shot escape hatch: prefix the command with TRIPWIRE_SKIP=1
grep -qE '(^|[[:space:]])TRIPWIRE_SKIP=1([[:space:]]|$)' <<<"$cmd" && exit 0

warnings=""
for g in "$dir"/*.sh; do
  [ -f "$g" ] || continue
  out=$(cd "$proj" 2>/dev/null || true; TRIPWIRE_COMMAND="$cmd" TRIPWIRE_INPUT="$input" bash "$g" <<<"$input" 2>&1); rc=$?
  if [ "$rc" -eq 2 ]; then
    echo "${out:-⛔ tripwire-guard: blocked by $(basename "$g") (no reason printed)}" >&2
    exit 2
  elif [ "$rc" -ne 0 ]; then
    warnings="${warnings}${warnings:+ · }$(basename "$g"): ${out:-exit $rc with no message}"
  fi
done
if [ -n "$warnings" ]; then
  jq -cn --arg m "⚠️ tripwire-guard: $warnings" '{systemMessage:$m}' 2>/dev/null || true
fi
exit 0
