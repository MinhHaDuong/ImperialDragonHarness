# Lead architect, round 1 (ticket 1096)

## Current state (cited)
- Double review: hunt runs the review-pr loop for up to 3 rounds (skills/hunt/SKILL.md:117-133); raid then runs /gaze on every MR (skills/raid/SKILL.md:282-289), which starts its own battery: Agent A adherence, Agent B native /review, Agent C = review-pr again via agents/gaze-pr-review.md, then simplify and gate (skills/gaze/SKILL.md:227-232, :446-470). The only hand-off from hunt is the verify:adherence-passed label (hunt:111, gaze:401-404). On 1080, "two complete five-seat cross-family panels preceded the final gate" (memory/journal/2026/2026-10-14-raids-1080-1089-wrap-up.md:15-16).
- "What was already reviewed" is inferred: review-pr counts its own posted reviews to get a round (skills/review-pr/SKILL.md:208-218) and scopes the panel by round (:220-238), never by revisions actually reviewed. The 1089 final gates had to verify blob equality after rebases by hand (journal:32-33).
- Duplication: review-pr-prose copies the concurrency contract and round scoping with "keep the two in sync" (skills/review-pr-prose/SKILL.md:157-171).
- Runtime coupling: gaze requires native /review and /simplify seats; every 1084-1086 verdict in detached Pi seats ESCALATEd on that alone (memory/topics/raid-review-and-merge.md:73-76). The gaze → Agent C → perspectives chain is three levels deep, a known degradation cause (no-agent-tool/depth, raid:292-297; memory:56-66).
- Naming constraint: `review` is a built-in command; rules/authoring-skills.md forbids a name the runtime already binds.
- The overrun also had other causes: bootstrap failures and timed-out semantic and gate processes (journal:29-31). No restructuring fixes those.

## Shared core (all options): one evidence record
- Where: the structured review comment review-pr already posts on the MR (the one it already counts for rounds). No second store. Not a file on the branch (committing moves the head it describes); not under .git/ (machine-local).
- Format: fenced `review-evidence: v1` YAML block: mr, mode code|prose, base (merge-base sha), head sha, risk row (decorrelation.md:17-21) + reason, scope {path: post-image blob sha}, seats [{perspective, worker, family, verdict approve|comment|request-changes, status ran|no-report, reused-from}], panel-integrity OK|DEGRADED <reason>.
- Reuse decided by a small deterministic script extending scripts/review-pr-anchor.py, not by a model. A seat is reused only if: verdict approve and status ran; every scope blob unchanged; any base move leaves the reviewed paths alone (git diff old-merge-base new-merge-base -- scope is empty).
- Re-review triggers: changed scope blob → re-run objecting seats plus one regression seat over the change (today's rule review-pr:220-234, keyed to blobs instead of count); new path or >~half lines rewritten → full plan (review-pr:236-241); base change touching scope; raised risk row or review:standard request.
- no-report seats never reused and never count as approval.
- Departure: gaze kept a full battery on an unchanged diff because of the #562 lesson (gaze:288-292). Dropped as automatic: re-running unchanged seats is replication (decorrelation.md:9). The plan may still buy a priced replication or other-family seat when risk justifies.

## Option A: one review skill with content modes (recommended)
- review-pr (name kept) takes mode=code|prose|auto (auto via scripts/prose_predicate.py). Prose body → skills/review-pr/references/prose.md; code panel → references/code.md; router keeps the shared contract (panel manifest, artifact polling, anchor, evidence block, reuse script). Simplification becomes a code-mode perspective via the portable route in gaze:556-571. Native /review and /simplify become optional adapter seats, never required. Standalone invocation preserved and reuses evidence the same way.
- hunt owns the plan: before step 11 picks risk row and budget, passes them to review-pr, runs verify-gate once at the end. Adherence step stays; its result becomes head-keyed evidence.
- raid coordinates tickets and merges; phase 6 = rebase, review-pr (reuses evidence; zero seats if nothing relevant changed), verify-gate.
- verify-adherence, reviewers unchanged.
- Deleted: review-pr-prose (→ references/prose.md), the gaze battery and skills/gaze/telemetry.yml, agents/gaze-pr-review.md, gaze tier tables (gaze:223-257).
- Naming: keeping review-pr resolves the clash: one name for the object (an MR), modes for content; avoids a ~40-file rename. Any alternative name must be checked against the Claude Code, Codex and Pi command lists; `review` is barred.
- gaze: ~15-line alias `review-pr <mr>` then `verify-gate <mr>`; a repeat call on an unchanged head runs no seats. Keep one release, then delete.
- verify-gate: all non-negotiables unchanged (verify-gate:31-58). Added: the latest evidence block must cover the final head and base (blobs equal, base change disjoint) else REROLL "stale review evidence"; a required seat with no-report → ESCALATE. Merge stays caller's.
- Runtime: portable only (forge comments, git plumbing, subagent or detached headless seats with artifact polling, already in place). Removing gaze cuts nesting depth by one. review-pr's `context: fork` frontmatter is a Claude Code convenience only.
- Size: ~35-45 files (incl. ~20 tests referencing gaze/review-pr, two profiles, rules/git.md:23-24, rules/workflow.md:110, skills/merge/SKILL.md:92, README catalog) → 15-file breaker → tracker + 3 children: (1) evidence block, reuse script, verify-gate stale check, behavioural regression tests (~6 files); (2) hunt owns plan, raid phase 6, gaze alias, gaze-pr-review deleted (~12 files); (3) fold prose into mode, delete review-pr-prose, profiles and catalog (~12 files).
- Price: ~8 agent-hours, ~1.5 author-hours.
- Closing-time effect (estimate, no per-phase timings recorded): unchanged heads close by rebase + evidence check + gate + merge; removes one full panel cycle plus gaze A/B/simplify, ~10-25 min per MR. Launch/timeout failures untouched.
- Main risk: a wrong reuse decision is approval nobody gave. Defence: deterministic script, behavioural tests, verify-gate recomputes blob comparison independently.

## Option C: delete the second battery only (smallest change)
- Keep review-pr and review-pr-prose as is; add the evidence block and reuse rule to both; gaze → alias; raid phase 6 = rebase, review-pr, verify-gate. Plan ownership, reuse and verify-gate as in A; reuse rule written twice.
- Size ~25 files, 2 children (A's 1 and 2). ~4 agent-hours, ~0.75 author-hours.
- Closing time: same as A (estimate); nearly all of A's saving.
- Risk: naming clash stays (justified, not resolved); "keep in sync" duplication grows. C is A's first two children, so it does not close off A.

## Option B: separate helpers, hunt orchestrates (no top-level review skill)
- review-pr → review-code, review-pr-prose → review-prose, separate panel helpers; plan logic in skills/hunt/references/review-plan.md; no third `review` router. gaze, verify-gate, evidence as in A.
- Problems: standalone review loses plan/reuse unless helpers duplicate them; hunt grows past 133 lines; two renames touch ~45 files, 3 children, ~10 agent-hours, ~2 author-hours; no extra closing-time saving vs A.
- Risk: helper panel contracts drift; reuse only enforced when hunt is caller.
- The three-skill candidate (review router over code/prose helpers) = B plus a layer with no demonstrated need, and its name collides with the built-in. Not put forward.

## Ranking
1. A — one mechanism, one reuse rule, deletes three components, resolves naming without rename.
2. C — half the cost, nearly all time saving; first step if naming is deferred.
3. B — costlier, two panel contracts, standalone review outside the plan.
None addresses the launch/timeout failures (journal:29-31); those belong to a separate ticket.
