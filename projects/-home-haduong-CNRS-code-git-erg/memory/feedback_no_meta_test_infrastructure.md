---
name: feedback_no_meta_test_infrastructure
description: "The harness's test-validation infrastructure was removed deliberately; do not propose rebuilding it, because the goal is research."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a27d6179-c527-421f-a14a-e4de26d3f494
  modified: 2026-09-16T15:32:24.823Z
---

Do not propose mutation-testing sweeps, meta-test batteries, or any other
machinery whose subject is *the test suite itself*. That infrastructure existed
in the harness and was **removed on purpose**.

On 2026-09-16, after a raid found thirteen guards whose "all clear" could not be
told from "I could not look", I proposed mechanizing a mutation pass over the
41 suites in `TEST_SUITES`. The author's answer: *"C'était ironique. On a retiré
du harnais l'infrastructure de validation des tests. Parce qu'à un moment faut
pas oublier que le but c'est de faire de la recherche."*

**Why:** validating the tests of the tool that builds the tool that supports the
research is three levels of indirection from the science. The author's attention
and the project's effort are finite, and that chain spends both on the layer
furthest from the deliverable. The removal was a decision, not an oversight —
treating it as a gap to fill re-litigates a settled call.

**How to apply:** find vacuous guards the way the thirteen were actually found —
opportunistically, as a side effect of already having a file open for another
reason. That is near-zero marginal cost and it is sufficient. When a sweep is
tempting, check first whether the capability was deliberately removed; the
recorded failure mode here was not a bad choice but an *absent* one — I never
looked before proposing. Suites nobody had a reason to open stay unmeasured, and
that is the intended state, not debt.

The per-case discipline still applies to any guard you do touch — see
[[feedback_non_vacuity_is_per_case.md]]. The distinction is between *proving the
guard you are writing* (always) and *auditing guards nobody asked about* (never).

Related: [[feedback_raid_no_debt_contract]].
