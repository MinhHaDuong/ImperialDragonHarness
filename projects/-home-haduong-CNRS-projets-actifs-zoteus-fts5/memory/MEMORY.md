## Key insights

- **The measurements were wrong far more often than the code was.** Across the SQLite/FTS5 chantier, four defects came out of this repo's own settled claims rather than out of the implementation, and five review rounds on one merge request produced fifteen-odd blockers with none in what shipped.
- **A claim whose evidence was never captured is not a finding, and producing that evidence is not bookkeeping.** Asked for the artifacts behind three claims, two turned out to be wrong — a codepoint sweep that contradicted its own ticket, and a ranking effect measured through a re-implementation of the ranker instead of the ranker.
- **A check can fail by never firing, by firing on everything, or by being untestable.** All three appeared in one session, and only sabotage — of the property *and* of each candidate guard in turn — tells them apart.
- **Guarding one instance of a defect class does not guard the class.** The same confusion is usually possible nine lines away, in a sibling function, on another axis — and a correct comment explaining why the guard is needed is what stops a reviewer looking further.
- **A ratio measured at one operating point is a fact about that point.** It has now been wrong in both directions here: a 13x speedup that inverted at the pool the design uses, and a synthetic fixture that turned out to be a *harder* problem than real data.

## Entries

- [Gates must bite before trusted](feedback_gate_must_bite_before_trusted.md)
- [Cited evidence ages out](feedback_cited_evidence_ages_out.md)
- [zoteus fork git isolation](project_zoteus_fork_git_isolation.md)
- [Agent-reported numbers need artifacts](feedback_agent_reported_numbers_need_artifacts.md)
- [A ratio from one operating point](feedback_ratio_from_one_operating_point.md)
- [Invisible bias in both arms](feedback_invisible_bias_in_both_arms.md)
- [Guarding one instance is not the class](feedback_guard_one_instance_not_the_class.md)
- [Re-running re-stales the prose](feedback_rerunning_the_measurement_restales_the_prose.md)
- [A null result needs a positive control](feedback_a_null_result_needs_a_positive_control.md)
