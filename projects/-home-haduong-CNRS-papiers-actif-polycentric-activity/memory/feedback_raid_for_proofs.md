---
name: feedback-raid-for-proofs
description: The raid workflow transfers to mathematical research if reviewers re-derive and integration checks notation collisions. Correction (2026-07-07) — always re-verify remote existence before assuming a no-remote fallback.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc2349a2-725b-4756-8875-771442f0f763
---

**Correction, 2026-07-07:** the "no-remote merge policy" below was based on a
determination made early in a 2026-07-06 session that turned out to be wrong
(or went stale mid-session) — `origin` (github.com/MinhHaDuong/polycentric_activity,
private) was reachable and writable all along. Acting on the stale premise, an
entire day's work (13 commits) was merged locally without ever pushing, and
was only caught the next day during `/molt` housekeeping when `git remote -v`
was re-run. **Before falling back to the no-remote degradation pattern below,
re-verify with `git remote -v` and `git fetch origin` in the actual working
tree you're about to act in — do not trust a "no remote" conclusion carried
over from earlier in the session or from a different worktree.** Once a
remote is confirmed live, use the normal branch+PR+push workflow (git.md),
not this degradation.

Raids on proof tickets (2026-07-06, tickets 0004/0005/0007/0008) worked with
three adaptations that should be reused **when a remote genuinely is absent**.

**Why:** All four execute agents (opus) produced correct headline mathematics
but over-general side claims; all four REROLLs came from sonnet reviewers who
*re-derived* the calculations instead of reading the reports (over-general
lemma, wrong-directioned bound citation, over-ticked checkbox, missing
chordality hypothesis). One reroll-fix even retracted two of its own v0.1
propositions — honesty instructions ("obstruction documented beats fake
proof", sanctioned fallbacks in the ticket) are what made that safe.

**How to apply:**
- Reviewer prompts must demand independent re-derivation of the key
  calculations, never trust-the-report review.
- Wave integration review checks *notation collisions* across deliverables
  (μ collision caught post-merge; λ collision caught pre-execution — cheaper).
  Make the symbol-collision check a standing integration item.
- No-remote repo: replace push+PR+/gaze with local branch + cross-model
  review + verify-gate-style checkbox challenge + sequential `git -C
  <primary> merge --ff-only` after each logical unit; conflict policy for
  ticket files: user's wording wins, agent log entries interleave
  chronologically.
- Exclude shared files (idea note, refs.bib) from ALL agents' scope; the
  orchestrator consolidates once after merges — this is the no-forge
  equivalent of the coordination PR.
- Cross-document hardcoded theorem numbers are a defect class: verify
  against compiled .aux, never by eye (see [[project-p1-drafting-state]]
  and ticket 0010).
