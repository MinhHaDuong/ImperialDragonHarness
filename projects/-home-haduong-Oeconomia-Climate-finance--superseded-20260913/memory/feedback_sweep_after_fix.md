---
name: Sweep codebase after fixes
description: After fixing a pattern violation, sweep the codebase for similar instances and ticket them
type: feedback
---

After completing a fix for a code pattern issue (e.g., god module split, naming violation), sweep the entire codebase for the same anti-pattern before celebrating.

**Why:** The genealogy split (#542) revealed 4 more scripts with the same issue. The user expects systematic cleanup, not one-off fixes. Existing audits (like `docs/audit-multi-output-scripts.md`) can accelerate the sweep.

**How to apply:** During celebration (or end-of-session), review today's fixes and grep/audit for similar patterns. File tickets for all instances found. This should become a standard step in the celebrate skill.
