---
name: feedback-paraphrase-drifts-toward-the-argument
description: "A quote reproduced from a research summary, not from the source, drifts toward whatever the citing argument needs — verify verbatim before it decides anything."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6251382b-c701-4305-92b9-b5c811ec201a
  modified: 2026-09-16T16:36:14.126Z
---

A spec sentence quoted into ticket 0810 read *"Other components, such as commands, hooks, and agents, remain with clients."* The real sentence was *"Other proposed component types — such as commands, hooks, agents, **rules**, and LSP servers — remain too client-specific for a stable portable contract and are outside the v1 format **until their formats converge**."*

Three differences, all pointing the same way: two omitted categories, one of them (`rules`) a layer the argument was about; a stated reason dropped; and a provisional exclusion rendered as a permanent one. The paraphrase was not random noise — every distortion strengthened the conclusion being argued for. The quote came from a single research pass that had itself flagged secondary sources, and it was reproduced without re-fetching.

**Why:** a quotation is the one form of evidence a reader cannot audit from the text alone; it converts "a summary said so" into "the source says so" while hiding the conversion. Distortions travel in the direction of the argument because that is the direction the summarizer was already facing, so the error is systematic rather than random and will not average out across several paraphrases.

**How to apply:** when a quotation is load-bearing — when an argument or a decision rests on the source having said *that* — fetch the primary text and compare word for word before it lands anywhere durable. A research agent's report is a pointer to a source, never a substitute for it. Flag the specific sentence for verification when commissioning the check, rather than asking for the claims in general: the sentence is what a second pass can actually falsify.

Corollary, found the same day and separately confirmed by four reviewers: **correcting the ticket is not correcting the pull request.** The body still carried the disproven version after the file was fixed, and under a `--merge` method that text freezes into the merge commit, where it outlives the correction. Fix the artifact and its description in the same pass, and read the description back.

Related: [[feedback-a-test-green-for-an-accidental-reason]], [[feedback-positive-control-validates-the-detector-not-the-enumerator]].
