# 2026-11-07 — Smelt prompt folded into the skill (ticket 1451, PR #2225)

Context: a /smelt run on sen-causal-reading refused because the project had
no `memory/SMELT.md`. On the author's order ("file the tickets, then raid
them", 2026-11-07, option: no per-project prompt), a headless raid (34342e)
filed ticket 1451 and landed it.

Events:
- The generic consolidation text moved to `skills/smelt/references/consolidation.md`;
  harness `memory/SMELT.md` was retired by running `smelt_migrate.py` on the
  harness itself. A missing prompt is now the default.
- Gaze round 1 found the migration could delete an untracked or edited prompt
  (its `git show HEAD:` recovery hint then pointed at nothing); fixed by refusing
  unless HEAD holds the file unchanged. Round 2 REVIEWED; verify-gate APPROVED
  round 1 (session 2a9968e3).
- `memory_sizes.py --before <ref>` had resolved the ref in the harness repo,
  comparing another project's pages against the harness's topics; fixed in the
  same PR.
- Two sibling projects already held open "rename DREAM.md to SMELT.md" tickets
  (JETP-observer 2100, climate-finance-het 2721); the retire tickets filed there
  (2102, 2771; padme 0108) state that they supersede them. All three landed as
  ticket-only PRs (#245, #2021, #225).
- `raid_land.py` merged #2225 but exited 4: the primary checkout held another
  session's uncommitted ticket edit, so local main was left unsynced.
- The writer attribution lines were not recorded on notes before landing
  (`attribution: not derivable: writer`).

Open minors left by review (below the ticket floor): fast-tier tests in
`tests/test_smelt_migrate.py` now spawn git without the integration marker;
recovery hint `HEAD:<name>` needs `HEAD:./<name>` when the project is a
subdirectory of its repo (`scripts/smelt_migrate.py:316`); no test for a topic
filename with a space in `memory_sizes.py`; a rerun after retirement no longer
lists files still naming the retired prompt; the pinned 2026-10-29 Commission
line's location pointer was changed to "Now in the smelt skill" (wording of the
ruling unchanged).

Sources: ticket `tickets/closed/1451-smelt-fold-the-per-project-smelt-md-prom.erg`,
PR #2225, attribution `memory/evidence/attribution/2026-11-07-review-attribution-pr2225.md`.
