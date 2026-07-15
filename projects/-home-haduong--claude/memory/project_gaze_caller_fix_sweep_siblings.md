---
name: project-gaze-caller-fix-sweep-siblings
description: verify-gate and verify-adherence share gaze's fixed hard-refuse-without-arg pattern; left unticketed per the harness cool-down severity floor
metadata:
  type: project
---

PR #649 fixed `/gaze` so the invoking session resolves an ambiguous PR
number from context before spawning the fork, instead of hard-refusing
(see [[feedback_gaze_resolve_pr_number_before_invoking]]). A sweep for the
same anti-pattern found it also in `skills/verify-gate/SKILL.md` and
`skills/verify-adherence/SKILL.md` — both `context: fork`, both carry the
identical "STOP … do NOT infer a task from the environment" directive with
no caller-side resolution guidance, and both are user-invocable standalone
("standalone-callable for debugging").

**Why left unticketed:** pure UX friction in a tooling repo, not a
merge-blocker, state-corruption, or science-repo defect — below the
severity floor set by [[feedback_harness_cooldown_stop_second_order_tooling]]
(2026-07-14, equilibrium reached, second-order tickets no longer licensed).

**How to apply:** if either skill is touched for an unrelated reason, add
the same caller-responsibility paragraph gaze now has (a note that the
invoking session, not the fork, resolves the PR/branch from context or
conversation before invoking). Don't open a ticket solely for this.
