# Does multi-model ensemble code review beat a single strong model?

> Deep-research report on the decorrelation premise behind the verify
> external-reviewer panel (tickets 0205/0217). Generated 2026-06-05 via the
> deep-research workflow (16 sources, 76 claims extracted, 25 verified by
> 3-vote adversarial panel, 19 confirmed, 6 killed). Companion to
> [agnostic-reviewer-landscape.md](./agnostic-reviewer-landscape.md), which
> flagged this question as its top open gap.

## Question

Does N>1 decorrelated LLM reviewers measurably beat N=1? What is the optimal
N and the precision cost? Is cross-vendor decorrelation real or illusory given
shared training corpora? Does Linus's Law ("given enough eyes, all bugs are
shallow") transfer from human open-source review to LLM panels?

## Verdict

**Qualified yes to N>1 (small, conditional); strong "mostly illusory" to
cross-vendor decorrelation among strong models; Linus's Law is folklore for
LLM panels.**

### (a) N>1 beats N=1 — but the gain is conditional and modest (HIGH confidence)

- A jury of three small disjoint-family models (Cohere/Anthropic/OpenAI)
  out-correlates a single GPT-4 judge with human ratings (Cohen's kappa
  0.763/0.906/0.867 vs 0.627/0.841/0.830) at ~7-8x lower cost
  (PoLL, Verga et al. [arXiv:2404.18796]).
- Ensembling lifts recall most on hard/imbalanced cases: +34% avg recall on
  imbalanced ReVeal; +18% recall on complex multi-file vulnerabilities
  [arXiv:2509.12629, 2512.12536].
- BUT: ~2-4 F1 points on balanced data, and **negative on simple detection** —
  a 10-LLM ensemble lost to 7 of its own 10 members (its headline gain was vs
  the MEAN member, not the best) [arXiv:2512.12536].

### (b) Optimal N: small panel (2-4); composition dominates size (HIGH confidence)

- A single LLM reviewer has no stable safe operating point (best k=1
  Youden's J < 0.4); prefer "a small, unanimous panel composed of strong
  models over a single judge" [arXiv:2602.18492].
- Every extra unanimous seat is another veto: at k=4-5, FPR stays low but TPR
  compresses — diminishing-then-negative coverage returns.
- "Which models you group together matters, not just the value of k."

### (c) Cross-vendor decorrelation is largely ILLUSORY for strong models (HIGH confidence)

- Kim et al. (ICML 2025, 350+ models): strong models agree ~60% of the time
  when both err (vs ~33% chance) — "larger and more accurate models have
  highly correlated errors, even with distinct architectures and providers"
  [arXiv:2506.07962].
- Turkmen et al. (2026): a top-k ensemble of the strongest models (81% avg
  accuracy) FAILED ("almost all GPT models share the same error pattern")
  while a lower-accuracy (72%) cross-family ensemble succeeded. Measured
  inter-model error correlation rho ~0.55-0.90; there is an
  information-theoretic error floor added seats cannot cross — gains must
  come from REDUCING effective correlation, not adding accurate-but-correlated
  models [arXiv:2602.08003].
- **Design implication: a genuinely different (even weaker) open-weights local
  model is the seat that adds real independence — not a second frontier
  vendor.** This vindicates the llama-server local seat (0207/0217) as the
  scientifically-supported decorrelation play, not the budget option.

### Precision economics: the consensus threshold is the dial (HIGH confidence)

- Sweeping consensus threshold 30%→80%: higher agreement raises precision but
  eliminates true detections made by isolated models (CVE-2009-0747 was found
  by only 2/10 models — killed by a 60% threshold) [arXiv:2512.12536].
- No source quantified alert-fatigue/optimal-N-before-precision-collapse for
  automated PR review specifically; closest proxy is the unanimity
  TPR-compression result.

### What decorrelation DOES reliably buy: bias reduction (HIGH confidence)

- Single-judge self-preference is real: a GPT-4 judge ranked a GPT-4 variant
  at position 2 vs true position 4; "the highest positive delta for each
  model occurs when it is judged by itself" [arXiv:2404.18796].
- A disjoint-family jury hedges per-model blind spots (GPT-4 was the WORST
  judge on fuzzy-string QA) even though it does not buy general
  error-independence. For the harness this maps to: never let the coder's own
  family be the sole gate on its work — which the existing "Sonnet reviews
  Opus" rule only partially achieves.

### (d) Linus's Law: folklore for LLM panels (MEDIUM confidence)

- No source tested it for LLMs, none validated the human original (Raymond,
  Cathedral & Bazaar; Heartbleed counterexample unexamined in this evidence
  set), and the correlated-errors literature actively contradicts the "many
  eyes are independent eyes" assumption it rests on.

## Caveats (load-bearing)

- **Domain mismatch dominates:** almost none of the evidence is frontier
  reviewers voting on code DIFFS in a merge gate. Vulnerability papers
  ensemble 7B-34B open models on classification benchmarks; the
  operating-characteristics paper is text-to-SQL under a unanimity rule;
  the jury paper judges QA correctness. Every transfer to /verify is a
  directionally-consistent extrapolation.
- The two strongest findings (correlated errors; jury-beats-judge) are
  peer-reviewed/canonical (ICML 2025; Cohere PoLL); several others are
  unrefereed 2026 preprints without replication.
- Six claims were killed in verification, including two
  cross-vendor-decorrelation mechanism claims (0-3) — the refuted list is as
  informative as the confirmed one.

## Design consequences for the panel (0205/0217)

1. **Cap the panel at 2-4 seats.** More seats = more veto/noise, not more
   coverage.
2. **Composition rule:** one strong same-family-as-nothing seat (local
   open-weights via llama-server) buys more independence than a second
   frontier vendor. Prefer architecturally/RLHF-distinct over
   leaderboard-strong.
3. **The aggregation rule is an explicit dial** (unanimity = precision,
   isolated-finding = recall); 0205's advisory/verifiable disposition should
   state which it is buying.
4. **Expect ensemble value on complex multi-file changes; expect ~nothing on
   trivial diffs** — gate seat invocation on diff complexity to save
   latency/cost.
5. Single-judge self-preference justifies the panel's existence even where
   error-independence is illusory.

## Open questions

- Does the small-decorrelated-panel result replicate with frontier reviewers
  on actual code diffs? (Untested anywhere.)
- Optimal aggregation rule beyond unanimity (majority, cost-weighted)?
- Can effective error-correlation be deliberately reduced (distinct
  architecture / different RLHF) and at what accuracy cost?

## Key sources

- PoLL jury: https://arxiv.org/pdf/2404.18796 (Verga et al., Cohere)
- Correlated errors: https://arxiv.org/abs/2506.07962 (Kim et al., ICML 2025)
- Error-correlation floor: https://arxiv.org/html/2602.08003 (Turkmen et al.)
- Panel operating characteristics: https://arxiv.org/pdf/2602.18492
- Vulnerability-detection ensembles: https://arxiv.org/html/2509.12629 ·
  https://arxiv.org/pdf/2512.12536
- Multi-role consensus: https://arxiv.org/pdf/2403.14274
