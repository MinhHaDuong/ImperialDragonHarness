---
name: Project — formal model (progressive graph section) structure
description: Key design decisions established in section 5 (progressive graph discovery)
type: project
---

Two normalization problems, two different solutions:
- **Incoming (prestige/authority)**: normalized score can decrease as new citers are discovered → replaced by absolute thresholded score (S, T parameters)
- **Outgoing (focus)**: reference list is finite and complete once fetched → restrict focus computation to *fetched* works; zero-denominator case handles the rest automatically

**Fetched vs discovered** (not "known" — too ambiguous):
- $\mathcal{F}^{(s)}$ = fetched: reference list retrieved, outgoing row complete
- $\mathcal{W}^{(s)} \setminus \mathcal{F}^{(s)}$ = discovered: appeared as a reference, outgoing row zero
- A discovered work can receive authority (if citers are known) but propagates nothing until fetched

**Theorem structure**:
- *Lemma*: convergence on a fixed observed graph (supporting result)
- *Theorem*: convergence under progressive discovery (the result we want)
- *Proposition*: outgoing-complete fetching policy instantiates the theorem's hypothesis

The lemma is fully needed by the theorem: proving $\mu_*^{(s)} \leq \mu_*^{(s+1)}$ requires iterating $H^{(s+1)}$ from $\mu_*^{(s)}$, which invokes the lemma's convergence argument.

**Why:** Established through a multi-session editorial pass (PRs #19, #20).
**How to apply:** When editing or extending the progressive graph section, respect these distinctions. Don't add vocabulary like "observed work" without specifying fetched or discovered.
