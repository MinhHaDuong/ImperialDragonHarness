---
name: feedback_escalate_procedural_vs_substantive
description: "Overnight protocol accepted by the author 2026-09-21 — the orchestrator merges an APPROVED gate on its own; an ESCALATE whose only causes are circuit breakers (budget, duplicate gate comment) is judged on the evidence and may merge; an ESCALATE with a real design question stops the ticket for the author with the diagnosis and a recommendation"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a12625da-f40d-43cd-8b7d-fd6f422a6920
  modified: 2026-09-22T06:34:56.317Z
---

Batched decision round of 2026-09-21 (autonomous night on tracker 0834): the
author chose "fusion autonome" after APPROVED, with "un ESCALATE ou deux
REROLL arrêtent le ticket concerné, je vous le laisse au matin avec le
diagnostic". Two ESCALATEs then came:

- PR #1433 (0838): ESCALATE only from telemetry thresholds and a stray
  duplicate gate comment on PR-body minors already fixed; five criteria
  ADDRESSED, zero blockers, gate text said "merge-ready". Merged, reason
  stated. Not contested.
- PR #1439 (0855–0857): ESCALATE with one genuine design call (rendering of
  55 sources with facts but no extracted row: note vs empty fold-out). The two
  trivial items were fixed on the branch; the decision was posted as a PR
  comment with a recommendation and the PR left open.

**Why:** the gate's ESCALATE conflates process budget breaches with
substantive disagreement; treating both as "wait for the author" wastes the
night, treating both as mergeable erodes the author's arbitration.

**How to apply:** read the gate rationale, not the label. Circuit-breaker-only
→ decide on the evidence and write why on the PR. Any item the gate itself
calls "author's call" → fix the rest, post the choice with a recommended
default, stop. Related: [[feedback_escalate_check_merge_after_note]].
