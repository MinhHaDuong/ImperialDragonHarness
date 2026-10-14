# Imperial Dragon Harness — State

Last updated: 2026-10-14T20:36Z
Housekeeping (molt) run: 2026-10-14T20:36Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-14T20:36Z · as of 5d107443 -->

**Tickets:** 2 ready · 2 blocked — `erg ready tickets/` for full list
  next: 1045 Local merge gate replaces the forge's required … · 1100 Implement review orchestration: gaze as the sin…
**In flight:** 1 open PR (1 draft), oldest #1415 0d · CI main: in progress
**Recent (first-parent):**
  5d107443 Merge pull request #1414 from MinhHaDuong/t1096-design-close-2
  a58d4003 Merge pull request #1413 from MinhHaDuong/roar-1098-20261014
  6c0957aa Merge pull request #1409 from MinhHaDuong/t1098-roar-exit-check

## Ready work
Ready: 1045 (local merge gate), 1100 (review orchestration implementation: gaze as the single review skill; children 0-4 listed, file each before its work starts).
Blocked: 1099 (bounded review time) waits on 1100. Deferred: 1095 (task-owned tmp cleanup and crash recovery).
Arena-only work lives in the independent repository; see docs/arena-integration.md.

## Resume point
Design ticket 1096 is closed (#1414); its plan of record is docs/discussions/2026-10-14-1096-design.md (three panel rounds and the author's answers). Implementation is 1100. Tickets 1077, 1090, 1097 and 1098 are closed: sessions enter worktrees with plain git and roar leaves by cd plus `git worktree remove` (#1407, #1409).
Main passed `make check` on padme at 5d107443: 1592 passed, 3 skipped in 51.39s (2026-10-14T20:36Z).
Branch census 2026-10-14: remote branches are main, archive/review-1319-20261013 (kept) and ci-pytest-guard-speed (#1415). The superseded raid-1080-prep, raid-1089-prep, t1084-roar-close-and-clean and dream/2026-10-07 were deleted with the author's approval; stale 1097 and readback worktrees removed.
Arena remains independent. Routing consumes the independent arena's reviewed evidence through docs/arena-integration.md. 17 journal entries on main are not yet covered by an accepted Dream.

## Next actions
Continue from `erg ready tickets/`. Open PRs: #1415 (pytest-guard speed; its worktree explore-ci-speed-2014346 is locked with no session found running in it) and #1416 (roar journal, auto-merge armed).
Zotero staging reconciliation could not run on 2026-10-14T20:36Z: no ZOTERO_USER_ID in the flag, environment or ~/.config/keys/zotero.env. Author-side Zotero actions below remain outstanding.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the Zotero client via the report from `python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html` (0485 closed; author-side chore).
- Zotero train residue: decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
