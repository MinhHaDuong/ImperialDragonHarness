---
name: feedback-the-tickets-own-test-needs-a-control
description: Run the test a ticket specifies against the defect BEFORE building it — twice in one session the specified guard was green on the very tree whose defect it existed to catch
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3a847be0-f9fa-412a-ae82-7b3dd03e1c6d
  modified: 2026-08-29T14:14:37.799Z
---

A ticket's `## Test` section is written from a mental model of the defect, by
someone who has not yet run it. Treat it as a hypothesis, not a spec. Execute
the specified check against the unfixed tree first. If it comes back green, the
mental model was wrong and building it as written ships ceremony: a guard that
passes today, passes tomorrow, and never fires.

**Why.** Raid 50/52/54 on search-works-for-zotero (2026-08-29), three
specification-chain tickets. Two of the three specified a test with no positive
control, and neither was obviously wrong on the page.

Ticket 0054 asked for "a check that fails when the same sentence, normalised,
appears in more than one chain document", and said explicitly *red first: it
must fire on the current tree*. Measured, it found **nothing**. All five
documents restated the authority chain in their own words — "Authority works
like this…", "Ratifications are recorded in…", "The author's rulings land here
first…". Paraphrase duplication, not string duplication. The ticket's own
red-first requirement was unsatisfiable by its own specified mechanism, and
only running it revealed that.

Ticket 0050 asked for a grep for lowercase modal verbs inside R-item and gate
lines. That one *does* fire — on REQUIREMENTS.md. But DESIGN §2.9, half the
ticket's own named scope, contained **zero modal verbs of any kind**, so a
lowercase-modal grep reports the budgets section clean while every budget in it
is unforced. The check would have been green precisely where the defect was
total.

**The shape.** Both failures are the same: the specified test keys on a
*symptom the author imagined* (a copied sentence, a lowercase "must") rather
than on the *defect* (a fact stated in five places, a requirement with no
declared force). Where the defect is present but the symptom absent, the test
is silent — the "all-clear indistinguishable from I-could-not-look" shape, one
level up from where the harness rules usually name it: not in the check's
verdict, but in whether the check can reach the thing at all.

**How to apply.** Before implementing a ticket's specified test, materialise the
pre-fix tree (`git show <ref>:<path>` into a scratch dir, or `git archive`) and
run the check against it. Record the count. If it is zero, say so in the report
and propose the mechanism that does fire, with its measured count — that is a
finding, not a deviation. Both replacements here were argued from the measured
zero and both landed: 10 hits and 30 hits respectively on the pre-change tree,
each pinned by a test whose fixture is the *real* pre-fix sentence rather than
an invented one. An invented fixture proves the regex compiles; the real
sentence proves the guard would have caught the thing that happened.

**Corollary on scope, same session.** Scope a guard to the region where the
defect lives, not the whole file. The chain-dedup guard initially read whole
documents and fired on a *ratified* DECISIONS.md entry saying CONSTRAINTS.md and
DESIGN.md "are edited to match" about one specific ruling — the chain working
correctly. Worse than noise: DECISIONS.md is append-only, so a guard able to
demand an edit to a ratified entry is wrong however politely it complains, and
the only fixes available are editing the record or disabling the guard.
Narrowing it to each document's head removed the class, and re-running the
pre-change control confirmed the silence was not bought by looking nowhere —
still ten hits. **Always re-run the positive control after narrowing a scope.**

Related: [[feedback-probe-needs-discriminating-control]] (a probe's control must
discriminate), [[feedback-a-move-can-leave-the-gate]] (a gate's scope list fails
asymmetrically), [[feedback-guard-the-silent-failure-first]].
