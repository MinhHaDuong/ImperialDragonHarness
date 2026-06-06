---
name: primary-checkout-staleness-gates-skills
description: "Skills resolve from the primary checkout (~/.claude) — a merged skill change is inert until that checkout pulls; sync it before judging new-mechanism behavior, and check it for divergence (unpushed local-main commits starve every session of upstream)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 633a0ecb-ca76-4fe9-b33d-7a42ea9e294a
---

Skills load from `~/.claude/skills/` (the primary checkout), not from the
session worktree or origin. Two raid-day consequences (2026-06-06):

1. **Merged ≠ live.** PR #329 rewrote the gaze mechanism, but the two
   wave-2 gaze runs still exercised the old fork text because the primary
   checkout was 13 commits behind. Mechanism evidence judged on those runs
   would be false-negative. After any merge that changes skill behavior,
   `git -C ~/.claude merge --ff-only origin/main` before the next run that
   depends on it.
2. **Divergence is silent and double-bad.** The same checkout was 1 commit
   AHEAD — a dream session had committed directly to local main, never
   pushed (rescued via branch + PR #334, ticket [[0234]] guards the class).
   Ahead-of-origin blocks the ff sync; behind-origin starves skills.

**Why:** every session assumes "skills = main", but the primary checkout is
a manually-synced replica (daily timer + ad-hoc pulls).

**How to apply:** when a raid/PR changes skill text, fast-forward the
primary checkout immediately after merge and re-check
`git -C ~/.claude status`/`log origin/main..main` for divergence before
attributing behavior to the new text. Related: [[feedback_beat_checkout_model]],
[[feedback_rogue_agent_pattern]] (a 0229 execute agent also pre-closed its
ticket on the branch — add "do not close the ticket; erg-pr-merge closes at
merge time" to execute-agent prompts).
