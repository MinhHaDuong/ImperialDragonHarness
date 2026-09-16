---
name: feedback-plan-agent-test-inversion
description: Plan agents reframing a ticket can silently invert the original red-test semantics — diff the Test section against the original before committing the plan
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a2a9d636-a0c1-45b7-a2ce-1dc30a8b05b1
---

During raid 0544 (2026-06-11), the Plan agent redefined "structural false-match set" from the original pre-veto semantics (Vũng Áng 1/2 MUST appear) to post-veto semantics (MUST NOT appear) — a sign-flip of the ticketed red test, while leaving exit criteria untouched, so the drift guard on exit criteria alone did not catch it.

**Why:** Reframing (here: "the veto makes this a documentation exercise") naturally pulls definitions toward the new frame; the Test section is part of *what* to deliver, not just *how*.

**How to apply:** In raid Phase 3 review, diff the rewritten Test section against the original ticket's Test line(s), not only the exit criteria. A reversed assertion or membership flip is an orchestrator-level fix (keep original semantics, add the new insight as an extra flag/column) — as done in 0544: set keeps pre-veto membership + `veto_blocked` column. Related: [[feedback-conversation-not-manuscript]].
