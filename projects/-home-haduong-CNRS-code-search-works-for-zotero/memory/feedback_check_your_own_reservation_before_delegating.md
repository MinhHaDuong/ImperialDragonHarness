---
name: check-your-own-reservation-before-delegating
description: "A doubt named in the morning brief is a five-minute check, not a footnote; launching an executor past it burned an Opus run on 0809 (2026-09-17)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 946223c4-b40b-451a-93e6-9ad66de1a9fa
  modified: 2026-09-17T07:59:47.326Z
---

On 2026-09-17 the morning brief on ticket 0809 carried the exact reservation that
settled it: the acceptance's step 3 asserts on `completed`, a counter that can rise
for work the sitter never admitted. I then launched a detached Opus executor on the
ticket as written. The author had already seen the pause work live; the executor
was killed mid-run after reworking step 3, and nothing was kept. The next day's
rerun of the same script PASSed 0 to 0 where it had FAILed 0 to 4: an ordering
effect, not the regression the ticket described.

**Why:** a reservation the reviewer writes down and then delegates around is the
most expensive kind of unverified claim: it costs the executor's whole run, and the
author's attention when they have to stop it. The author's words: "tu as lancé 809
sur une fausse piste, on brûle des tokens pour rien".

**How to apply:** before `/hunt` or any detached launch, reread the brief's own
caveats. Each one that can be checked by reading a script or running a probe in
minutes gets checked first, and the ticket gets corrected or closed on the result.
Delegate only what survived. Related: [[verify-the-load-bearing-claim]],
[[probe-needs-discriminating-control]], [[no-past-tense-without-a-run]].
