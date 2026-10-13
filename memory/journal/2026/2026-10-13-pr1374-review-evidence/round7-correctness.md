# Correctness — PR #1374, round 7

Anchor: `ddc6210ab38d1b6f2e49f7f4f9c0c92758591ab2`, base `refs/remotes/origin/main`; anchor helper passed before and after review. Reviewed the complete `3a5fcb313cb952694e5d24f1acc2a938e511cb54..ddc6210ab38d1b6f2e49f7f4f9c0c92758591ab2` revision against the prior review and corrected completed-task contract.

Identity: requested model pin `gpt-6.1-sol`, medium effort. Runtime identifies this agent as GPT-6; backend identity is not independently attestable. Same OpenAI family as producer Sol6.1 medium: this is not an independent seat. No gate or merge invoked; historical gate cap remains intact.

## Prior finding resolved

The round-6 preflight fail-open is fixed at `skills/roar/close-and-clean.sh:141`: each metadata command must succeed and produce nonempty output before the directory comparison can authorize a skip.

Reran the identical isolated fixture `/tmp/correctness-1374-7_ym9dlj/peer`, a linked worktree with untracked `uncommitted.txt`. Positive control with real Git still returns 1 and reports DIRTY. The same PATH wrapper returning 128 for metadata `rev-parse` now returns 2, reports `PREFLIGHT: COULD-NOT-LOOK`, and never reports clean. The uncommitted file remains in both cases. The new shell controls additionally cover failures of either metadata path individually and verify review scratch is preserved when reads fail.

## Regression verification

- Ran `bash /tmp/idh-review-1374-revision/tests/test_roar_close_and_clean.sh`: exit 0, all 117 assertions pass. Late unmerged self-tracking tips, concurrent occupied worktrees, and remote competing pushes remain refused.
- New direct and opportunistic configured fetch mappings preserve unrelated unmerged local heads. The exact integration-only refspec plus empty refmap at `skills/roar/close-and-clean.sh:254` avoids configured foreign ref writes, while symbolic integration destinations are refused before fetch. Tags, pruning, recursion, and automatic maintenance are explicitly disabled.
- Default/current/occupied targets are retained and reported as findings; no-target cleanup remains a clean no-op. No cleanup candidate enumeration or delete-and-restore behavior has returned.
- The updated Roar pre-check and step-9 prose propagate bounded fetch and exact integration ref names. Metadata/fetch failures explicitly preserve work and stop before the patch-equivalence fallback; fallback remains available after successful fetch when ancestry fails.
- Reviewed producer logs: core full suite 1603 passed / 4 skipped before doc-only propagation; after SKILL changes and one static assertion change, 13 implicated ratchets and 185 mechanical adherence checks pass. Those full/static runs are producer evidence, separate from this seat's fresh shell suite and original-repro rerun.

No remaining correctness findings or regressions in this revision. No universal concurrency guarantee is assumed. Authorized discovery 1089 and post-merge measurement 1090 remain within the settled scope; measurement is not claimed as completed now.

Verdict: **approve**.
