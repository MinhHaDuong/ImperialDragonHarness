---
name: feedback_verify_each_before_batch_action
description: When a sweep buckets multiple items as "the same," verify each individually before committing to a batch action — per-item inspection repeatedly contradicts the batch framing
metadata:
  type: feedback
---

When a sweep or audit groups several items under one label ("these N repos all
have the same stale footprint", "discard all these stale edits"), **inspect each
item before acting on the batch as one.** The shared framing is a hypothesis, not
a finding.

**Why:** In the 2026-06-08 fleet erg-footprint sweep this bit three times in one
session:
- "fuzzy-corpus's edits are stale leftovers, discard them" → per-file diff showed
  they were *migration-in-progress*, more correct than HEAD (mtimes actively
  misled; only diffing content against the binary's own `erg spec` settled it).
- "all three remaining repos have the same stale footprint, do all three" → on
  inspection only Climate_finance matched; aedist was skills-only with an
  *accurate* CLAUDE.md, padme was already clean.
- The advisor caught two scope over-reaches that flowed directly from the batch
  framing (a cherry-fixed verb line; reducing aedist's accurate, deliberately
  maintained docs).

Each wrong batch framing cost a re-ask or a reverted edit. The cheap per-item
check would have pre-empted all of them.

**How to apply:**
- Treat a sweep's bucket as a list of candidates, not a decided action. Before a
  batch edit/delete/commit, open each item and confirm it actually matches.
- Distrust timestamps as evidence of intent — verify by content against the
  authoritative source (the tool's own `spec`/`--help`, the binary, the test),
  not by mtime or by another stale doc.
- An *accurate* artifact that merely carries a stale marker is not stale; don't
  strip maintained content for cosmetic uniformity unless explicitly asked.
- This is the per-item complement to "sweep results are decisions": the sweep
  tells you *where* to look; it does not pre-authorize the *same* action everywhere.

See [[reference_git_erg_adopter_canonical_shape]] (the sweep this came from) and
the harness "Rename/refactor sweeps cover the full logical unit" rule — that says
sweep *widely*; this says verify each hit *before* acting.
