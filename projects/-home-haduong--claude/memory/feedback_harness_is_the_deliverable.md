---
name: harness-is-the-deliverable
description: For a tooling/library project (IDH, git-erg) the harness IS the deliverable — the raid balance rule (deliverable ≥60% / tooling ≤40%) is for science projects and does not apply; don't report "balance debt" for harness work here
metadata:
  type: feedback
---

The raid skill's balance rule throttles tooling to ≤40% so a *science*
project's real output (papers, slides, figures) doesn't get starved by
infrastructure. IDH's north star is "a reusable, science-backed personal
harness" — so skills, rules, tests, and helpers ARE the product, not
overhead. Same for git-erg. Calling a 100%-harness raid "balance debt"
miscategorizes the deliverable as throttled tooling.

**Why:** the ratio reads "deliverable" off the project's north star, not off
a fixed papers/slides list. The category flips with the project type.

**How to apply:** in a tooling/library repo, harness work needs no
deliverable-balance justification and STATE.md should not carry a "balance
debt — all tooling" warning. Apply the ≥60/≤40 ratio only where the north
star names a non-tooling product (manuscripts, data, slides). Author
correction, 2026-06-08. Fixed in skills/raid/SKILL.md § Balance rule.
Related: [[feedback_skills_just_work_no_config_blocks]].
