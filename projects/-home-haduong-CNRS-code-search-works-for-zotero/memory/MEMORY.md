## Key insights

- This repo's recurring defect class is a per-model axis silently dropped or hardcoded between registry and driver (pooling, then device, then normalize); guards must chase declared-but-unconsumed data, not only hardcoded literals.
- Proxies mislead and the task metric decides: fidelity-to-fp32, the X8 cosine bar, and self-referential recall each priced the same defect differently from task recall, sometimes reversing the verdict.
- A check earns trust only through a demonstrated red state — red-first tests, discriminating contrast arms, positive controls on probes; an all-clear indistinguishable from could-not-look is not a check.
- Measurement campaigns are ledger-shaped: registry-driven, resumable, one atomic file per cell with distinct terminal states — that shape let three interrupted campaigns finish in one day without losing or double-counting a cell.
- Delegation runs on explicit process constraints: leads park on untracked background work, skip close claims, and over-claim standing rows — the orchestrator's claims-versus-tree review is load-bearing, not ceremony.

## Entries

- [Author voice corpus](reference_author_voice_corpus.md) — 48 311 words he curated himself at chemin-de-voix/corpus/clean/voix-auteur-en; tic-removal reaches neutral, not his voice
- [Execute authorized outward actions](feedback_execute_authorized_outward_actions.md) — once he says yes, do it; never hand him a URL to click or text to paste — but show him the document before publishing it in his name
- [Repo prepares upstream, ships nothing](feedback_repo_prepares_upstream_it_ships_nothing.md) — repo PRs are spec/measurement records; upstream-code actions bundle into the upstream PR being prepared, not standalone filings
- [Benchmark harness traps](feedback_benchmark_harness_traps.md) — polymorphic call sites, ±15% single runs, and: a big number needs a control arm, a component needs its null alternative
- [Decision briefs, not option menus](feedback_decision_briefs.md) — argue each alternative with pros/cons from best practice + the field review; a labelled option list is not a brief
- [Preserve agent output, not just its report](feedback_preserve_agent_output.md) — uncommitted subagent work dies with the worktree; git status before remove, or have it push a branch
- [Verify the load-bearing claim](feedback_verify_the_load_bearing_claim.md) — the sentence an outside reader checks first is the one nobody ran; execute it, don't re-read it
- [The metric decides the verdict](feedback_metric_decides_the_verdict.md) — self-referential recall priced a truncation at 22 points where a task metric priced it at 4,8%; it reversed the recommendation
- [Adopted constants carry mechanisms](feedback_adopted_constants_carry_mechanisms.md) — copying a number without the min()/drop rule around it; 4 of 8 upstream attributions were wrong
- [Probes need a discriminating control](feedback_probe_needs_discriminating_control.md) — a control must be able to come out the other way; three vacuous probes in one session
- [Guard the silent failure first](feedback_guard_the_silent_failure_first.md) — the loud guard is the one you think of; enumerate the no-exception failures and mirror the upstream validator
- [A move can leave the gate](feedback_a_move_can_leave_the_gate.md) — a hand-listed gate scope fails asymmetrically: guarding removal is easy and feels done; a file *arriving* stays unguarded
- [Append-only merges keep both](feedback_append_only_merge_union.md) — DECISIONS.md conflicts by construction; assert the union in a script, because deleting a whole ratified entry leaves every gate green
- [A close claim needs a manual check](feedback_close_claim_needs_a_manual_check.md) — erg-pr-merge can't reach a branch in another session's worktree; gh pr merge skips the close silently
- [No optional offers](feedback_no_optional_offers.md) — decide yourself; an offered extra is work you already judged not worth doing
- [Warm runs and single-point fits](feedback_warm_runs_and_single_point_fits.md) — a cold run measures the download; a predictor fitted on one point matched it exactly and missed the next by 106 MB
- [The ticket's own test needs a control](feedback_the_tickets_own_test_needs_a_control.md) — run the specified check against the unfixed tree first; twice in one session it was green on the very defect it existed to catch
- [A judgement must not outlive its subject](feedback_judgement_must_not_outlive_its_subject.md) — a read-not-run status page can't recompute; invalidate on baseline move, and put provenance beside the numbers
- [Green PRs, red union](feedback_green_prs_red_union.md) — two reviewed PRs merged into a red main; only a wave-level check sees it, and a guard's scope claim is retroactive
- [Executor gate-loop stall](feedback_executor_gate_loop_stall.md) — duplicate seat reports + an unmoving branch tip means take over; the findings are already in your context
- [Registry, not knobs](project_registry_not_knobs.md) — rulings 2026-08-29/30: entries pin the mechanics, rung is per-device, R30 ratified, C3 at 750; 0440 drafted awaiting the author
- [Room for multilingual embedders](feedback_room_for_multilingual_embedders.md) — C3 ratified at 750 from the measured floor; the lesson survives: never argue headroom under a ceiling a ruling has displaced
- [Negative results name their mechanism](feedback_negative_result_names_its_mechanism.md) — X4 killed json_each scoping, not scoping; the author was right to reject "no", and a year predicate measured 43x cheaper
- [Leads park on untracked background](feedback_leads_park_on_untracked_background.md) — three sonnet leads in one day deadlocked waiting on nohup runs; prompt chunked-foreground up front, one resume recovers
