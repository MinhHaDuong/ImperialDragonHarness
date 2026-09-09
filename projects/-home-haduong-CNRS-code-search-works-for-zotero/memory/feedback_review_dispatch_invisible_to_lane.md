---
name: review-dispatch-invisible-to-lane
description: "The raid skill's coordinator-dispatched review panel and an Execute agent's own hunt-contract panel can't see each other -- bit twice in one raid, causing a merge with no verdict on the PR page"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d5b346ef-7983-4572-a95a-cf476a17df19
  modified: 2026-09-06T16:04:48.027Z
---

During the 2026-09-06 sitter-hardening raid (search-works-for-zotero), two
separate Execute agents (tickets 0699 and 0701-0704) each reported "the
correctness/review-pr seat never ran" when in fact I (the raid coordinator)
had dispatched a full 5-perspective panel myself, directly via the Agent
tool, bypassing the lane's own `hunt` contract's `/review-pr` step. Each
agent could only see the panel *it* launched (or tried to launch, sometimes
failing) inside its own worktree -- it had no visibility into a panel the
coordinator ran separately and relayed findings from via SendMessage.

The second occurrence was worse: the 0701-0704 agent correctly refused to
transcribe the verdicts I relayed as if they were a posted review (per this
repo's AGENTS.md: "never write a verdict on a reviewer's behalf" -- doing so
would manufacture the appearance of a review that happened, when the actual
record exists only in my session). It merged the PR, since the actual
verdicts (all approve/comment, no blockers) were real and correct -- but the
PR page carried no verdict at merge time, the exact shape of the repo's own
prior 2026-09-02 incident that its merge-authority section was written to
prevent. I closed the gap after the fact by posting the panel's actual
findings as a PR comment, but the right fix is structural, not per-PR.

**Why:** the raid skill lets the coordinator either delegate review to the
Execute agent's own hunt-contract loop, OR dispatch a review panel directly
and relay results -- and nothing in the skill or in the Execute agent's
prompt tells the agent that the second path exists, or gives it a way to
check for it before declaring "the panel never ran" or merging without a
posted verdict.

**How to apply:** when coordinating a raid and choosing to dispatch review
panels myself (bypassing an Execute agent's own hunt-contract loop, e.g. to
manage concurrency or because a lane's own panel already got interrupted by
an environment failure), either (a) tell the Execute agent explicitly, in
the same message that relays findings, that panel dispatch happened outside
its own lane and it should not attempt its own `/review-pr` run nor merge
without a posted page record, or (b) post the panel's verdicts to the PR
page myself, before or immediately after any merge, rather than only
relaying them via SendMessage. Don't assume an Execute agent can infer that
a coordinator-relayed "the panel found X" summary is equivalent to a review
that happened -- from its own vantage point, correctly, it isn't, until it's
on the page. A durable fix would be a raid-skill note making this dispatch
split explicit; flagged here as a real, twice-repeated gap rather than filed
as a ticket, since fixing it means editing the global `~/.claude/skills/raid/`
files, not anything in this project's own tracker.
