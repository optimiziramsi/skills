#!/usr/bin/env python3
"""UserPromptSubmit — inject the code-first contract (only the code-first part; the output
contract itself is the `reporting` plugin's).

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
    text, warning = cf.contract(cf.hookio.project_dir(cf.hookio.payload()))
    print(f"⚠️ code-first DISARMED — {warning}." if warning else text)


if __name__ == "__main__":
    cf.hookio.guard(main)
