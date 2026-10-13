# PR 1374 review round 4

Forge review: PRR_kwDORsAV3c8AAAABR2Pxcg
Reviewed commit: 3cf977c313653942f804aff8c142d959121c3fd0
Submitted: 2026-10-12T15:15:05Z

## /review-pr round 4 — PR #1374 (RE-GAZE fixes)

Reviewed HEAD: `3cf977c313653942f804aff8c142d959121c3fd0`; base `origin/main`. Parent review-pr-anchor passed before and after battery. 7 content-bearing files / 1026 lines, high risk; fix patch `3dbdcbbf..HEAD` reviewed. This is panel-history round 4, **not** a fourth gate attempt. Scoped roster: prior objecting consistency, red team, scope + correctness/doc-propagation regression. All four distinct Pi subagent processes returned substantive SHA-specific reports; no simulated review.

PANEL-INTEGRITY: DEGRADED — native `/review` NOT-RUN/unavailable (missing built-in general review perspective). Four perspective seats and separate portable simplify are pinned via reviewer.md to openrouter/~openai/gpt-sol-latest, functions.subagent; evidence: actual completed tool reports + before/after HEAD and listed-file analyses. OpenAI lineage is cross-family versus recorded Anthropic producer; resolved model/version/effort masked, so alias/effort grid compliance NOT established. Adherence worker reports openrouter/~anthropic/claude-sonnet-latest/high; evidence: live contract, make lint 182 passed, unchanged refs/worktree roster/status. Sonnet high not benched grid medium; route mismatch explicit. Artifact/manifest polling NOT-RUN under caller no-edit rail; actual blocking tool completion collected each roster entry. Individual Python anchors restricted in reviewer profile, parent live anchor + per-seat HEAD reads substitute. Correctness/doc propagation represented by regression, not separate re-reviews. Optional external panel not selected. Full destructive fixture battery NOT-RUN under caller branch/worktree-deletion prohibition; earlier claimed full-suite success is historical evidence, not rerun here.

### Blocking regression
**Local deletion can remove a newly occupied branch** — `skills/roar/close-and-clean.sh:228-229` (red team and regression independently). Expected-old OID protects contents, not occupancy. A peer checks out the branch after final worktree snapshot and before update-ref; OID stays A, so CAS passes. `update-ref` lacks branch deletion's checked-out refusal. Parent non-mutating injection executes current source with mocked Git: `peer checks out topic AFTER final snapshot BEFORE update-ref`, `CAS DELETED ... occupied=1`, `RESULT: clean`, rc0. Same command-entry interleaving on actual pre-fix source `3dbdcbbf`: mocked `branch-D refused occupied topic`, rc1. No real branch/worktree was touched. Earlier-occupancy control preserves topic; unreadable occupancy list exit7 preserves topic and yields rc2. A second snapshot alone is insufficient; retain both frozen-OID and occupancy safety, or conservatively defer local deletion absent a coordinated guarantee. By-name deletion alone reopens the advanced-B race.

### Round-1 fix verification (parent-run, non-mutating Git fault injections)
- Lease reread: current approves A, tracking/remote advances B, lease refuses (1); pre-fix adopts/deletes B, clean0. Verified fixed.
- Enumeration: both/local-only/remote-only enumerator exit7 -> current could-not-look2; all corresponding pre-fix runs clean0. Partial sweep may proceed on readable side; no global nothing-deleted guarantee implied. Verified fixed.
- Fresh preflight: current SKILL9a:250-266 explicitly runs phase preflight after integration/wrap-up and before exit checks. Step-bounded assertion passed. Current clean linked head's **real** `--phase preflight` ran helper, ok/0; mocked clean and dirty helper gave0/1; pre-fix rejects new phase2. Verified fixed.
- Tag shadow: mock tag is above unmerged topic, qualified actual base below; current keeps local/remote topic, pre-fix deletes both. Verified fixed at script-order/ref-resolution level; no real tag/branch mutation claimed.
- Local A->B: current CAS expects A, refuses B (1); pre-fix by-name deletes B, clean0. Original race fixed, but newly occupied branch regression remains.
- touch: whitelist includes touch; sentinel now builtin redirection. Source assertion passed. Verified fixed.
- Prerequisite contract: mock absent tickets -> explicit CLOSE/CLAIMS skips and0; existing tickets with unavailable erg ->2/no clean; old absent-store path2. This keeps **inapplicable** separate from **could not inspect applicable storage**; clean means applicable operations clean, not skipped checks performed. Missing/nonexecutable check is not proof of executable runtime health. Stale header is informational documentation follow-up, not reopening settled behavior.
- 1089: orchestrator's explicit bundled bookkeeping disposition remains TICKETED/informational, not independently blocking and not remeasurement evidence.

### Guard-control adjudication
All five concern tests exist, but **not all individually stripped-and-destructive**. Parent in-memory guard mutants reproduced the source's expected outcomes without real deletion:
- symref stripped -> attempted invalid delete/refusal1, not destruction;
- default stripped -> mocked main deletion0;
- current + overlapping worktree guards stripped together -> mocked occupied branch deletion0;
- worktree guards stripped -> mocked other-session branch deletion0;
- force/CAS replaced with `branch -d` -> false retention/refusal1, not destruction.
Actual tests at test_roar_close_and_clean.sh:105-107,117-119,132-134,146-148,169-171 assert these distinct failures. Tests12a/b have mutants; enumeration, tag-shadow and standalone-preflight cases do **not** have paired mutants in the committed suite. Do not certify author's blanket mutant claim. Historical pre-fix comparisons above supply independent controls, but do not pretend these are new committed fixtures.

### Non-blocking
- consider: synchronize header's missing-store wording, DIRTY retry guidance and step10's historical `-D` wording with new code; narrow blanket mutation claims (script9-10,145; SKILL342-346; tests5-9,335-378).
- consider: make preflight documentation assertion step9a-bounded rather than grep anywhere; add late-checkout occupancy regression.

### Gate evidence / scope
Adherence make lint: 182 passed; four retained Python branch-cleanup ratchets pass. Full make check and real destructive shell fixtures NOT-RUN under caller rails, not represented as current passes. Portable simplify CLEAN with concrete rejected candidates (loop unification, PROBED abstraction, cached occupancy, stale preflight reuse, fixture consolidation); **not** a correctness approval. No fixes applied.
1084 boxes1-4 checked, box5 open. Criterion5 requires future postmerge roars plus journal; cannot certify before merge, no waiver claimed. Closing claim still names1084. 1089 is informational with explicit orchestrator disposition.

### Verdict roster
- consistency: comment
- red team: request-changes
- scope: comment
- regression (correctness + doc propagation): request-changes

dissent: red team/regression block on late checkout; consistency/scope report no new implementation blocker. Synthesis: request-changes on reproduced regression. Parent anchor unchanged; source status clean, branch unchanged. No edits, commits, pushes, real branch/worktree deletes or other-worktree access.
