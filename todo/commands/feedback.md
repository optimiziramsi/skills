---
description: >-
  Process the user's .todo inbox into the agent-owned .agent/FEEDBACK.md ledger and work the items
  now (runs the feedback skill)
disable-model-invocation: true
---

Invoke the `feedback` skill via the Skill tool and follow its SKILL.md steps exactly. This wrapper
carries no logic — the skill is the single source of the steps.

Arguments: $ARGUMENTS
