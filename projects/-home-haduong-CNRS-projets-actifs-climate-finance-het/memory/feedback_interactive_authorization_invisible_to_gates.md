---
name: feedback-interactive-authorization-invisible-to-gates
description: "a mechanical merge gate only sees committed artifacts (ticket text, PR body) — real-time author authorization in a live conversation is invisible to it, so scope can be legitimately extended mid-session while the gate still enforces the stale written invariant"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4416da70-2381-4a58-904a-29125c1a1dde
---

`/gaze` round 1 on PR #1045 (ticket 0243, 2026-07-15) REROLLed and reverted
five hunks — a bibliometric-complement citation, two primary-source-verified
correction citations, two hedge-phrase fixes — all of them explicit,
real-time author direction given interactively in the same session, verified
against locally staged primary-source PDFs before being applied. The gate's
verdict was locally correct: the diff really did violate both the stale PR
body ("pronoun-only pass") and the ticket's own written invariant ("no
factual/numerical/citation change — style only"), because that invariant was
authored for an earlier, narrower phase of the ticket before the interactive
session extended its scope to include citation-precision corrections.

This is the sibling case to [[feedback_gate_verify_branch_not_pr_body]] (PR
#1048: a stale PR body claiming an unresolved gap that later commits had
already fixed) — but inverted. There, the body claimed a defect that no
longer existed; the fix was to trust the diff at HEAD over stale prose. Here,
the diff added content that the gate's textual sources (PR body, ticket
invariant) said shouldn't be there, but a party outside those sources (the
live author, in this conversation) had authorized it. A gate reading only
committed text cannot see that authorization — there is no artifact for it
to check.

**Why:** the interactive session evolved organically — D1-D4 mechanization,
then a 20-item voice-critique pass, then citation corrections the author
specifically requested mid-pass — faster than the PR description or the
ticket's own invariant text was updated to match.

**How to apply:** in an interactive session, update the PR description
*every time* the branch's actual scope expands beyond what was last written
there — not just at PR-open time. Before invoking `/gaze` (or any mechanical
gate) on a branch built across many interactive rounds, do a last-mile
description refresh so the gate's textual context matches reality. If a gate
still REROLLs/reverts content the author explicitly authorized in the live
conversation, that is very likely this exact false-positive class — verify
against the conversation's own record (commit messages citing the author's
directions, primary-source verification already on file) before accepting
the gate's verdict, restore the content, fix the description, and document
the override on the PR rather than silently re-applying or spending a third
gate round on a documentation problem the content itself never had.
