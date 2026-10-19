# Ticket 1117: denied branch-rule inspection

On 2026-10-19, PR [1454](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1454)
merged as `3cf4e52bb60e272c775177d14e51da439472ce99`. Ticket1117 is archived.
The helper permits ordinary non-admin merge after an HTTP403 requirement
inspection denial, while retaining refusals for known requirements, malformed
or partial responses, other inspection failures, and pending/failing checks.

The first Anthropic red-team report identified a paginated response that emits
required-check data before failing with403. The executor reproduced it against
the first implementation, separated stdout/stderr and added a refusal for
partial responses. Review also produced warning-stream and actual retry-outcome
regressions. The final matrix contains18 new scenarios.

Four review-pr rounds completed: five separate Anthropic contexts per round in
rounds1–3; documentation plus one regression context in round4. Actual runtime
results identify `firstParty/claude-haiku-5-5`; requested effort was medium,
observed effort unavailable. Codex native review and portable simplification
were clean. Gaze approved all3 exit criteria at
`c952ed92b6058bb0e2f23ad24baac03bda8bfeab`. The merge helper subsequently pushed
close-only head `bc8a72bf8801b232cf891837532750f020be94a4` and queued auto-merge.

Initial external-launch permission objections concerned private export; public
repository metadata supported accepted retries. Five initial E2BIG dispatches
started no process; stdin transport then completed the seats. The uv cache
required normal environment access. A transient Xvfb failure skipped GUI tests;
85 supplemental integrations passed afterward. A review gate invoked with
`make -C` added directory banners to metrics-test output; the corrected
`--no-print-directory` invocation passed1702 tests with3 skipped at the exact
final code head. All10 forge checks passed. Local container CI passed10 jobs
on the first head and its test job on the runtime-equivalent review-fix head.

The ref-based sweep found only this helper using the two inspected branch
endpoints. No additional repair was made. The historical attribution backfill
reported appended0, no-match0, unresolved91; absent reviewed coordinates were
not inferred. The close-claim sweep examined30 recent PRs and found no dropped
claim (15 claims across11PRs;2 unrecognised Ticket lines retained as a limitation).

Raw findings, dispositions, attempt outcomes and runtime facts are retained in
[the evidence](../../evidence/2026-10-19-pr1454-review-trail.md) and the
[attribution record](2026-10-19-review-attribution-pr1454.md).
