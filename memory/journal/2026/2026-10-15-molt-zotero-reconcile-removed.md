# Zotero reconcile step removed from /molt

2026-10-15, host doudou. The author reported that the Zotero step of `/lair`
was causing trouble. The step was `/molt` 1.8, which ran
`scripts/zotero.py reconcile` in any repository with a `docs/` directory or a
`.bib` file, including the harness.

Observed: a report-only run on the harness, where discovery found zero files
to audit, was killed by `timeout 300` with no report; the 24 h library index
cache (written 2026-10-14 15:21) was not rewritten. No project carried
`.zotero-reconcile.json`, so no run could write to Zotero. The cause of the
slow rebuild was not established (ticket 1113).

Decision (author, option A among A remove / B gate on opt-in / C fix cost
only): remove the step from `/molt`; keep `/zotero reconcile` on demand; make
reconcile exit before loading the index when nothing is staged. Merged as
PR #1434 after one /gaze round (APPROVED, same-family panel). Review minors
filed as tickets 1111 and 1112 at the author's request.
