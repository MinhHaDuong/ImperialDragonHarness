---
name: feedback-green-prs-red-union
description: Two PRs each green and each reviewed can merge into a red main — only a wave-level integration check can see it, and per-PR gates cannot by construction
metadata:
  type: feedback
---

Ticket 0261 added a guard failing any hard-coded model id under `bench/`. The
same evening, a parallel session merged issue-30 drivers that name
`Xenova/all-MiniLM-L6-v2` directly. Each PR was green. Each passed a five-seat
review. Their union turned `main` red within minutes of the second merge
(2026-08-29, raid 240).

Nothing was wrong with either review. A per-PR gate evaluates branch ⊕ base at
the moment it runs, and neither branch contained the other's change. The defect
lives only in the combination, so no amount of per-PR rigour reaches it.

**Why:** with many sessions running in one repo, the *union* is a state nobody
tested. It is also the state everyone then works from — a red `main` blocks every
parallel session at once, so the blast radius is the whole team rather than one
branch.

The guard being new is what made this visible rather than merely true. A guard
lands with a scope claim ("nothing else in `bench/` names a model") that is
retroactive: it asserts something about files it has never seen, including files
arriving in flight. That is the arrival case, and it is the half that a
registry-derived or removal-only check misses entirely.

**How to apply:** when a change adds or widens a *gate* (not just code), run it
against `origin/main` as it will exist after the other in-flight PRs land, not
only against your branch — `git merge origin/main` into the branch and run the
gate, immediately before merging, even when the mergeability status reads CLEAN.
After merging, run the full suite on `main` itself rather than trusting the
merge's clean exit; here that check is the only thing that caught it, and it took
one command. The raid's wave-level integration review exists for exactly this and
is the step most tempting to skip when every individual PR came back approved.

Second lesson, from the fix: six guard hits were not six of the same thing. Two
were real wiring; four were prose — docstrings and a result's own provenance
label — where the guard's remedy ("resolve it by registry id") is *impossible*.
A flagged site whose prescribed fix cannot be performed is a scope error in the
guard, not a defect in the file. The repair was a per-line exemption carrying its
reason, never a per-file pass, with a test requiring an unmarked assignment
beside a marked comment to still fail.

Related: [[feedback-a-move-can-leave-the-gate]],
[[feedback-guard-the-silent-failure-first]].
