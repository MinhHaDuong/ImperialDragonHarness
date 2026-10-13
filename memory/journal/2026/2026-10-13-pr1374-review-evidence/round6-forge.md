# PR 1374 review round 6

Forge review: PRR_kwDORsAV3c8AAAABR_3yKQ
Reviewed commit: 3a5fcb313cb952694e5d24f1acc2a938e511cb54
Submitted: 2026-10-13T11:28:09Z

## /review-pr round 6 — author scope revision

Reviewed HEAD `3a5fcb313cb952694e5d24f1acc2a938e511cb54`, base `8208787ea3be115ca6056d187a31db4bf3a6f0e0`. Full proportional panel: ten changed paths; rewrite/reset exception changes the roster, not the historical round count. The author explicitly limits Roar to current completed-task targets; repository-wide cleanup belongs to Lair/Molt. No gate reset or merge approval is implied.

### Findings

- **Correctness, blocking:** `skills/roar/close-and-clean.sh:139` compares the two Git metadata reads without checking their success. Both failing with exit128 produce empty==empty, skip preflight and report clean0 even in a dirty linked worktree. A normal dirty-tree positive control returns1. Reproduced in a private /tmp fixture.
- **Red team, medium/high confidence:** `skills/roar/close-and-clean.sh:225` uses bare fetch and honours configured fetch refspecs that can rewrite unrelated local refs. Actual Git reproduction: `remote.origin.fetch=+refs/heads/other:refs/heads/scratch` rewrote unmerged scratch while another target was cleaned, with clean0. Fetch must be scoped explicitly and ignore configured mappings. Scope seat approved the explicit deletion targets; its approval did not catch this fetch side effect.
- **Red team, minor verifiable:** `skills/roar/close-and-clean.sh:267` silently skips default/current/HEAD/occupied targets while the documented contract reports retained targets. Emit a retention reason and findings status.
- **Consistency, minor consider:** `skills/roar/close-and-clean.sh:9` says missing ticket store means2; supported no-ticket-store case is skip0. Distinguish absence from unreadable existing store.

The removed generic enumeration and delete-and-restore parsing address the prior implementation design. All five seats report the explicit cleanup/worktree ownership contract respected except the concrete fetch side effect above. No universal concurrent-writer guarantee or new global lock was demanded.1090 preserves future measurement;1089 remains the explicitly authorised nonclosing discovery.

### Evidence and integrity

Producer validation: shell87 assertions, fast960, mechanical adherence185, full1603 passed/4 skipped. Correctness independently reran shell87 and reproduced preflight failure. Red team used actual isolated Git reproductions; it read only the test tail, not the whole test file. Other seats inspected the actual SHA-specific diff. No full-suite rerun by this panel is claimed. Source was anchored before/after each seat.

Actual CLI metadata reports claude-sonnet-5-5, medium launch, session1f43ae63-d61c-4df3-b223-fa6f4f41599b, successful report; reported list-cost estimate $0.3136538. Producer is selected gpt-6.1-sol medium (OpenAI), so this Anthropic seat supplies cross-family coverage. The raw seat called itself not cross-family as a standalone seat; that statement does not describe the producer/reviewer pair. Collaboration exposes selected pins rather than full backend provider/version evidence. No missing seat; no backend identities invented.

### Verdict roster

- correctness: request-changes
- consistency: comment
- scope: approve
- doc propagation: approve
- red team: comment (its fetch finding explicitly requires correction before merge)

Synthesis: **request-changes**. Dissent is retained: Scope and Doc propagation approve; Correctness blocks on metadata failure, Red team found the fetch rewrite. Parent has authorised the cheap fixes under the requested revision, with regression review to follow. The historical gate cap remains unchanged.
