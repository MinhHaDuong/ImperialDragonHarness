# Roar: raid a8b3e4 (tickets 1484, 1487, 1490) and four ticket filings

Date: 2026-11-09 night, host padme. Team lead of the interface session.
Merged, each read back MERGED on the forge:
- Filings (bookkeeping tier, `raid_land.py`): PR 2318 (ticket 1484, head
  a1ded7fc), PR 2324 (1487, head 0e3c8424), PR 2329 (1490, head 56fd5956),
  PR 2350 (1471, head cd3fb224, carried from the unopened branch
  `ticket-jetp-host-baseline-gate` onto a fresh branch, plus the claim file
  `erg check` required), PR 2353 (raid annotations, head b8a58c67).
- Work: PR 2354 (1484, head fc75d4b0), PR 2357 (1487, head 51518c7f), PR 2359
  (1490, head c270ca0c). Each gate verdict APPROVED in round 1.

Observations:
- 1484 was filed before PR #2325 replaced `submission-event` with `paper`.
  Its third exit criterion read on `skills/paper/SKILL.md`, which kept the
  hand-back clause "if the runtime refuses the load, ask the author to type
  it". The criterion text was left as filed. The replacement sentence says to
  load update-publist in the session that talks with the author, never in a
  delegated worker, since its gates say "the user" and no hook guards
  `make sync` or SWORD.
- 1487's premise ("cleanup does not consult .gitignore") did not match the
  tree: `worktree_residue` counts ignored files on purpose since ticket 1212.
  The fix is an opt-in `--ignored-ok` flag on `worktree-exit-preflight.sh`,
  refused outside `review-*`/`gate-*` trees; roar, lair, molt and
  `worktree-gc.sh` keep the strict rule. The criterion-3 observation (tracked
  files deleted then restored in a review copy) was recorded as not
  reproducible from harness code.
- 1490: gaze on PR 2359 ran three rounds. Two blocking findings came from the
  OpenAI red-team seat, each reproduced: a stale gate tree holding a commit
  nothing else reaches would have been removed, first with the directory
  present, then with it deleted. Both fixed before REVIEWED.
- The cross-ticket blind-spot pass redirected 1490 toward the existing
  `scripts/raid-gate.py` heartbeat and away from a new polling rule, and
  flagged that `tests/test_worktree_tools.py` was owned by the peer raid's PR
  2348; 1487's tests went to a new file.
- No permission-layer refusal on any of the eight merges.

Left out of scope: `worktree-gc.sh` still applies the strict ignored-file
rule to stranded review and gate trees (files owned by PR 2348).
