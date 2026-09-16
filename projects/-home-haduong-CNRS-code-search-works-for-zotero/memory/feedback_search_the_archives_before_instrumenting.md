---
name: feedback-search-the-archives-before-instrumenting
description: "Before instrumenting a symptom, grep verification/ and closed tickets for its vocabulary — a correct conclusion reached from live data can still be an eleven-day-old rediscovery"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3cdf4883-8bf7-4ffa-8060-2e328114969d
  modified: 2026-09-16T11:14:10.572Z
---

A symptom that looks fresh is not evidence that nobody has studied it. Before
building a probe or reading upstream source for a behaviour, grep
`verification/`, `tickets/` **and `tickets/closed/`** for the symptom's
vocabulary — the number, the stage name, the function name.

**Why:** on 2026-09-16 the AR6 extraction plateaued at 90 %. I read the live
journal, then Zotero's shipped `worker.js`, and established that
`reportPageProgress` caps the page phase at 90, that the gap is the citation and
reference-application stage, and that it resolves normally. All correct, and all
of it had been written on 2026-09-05: `verification/SDT-PALGRAVE-AUDIT.md` maps
the 90/95 boundary, and `SDT-PALGRAVE-PHASES.md` already calls it "a healthy
long progress gap, not a hung job" in those words. The analysis ticket 0678 was
closed and the patch ticket **0679 was open the whole time**, naming the
O(B × R) `isReferenceBlock` scan that lives in that stage. The author had to say
"regarde les archives" before I looked.

The cost was not a wrong answer. It was a day's rediscovery, and an incident
note that would have published an eleven-day-old finding as its own if he had
not intervened — which misrepresents where the knowledge came from and buries
the ticket that was already waiting for work.

**How to apply:** the first move on a symptom is a search, not a probe. Search
the symptom's *numbers* and *stage names*, not just its prose: `grep -rliE 'N \*
M|quadrati|O\(n\^?2\)'` found 0679 in one command, where "reference linking"
would not have. Include `tickets/closed/` — the analysis that explains a live
symptom is usually closed while its patch ticket stays open. When the search
does hit, cite the prior work in whatever you write and say which part is new;
a second independent confirmation on a bigger case is worth recording, but only
as that.

Related: [[feedback_search_the_fork_before_claiming_absence]], which governs
claiming a thing is absent; this one governs claiming a thing is new.
