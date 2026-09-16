---
name: Feedback — verify proof dependencies before claiming a lemma is oversized
description: When asked whether a lemma is the minimum needed, read the proof of the theorem that uses it before answering
type: feedback
---

Before claiming that a supporting lemma "proves more than needed", re-read the theorem's proof line by line and identify exactly what is invoked.

**Why:** In this project said the fixed-graph convergence lemma proved "more than needed" for the inter-stage convergence theorem — suggesting Tarski sufficed. This was wrong. The theorem's proof for $\mu_*^{(s)} \leq \mu_*^{(s+1)}$ iterates $H^{(s+1)}$ from a sub-fixed-point and appeals to convergence, which is exactly the lemma's mechanism, not just existence.

**How to apply:** When asked "is this lemma the minimum needed?", trace each line of the downstream proof to its dependencies before answering. Tarski gives existence; constructive convergence proofs give more and are often genuinely used.
