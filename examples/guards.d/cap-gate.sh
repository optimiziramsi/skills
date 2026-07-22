#!/usr/bin/env bash
# cap-gate — tripwire-guard project guard, BLOCKING: refuse a `git commit` while the instruction
# surface is over cap. The ENFORCEMENT complement to the caps.sh hook (opsi), which
# only NUDGES at SessionStart/Stop — copy this into `.agent/guards.d/` when a repo wants bloat kept
# out of history outright. Opt-in example; not wired by default.
#
# Mirrors caps.sh's house defaults; every cap is env-overridable (CAP_CLAUDE, CAP_AGENTS,
# CAP_HANDOFF, CAP_CHANGELOG, CAP_LESSONS_INDEX, CAP_SKILL, CAP_AGENT, CAP_RULE, CAP_COMMAND,
# CAP_LESSON). Only files that EXIST are checked → safe no-op in any repo. Fails open. Escape hatch:
# prefix the commit with CAP_GATE_OFF=1 (or the tripwire-wide TRIPWIRE_SKIP=1).
# Contract: reason on stdout + exit 2 = BLOCK, exit 0 = allow. Self-test: bash cap-gate.sh --test
set -u

# `git [-C dir | -c cfg | --flag]* commit` — anchored like the other guards (no \b, BSD-safe)
CG_COMMIT='(^|[;&|(]|\$\()[[:space:]]*git([[:space:]]+(-[Cc][[:space:]]+[^[:space:]]+|--?[A-Za-z][A-Za-z-]*))*[[:space:]]+commit([[:space:]]|$)'

_cg_size() { wc -c < "$1" 2>/dev/null | tr -d ' '; }

cap_breaches() { # prints "path SIZEc > CAPc" for each existing over-cap file
  local entry p cap sz
  local file_caps=(
    "CLAUDE.md:${CAP_CLAUDE:-6000}"
    "AGENTS.md:${CAP_AGENTS:-6000}"
    ".agent/handoff.md:${CAP_HANDOFF:-4000}"
    ".agent/instructions-changelog.md:${CAP_CHANGELOG:-8000}"
    ".agent/lessons/README.md:${CAP_LESSONS_INDEX:-8000}"
  )
  for entry in "${file_caps[@]}"; do
    p=${entry%%:*}; cap=${entry##*:}
    [ -f "$p" ] || continue
    sz=$(_cg_size "$p"); [ -n "${sz:-}" ] && [ "$sz" -gt "$cap" ] && echo "$p ${sz}c > ${cap}c"
  done
  _cg_glob() { # $1=glob  $2=cap  $3=skip-basename (optional)
    local q s
    for q in $1; do
      [ -f "$q" ] || continue
      [ -n "${3:-}" ] && [ "$(basename "$q")" = "$3" ] && continue
      s=$(_cg_size "$q"); [ -n "${s:-}" ] && [ "$s" -gt "$2" ] && echo "$q ${s}c > ${2}c"
    done
  }
  _cg_glob ".claude/skills/*/SKILL.md" "${CAP_SKILL:-9000}"
  _cg_glob ".claude/agents/*.md"       "${CAP_AGENT:-4000}"
  _cg_glob ".claude/rules/*.md"        "${CAP_RULE:-2000}"
  _cg_glob ".claude/commands/*.md"     "${CAP_COMMAND:-800}"
  _cg_glob ".agent/lessons/*.md"       "${CAP_LESSON:-4000}" "README.md"
}

cap_gate() { # $1 = command string; returns 2 (block) or 0 (clean)
  [ "${CAP_GATE_OFF:-0}" = "1" ] && return 0
  grep -qE "$CG_COMMIT" <<<"${1:-}" || return 0
  local breaches; breaches=$(cap_breaches)
  [ -z "$breaches" ] && return 0
  echo "⛔ tripwire [cap-gate]: instruction surface over cap — compact before committing (merge → route → tighten → retire), do NOT raise the cap:"
  while IFS= read -r b; do [ -n "$b" ] && echo "  • $b"; done <<<"$breaches"
  return 2
}

tripwire_test() {
  local fails=0 tmp out
  t() { if [ "$3" = "$2" ]; then echo "PASS  $1"; else echo "FAIL  $1 (want $2, got $3)"; fails=$((fails + 1)); fi; }
  tmp=$(mktemp -d)

  ( cd "$tmp" && cap_gate 'git commit -m x' >/dev/null ); t "clean surface → commit allowed" 0 "$?"

  head -c 7000 /dev/zero | tr '\0' x > "$tmp/CLAUDE.md"
  ( cd "$tmp" && cap_gate 'git commit -m x' >/dev/null ); t "oversized CLAUDE.md → commit blocked" 2 "$?"
  ( cd "$tmp" && cap_gate 'git status' >/dev/null );      t "non-commit command → allowed" 0 "$?"
  ( cd "$tmp" && cap_gate 'git -C . commit -m x' >/dev/null ); t "git -C … commit → still gated" 2 "$?"
  ( cd "$tmp" && CAP_CLAUDE=8000 cap_gate 'git commit -m x' >/dev/null ); t "CAP_CLAUDE override respected" 0 "$?"
  ( cd "$tmp" && CAP_GATE_OFF=1 cap_gate 'git commit -m x' >/dev/null );  t "CAP_GATE_OFF=1 escape" 0 "$?"
  out=$( cd "$tmp" && cap_gate 'git commit -m x' 2>&1 )
  case "$out" in *CLAUDE.md*) echo "PASS  block reason names the breaching file" ;;
                 *) echo "FAIL  block reason: $out"; fails=$((fails + 1)) ;; esac

  rm -rf "$tmp"
  return "$fails"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ "${1:-}" = "--test" ]; then tripwire_test; exit $?; fi
  cap_gate "${TRIPWIRE_COMMAND:-}"
  exit $?
fi
