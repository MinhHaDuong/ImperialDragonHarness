# Imperial Dragon Harness — State

Last updated: 2026-10-15T19:59Z
Housekeeping (molt) run: 2026-10-15T20:01Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-15T19:59Z · as of 82ad5096 -->

**Tickets:** 5 ready · 2 blocked — `erg ready tickets/` for full list
  next: 1045 Local merge gate replaces the forge's required … · 1100 Implement review orchestration: gaze as the sin…
**In flight:** 2 open PRs, oldest #1422 0d · CI main: failure
**Recent (first-parent):**
  82ad5096 Merge pull request #1438 from MinhHaDuong/hoard-20261015
  8feefc51 Merge pull request #1437 from MinhHaDuong/fix-1111-reconcile-empty-reports
  e39653f4 Merge pull request #1436 from MinhHaDuong/housekeeping-20261015

## Ready work
Ready: 1045 (local merge gate), 1100 (review orchestration implementation; file its planned children before implementation), 1111 (Zotero repair merged in #1437; ticket still open), 1112 (reconcile trigger decision), 1113 (slow index rebuild).
Blocked: 1099 waits on 1100. Deferred: 1095 (task-owned tmp cleanup and crash recovery).
Arena work remains in the independent repository; see docs/arena-integration.md.

## Resume point
The fourth Hoard is accepted through #1438. It consolidates 29 new journal sources into eight topics, retains measurement/attribution uncertainties, and keeps the index at 30 lines. Canonical Hoard/Yawn activation remains verified across Claude, Codex and Pi.
Main at `82ad5096` passed `make check` on padme: 1640 passed, 3 skipped in 51.97s. Premerge local CI passed all ten jobs (container pytest 1633 passed, 10 skipped). Yawn's fast probe passed 987 tests. The postmerge forge run failed only the skill-seam byte snapshot: `.git/objects/maintenance.lock` vanished in an unrelated fixture. The housekeeping branch disables automatic Git maintenance for that fixture; its full gate passed 1640 tests, 3 skipped in 50.99s.
Review attribution for #1423/#1425 remains pending because producer or initial reviewer context facts are unavailable; masked model pins remain masked. #1438 had no recorded review, so no review-attribution entry was invented.
The task's hoard branch/worktree were removed after merge. The foreign Arena checkout `/tmp/arena-cycle3-routing` and locked CI worktree `explore-ci-speed-2014346` were retained. Housekeeping removed three orphan scratch directories (12 KB), retaining both live sessions. No other worktree or branch was deleted.

## Next actions
Continue from `erg ready tickets/`. Other work has open PRs #1422 (morning factual capture) and #1431 (tentative review storage/delivery proposal for 1100); neither belongs to this session.
Zotero staging reconciliation no longer runs in `/molt` or `/lair` (#1434): it fired in any repository with `docs/` and stalled over 5 min on a stale index. Run `/zotero reconcile` on demand in paper repositories. The 1111 implementation landed in #1437 and integrated main now passes the full suite; its ticket still awaits administrative closure. Follow-ups 1112 (who runs the periodic reconcile) and 1113 (slow index rebuild) remain open. No library completeness claim or import was made.
Review attribution pending for #1423/#1425 is durably documented in the raid journal; do not fill missing identities from aliases or guesses.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the Zotero client via the report from `python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html` (0485 closed; author-side chore).
- Zotero train residue: decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
