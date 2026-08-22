---
name: feedback_a_null_result_needs_a_positive_control
description: A probe that finds nothing has said nothing until it demonstrates it would have found something; run it against a known-positive case first
metadata:
  type: feedback
---

A probe that returns zero is reporting one of two things and cannot tell you
which: the phenomenon is absent, or the probe cannot see it. Only a case known
to be positive separates them.

zoteus-fts5 ticket 0007, 2026-08-21/22. Three probes over ten hours counted
`.zotero-sdt-cache` files and found none, which was read as "Zotero does not
produce structure packs on this build". The artifact honestly flagged the gap —
"NO POSITIVE CONTROL. Nothing here shows the probe would find a pack if one
existed" — and the conclusion drifted toward a verdict anyway, because three
independent zeros feel like evidence. They are one zero, measured three times.

The fourth probe ran after the author opened two PDFs in Zotero's reader. Two
packs appeared within a minute, for exactly those two items, and
`.zotero-reader-state` appeared beside them: the probe demonstrably saw the path
it was testing. Extraction never triggers SDT; the reader always does. The
recorded conclusion had been wrong in its implication for a day.

**Why the honest caveat was not enough.** Writing "this has no positive control"
buys accuracy in the artifact and does not stop the finding from being used as
though it did. The ticket said "extraction runs, SDT does not, so structure-aware
chunking is a future option" — accurate about extraction, and read by every later
reader as a verdict on SDT.

**How to apply.** Before reporting a null result, name what a positive would look
like and produce one: a deliberately broken fixture, the state while the
phenomenon is live, a mock that lies in the right direction. If the positive case
needs a human action the tooling cannot perform, that is not a reason to report
the null — it is the finding, and it should be stated as an open question with
the one experiment named. Distinguish in the prose between "this path does not
cause it" and "nothing causes it"; the first is what a null probe can support.

Related: [[feedback_gate_must_bite_before_trusted]],
[[feedback_agent_reported_numbers_need_artifacts]].
