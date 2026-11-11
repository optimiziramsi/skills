#!/usr/bin/env python3
"""UserPromptSubmit — inject the code-first contract when the turn is code-first (only the
code-first part; the output contract itself is the `reporting` plugin's).

Opt-in, so a design or architecture session is not told to write code. The contract is printed:
  - for the rest of the session once a prompt invokes the idea command (`/idea …` or
    `/code-first:idea …`);
  - for one prompt that matches CODE_FIRST_TRIGGER_PATTERN (default: propose / proposal / sketch);
  - on every prompt under CODE_FIRST_INJECT=always.
Any other prompt prints nothing.

Text: first hit wins, project-relative — $CODE_FIRST_CONTRACT_FILE → .agent/code-first.md →
.claude/code-first.md → the shipped hooks/code-first-reminder.txt; `{{BASE}}`, `{{PREFIX}}`,
`{{SURFACE}}`, `{{TAG}}` are rendered from env. A broken override prints a visible DISARMED line.

Off: CODE_FIRST_OFF=1
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _codefirst as cf  # noqa: E402


def main():
    if cf.off():
        return
    data = cf.hookio.payload()
    if not cf.code_first_turn(data.get("session_id"), data.get("prompt"), mark=True):
        return
    text, warning = cf.contract(cf.hookio.project_dir(data))
    print(f"⚠️ code-first DISARMED — {warning}." if warning else text)


if __name__ == "__main__":
    cf.hookio.guard(main)
