---
name: Fuzzy corpus methodology — SWOT, not ranking
description: In the fuzzy-corpus paper and its Climate_finance application, frame validation as SWOT characterization, never as "method X beats method Y". LLM outputs, reranker scores, PageRank, column-filter membership are all fuzzy signals with their own biases — none is ground truth.
type: feedback
originSessionId: a1e1fc5e-956b-4f8a-bca4-4e2b976f870b
---
When working on the `fuzzy-corpus` repository's application to
`Climate_finance`, the validation framing is **SWOT characterization of
the fuzzy snowballing method**, not comparison against a ground truth.

**Why:** User (the paper's author) stated explicitly: *"Attention le LLM
c'est pas un ground truth. Dejà faut voir comment il a été prompté, et
puis c'est vraiment une affaire floue. Il s'agit pas de dire telle
méthode est mieux mais de comprendre si ca marche, a quelles conditions,
ses points forts et ses points faibles. SWOT"*. The LLM outputs in
`llm_relevance_cache.csv` and `llm_audit.csv` were produced under a
prompt we have not audited, on a specific corpus, with their own biases.
Treating them as ground truth measures alignment with one particular
fuzzy signal, not method quality.

**How to apply:**

- Never write "fuzzy beats X" or "recovers Y % of Z" as a headline claim.
- Never compute "precision / recall / F1" where a non-audited signal is
  the ground truth.
- WP7 (and any label-based validation) is a **characterization study**:
  Strengths, Weaknesses, Opportunities, Threats of the fuzzy method.
- All signals (fuzzy µ*, personalized PageRank, LLM score, reranker
  score, HITL labels, column-filter membership, semantic similarity)
  are treated as **co-equal fuzzy views** on the same corpus.
- Deliverables are: agreement matrices, correlation structure,
  population of disagreement (where signals diverge), conditions under
  which fuzzy behaves well or poorly.
- Preflight's use of PR/column-F1 ratio (check b) is only a heuristic
  sanity check on noise floor, not a method-ranking claim.
