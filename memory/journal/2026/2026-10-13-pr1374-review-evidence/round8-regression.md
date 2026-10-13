# PR 1374 — round 8 scoped regression

Scope: one regression check covering round-seven cleared Correctness, Consistency, Scope and Doc propagation. Reviewed only `ddc6210ab38d1b6f2e49f7f4f9c0c92758591ab2..c3d769ef70a2893063a666d44b2f191186ff5041`, with the native-delete context, previous reports and author-revised ticket 1084 criteria. This is not a full re-review, gate reset or merge.

Reviewer route: requested OpenAI gpt-6.1-sol, medium effort. The runtime does not expose a provider-qualified full backend ID. Same OpenAI family as producer; this seat is not cross-family independent.

Anchor: HEAD `c3d769ef70a2893063a666d44b2f191186ff5041`, base `refs/remotes/origin/main` at `8208787ea3be115ca6056d187a31db4bf3a6f0e0`. Anchor helper passed before and after review with the same ten-path full-PR roster.

No regression findings.

At `skills/roar/close-and-clean.sh:330-343`, the nonempty per-approved-OID alias is used only when the scoped config-regexp exits 1. Any configured alias key, including fetch-only configuration without a URL, retains the target with findings status; unreadable config yields 2. Native `branch -d` still performs its HEAD merge and worktree checks, without persistent upstream edits. Unexpected deletion exits, including 139, now yield 2 and explicitly report native failure rather than ordinary refusal or assumed preservation.

The patch adds no candidate enumeration, worktree removal, recovery, lock, or persistent config mutation. Explicit just-completed task targets and caller-owned worktree obligations remain intact; unrelated housekeeping stays with Lair/Molt. The updated description at `skills/roar/SKILL.md:374-389` matches this implementation and preserves the non-atomic precheck limitation. Ticket history records the bounded fix without resetting the gate ledger or claiming future measurement 1090 complete.

Fresh validation: `bash /tmp/idh-review-1374-revision/tests/test_roar_close_and_clean.sh` exited 0 with 132 PASS assertions on Git 2.53.0 (log `/tmp/regression-1374-shell.log`). This includes merged push-u local cleanup, configured fetch-only alias retention, unreadable alias inspection, unexpected native exit 139 classification, late unmerged self-tracking refusal without crash, preserved upstream configuration, occupied-worktree refusal, foreign-ref preservation and bounded-fetch controls. `git -C /tmp/idh-review-1374-revision diff --check ddc6210a..HEAD` passed.

Evidence correction within this same review: the producer record is the regular file `.panel/1374/producer-validation.md`, rather than a directory. After the caller supplied that exact path, direct reads succeeded. I inspected it and the regular `/tmp/revise-1374-round7-{full,adherence,fast,preflight}.log` footers: full 1603 passed / 4 skipped in 78.80s; adherence 185 passed; fast 960 passed; preflight 11 passed. The record says runtime/tests/docs were frozen before these runs and only a factual ticket note followed. These are producer runs; this seat independently reran only the 132-assertion shell suite, not the full suite.

Verdict: **approve**.
