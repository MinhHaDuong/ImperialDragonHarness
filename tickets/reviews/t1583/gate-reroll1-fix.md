# Gate round 1 citation repair

Caller reported REROLL on head `e437d0a2ac466dd1ee86dc22789e0b3514e1f30f`,
gate session `4b98ce4a-41a8-4fd4-9021-fd9ed44fe3c8`: agnostic guard failed,
and lint had 190 passes and one failure. The prior semantic source-equivalence
review did not catch the forge-specific URL violating skill portability.

Before repair, `./scripts/check-agnostic.sh skills` reproduced a
`github\.com` violation at `skills/replicate/references/assessment.md:156`
and exited 1. Only that citation now names ticket 1575 and the same reception
commit `12e3c106b3980a972bedabca69802e136809ff9f` in plain text. The cited source,
author ruling, and all rounding text remain equivalent; the guard is unchanged.

After repair, the same agnostic command exited 0. Full `make lint` exited 0:
===================== 191 passed, 3736 deselected in 7.92s =====================

No fast suite or substantive gaze was repeated for this reference-only delta.
The caller owns documented round 2 reroll-fix admission; no new gate approval
or updated substantive reviewed head is claimed here.

The first `erg log 1583` default lookup failed to find the archived ticket and
wrote nothing. The supported explicit store argument `tickets/closed` then
appended the exact requested `note verify-reroll — round 1: stable ruling
citation fails agnostic-guard and lint`. Closure/archive and the previously
released 1584 dependency are preserved. New 1589 pause authority is unaffected.
