# Instruction-contradiction sweep and PR 1622

Context: the author asked for a large Haiku workflow to detect contradictions in the harness instructions (rules, skills, profiles, agents; memory and tickets excluded).

Events:
- The workflow ran 116 Haiku detect passes (58 units, two lenses) and 184 Sonnet verify passes: 301 agents against an allowance of about 130, which the first report omitted. 94 raw findings, 92 after dedup; 24 confirmed, 11 disputed, 56 refuted. A control copy of one skill with 5 planted contradictions: the git/review lens found 5 of 5, the delegation lens 2 of 5.
- PR 1622 fixed the confirmed findings. Author rulings during the work: one question at a time after asking up (message-framing, reading-note); no private companion store for memory (workflow.md); no model names or tiers in instructions, with cheap-first review seats recorded in route.
- Five `/gaze` rounds each returned FINDINGS, mostly wording defects in the PR's own re-pointed citations; round 1 found a failing test (`tests/test_gaze_prose_routing.py`) that the fast tier does not run. The author overruled the sixth round (`--force-approve`); `/verify-gate` ruled APPROVED at 2e0efaa3 and the author merged directly (d7a5f18e).
- An advisor-model consultation advised loosening wording and dropping the advisor term; the writer kept the term and added a route line.

Outcome: merged; follow-up sweep on the merged ref found no remaining stale prose-section citation, "both guards" or tier wording in rules, skills, profiles, agents or scripts. Left open: merge/references/claims.md staging order, the hunt phase label, lair's fallback merge wording, tool names in skills (biblio-saturation, related-work-note, verify-gate). References: PR 1622, memory/journal/2026/2026-10-21-review-attribution-pr1622.md.
