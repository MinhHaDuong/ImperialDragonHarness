# Gaze — phase 1 collection and preflight

Loaded from `skills/gaze/SKILL.md` § 1. Setup. `"$IDH_ROOT/scripts/gaze_setup.py"`
does the mechanical part in one call, in this order:

- Reads the PR through the forge CLI; aborts (exit 1) on merge conflicts.
- Checks the liveness lock (a tree holding `gaze-closed` in its git dir, written by
  `gaze_close.py` before cleanup and kept by a refused close, is dead, not live), creates the isolated review worktree
  `review-<pr-number>` and runs `"$IDH_ROOT/scripts/review-anchor.py"` on it. A
  nonzero anchor result stops the run (exit 2): do not review an empty or
  wrong-tree diff. Carry its HEAD and changed-file roster into every plan item.
- Lists the ticket file(s) named by PR-body close claims (`tickets/*.erg`). A
  claim naming a file that exists neither under `tickets/` nor `tickets/closed/`
  is a breaker (exit 1, ESCALATE). No claim → `ticket=none`: proceed, the gate
  reviews against the PR body (verify-gate § Circuit breakers).
- Writes the PR body and all PR and review comments to files in the panel
  directory, reports CI as `none`, `passing` or `failing: <names>`
  (informational: note failures in the setup summary, do not block; the reviewer
  decides).

What stays with gaze: the full diff and commit messages (read them in the
review worktree), ESCALATE with a clear message when the PR body, diff or
comments cannot be located, and the plan. A missing ticket with no claim and
no reference is not an escalation.
