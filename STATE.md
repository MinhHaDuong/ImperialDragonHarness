# Imperial Dragon Harness — State

Last updated: 2026-10-16T13:48Z
Housekeeping (molt) run: 2026-10-16T13:50Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-16T13:48Z · as of 99780e84 -->

**Tickets:** 2 ready · 2 blocked — `erg ready tickets/` for full list
  next: 1045 Local merge gate replaces the forge's required … · 1100 Implement review orchestration: gaze as the sin…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  99780e84 Merge pull request #1449 from MinhHaDuong/roar-20261016c
  13f3d4b7 Merge pull request #1448 from MinhHaDuong/t1116-zotero-search-lookup
  db9bcfe3 Merge pull request #1447 from MinhHaDuong/t1116-zotero-subcommands

## Ready work
Ready: 1045 (local merge gate), 1100 (review orchestration implementation; file its planned children before implementation).
Blocked: 1099 waits on 1100. Deferred: 1095 (task-owned tmp cleanup and crash recovery).
Arena work remains in the independent repository; see docs/arena-integration.md.

## Resume point
The Zotero helper train is complete. #1441 made `scripts/zotero.py` local-only (pyzotero local client, writes through the local API, launch-or-nothing; Zotero 10.0+ and an "Always Allow" key) and closed 1111 and 1113. #1447 and #1448 closed 1116: subcommands named for what they do, lookups through Zotero's own search, exact identifiers asserted and title hits returned as candidates; the hand-rolled title scorer was cut (3,100 → 2,789 lines).
Main at `99780e84`: forge CI green on #1447/#1448; yawn's fast probe passed 967 tests. Review identities for #1447/#1448: `memory/evidence/2026-10-16-review-identities-pr1447-1448.md`. Attribution for #1423/#1425 stays pending; do not fill it from aliases or guesses.
Housekeeping 2026-10-16 deleted the merged local branches `roar-20261016{,b,c}` and `arena-cycle3-routing`; worktree GC removed `/tmp/arena-cycle3-routing` (upstream gone). Retained: locked `explore-ci-speed-2014346` and `review-1447`, local `review-1441-head` (squash-merged PR head), remote `ccr-*` cloud-session branches.

## Next actions
Continue from `erg ready tickets/`. No PR is open.
Run `/zotero check-staging` on demand in paper repositories; `/molt` and `/lair` only propose it.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the Zotero client via the report from `scripts/zotero.py report-duplicates --out /tmp/zotero-duplicates.json` (0485 closed; author-side chore).
- Zotero train residue: decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
