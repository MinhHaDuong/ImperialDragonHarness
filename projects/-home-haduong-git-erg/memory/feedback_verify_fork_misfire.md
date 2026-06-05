---
name: verify-fork-misfire
description: "A forked /verify can re-run the previous skill's task; discard the output and retry with an explicit, self-describing args string"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7486d7d8-cc88-47ed-b071-07569335661d
---

On 2026-06-05, `Skill(verify, args: "285")` returned a completed fork
that had re-executed the *previous* skill's task (/nightbeat-report)
instead of verifying PR #285 — forked-skill context bleed. Its output
even contradicted data I had gathered directly.

**Why:** a bare numeric arg gave the fork too little signal to override
the residual context; the fork's result is authoritative-looking but
can be entirely off-task.

**How to apply:** (1) sanity-check that a fork's result actually answers
the request before consuming it; discard wholesale on mismatch, don't
salvage. (2) Retry with a self-describing args string ("PR 285 — branch
t0237, repo git-erg. Run the full per-PR verification loop…") — that
worked first try. Related: post-fork cwd confusion in [[cross-session-worktree-hijack]] territory; forks inherit leftover state.
