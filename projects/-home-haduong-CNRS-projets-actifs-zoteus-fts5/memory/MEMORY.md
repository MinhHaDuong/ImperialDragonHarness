## Key insights

- **The measurements were wrong far more often than the code was.** Across the SQLite/FTS5 chantier, four defects came out of this repo's own settled claims rather than out of the implementation, and five review rounds on one merge request produced fifteen-odd blockers with none in what shipped.
- **A claim whose evidence was never captured is not a finding, and producing that evidence is not bookkeeping.** Asked for the artifacts behind three claims, two turned out to be wrong — a codepoint sweep that contradicted its own ticket, and a ranking effect measured through a re-implementation of the ranker instead of the ranker.
- **A check can fail by never firing, by firing on everything, or by being untestable.** All three appeared in one session, and only sabotage — of the property *and* of each candidate guard in turn — tells them apart.
- **Guarding one instance of a defect class does not guard the class.** The same confusion is usually possible nine lines away, in a sibling function, on another axis — and a correct comment explaining why the guard is needed is what stops a reviewer looking further.
- **A ratio measured at one operating point is a fact about that point.** It has now been wrong in both directions here: a 13x speedup that inverted at the pool the design uses, and a synthetic fixture that turned out to be a *harder* problem than real data.

## Entries

- [Gates must bite before trusted](feedback_gate_must_bite_before_trusted.md) — sabotage the property or the gate is decoration; and a gate that fires on everything is retired just as fast
- [Cited evidence ages out](feedback_cited_evidence_ages_out.md) — a grep or line number written into a ticket decays as later waves land; cite the invariant, not the command
- [zoteus fork git isolation](project_zoteus_fork_git_isolation.md) — code lives in fork/, a nested independent repo; the worktree guard blanket-blocks git there
- [Agent-reported numbers need artifacts](feedback_agent_reported_numbers_need_artifacts.md) — a figure in a report but not in a file is prose; make the driver record its own environment
- [A ratio from one operating point](feedback_ratio_from_one_operating_point.md) — 13x at k=30 became slower-than-baseline at the pool the design uses, and the fixture was harder than real data
- [Invisible bias in both arms](feedback_invisible_bias_in_both_arms.md) — a bias that cancels in the difference still eats the sensitivity the comparison needed
- [Guarding one instance is not the class](feedback_guard_one_instance_not_the_class.md) — 0006 guarded the version-sequence confusion on one axis and committed it on another, nine lines later
- [Re-running re-stales the prose](feedback_rerunning_the_measurement_restales_the_prose.md) — a re-run after every review round is the loop's engine; freeze the artifact, generate the figures
- [A null result needs a positive control](feedback_a_null_result_needs_a_positive_control.md) — three probes found zero packs and could not have seen one; the fourth, with a control, reversed the finding
