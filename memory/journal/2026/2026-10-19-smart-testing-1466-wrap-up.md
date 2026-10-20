# Smart-testing integration and daily timer removal

Date: 2026-10-19
Project: ImperialDragonHarness

PR [1466](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1466) merged
as `af7b7c5dda97aaf7dbd9f11a133dfec446f2f9d6`. Reviewed head was
`8e05c4b6d1ac17830e754234c529eabcafab909a`, reference source parent
`bfd63659ffabf4979ae50c1715a69102dc47cac6`.

The integration uses native pytest-testmon2.2.0 and a public pytest/audit
adapter for recorded and explicitly declared inputs. Slow/integration tests
are eligible for reuse; live opt-outs remain explicit. Tool installation
identity follows the user's choice: hash complete successful version stdout
and stderr, rather than launchers. Git and workload-specific indirect input
declarations remain required. No other project's adoption or arena benefit
was measured or claimed.

Actual regressions exposed Python-as-data reads, private database/reference
baseline mismatch, overbroad frame exclusions, memoized inventory consumers,
nested conftest initialization and missing-path assertions. Each reproduced
fault received a correction and behavioral controls; source reviews and
historical source coordinates are retained in the
[review evidence](../../evidence/2026-10-19-pr1466-review-trail.md).
Final source validation: 1822 passed,4 skipped; complete refresh1822/4;
serial warm invocation6.39s; all ten exact-head forge checks succeeded.
Warm timing is a local observation, not a coding-task benchmark.

PR1478/ticket1121 merged during review. Its new assertion that
`scripts/refresh-STATE.py` is absent was initially a cached false green when
the missing file was restored. The integration now declares that missing
path; the real-helper control fails twice after restoration.

The initial formal gate held this PR for the unrun arena1103 experiment.
The author explicitly clarified: PRs are not waiting points; the existing
ticket carries the follow-up. The second gate approved the unchanged source
with the arena experiment open, and the implementation merged. No arena run
was launched. The arena ticket remains in its own repository.

At roar, the author asked about daily refresh. Padme's
`claude-harness-pull.timer` was enabled/active with OnCalendar=daily. Its
service had failed at midnight2026-10-19 with exit128 because it invoked
`git -C ~/.idh pull --ff-only --quiet`; the retired directory was absent.
The author instructed removal. The timer was disabled/stopped; its timer
and dedicated service files were removed, systemd reloaded, and the failed
state reset. The final timer listing returned no such timer. No other
scheduled job was changed. A newly drafted repair ticket was withdrawn
before commit because removal replaced the proposed repair.

Sweep on actual origin/main content confirmed both memoized source_texts
consumers have explicit canonical-root declarations and the retired-generator
absence guard has its exact missing input. No additional reproduced source
fault was found by that bounded sweep. Other installed nightbeat/night-sweep
units still contained retired-path references; their operation was not
assessed and they were not modified by the daily-timer removal.

Roar mechanical checks: 30 recent merged PRs,4 recognized close claims,
20 explicit no-close,6 unrecognized Ticket lines; zero closure findings.
Backfill ran for actual merged PR1466/fixSHA af7b7c5d against integration
history: appended0,no-match0,unresolved101. Reviewed coordinates for those
past records were not established for every attempt, so no post-merge defect
labels were inferred. The new1466 record deliberately preserves multiple
source revisions and masked native identities rather than inventing a
single reviewed SHA or full model id.

The session-scoped temporary-candidate report used the live Codex thread id.
History attribution was partial (3535 of11639 files; two unreadable); unmatched
candidates and descendant scope remain unknown. No host-wide deletion was
performed from that report.
