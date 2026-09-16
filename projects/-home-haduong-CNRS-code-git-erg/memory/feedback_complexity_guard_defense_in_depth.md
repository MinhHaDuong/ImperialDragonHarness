---
name: feedback_complexity_guard_defense_in_depth
description: "git-erg complexity/O(N²) guards are defense-in-depth by design; don't chase a bulletproof detector"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8c3c77f4-e884-4ff7-b37d-a1c2c063bd4d
---

For git-erg's `fast`/scaling invariant, the author accepts a **layered** guard,
not a single bulletproof O(N²) detector. The layers: a deterministic op-counter
(0154, `contract_test.go`), a non-blocking wall-clock backstop
(`test_contract.sh`), and an empirical allocation-volume ladder (0159,
`scaling_test.go`, build-tagged `scaling`). Each layer has a known blind spot;
together they cover the realistic failure modes.

**Why:** no cheap deterministic proxy catches an arbitrary compute-bound O(N²)
(a zero-allocation comparison scan adds only ms at practical N). Chasing one
leads to invasive comparison-level instrumentation the author has twice declined.
The accepted residual — compute-bound zero-alloc O(N²) — is owned by the
wall-clock backstop plus code review.

**How to apply:** This was settled on 0154 (#169, via AskUserQuestion: "Accept
current depth") and again on 0159 (#173). If a reviewer or `/verify` re-raises
"the guard can't catch O(N²) algorithm X," that is the *expected* finding, not a
blocker — note the defense-in-depth posture and proceed. Do NOT redesign toward
deeper instrumentation. Two empirical specifics worth keeping: assert on
`TotalAlloc` (bytes/volume), never `Mallocs` (count) — `append` amortises an
O(N²)-byte build into O(N log N) alloc events; and `ReadMemStats` sees only the
parent heap, so subprocess-heavy commands (e.g. `next-id`'s `git for-each-ref`)
are invisible and must not be used as scaling targets. Related: [[feedback_squash_merge_precheck]].
