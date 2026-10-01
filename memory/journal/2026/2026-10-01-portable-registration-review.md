# Portable registration review and split

The harness registration PR [#1091](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1091)
was reviewed while parallel sessions changed memory design, agent entry points,
compute policy and scheduling. The author assigned memory to another session
and requested removal of all migration-specific controls.

The first gate returned REROLL. Findings included a dream commit targeting
memory outside the selected repository, a provenance path gap, destructive
merged-hook removal guidance and an unrecognized shipped Codex hook predecessor.
Five memory helper/procedure/test changes were extracted to the unapproved
`handoff-portable-memory` branch at `5ff0a2e5`; ticket 1002 records those defects.
The registration PR corrected hook handling and removal documentation, removed
historical migration tests and path-spelling ratchets, and retained current
installation, guard and configuration-preservation tests.

A later review found receipt adoption of pre-existing hook links and destructive
repair advice. Both were corrected; a non-executable launcher check was added.
The registration child was renumbered from 1001 to 1003 after a parallel memory
design PR independently allocated 1001. The existing memory ticket was retained.

At reviewed tip `5a4bf5dadef4ea363bca7163edc33302d6130e09`, the full suite passed
1267 tests with 2 skipped; lint passed 93 tests. Gate round 2 approved all five
child criteria. Original author live-runtime smoke evidence was explicitly
distinguished from final-tip fixture runs. A read-only merge-tree check against
the newly merged memory work verified that its files survived byte-identically.

The merge helper closed and archived only ticket 1003 in `cc4a2a75`. After all
ten checks passed, the queued merge was finalized without bypassing protections.
PR #1091 merged as `8af5cd16152306383e97a43c0f76d98f0bdf132a`. Parent 0999 and
memory child 1002 remain open. No runtime profile or memory data was deployed.

The shared primary checkout remains on `docs-portable-agents-plan` with unrelated
local modifications. The review worktree was removed after its reports were
published; author and memory handoff worktrees were preserved. A close-claim
audit from the current-main wrap-up worktree examined 40 recent PRs and 14 close
claims, finding none dropped. The same audit from the old primary checkout had
reported three absent newer tickets; those were present in the current ref.
