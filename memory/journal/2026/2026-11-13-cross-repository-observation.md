# Cross-repository observation: doctor revisit

Observation begins with ticket 1545's merge, PR #2496, at
2026-11-13T19:12:05Z, commit `e882172dfc2c62deef15bfcef1ab0c9975769374`.
The author authorized the three provisional children and their undefer on
2026-11-13 (planning PR #2494), superseding their individual holds while the
design note remains provisional for future work. The receiving-project review
and implementation authority boundary was included in child 1546, PR #2495.

Revisit after 20 foreign tickets or on 2026-12-25, whichever comes first.
This is a doctor-journal revisit, without a reminder ticket. The accompanying
[baseline artifact](../../evidence/2026-11-13-cross-repository-baseline.json)
records the source revision and post-start foreign ticket log evidence; it is an initial observation, not evidence of reduced delay.

At the revisit, deduplicate receiving ticket IDs with a `filed from` log line
since the start. The baseline uses the canonical provenance parser; foreign
origin omitted from those logs remains uncounted, rather than inferred. For
each, read the filing log and the first receiving-owner
review/pickup action; report elapsed time only when both timestamps are
established. Count recorded premise corrections at pickup and parked askers
released with `unblocked by` evidence. Branch names and worktree locks show
current work, not its starting time; missing owner timestamps stay unknown.
A closure or a merged ticket-only PR alone does not establish delivery.

If reports wait unread, assess an enrichment-only intake review; if pickup
repeatedly corrects false premises, assess moving that review earlier. Those
are the original design's evaluation questions, not new authorized work.

## Release integration evidence

The final 1547 gate used isolated, committed ticket snapshots from the author's
arena (`587adf6b47dd409f5ae0e38d93e6a1df3554ccbb`) and harness
(`4742071c17af04e4f6a937aa8cd1dfc2f57fe74b`) repositories. Synthetic asker
9998/9999 and receiver 9997 exercised sibling-path and absolute-file-URI
references. Actual vendored `erg ready` changed from absent to present for
both askers after result verification; the receiver's bytes stayed unchanged.
The release log named closure `baafdc8364c625d9082060de7dc05d935a56c846`.
These are snapshot integration results, not changes to live project tickets.

The first smoke attempt encountered a no-op fixture commit on its second
iteration. The gate corrected the fixture with `--allow-empty` and measured
the actual closure using the header-change history query; the complete rerun
passed. The gate removed its temporary scratch
`/scratch/tmp/gate2497-smoke-zfhrbypr` and driver `/tmp/smoke-2497.py` after
recording the result. The source commits and result above preserve the
evidence summary.

## Raid integration and wrap-up

Planning/undefer PR #2494 and children #2496 (1545), #2495 (1546), and
#2497 (1547) merged in that order. Each child has REVIEWED gaze evidence,
APPROVED round-one gate evidence, and writer/reviewer attribution captured
under `memory/evidence/attribution/`. Planning was bookkeeping-only.

The integration union sweep on main `7a64bcdc2f532d2b584999d49deb4c627f8e999a`
read all child diffs and checked the canonical rule, helper call sites, and
procedure references in molt, dashboard, hunt, raid, and merge. The rule is
stated in workflow; callers reference it and its procedure. Both helpers and
their behavioral tests are present. No dangling helper or procedure references
were found. The resident-rule budget stayed unchanged by condensing this
cross-project unit and moving procedure detail to its linked resource.

The close-claim sweep found no dropped claims. It detected tracker 1544 as due
for integration review. Its first preflight reported the expected uncommitted
roar bundle; those files are preserved in this wrap-up commit, rather than
removed. No qualifying unrelated follow-up tickets were created.

The 1546 review first reproduced two mechanical reference failures, which were
fixed. A subsequent gaze setup anchored its review tree to the new head but
bound the answer to an older cached request; closing refused that mismatch.
Refreshing forge metadata and requesting the current head with the official
notes helper allowed an integrity-checked replay of the same-head seat. After
rebasing onto 1545, all six previously reviewed artifacts byte-compared equal;
a narrow gaze inspected that proof and the close bookkeeping before gating.

[Measured clocks](../../evidence/2026-11-13-raid1544-timing.txt) contain the
recipe's exact merge intervals and the final narrow 1546 gaze interval. Other
gaze intervals and exact full gate end epochs were not measured separately;
the printed slowest-step rows compare only the recorded intervals. The 1547
gate's internal clock reported 2m18s; its source start was 1794597708.680.

The temporary-candidate report was partial (history/PR listing limits and
unreadable entries). It was report-only; unrelated host state was left alone.


The full after-merge record on integrated main
`7a64bcdc2f532d2b584999d49deb4c627f8e999a` passed all declared checks,
including the complete test suite and adherence. Tracker 1544 was closed only
after that record and the union review. The subsequent wrap-up is bookkeeping.
