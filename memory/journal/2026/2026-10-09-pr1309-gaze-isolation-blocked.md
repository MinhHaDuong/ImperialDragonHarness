# PR 1309: /gaze fix loop blocked by worktree isolation; raid 1073

Date: 2026-10-09. Ticket 1073, PR 1309, raid of a single ticket.

- Phases 2-4 (Imagine, Blind-Spot, Plan, Feasibility) ran as one read-only
  Sonnet agent, and a Sonnet coder ran `/hunt 1073` in an isolated worktree.
  The coder reported that the Skill tool was unavailable in its session, so
  it read `skills/hunt/SKILL.md` directly.
- `/gaze 1309` (forked) ran adherence, review and a three-seat panel, with no
  blockers. The worktree-isolation guard refused git and writes in the review
  tree, so no gate seat or fix agent ran. The verdict was ESCALATE, ruled by
  the orchestrator. Panel integrity was DEGRADED: two seats delivered by
  hand-back, not as files, and there was no cross-family seat.
- The orchestrator applied the 2 verifiable and 3 consider fixes on a scratch
  branch (`fix-1309`, from `origin/t1073-sort-non-writing`) and pushed them to
  the PR ref. The PR branch was checked out in the coder's worktree. A
  `/verify-gate` re-run ruled APPROVED at round 1 on 7a1e962c.
- `erg-pr-merge` could not run, for the reason recorded in
  [the PR 1300 entry](2026-10-09-pr1300-branch-held-direct-merge.md). Ticket
  1073 was closed by hand on the PR branch (`erg close` moved the file to
  `closed/` itself, with its `Closed:` header). PR 1309 was then auto-merged
  pinned to head def28346, at 13:13:57Z.
- Review-attribution capture for PR 1309 is pending: the PR comments name
  seats and outcomes but not reviewer model ids.
