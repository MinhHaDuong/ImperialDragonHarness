# Gaze — phase 1 collection and preflight

Loaded from `skills/gaze/SKILL.md` § 1. Setup, after the isolation script has run.

- Abort if not mergeable or if there are open merge conflicts.
- Collect:
  - The ticket file(s) referenced by PR-body close claims (`tickets/*.erg`);
    include any title/body reference when no close claim exists. No close
    claim and no title/body reference → proceed with `ticket: none`; the gate
    reviews against the PR body (`/verify-gate` § Circuit breakers).
  - PR body, full diff, all existing review comments, all inline comments, all commit
    messages on the branch.
- Check CI status for the merge request if the forge exposes it. If the forge CLI or API is unavailable, skip gracefully — CI status is informational only. If checks are configured and any are failing, note this in the setup summary; do not block on it (reviewer decides).
- First run `python3 "$IDH_ROOT/scripts/review-anchor.py" <pr-number> --worktree "$primary_root/.claude/worktrees/review-<pr-number>"`. A nonzero `REVIEW-ANCHOR:` result stops the battery: do not review an empty or wrong-tree diff. Carry its HEAD into every review prompt, and the brief's scope (`SKILL.md` § The brief) in place of its changed-file roster.
- No size stops or tiers the review: every PR gets adherence and what its brief names (under the default brief, the review panel and simplify on round 1 and on material growth, battery.md § 5); a large scope is read in review groups (§ 2–5).

- **Preflight before spawning phases 2–5.** Count distinct ticket close-claims
  from the PR **body**, using the merge recipe's line grammar (`skills/merge/references/claims.md`): bold or
  bare `Ticket: tickets/NNNN...` lines count; the title, `Ticket-ref:` lines,
  `Ticket: none`, and repeated claims for one ID do not. For example, extract
  IDs with `grep -oiP '^\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+' | sort -u`.
  If the count is two or more, record `multi_ticket: <IDs>` as a **non-blocking**
  finding for `/verify-gate` to disposition, and continue the normal review;
  genuinely bundled tickets are permitted by `rules/git.md` § Merging.

- ESCALATE with a clear message, and do not proceed, only if a close claim names a nonexistent ticket file or the PR body, diff or comments cannot be located. A missing ticket with no claim and no reference is not an escalation.
