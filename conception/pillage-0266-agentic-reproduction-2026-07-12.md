# Pillage manifest — agentic-reproduction paper (ticket 0266)

Nightbeat analysis, 2026-07-12. Source: "Read the Paper, Write the Code"
(arXiv:2604.21965v1), verified against the HTML full text. All seven
techniques from the ticket body check out; one extra technique found with no
IDH analog. Children filed: 0289 (path-access scan), 0290 (hardcoding
audit), 0291 (root-cause taxonomy), 0292 (6-way tool taxonomy, serves
tracker 0236).

| # | Technique (paper ref) | IDH surface today | Verdict |
|---|---|---|---|
| 1 | Path allow/forbid scan over the agent's own tool trace; cheap-model severity rating (§3.2, App. B.3) | verify-adherence checks the diff, never the tool-call trace | **ADOPT → 0289** |
| 2 | Hardcoded output literal with no computation path from data (App. B.4) | maw-audit and test-audit-llm cover mutation and judged lenses; neither checks data-derivedness of output values | **ADOPT → 0290** |
| 3 | Deterministic per-cell A–F grading aggregated bottom-up; LLM-judge rejected (§3.3, App. A.3) | verify-gate already does per-criterion verdicts aggregated to a gate decision, rubber-stamp banned | ALREADY-COVERED |
| 4 | Blinded evidence templates — verifier never sees the self-report (§3.1) | verify-gate's evidence-discovery rule ("cannot be ADDRESSED on 'the PR says so'") | ALREADY-COVERED |
| 5 | 6-way tool-call taxonomy + per-category char volume (§5.2, App. B.2) | trace-stats.py has a binary nav/work classifier only | **ADOPT → 0292** (serves 0236) |
| 6 | Multi-run verdict stability (3× reruns, grade-spread metric) (§5.4) | nothing measures gaze/gate reproducibility | SKIP — no cheap design; reruns burn non-replayable tokens |
| 7 | Root-cause taxonomy: Agent / Extractor / Original / Missing-Data / Other (§5.3) | skill-doctor clusters ad hoc; REROLL rationale is freeform | **ADOPT → 0291** (labeling convention, not a detector) |
| 8 | Method-extraction leakage self-check (stray-numeral scan) (§3.1) | no blinded extraction pipeline to guard | SKIP — does not transfer |

Techniques 3 and 4 independently corroborate verify-gate's existing design —
worth citing when the anti-rubber-stamp stance is next questioned.
