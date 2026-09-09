---
name: feedback-validate-utility-before-sending-upstream
description: "Green tests are not validation that an upstream PR solves the need it was built for — prove the downstream unblock before sending, not after"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: dc5e15a4-edc1-4528-b6bf-d9afd95441c1
  modified: 2026-09-04T07:47:21.590Z
---

Before sending a drafted upstream PR (or any prepared artifact meant to solve
a specific local problem), validate that it actually solves that problem —
not just that it's internally correct (tests pass, lint clean, builds).
"Ready to send" and "solves our need" are two different bars, and the first
is not evidence for the second.

**Why:** correctness and usefulness are orthogonal. A patch can be
durability-proven, pass the full upstream suite, and still not accomplish
the thing it was built for if a separate blocker remains — sending it
anyway asks the maintainer to spend review time on something whose actual
value is still unconfirmed on your own side. It also risks a PR that, once
merged, still doesn't unblock what you needed, discovered only after the
fact.

**How to apply:** when a change exists to unblock a specific downstream
check or goal, run that check against the patched artifact before
proposing to send anything upstream. Concretely, in this repo: ticket 0642
built durable work counters in a zoteus fork branch specifically to
unblock goal 1's R22 acceptance clauses. The counters patch passed its own
full test suite (1097 tests, lint, build, typecheck all clean) — but R22
still read `not-run` because a separate perturbation-vocabulary gap
remained. The author's correction: hold the send until R22 actually flips
to a real PASS/FAIL against the patched build, i.e., until the
*downstream* validation happens, not just the *upstream-facing* one
(2026-09-04, [[project_zoteus_ladder_goal1_status]]).

This generalizes past this one PR: any "prepare an artifact, get it
technically clean, then ask whether to send" flow should insert a
"does it actually work for what we needed it for" checkpoint before the
send decision, not treat a clean build/test run as that checkpoint.
