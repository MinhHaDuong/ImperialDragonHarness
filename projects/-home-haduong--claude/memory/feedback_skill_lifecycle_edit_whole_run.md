---
name: feedback_skill_lifecycle_edit_whole_run
description: "Adding an exit/cleanup step to a multi-step skill — place it at the true run-end and account for every commit/side-effect between, not at the step where the symptom first appears"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d183497e-90d0-4c82-a388-c4635c140031
---

When editing a multi-step skill to add a lifecycle guard (an exit contract,
cleanup, or state restore), reason about the **whole run's control flow**, not
the single step where the problem surfaces.

On IDH 0247 I put dream's push-or-restore exit inside step 8 (where the branch
is created), but the run continues to a **second commit at step 12** (the
promotion pass). Consequences the placement caused: the step-8 PR missed the
promotion commit; a death anywhere in steps 9–13 still stranded the checkout;
and the step-8 success path left the checkout off main and then tripped its own
probe. The multi-agent `/gaze` review caught all three — a single-step edit view
did not.

**How to apply:** for any "do X at the end of the run" skill edit, find the
*actual* last side-effecting step and place the guard after it; trace every
commit / branch / state mutation between the guard's naive position and the true
end. Run `/gaze` on skill-control-flow changes specifically — independent
reviewers reason across the whole run and catch structure a local edit misses.
Related: [[feedback_dont_pre_close_ticket_in_execution]].
