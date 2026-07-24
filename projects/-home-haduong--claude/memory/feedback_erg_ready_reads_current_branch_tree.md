---
name: feedback_erg_ready_reads_current_branch_tree
description: "erg ready lists tickets from the current branch's working tree, so a stale branch reports tickets already closed on main — fetch and re-check before acting on the list"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bb7d1a1f-202d-45bc-94f6-3ab7979c2dd9
  modified: 2026-07-24T20:12:39.898Z
---

`erg ready` reads `tickets/` from the **current branch's tree**, not from
`origin/main`. On a stale feature branch it happily lists a ticket that a
parallel session already implemented, merged, and archived to
`tickets/closed/` on main. Its header line names the branch it read
(`erg: branch t0357-… (tickets)`) — that line is the tell, and it is easy to
skim past.

**Why:** on 2026-07-24 a session sat on `t0357-cut-before-condense`,
`erg ready` listed 0357, and the session began re-implementing the rule from
scratch. PR #667 had already landed the identical work (`rules/prose/cutting.md`
+ a one-line pointer in `_all.md` + a README row + an adherence ratchet). The
duplicate edit collided with leftover conflict markers in `_all.md` and wasted
the turn. This is the same class as [[feedback_pipeline_presentation_overlays_raids]]
— a "ready" ticket may already be claimed or done elsewhere.

**How to apply:** before acting on `erg ready`, run
`git fetch origin && git log --oneline HEAD..origin/main` and re-run the picker
on a current tree — or read the branch name in erg's own header and distrust
the list if it is not the default branch. When the task is "finalize ticket N",
check `tickets/closed/` and the merged PR list first; finalization is often
already done. Use `rtk proxy ls` / `rtk proxy git` for these probes — the rtk
hook rewrites plain `git status`/`diff` output and can make a clean tree look
ambiguous (see [[feedback_rtk_rewrites_git_output]]).
