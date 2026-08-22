---
name: feedback_invisible_bias_in_both_arms
description: "A bias identical in both arms of a comparison cannot be seen in the difference, yet still destroys the sensitivity the comparison was built for"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 67eecdb2-7185-4e46-9b59-8b00cc04acd7
  modified: 2026-08-21T23:52:26.032Z
---

The usual worry about a benchmark bias is that it favours one side. The harder
case favours **both sides equally**: it then cancels out of every difference,
looks like nothing, and quietly consumes the headroom the measurement needed to
detect the effect under test.

zoteus-fts5 ticket 0008 (2026-08-22). A recall harness drew its query vectors at
random from the indexed corpus and left them in the index. Every ranking
therefore began with the probe retrieving *itself* — cosine 1,0, Hamming
distance 0 — in the exact arm and in the approximate arm alike. The bias
inflated both recalls by up to 1/topK and cancelled in their ratio, so no
comparison of the two columns could reveal it. What it destroyed was the
sensitivity: the driver existed to detect whether zero-thresholded binary
quantization degrades on real embeddings, and a guaranteed hit at rank 1 is
precisely where such a degradation would first show. A review seat caught it
before the run's numbers landed anywhere.

The remedy is leave-one-out: exclude the probe from its own candidate set, in
every arm.

**Why:** the reflex check on a benchmark is "does this favour the thing I want
to win?" A symmetric bias passes that check. It has to be found by asking a
different question — *what would the effect look like, and could this design
show it?*

**How to apply:** when the probes are drawn from the population being searched,
exclude each probe from its own result set. More generally, before trusting a
comparison, ask what a *real* effect would look like in it and whether anything
in the setup guarantees a floor under both arms. Report the structural
properties that make the task easier than the real one rather than filtering
them away — in the same run, 52% of a probe's true neighbours were sibling
chunks of its own document, which is the corpus rather than an artifact, so it
belongs beside the recall figure instead of being removed from it. Related:
[[feedback_gate_must_bite_before_trusted]],
[[feedback_ratio_from_one_operating_point]].
