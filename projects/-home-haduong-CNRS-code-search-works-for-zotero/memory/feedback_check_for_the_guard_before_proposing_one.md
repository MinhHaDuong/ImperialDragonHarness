---
name: feedback_check_for_the_guard_before_proposing_one
description: Measuring a hazard is not measuring whether it is already guarded; grep the guards before reporting anything as unprotected
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7edca1b9-893f-4ea5-9284-d24817150788
  modified: 2026-09-02T15:47:13.211Z
---

Measuring a document pair and finding 24 of 24 requirement sentences copied
verbatim proves the copy exists. It says nothing about whether anything watches
it. On 2026-09-02 I read that measurement as evidence of an unguarded hazard,
told the author "the promise column stays unguarded and a reader carries that",
and started building a check. `check_coverage` in `bench/check_progress.py`
already compared every promise cell to the sheet and already carried a comment
explaining the exact reasoning I was reinventing. A 100% verbatim result was
evidence of a working guard, read backwards.

**Why:** the wrong verdict here is expensive in both directions. It nearly spent
the author's guard budget (see [[feedback_guard_budget_is_net_negative]]) on
something that existed, and a report of "unguarded" invites a decision the facts
do not support.

**How to apply:** before describing anything as unguarded, grep the guard
sources for the artifact's name and read what the matching check does. Then
prove the verdict by making the state red — mutate the artifact and watch the
gate. Do that in a throwaway `git worktree`, never in the shared checkout, and
run the control on both sides of a two-document comparison: drift can start in
either file, and a check that only watches one is a different check from the one
you think you have.

The general shape: an absence of protection is a negative finding, and a
negative finding needs a positive control before it is reported. Same rule as
[[feedback_probe_needs_discriminating_control]], applied to the guards
themselves rather than to the code they guard.
