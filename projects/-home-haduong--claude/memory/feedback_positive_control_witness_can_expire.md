---
name: feedback_positive_control_witness_can_expire
description: "A positive control only validates a scan while its witness is still inside the population being searched; a witness that merged, closed or moved makes the control silently stop firing"
metadata:
  type: feedback
---

Filing ticket 0934 on 2026-09-16, the cross-PR ID collision scan from
`tickets/AGENTS.md` returned empty for the new ID — and so did its positive
control. The control searched open PRs for ticket 0933, which had been the
witness ten minutes earlier and had merged in between. A merged PR is not an
open PR, so the loop found nothing, correctly, and proved nothing.

Both outputs were empty and they meant opposite things: the query's emptiness
was the answer, the control's emptiness was the instrument failing to be an
instrument. Nothing in the output distinguished them. Re-running with a witness
still in the population — a path present in the one PR that was open — made the
control fire, and only then did the query's empty result carry information.

**Why:** a positive control is a claim about the *present* population, not a
property of the probe. The harness already knows that a scan whose all-clear is
indistinguishable from "I could not look" is not a check
([[feedback_positive_control_validates_the_detector_not_the_enumerator]] covers
the sibling failure, where the probe recognises a hit but never saw the whole
population). This is the third variant: the probe works, the denominator is
whole, and the witness has left. It bites hardest in a session that is itself
merging things, because the act of making progress destroys the witnesses.

**How to apply:** pick the witness from the population as it is at the moment
you run the control, not from memory of what was there. Prefer a witness you
just observed in that population over one you filed earlier in the session, and
prefer one you are not about to change. When the control comes back empty, treat
that as a broken instrument and fix it before reading the query at all — never
as weak evidence that the query is also empty. Related:
[[feedback_measure_whether_a_guard_ever_fired]].
