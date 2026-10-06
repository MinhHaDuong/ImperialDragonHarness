Date: 2026-10-06

Context: PR #1212 closed ticket 0913 after the memory-v8 dispatch. The ticket file moved from tickets/ to tickets/closed/.

## Observations

The first pytest-guard run for PR #1212 reported 6 failures, 1482 passed, and 9 skipped. Three documentation files still linked to the ticket under tickets/, and two tests searched only the tickets/ root.

## Observed result

The PR branch updated four relative links in three documentation files and changed two test searches to tickets/closed. The subsequent pytest-guard passed; all 10 required checks passed, and PR #1212 merged as bd2efaad7cbf0a44d57545a68ebf9394aaef8157.

## Evidence

- PR: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1212
- Ticket: tickets/closed/0913-retire-the-dead-retention-machinery-and.erg
- Fix commit: bd2efaad7cbf0a44d57545a68ebf9394aaef8157
