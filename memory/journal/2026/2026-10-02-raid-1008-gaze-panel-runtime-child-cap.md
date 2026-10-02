# Raid 1008: gaze panel under the runtime's silent child cap (PR #1121)

A `/raid 1008` ran the full eight-phase loop in one session on 2026-10-02:
Imagine, Blind-Spot, Plan, feasibility, execute via hunt, a full gaze battery
(adherence, diff review, five perspectives, external seats, copilot), one
REROLL fix round, a second gate round (APPROVED), merge of PR #1121, and the
bookkeeping PR #1125.

The runtime's subagent capacity cap is silent: `agent.spawn` calls beyond the
cap return `success` while the agent is never registered. The first
seven-seat gaze fan-out produced only three registered agents; the artifact
roster written before launch — names checked against `.panel/1121/` — is what
exposed the four missing seats, not the spawn return values. Closing finished
idle agents freed the slots and the relaunch registered. Wide fan-outs in this
runtime need the roster check and a slot budget, not trust in spawn results.

Direct pushes to main are declined by repository rule, including a one-line
ticket-log bump commit. The round-1 verify-reroll bump landed through a tiny
PR (#1125) merged with `erg-pr-merge` using `Ticket: none`; the helper refuses
to merge while CI checks run and succeeds on retry once the ten guards pass.

Gate round 1 refused two of the executor's fifteen mined board labels: pr 21
was a blame-move artifact (the defect predates the PR; the mechanical CONFIRMED
ancestry rule was satisfied by a byte-identical moved line) and pr 258's
confirming fix was a formatting-only revert. The shipped guard test could not
catch either class. The fix round removed both entries and taught the guard to
verify confirming-fix SHAs recorded as `# confirmed:` comments in the board;
the board now carries 23 entries, 17 defect-bearing. The external
openrouter-frontier seat flagged two out-of-diff findings; one was refuted by
evidence (the CI age-keygen step ran green on PR #1125) and the other was
verified and filed as tickets/1014 (memory-capture project-key port
collision).

Open threads recorded in the gaze round-2 review: the four raid `claude note`
log lines on the archived ticket sit in the body section rather than the log
section (an annotation-placement slip from the raid's own Phase 2-4 commits,
carried into the PR verbatim); the audition board stays single-repo, so
cross-project entries need a repo field plus seat-runner repo resolution
before they can be more than labels (no shortfall was hit this time); and the
incumbent seat (openrouter-frontier successor) has never replayed any board,
so ranking per the attribution spec section 7 still needs an incumbent replay
run with a pinned model id — an author sequencing decision.
