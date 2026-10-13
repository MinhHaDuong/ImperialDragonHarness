# PR 1374 review round 7

Forge review: PRR_kwDORsAV3c8AAAABR__g3g
Reviewed commit: ddc6210ab38d1b6f2e49f7f4f9c0c92758591ab2
Submitted: 2026-10-13T11:39:42Z

## /review-pr round 7 — scoped confirmation

Reviewed HEAD `ddc6210ab38d1b6f2e49f7f4f9c0c92758591ab2`, base `8208787ea3be115ca6056d187a31db4bf3a6f0e0`. Reused the three objecting contexts (Correctness, Consistency, actual Anthropic Red team); one fresh regression seat covered cleared Scope and Doc propagation. No gate reset/merge.

### Verified fixes

Correctness reran the original metadata-failure reproduction: now2; dirty positivecontrol1. All117shell assertions pass. Consistency verifies header skip/2 contract and qualified boundedfetch instructions. Redteam independently reproduced both configured-fetch overwrite cases plus wildcard local-head mapping: foreign unmerged scratch remains, explicit target is deleted. Protected targets now have reasons/findings1. Regression finds no Scope/Doc propagation regression. Earlier recovery-output/tag-shadow/crash protocol remains removed.

### New functional finding

**Redteam, medium severity/high confidence:** `skills/roar/close-and-clean.sh:327` sets `branch.<target>.remote` to the empty string before native `branch -d`. On tested Git2.53.0 this crashes with SIGSEGV139 for an upstream-tracking branch, including a normal merged `push -u` source branch. It is retained rather than destroyed, but normal PR branch cleanup cannot succeed. The existing negative moved-tip test accepts retention and therefore also accepts this crash. Add a positive merged+upstream control and an actual surviving native HEAD-check form; retain unmerged self-upstream protection. Parent independently verified a command-local nonempty unconfigured remote uses native HEAD fallback on merged and unmerged fixtures; implementation must check that alias is unconfigured, including mappings without URLs, and not persist configuration. No unsafe plain-upstream deletion or global lock is requested.

### Evidence/integrity

Source runtime helper/behavioural tests passed full1603/4skip, shell117,fast960,lint185; after doc propagation and one static-ref assertion update,13 targetedratchets andlint185 passed. No exact-tip fullsuite rerun by panel claimed. Correctness andRedteam actually reran117shell controls. Same Anthropic CLI context1f43ae63-d61c-4df3-b223-fa6f4f41599b reports actual claude-sonnet-5-5, medium selected; reported list-cost estimate0.6511574USD for this returned run. It is cross-family relative to OpenAI producer. Collaboration backend IDs/versions remain masked. Allfour reports landed, anchored before/after, no missingseat.

### Verdict roster

- correctness: approve
- consistency: approve
- regression (cleared Scope/Doc propagation): approve
- redteam: comment (functional failure requires correction before completion)

Synthesis: **request-changes** for normal upstream-tracking cleanup functionality. Safe retention is acknowledged; the PR still needs to perform the cleanup it promises. Parent has authorised that final bounded fix under the revision request. Historical gate cap remains unchanged.
