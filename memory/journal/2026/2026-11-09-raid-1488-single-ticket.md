# Raid 681f31 on ticket 1488 (update-publist prior record check)

Date: 2026-11-09. Context: `/raid 1488`, one ticket, one wave, PR #2336
merged at fc890a2a. Orchestrator Fable 5.1; reimagine Sonnet 5.5; blind-spot
Opus 5.5; executor Sonnet 5.5 (coder profile, hunt inline); gaze self-only;
verify-gate APPROVED round 1 (3m10s); merge 24s.

Observed:

- The Blind-Spot pass changed the plan materially. The reimagine agent
  found no "release record template" in the repository and proposed an
  in-skill block as the template. The Blind-Spot agent located the
  release-journal entry prose of `skills/paper/references/{submitted,
  resubmitted,accepted}.md` as the record every HAL deposit is routed
  through; the plan edited those three lines in addition to the block.
- `scripts/scoped-check.py` exits with an error in this repository: it
  needs an `.idh-checks.json` map and the harness has none. The executor
  fell back to the full `make check-fast`. `skills/raid/references/fix-and-regate.md`
  names scoped-check for a mapped doc-only fix.
- `raid_log.py` refuses `PR step=merging`; the vocabulary is `executing,
  gaze, gate_round_N, merged, escalated`, so the merge step has no in-flight
  value in the sitrep.
- `make check-fast` with `TMPDIR=$W/.tmp` reproduced the three known
  "outside a git repository" failures; they passed by name with the default
  TMPDIR (memory: hunt TMPDIR breaks git tests).
