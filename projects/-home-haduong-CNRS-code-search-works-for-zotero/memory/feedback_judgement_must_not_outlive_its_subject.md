---
name: feedback-judgement-must-not-outlive-its-subject
description: "A status page whose verdicts are read rather than run cannot be recomputed when its subject moves — so invalidate it, and say per row how each verdict was established"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8e6ff355-1eee-4380-9f1c-3429c483a129
  modified: 2026-08-30T06:28:48.386Z
---

Built `spec/README.md` for search-works-for-zotero on 2026-08-29: where each of
28 requirements stands against a named upstream release. The author asked two
questions that each exposed a defect, and both are general to any status
artifact.

**"Is it auto-recomputed on upstream move?"** It was not, and it could not be —
the verdicts are judgements made by reading source, not measurements. But the
guard had never opened the file declaring the reviewed baseline, so four sites
named a release with nothing tying them to it. The failure mode: someone
reviews a new release, bumps the baseline, and the page keeps answering for the
release it never saw, *with every bar still arithmetically perfect* — which is
why no other check would catch it. Fix: a guard cannot recompute a judgement,
so make it refuse to let one outlive its subject. Default-deny on the release
named, fail the build the moment the declared baseline names a release the page
does not. Two tripwires in sequence — one for "upstream moved", one for "the
baseline was bumped and the page did not follow".

**"I thought requirements were objectively testable."** They were, and the
sheet's own RFC 2119 pass had already made them 40 enumerable MUST clauses. The
softness was mine: one `partial` token covered both "some clauses fail, with
ten tests demonstrating it" (R12) and "the mechanism landed but nobody checked"
(R11). Those are opposite epistemic states and they had the same glyph.

**Why:** a status page's verdicts and its arithmetic get read as one kind of
claim. Recomputed bars look exactly like measured ones, and a reader — the
author included — will assume a test suite behind them. Conflating "half-holds"
with "unchecked" then hides how little is actually known, and the page's
own hedge at the bottom ("the guard cannot check that a row is honest") is too
far from the numbers to do any work.

**How to apply:** put provenance beside the numbers, not in a footnote. Add an
evidence axis orthogonal to status — here `measured` (something ran), `code`
(the source was opened at the reviewed baseline), `inferred` (neither) — and
make the guard recompute its tally like any other count. The distribution *is*
the honest answer: 6 measured, 14 read, 8 inferred, out of 28. Say plainly that
a soft verdict is the harness's fault and never the specification's, and name
the ticket that would convert the column from argued to derived. When a
compound requirement is graded as one atom, that atom is where judgement hides
— the clause, not the requirement, is the unit that makes a status a count.
**Instance, 2026-08-30 (SYNC.md, PR #84):** the same defect in table form. A
sync pass dates itself — the 2026-08-29 update stopped two hours before the
day did, so issue #34 (filed 16:44) had no row. Worse, two rows (#24, #26)
still read "open and unanswered" although a *sibling row in the same table*
described the v1.10.0 sweep that closed them: the pass that recorded the sweep
updated the rows it came to edit and left the others answering for the day
before. When touching a status table, grep it for every live-state claim
("open", "unanswered", "in flight") and re-verify each against the forge —
the stale rows are never the ones you came for.

**Instance, 2026-09-02 (PR #212): the decay window was eleven minutes.** The PR
argued a REJECT on reusing Zotero core's #6012 inference runtime, and supported it
with a currency claim about that PR's state. The upstream head **force-pushed
eleven minutes after our PR opened**, falsifying the claim before any reviewer
read it. The verdict survived — `ml.js` is byte-identical across both heads, so
the REJECT rests on content, not on currency — but the supporting sentence was
false as written.

A forge reading (a head SHA, an open/closed state, a CI status) is an
*instantaneous measurement*, and prose has no expiry field. Two habits, both
cheap: **pin the SHA in the sentence** so the claim is scoped to what was actually
observed ("at <sha>, ml.js is …") rather than to a moving ref, and **separate the
load-bearing evidence from the currency note**, so that when currency decays the
verdict does not have to be re-argued. Here the separation existed by luck; had
the REJECT rested on "#6012 is still open", eleven minutes would have voided it.

Related: [[feedback-a-move-can-leave-the-gate]],
[[feedback-verify-the-load-bearing-claim]].
