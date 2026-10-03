# Verification-loop raid 2026-10-03 — WAVE_BASE's first live run, mid-gaze merge, orchestrator-run gaze

Raid on tickets 1016, 1017, 1021, 0879 (wave 1) and 0990 (wave 2), run
concurrently with a second session's raid on the attribution train (1004-1009),
both operating from the same primary checkout of this repo.

## Observable events

- **WAVE_BASE used live before its own fix landed.** All four wave-1 branches
  forked from one annotation commit (27378b86, 1016's approved option 1);
  the per-wave integration review found zero ticket-file conflicts across all
  six PR pairs (`git merge-tree --write-tree` clean), versus the 2026-10-02
  raid's three divergent annotation copies. The parallel session advanced
  origin/main mid-wave (PR #1165); no collective rebase was needed because
  the wave PRs merged before branching again for wave 2.
- **A PR merged mid-gaze.** PR #1161 was merged (by the parallel session /
  author) while its gaze round was still open; the gaze returned ESCALATE
  with a mechanically reproduced defect in the collective-rebase text and a
  validated fix commit on the branch. The resolution was a gated follow-up
  PR (#1166) carrying the fix, itself gazed (one REROLL round fixed an
  unexecutable `git rebase --onto` form for worktree-held branches) and
  merged. Pattern: an ESCALATE caused by a premature merge resolves through
  a follow-up PR, not by re-opening the merged one.
- **First observed orchestrator-run gaze (ticket 0990's own mechanism).**
  The gaze on PR #1167 was run by the raid orchestrator itself (top-level
  session, native agent-connector seats, artifact-polled) — recorded in
  ticket 0990's log as the exit-criterion-1 observed run. The round-1 REROLL
  exercised ticket 0879's reroll_bump flow end to end: the fix agent posed
  the `note bump verify-reroll` line onto the PR branch via the re-vendored
  erg (landing contiguous), never on main mid-wave.
- **0879's corpus reality.** The "malformed" log-entry shape the ticket
  described is `appendLogLine`'s own systematic output (460/534 harness
  ticket files; upstream 262/286); the incident shape and erg's shape are
  byte-identical. A blocking read rule would have wedged both repos' gates;
  the landed design is normalize-then-append on write plus advisory WARN on
  read (position and monotonicity), with the norm added to
  tickets/spec-erg-v1.md. `erg check tickets/` now reports ~543 advisory
  warnings by design, exit 0.
- **Detached CLI seats worked as the transport for child-session panels**
  (1017's documentation dogfooded by its own executor and by every gaze run
  this raid): one headless process per seat, one-string deny rules, artifact
  polling, spawn success never trusted. A vibe-transport limitation was
  recorded in ticket 1017's log (detached `vibe -p` seats blocked by the
  runtime's approval policy; claude transport worked).

## Outcome

All five tickets closed and archived; six harness PRs merged (#1161, #1162,
#1163, #1164, #1166, #1167) plus upstream git-erg#375; `make check` green
throughout (baseline 1350 → final 1371 passed, 2 skipped, the delta being
the raid's new pin tests). Follow-up ticket 1023 (stale bump-line consumers)
was filed by the 0879 executor and rides that merge.

## Decisions already made (recorded elsewhere)

- 0879's advisory narrowing (WARN, not reject) — tickets/0879 log, author
  informed with veto window at review; merged without objection.
- 1021's upstream Vibe issue filing deferred to the author (wrap-up list).
