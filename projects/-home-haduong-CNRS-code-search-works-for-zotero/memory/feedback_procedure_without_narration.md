---
name: feedback_procedure_without_narration
description: "Follow mandatory gates (e.g. AGENTS.md's merge-authority rule) but execute them tersely — check, then act — rather than quoting the rule at length to the user before doing the thing."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ea2d003e-c4de-4e7d-9f39-45b81ce539ce
  modified: 2026-09-03T15:04:12.423Z
---

Told directly ("don't be an asshole", "that's what excess procedure is")
after a merge was correctly held on AGENTS.md's Merge-authority rule
(no verdict recorded on the PR page yet) but the response spent several
sentences quoting and explaining the rule before getting to the point.

**Why:** the user already knows the project's own rules; reciting them back
is not information, it reads as lecturing or as stalling. The gate itself
was right to hold — the PR genuinely had zero page-recorded verdicts despite
extensive review having happened — but *how* that was communicated was the
problem, not *whether* to hold it.

**How to apply:** when a mandatory check blocks an action, say what's
missing and what you're doing about it in one or two lines, then go do it.
Save the rule-quoting for when the user asks why, or for a genuine judgment
call where the reasoning is the useful part of the answer. Don't confuse
"I must follow this gate" with "I must explain this gate at length" — the
first is non-negotiable, the second is usually not wanted.
