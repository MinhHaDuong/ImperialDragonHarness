---
name: feedback_deposit_prose_is_unguarded
description: "The revision documents describing the Zenodo deposit to the editor sit outside every check, so a retired product keeps being promised in prose"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-27T19:15:49.472Z
---

The deposit has a guarded half and an unguarded half, and the split is not where
you would guess.

**Guarded:** `tests/test_datapaper_archive_layout.py::PRODUCTS` pins the product
list across the build script, the archive README, and `data-paper.qmd`.
`TestDepositCountsTrackTheCorpus` pins the hand-pasted *counts* in the README and
the ed04 runbook to the generated vars.

**Unguarded:** the `revision-rdj26561/` correspondence — `response-letter.md`,
`summary-of-revisions.md`, and the ed04 upload runbook, *including the record
description the author pastes into Zenodo*. Filenames there are checked by
nothing.

So when ticket 0354 retired `codebook.md`, three submission documents kept
promising the editor a file the deposit no longer shipped, and only a manual grep
found them. Ticket 0403 files the standing guard.

**How to apply:** any change to what `data/products/` contains needs a manual
sweep of `deliverables/data-paper/revision-rdj26561/*.md` until 0403 lands. Treat
the ed04 record description as production text, not notes — it is pasted into the
live Zenodo record. Fix factual claims there directly; leave wording in
`response-letter.md` and `summary-of-revisions.md` to the author (they carry a
sign-off line), and report rather than expand submission prose.

**Why:** these documents are the ones a human actually reads at the journal.
Drift there costs credibility in a way a stale test comment does not
(→ [[feedback_filename_keyed_guards_collide_at_merge]]).
