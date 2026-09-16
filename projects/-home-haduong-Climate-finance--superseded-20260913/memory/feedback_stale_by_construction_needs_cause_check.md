---
name: stale-by-construction-needs-cause-check
description: "Producer changed → artifact stale" is a hypothesis; rerun the OLD producer on current inputs to attribute the diff before writing the story
metadata:
  type: feedback
---

Ticket 0610 assumed three tracked artifacts were stale because PR #1272 changed their producers. The execute agent reran the *pre-change* producers against the current corpus and got the new artifacts byte-for-byte: the code change was a latent-risk fix, and the real drift was the committed copies predating the corpus `dvc.lock` pins. The wrong attribution would have hidden a live class — corpus drift also affected `tab_network_limitations.csv`, quoted verbatim to RDJ26561 reviewers (ticket 0625; systematic audit 0641).

**Why:** an artifact diff has at least two candidate causes (code change vs input change); "the producer changed" only proves staleness, not which cause moved the content.

**How to apply:** before characterising a regeneration diff, run the old code on the current data (or the new code on the old data) as the discriminator. Same instinct as [[check-the-detector-first]] and the diagnosis discipline: report the observation, isolate the cause, then write the ticket outcome.
