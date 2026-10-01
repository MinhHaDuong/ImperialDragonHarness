---
name: feedback_single_standard_pooled_screen
description: "Pool every source raw, then apply the inclusion rule once to everything; never add records screened by one rule to a corpus filtered by another"
metadata:
  node_type: memory
  type: feedback
  originSessionId: defcd2ff-c1d3-4c08-b691-d9c570f60034
  modified: 2026-09-29T16:01:41.738Z
---

When new records are harvested for a review, pool them with the raw catalogue and run the review's inclusion rule once over the whole pool. Do not bolt screened additions onto an already-filtered corpus.

**Why:** on 2026-09-29 I had screened the REL "Sud et langues" candidates against the international-climate-finance (ICF) rule while the v2 `refined_works` corpus had passed a broad topical filter (a reranker score, citation isolation, no-abstract rules). The author saw it at once: "we are adding filtered records to a v2 of raw records?" Measured on the 489 works the v2 filters had removed and the new search re-found: 122 are ICF after review (`llm_irrelevant` 45 of 178, `citation_isolated_old` 61 of 180). The flag named `llm_irrelevant` is in practice a reranker cut (bge-reranker-v2-m3), not an LLM judgment.

**How to apply:**
- Judgments (labels, adjudications, model votes) go in their own append-only table keyed by work and stage, never in a regenerable flag column; the review's view is derived by join (ticket 1655). `refined_works` stays pinned for the other deliverables.
- Old flags stay as information beside the new label; they do not filter.
- A PRISMA flow is simplest with one pool and one screen: state the automation tools, their versions, prompts and agreement with the reference judge.
- See tickets 1655 and 1656 (archive path, sentinel classes) and [[feedback_check_for_existing_library]].
