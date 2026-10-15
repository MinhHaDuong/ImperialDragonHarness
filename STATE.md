# Imperial Dragon Harness — State

Last updated: 2026-10-15T10:37Z
Housekeeping (molt) run: 2026-10-15T10:37Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-15T10:37Z · as of dad86937 -->

**Tickets:** 2 ready · 2 blocked — `erg ready tickets/` for full list
  next: 1045 Local merge gate replaces the forge's required … · 1100 Implement review orchestration: gaze as the sin…
**In flight:** 2 open PRs, oldest #1422 0d · CI main: success
**Recent (first-parent):**
  dad86937 Merge pull request #1432 from MinhHaDuong/roar-raid1101-1103
  ec5571a7 Merge pull request #1430 from MinhHaDuong/t1109-hoard-docs
  2e108f5f Merge pull request #1429 from MinhHaDuong/t1106-hoard-memory

## Ready work
Ready: 1045 (local merge gate), 1100 (review orchestration implementation; file its planned children before implementation).
Blocked: 1099 waits on 1100. Deferred: 1095 (task-owned tmp cleanup and crash recovery).
Arena work remains in the independent repository; see docs/arena-integration.md.

## Resume point
Canonical memory consolidation is `/hoard`, using `memory/HOARD.md` and `memory/hoards/`; selected old-format projects migrate on the isolated invocation branch. `/yawn` is the repository healthcheck. Claude, Codex and Pi discovery and canonical links were verified; no managed old-name alias remains.
Main at `dad86937` passed `make check`: 1627 passed, 3 skipped in 53.00s (2026-10-15). Yawn's fast probe passed 972 tests. The integration raid is closed; its raw review trail and six validated attribution records are in memory. Attribution for PRs #1423 and #1425 remains pending because required producer or initial reviewer context facts are unavailable; model pins remain runtime-masked.
The foreign Arena checkout is retained at `/tmp/arena-cycle3-routing`, branch `arena-cycle3-routing`, head `2de660d9`; Molt GC removed its clean upstream-gone checkout and it was restored at the same commit. The locked foreign CI worktree `explore-ci-speed-2014346` is retained; #1415 is merged. No task-owned raid branch or worktree remains.

## Next actions
Continue from `erg ready tickets/`. Other work has open PRs #1422 (morning factual capture) and #1431 (tentative review storage/delivery proposal for 1100); neither was part of this raid.
Zotero staging reconciliation could not run on 2026-10-15: no ZOTERO_USER_ID was available. No library completeness claim or import was made. Author-side actions below remain outstanding.
Review attribution pending for #1423/#1425 is durably documented in the raid journal; do not fill missing identities from aliases or guesses.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the Zotero client via the report from `python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html` (0485 closed; author-side chore).
- Zotero train residue: decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
