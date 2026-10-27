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
- First run `python3 "$IDH_ROOT/scripts/review-anchor.py" <pr-number> --worktree "$primary_root/.claude/worktrees/review-<pr-number>"`. A nonzero `REVIEW-ANCHOR:` result stops the run: do not review an empty or wrong-tree diff. Carry its HEAD and changed-file roster into every plan item.
- ESCALATE with a clear message, and do not proceed, only if a close claim names a nonexistent ticket file or the PR body, diff or comments cannot be located. A missing ticket with no claim and no reference is not an escalation.
