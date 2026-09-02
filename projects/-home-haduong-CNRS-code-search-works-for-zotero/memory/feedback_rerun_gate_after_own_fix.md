---
name: rerun-gate-after-own-fix
description: The commit closing a ratchet gap contained the same defect class it closed (a .PHONY silent no-op); the fix for a gate defect gets the gate re-run on itself
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9970023e-fc7f-4ab4-80ee-07075e1dc25f
  modified: 2026-09-01T06:01:20.282Z
---

On t0507 (2026-08-31), the commit titled "Close the erg-check ratchet gap"
added a `tickets:` Makefile target that collided with the `tickets/`
directory and was missing from `.PHONY` — make reported it "up to date" and
the erg check never ran. A silent no-op inside the very commit claiming to
close a silent-no-op gap. It was caught only because the adherence gate was
re-run after the fix rather than trusted on the fix's say-so.

**Why:** the all-clear-indistinguishable-from-could-not-look class does not
spare the code that guards against it; if anything, guard-wiring code is
where the class concentrates, because its output is a green line nobody
reads twice.

**How to apply:** after fixing a gate or guard, re-run the full gate and
verify the new check's output APPEARS in the transcript (not just exit 0),
then prove the mechanism red once (here: `make --always-make`, then the
`.PHONY` fix, then the class test run red against the unfixed tree).
Related: [[the-tickets-own-test-needs-a-control]] — same family, one step
earlier in the lifecycle.
