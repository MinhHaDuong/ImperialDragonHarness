---
name: feedback-review-rounds-dont-fix-code
description: "A review-pr loop that keeps finding real defects can still spiral — cap rounds at the orchestrator level and stop once a real blocker is confirmed, rather than trusting the hunt skill's own round limit to self-regulate"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7dbffd44-66ae-4f29-8294-15df4a99ecc2
  modified: 2026-09-01T15:32:03.211Z
---

A detached hunt (ticket 0553, conductor extract shim) ran two full rounds of
`/review-pr`'s five-perspective panel (correctness, scope, consistency, doc
propagation, red team) against real code. Both rounds found genuine,
independently-reproduced concurrency bugs — not review noise: a claim-race
that let two workers silently clobber each other's completion, and a
truncation-detection gap. This was productive work, unlike
[[feedback-executor-gate-loop-stall]]'s stuck-in-a-loop case.

**The cost showed up anyway, in volume rather than stall.** By the time the
orchestrating session noticed, round 3's panel (six fresh agents) had
already launched *before round 2's synthesis had even posted to the PR* —
one round's fix-and-recheck cycle overlapping the next round's fresh attack,
agents cross-messaging each other under mistaken identities ("you are red
team" / "no, I'm doc propagation"), and duplicate task notifications
resending the same finding four and five times. None of this was wrong
individually — each reviewer's work was real — but the aggregate was dozens
of subagent-hours for two bugs neither round actually fixed, because review
rounds verify, they do not write patches.

**Why the hunt skill's own "up to round 3, then escalate" limit didn't
save this:** that limit caps *rounds*, and round 3 had already started
before anyone checked whether round 2's findings even needed more review
or just needed code changed. A limit on count doesn't catch "the marginal
round is adding cost, not information" — that judgement has to come from
whoever is watching, not from the loop itself.

**How to apply:** when a detached hunt's review loop is still running after
a round has *already confirmed the same class of defect twice* across
independent reviewers, that is the signal to intervene — not to wait for
round 3, and not to trust the skill's own cap. Salvage the worktree, stop
the hunt agent and every orphaned review sub-agent it spawned (`ListAgents`
finds them; `TaskStop` each), and convert the finding into a written record
(a PR comment naming the exact defects, a `Ticket-ref:` instead of `Ticket:`
so a routine merge can't auto-close the ticket on the unfinished work) —
then either fix the code yourself or hand it back as a "needs an actual fix,
not another review" ticket. More review rounds were never going to be the
thing that closed a concurrency bug.

Related: [[feedback-executor-gate-loop-stall]] (the stalled-not-spiraling
sibling case), [[feedback-preserve-agent-output]] (salvage before stopping).
