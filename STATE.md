# Imperial Dragon Harness — State

Last updated: 2026-10-13T20:22Z
Housekeeping (molt) run: 2026-10-13T20:21Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-13T20:22Z · as of ba8456ca -->

**Tickets:** 5 ready · 0 blocked — `erg ready tickets/` for full list
  next: 1045 Local merge gate replaces the forge's required … · 1077 Decide the session EnterWorktree opt-in after a…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  ba8456ca Merge pull request #1387 from MinhHaDuong/roar-arena-2026-10-13
  87ec7481 Merge pull request #1386 from MinhHaDuong/separate-arena
  c98bef7f Merge pull request #1385 from MinhHaDuong/housekeeping-state-2026-10-13-evening

## Ready work
Ready: 1045 (local merge gate), 1077 (worktree opt-in), 1080 (adherence semantic phase), 1089 (npm-global Pi linking), 1090 (post-merge Roar measurement). Arena-only tickets have moved to the independent repository; see docs/arena-integration.md.

## Resume point
Arena is independent: #1386 merged and 1094 closed; analysis, protocol, reports and eight open arena tickets now live in the arena repository. Harness copies of 1048 and 1087 are archived as wontdo with transfer reasons. The harness retains routing data and historical journals; installed Claude/Pi arena links point to the independent repository. Integration: docs/arena-integration.md.
Main passed `make check`: 1579 passed, 3 skipped on padme (2026-10-13). Local CI passed all ten jobs before the task merge. Review facts are merged through #1387: author-approved force merge; same-family local reviews, native /review unavailable, external launches rejected before execution. Runtime-masked local attribution and the pre-launch identity gap are preserved without inferred IDs.
Housekeeping removed two dead historical worktrees, their merged local branches, owned transfer/review worktrees and one orphan scratch after permission repair on three user-owned temporary directories. No WIP was found. Retired zotero-import links were removed; `idh check` passes. Historical rewritten commits remain on the three existing archive branches.
The third Dream is accepted (#1382). Historical review-attribution gaps for #1374 and the earlier backfill remain documented; no missing identities were inferred.

## Next actions
Continue from `erg ready tickets/`. Arena cycle 3, role-split redesign and publication correction are followed in the independent arena repository (1048, 1061, 1093). Consume reviewed cycle evidence through skills/route; no publication ran during separation.
Zotero staging reconciliation could not run on padme: no user ID configured. The earlier 28-file report was not refreshed; no import or purge ran.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the Zotero client via the report from `python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html` (0485 closed; author-side chore).
- Zotero train residue: decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
