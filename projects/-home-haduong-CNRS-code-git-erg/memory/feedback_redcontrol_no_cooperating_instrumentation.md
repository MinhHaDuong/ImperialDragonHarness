---
name: redcontrol-no-cooperating-instrumentation
description: "Red-control mutations must not cooperate with the guard's instrumentation — mutate the defect only; gaze round-1 caught a counter-based fang whose red-control moved the counter inside the scan"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff83e53f-129c-436d-b421-d6c97d72674d
---

Verifying a counter-based guard goes red (PR git-erg#294, ticket 0240): my mutation replaced the O(1) map lookup with a linear scan AND moved `refLookupComparisons++` inside the scan loop — so the test went red only because the mutation helpfully incremented my own counter. A real regression (scan without touching instrumentation) kept the per-call count linear and PASSED: the fang was toothless and my red-control hid it. `/gaze` round 1 caught it; the fix was a wall-clock guard (`TestIdExistsO1`, `//go:build scaling`) that measures the work itself, not a counter the defect must volunteer to bump.

**Why:** a counter counts what the code *reports*, not what it *does* — any guard whose signal lives inside the mutable region can be silently orphaned by the very defect it watches for.

**How to apply:** when red-controlling a guard, write the mutation as an adversary would — change only the defect, never the instrumentation. If the guard cannot go red under that constraint, the signal is in the wrong place: measure externally observable cost (time, allocations, fds) instead. Related: [[negative controls must prove the property they claim]], [[complexity guards are defense-in-depth]].
