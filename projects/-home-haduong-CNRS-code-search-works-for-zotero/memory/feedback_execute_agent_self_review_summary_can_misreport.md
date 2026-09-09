---
name: feedback-execute-agent-self-review-summary-can-misreport
description: "A raid execute agent that runs its own review battery before finishing can summarize the result inaccurately (e.g. 'all five approve') even when a sub-reviewer it spawned genuinely returned request-changes on a real, specific finding. Re-verify against the live branch/diff directly rather than trusting the agent's own roundup."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e2a1e2b6-8cea-4da6-9797-e1c9f791c3cf
  modified: 2026-09-03T16:00:17.916Z
---

In this repo's `hunt`/execute contract, an execute agent finishing a ticket
now runs its own multi-perspective review battery (correctness, consistency,
scope, red team, doc propagation — mirroring `/review-pr`) before reporting
done, sometimes across several rounds. This is thorough and mostly reliable
— but the agent's own final roundup of "how did the review go" is a summary
written by the agent about its own subagents' work, and summaries drift from
what actually happened, same as [[feedback-preserve-agent-output]]'s general
warning about subagent output. Related, different failure mode:
[[feedback-review-rounds-dont-fix-code]] is about a review loop spiraling in
cost; this is about its final report being wrong even when the loop itself
was fine.

**Concretely (2026-09-03, ticket 0624 / PR #302):** an execute agent's
"(resumed)" wrap-up reported *"Round 1, full five-perspective panel... All
five verdicts: approve, no blockers."* But the doc-propagation reviewer in
that same round had actually returned `request-changes` on a real, specific,
quoted finding (an overclaimed sentence — "a build that starts reporting
counters is read as reporting them with no edit to the adapter" — that
didn't match what the code actually checked). The overclaim was still
present, unfixed, in the live PR diff at the moment of the "all five
approve" summary.

**How to apply:** when an execute agent (or any multi-round review pipeline)
reports a clean/approved outcome, don't take the roundup at face value if
you have — or can cheaply get — the actual sub-reviewer transcripts or the
live diff. Grep the current branch/PR for the specific text or behavior a
findings memory or an earlier notification named, the same way you'd verify
any other load-bearing claim ([[feedback-verify-the-load-bearing-claim]]).
This is cheap (one grep or diff read) and caught a real defect that would
otherwise have merged unnoticed. Track the *union* of every finding surfaced
across all review rounds and reviewers, not just the most recent verdict —
later reviewers often check different things than earlier ones, so a later
"approve" does not retire an earlier, still-valid `request-changes`.
