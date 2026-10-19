# Catalog grouping merge and observed auto-merge delay

2026-10-19. Audience: public repository work and already-made author decisions.

The author asked to merge the pending Generalist/Research catalog grouping,
keeping AGENTS outside this work. The42 metadata additions were divided into
four PRs below the15-file review breaker:1467,1468,1469 and1470. PR1472
contains the renderer, tests, generated skills-catalog.md and CONTRIBUTING.md.
All five merged; integration commitd32afaf863e27c8c9c5c41dc212dcb6ccf4eddda
contains the complete result. AGENTS was not changed.

The metadata-only reviewer initially approved top-level category fields.
The renderer reviewer found two pre-merge issues in combined snapshotff9e9529:
its adapted privacy test asserted only the last row, allowing a planted
private row earlier in sorted output; and the installed Codex validator
rejected the new top-level category field. The fixes compare every command
row and place categories under supported metadata.category. The same renderer
reviewer verified that disabling symlink exclusion now fails the privacy test
and that the previously rejected sample card passes the validator. These
were findings on unmerged implementation snapshots, not a commissioned
post-merge defect backfill; backfill is skipped for this wrap-up.

The corrected combined snapshot4dfe63f1 passed full make check:1763 tests,
3 skips. Selected local skill-lint and pytest container jobs both passed
(container pytest1671 passed,95 skipped); this was not the full ten-job local
CI. Each corrected metadata batch passed1758 tests with3 skips. All42 original
command-description rows were preserved. After the metadata PRs merged,
PR1472 was rebuilt atop current main with exactly4 changed files. Its whole
tree48d342e1868673db905b14abcfa75f4a43700863 equals4dfe63f1 byte-for-byte, so
prior full-suite/container evidence was explicitly reused. The renderer's
same reviewer checked the new base; fresh forge checks ran on29db8d57.

Earlier metadata workflows remained queued without assigned runners for a
period; this session did not establish a cause. Final renderer auto-merge
was armed at16:51:00 UTC; the last check succeeded at16:51:27. Subsequent
one-shot Roar pre-checks reported pending, including zero running checks.
The merge completed at16:58:22,6 minutes55 seconds after the final check and
7 minutes22 seconds after arming. Effective main rules required seven status
checks, all satisfied; no unmet rule was found. Timeline/API evidence did
not establish why the merge waited, nor distinguish a scheduling cause from
other causes. The user explicitly requested investigation before wrap-up.

Roar captured five validated attribution records and
[review evidence](../../evidence/2026-10-19-catalog-review-identities.md),
preserving reused contexts and runtime-masked full model pins. Same-family
multi-perspective passes were not independent model reviewers. The metadata
context was reused across all four PRs and their rechecks; the renderer
context was reused across initial findings, corrected review and final gate.

The integration-ref sweep found no remaining top-level category field or
unhandled catalog propagation issue. The remaining live README/catalog
references are in AGENTS, explicitly deferred by the author; the test's
historical README mention remains history. Close-claim inspection examined30
merged PRs,6 claims across5 PRs, and found zero dropped claims;5 bodies had no
recognized Ticket line. No task ticket or parent tracker applied.

The session-scoped report-only temporary scan found959 candidates. History
coverage was partial after3416 of11469 files under its20-second budget, with
2 unreadable history locations and15 unreadable candidate locations.
Unmatched ownership and descendant scope remain unknown. Nothing was deleted
by the scan. AGENTS edits remain in docs-refresh-20261019 and its original
worktree; its old grouping experiments are superseded by the merged catalog.
