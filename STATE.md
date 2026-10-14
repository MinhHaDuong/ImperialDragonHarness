# Imperial Dragon Harness — State

Last updated: 2026-10-14T11:07Z
Housekeeping (molt) run: 2026-10-14T11:07Z

## North star
A reusable, science-backed personal harness for AI-assisted research across projects, machines and runtimes.

## Status
<!-- generated 2026-10-14T11:07Z · as of 66c6850e -->

**Tickets:** 3 ready · 2 blocked — `erg ready tickets/` for full list
  next: 1045 Local merge gate replaces the forge's required … · 1077 Decide the session EnterWorktree opt-in after a…
**In flight:** no open PRs · CI main: success
**Recent (first-parent):**
  66c6850e Merge pull request #1393 from MinhHaDuong/roar-raids-1080-1089
  fea2413a Merge pull request #1390 from MinhHaDuong/t1089-pi-subagent-npm
  ae72703f Merge pull request #1389 from MinhHaDuong/t1080-adherence-semantic

## Ready work
Ready: 1045 (local merge gate), 1077 (worktree opt-in), 1090 (post-merge Roar measurement).
Deferred: 1095 (task-owned tmp cleanup and crash recovery), 1096 (review orchestration refactor). The three-skill review architecture remains a candidate; compare simpler alternatives before choosing it.
Arena-only work lives in the independent repository; see docs/arena-integration.md.

## Resume point
Main supports actual semantic-worker execution/evidence in verify-adherence and both managed-release and npm-global Pi module discovery. Tickets 1080 and 1089 are closed. The helper creates no ~/bin; the requested upstream installer issue is earendil-works/pi#10932, auto-closed by contributor policy.
Main passed `make check` on padme at 66c6850e: 1595 passed, 3 skipped in 48.52s (2026-10-14). Healthcheck's fast suite passed 946 tests; forge checks on the repaired review journal also passed. The journal and review-attribution records are integrated through #1393, including failed attempts and retained documentation dissent. Absolute links in captured reports were repaired; all seven memory-portability tests pass.
All local preparatory work is pushed. Historical rewritten branches are preserved; no uncommitted deliverable was found. Current review identities are explicitly runtime-masked where the provider-qualified ID was unavailable. Historical attribution backfill reported 70 unresolved records per fix; no reviewed revision or model identity was inferred.
Arena remains independent; transferred harness tickets 1048 and 1087 are archived. Routing consumes the independent arena's reviewed evidence through docs/arena-integration.md. The third Dream is accepted; subsequent journal entries remain available for a separate Dream.

## Next actions
Continue from `erg ready tickets/`. Resume 1095 and 1096 only when selected for a later session. Arena cycles, role-split redesign and publication correction belong to the independent arena repository; no publication ran here.
Zotero staging reconciliation checked this repository's docs directory and found zero candidate files; no import or purge ran. Author-side Zotero actions below remain outstanding.

## Author actions
- Install the ILaaS consortium key in `~/.config/keys/ilaas.env`, then configure `models.json` (0977).
- Rotate the six exposed bash-x values and the Albert key, deferred to October 2026.
- Merge the 266 hash-duplicate clusters in the Zotero client via the report from `python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html` (0485 closed; author-side chore).
- Zotero train residue: decide on the drifted vendored URL-intake copy in livre-milliards-climat; the 0485 byte-for-byte reproduction needs the live library.
