---
name: review
description: >-
  Conduct architectural reviews, code audits, and deep-dive analyses. Use this skill when asked to:
  review code quality, audit architecture, check for drift from specs, deep review a subsystem,
  security audit, performance audit, or any structured assessment of existing code. Triggers:
  "review", "audit", "deep dive", "check the code", "how healthy is", "architecture assessment",
  "code quality". Results go in .agent/reviews/ — never in .docs/.
---

# Review & Audit

Structured approach for conducting code reviews, architecture audits, and deep-dive analyses. Output
goes in `.agent/reviews/`, not `.docs/` — docs are specs, reviews are point-in-time assessments.

## Output

### File location and naming

```
.agent/reviews/YYMMDD_short_description.md
```

6-digit date prefix (no separators), generated with `date '+%y%m%d'`. Examples:

- `.agent/reviews/260331_scaling_architecture_review.md`
- `.agent/reviews/260401_permission_system_audit.md`

### Document structure

```markdown
# {Review Title}

**Date**: YYYY-MM-DD
**Scope**: what was reviewed (files, packages, subsystems)
**Triggered by**: why this review happened (user request, post-implementation, pre-release)

## Summary

2-3 sentences. Overall health assessment. Key takeaway.

## Findings

### [P0] Critical: {title}

**Location**: `path/to/file.ts:L42`
**Issue**: what's wrong
**Impact**: what breaks or could break
**Fix**: concrete recommendation

### [HIGH] {title}
...

### [MED] {title}
...

### [LOW] {title}
...

## Scores (optional, for broad reviews)

| Area | Score | Notes |
| ---- | ----- | ----- |
| ...  | /10   | ...   |

## Recommendations

Prioritized list of next steps. Reference specific findings.
```

## Severity levels

- **P0 / Critical**: correctness bug, data loss risk, security hole. Fix before release.
- **HIGH**: will cause problems under load, in edge cases, or when scaling. Fix soon.
- **MED**: tech debt, drift from conventions, missing tests. Fix when touching the area.
- **LOW**: style, naming, minor improvements. Note for future.

## How to conduct a review

### 1. Define scope before reading code

Don't start reading files randomly. Decide what you're reviewing:

- Specific subsystem (event sourcing, permissions, SSE)
- Cross-cutting concern (error handling, logging, i18n)
- Spec compliance (code vs `.docs/` spec)
- Security surface (auth, input validation, injection)

### 2. Read the relevant spec first

If the project keeps specs in `.docs/`, read the spec for your review area first (check a
`.docs/README.md` routing table if present). You need to know what the code _should_ do before
judging what it _does_ do.

### 3. Read code systematically

For a subsystem review: start at the entry point (handler, route, command), trace the full flow,
note every deviation from spec or convention. For a cross-cutting audit: grep for the pattern across
the codebase, categorize (correct / incorrect / missing usage), count violations per category.

### 4. Verify findings

Before reporting something as a bug or issue: check if a test covers it; check git blame (was it
intentional?); check if a plan file or open task already addresses it.

### 5. Write actionable findings

Every finding needs a location (file + line) and a concrete fix recommendation. "This area needs
improvement" is not a finding.

## What NOT to do in a review

- Don't fix code during a review — reviews are read-only assessments.
- Don't create plan files — just document findings, let the user decide next steps.
- Don't review things outside your defined scope.
- Don't mark style preferences as HIGH or P0.

## Delegating to review subagents

Delegate the heavy reading to review subagents and aggregate their findings into the
`.agent/reviews/` doc — run them in parallel for a deep review. This plugin bundles:

- **spec-cross-checker** — one-feature drift between docs and code (lighter than a full review);
- **semantic-reviewer** — a lifecycle/error-handling/cleanup/cast checklist for refactors;
- **wireframe-vs-code** — functional gaps between a wireframe and its implementation;
- **doc-auditor** — project-wide drift audit of binding docs against code reality;
- **isolation-reviewer** — adversarial multi-tenant isolation review of a diff or module.

If your project provides its own agents for these roles (e.g. a pattern/style verifier), prefer
the project's wiring.

## Preparing follow-up work

After a review the user may ask you to prepare follow-up work for the findings. That's a separate
step — route it through your project's task/plan/loop workflow. The review itself stays clean: just
findings and recommendations.
