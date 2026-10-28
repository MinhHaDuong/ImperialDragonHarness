# Diminishing-returns bar for review findings (PR #1847)

Context: the author named a "frog boiling" loop in review rounds: findings
narrow round by round, each judged justified against the previous one, ending
in gold-plating and windmill defence. The round caps (verify-gate two rounds,
fix-and-regate fix-on-fix rule) did not stop it; the stopping rule existed only
in a memory note.

Author's framing, stated as reasoning, not for literal inclusion:
- Drift means a round-N "medium" is a little more exotic than round N-1's and
  so locally passes as medium; after three rounds it sits under the absolute
  severity bar.
- No diminishing returns after three rounds: the approach must be redesigned.
- Diminishing returns yet still serious flaws: the coder or the reviewers are
  bad.
- Diminishing returns and below the bar at rounds 2-3: situation normal; hold
  the bar.
- Coder and reviewer health could be assessed ex post by a doctor.

Decisions and outcome: the author chose option B (schema fields) over a
rule-only sentence. PR #1847 merged 2026-10-28 at 6bf52b9b: a `blocking` or
`verifiable:` finding carries `scenario:` and `on main:`, else it is a
`consider:`; the bar is fixed in advance and the same every round; fresh
blockers at round 3 mean a redesign, re-ticketed. Stated in
`skills/gaze/references/panel.md` § Finding tags. `rules/workflow.md` only
names the principle: the resident budget (17 800 chars) left no room for more.
Two gaze rounds (cross-family seat) and verify-gate round 1 APPROVED.

Pending: the ex-post health read (proposed owner trace-doctor, reading gaze and
gate comments per merged PR) awaits the author's decision; not ticketed.
