---
name: feedback-red-step-before-editing-callers
description: Delete the dead code first and run the suite before touching callers — a reference manifest and the set of things that break are different sets
metadata: 
  node_type: memory
  type: feedback
  originSessionId: aceca52d-6c71-4a74-ae75-85a9b713e441
  modified: 2026-09-09T16:38:47.671Z
---

When removing code that other code references, delete it **first**, run the full
suite, and let the failures name the callers. Do not build a reference manifest
and edit the callers from it.

**Why:** a textual reference graph lists what *points at* a file. The suite
lists what *breaks without* it. Those are different sets, and the gap is
invisible until something goes red. Removing the nightbeat block on 2026-09-09
turned **six** tests red where a careful `grep`-and-`deps`-graph manifest had
predicted three. The fourth file was `tests/test_fewer_permission_prompts_helper.py`:
its subject had been deleted, but nothing in the repository referenced the test
by the name the sweep searched for, so no manifest could have seen it.

**How to apply:** stage the removal, run the suite before any caller edit, and
treat each failure as the red step for exactly one edit. Record in the ticket
what the run actually caught versus what was predicted — the delta is the
reusable part. Then, when a *guard* is among the casualties because its subject
disappeared, delete the guard with its subject rather than relaxing it: a lens
scanning an empty corpus is green whatever the truth, which is the very defect
the guard existed to prevent (two instances the same day —
`test_model_rightsizing.py`'s workflow-`.js` lens, and six of the seven lenses
in `skill-doctor-survey.py`). See [[feedback_a_test_green_for_an_accidental_reason]]
and [[feedback_verify_each_before_batch_action]].
