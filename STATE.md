# Imperial Dragon Harness — State

Last updated: 2026-10-13T17:40Z
Housekeeping (molt) run: 2026-10-13T17:40Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-13T17:40Z · as of 07bf3281 -->

**Tickets:** 7 ready · 6 blocked — `erg ready tickets/` for full list
  next: 1045 Local merge gate replaces the forge's required … · 1048 Model tournament cycle 3: locals @medium vs hos…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  07bf3281 Merge pull request #1384 from MinhHaDuong/roar-dream3-2026-10-13
  bdf25e00 Merge pull request #1382 from MinhHaDuong/dream/2026-10-13-third-dream
  240d1dc8 Merge pull request #1383 from MinhHaDuong/chore/drop-legacy-index-link-pin

## Ready work
Ready: 1045 (local merge gate), 1048 (cycle-3 completion), 1077 (worktree opt-in), 1080 (adherence semantic phase), 1087 (arena provider errors), 1089 (npm-global Pi linking), 1090 (post-merge Roar measurement). Six other tickets are deferred, including 1050 blocked on hardware 1049.

## Resume point
Main passed `make check`: 1603 passed, 4 skipped on doudou (2026-10-13). Tickets 1092, 1091 and 1084 are closed through #1377, #1378 and #1374. Roar cleanup now uses explicit completed-task targets; 1090 retains the unmeasured performance follow-up. The third Dream is accepted through #1382; #1383 removed the duplicate-index test pin.
Housekeeping removed four inactive, clean historical worktrees and four orphan session scratch directories. No WIP was found. Merged Roar branches were deleted; rewritten historical commits remain pushed on `dream/2026-10-07`, `t1084-roar-close-and-clean` and `archive/review-1319-20261013`.
Review-attribution gaps for #1374 and 69 unresolved historical backfill records remain documented in the journal; no missing identities or revision coordinates were inferred.

## Next actions
Continue from `erg ready tickets/`. Complete cycle 3 under 1048 before treating its results as routing-grade; role-split redesign remains deferred under 1061. Publication correction 1093 stays deferred, with its frozen bundle in the arena repository; no publication ran.
Zotero reconciliation reports 28 staging files absent from the consulted index (report-only; no import or purge). Inspect provenance before any archival action.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the Zotero client via the report from `python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html` (0485 closed; author-side chore).
- Zotero train residue: run `idh check` for the dangling installed skill symlink (1018); decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
