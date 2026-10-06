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

## Follow-up CI observation

The first CI run for wrap-up PR #1217 tested synthetic merge f585e2e02601d13ce9a19a16b406518c46c2df82, built on base bd2efaad7cbf0a44d57545a68ebf9394aaef8157. Its pytest-guard reported 3 failures, 1484 passed, and 9 skipped: three projection-validator assertions expected diagnostic strings removed by PR #1209. PR #1215 merged the test correction during that CI run as bab206ac586277d6b85b1a3d0344b9189c4bf540; ticket 1040 records the correction and passing follow-up validation.

- Wrap-up PR: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1217
- Failed CI run: https://github.com/MinhHaDuong/ImperialDragonHarness/actions/runs/37406917572
- Corrective PR: https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1215
- Corrective ticket: tickets/closed/1040-repair-projection-tests-after-generic-in.erg
