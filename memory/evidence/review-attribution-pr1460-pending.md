# PR 1460 review-attribution capture status

Status: pending; no `kind: review-attribution` record was written because required identity facts are missing from the durable trail.

PR 1460 merged on 2026-10-19 at integration commit `0a2deb7c`; its source head was `0bfd97e4a4f1425cf28bdafa9334c6713c4803e6` on `t1120-bounded-report-timeout`.

The public Sol formal gate and combined ticket-1095 union review ([gate](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1460#issuecomment-6266772633)) reports approval and gives three adopted regression findings: iterative trie emission for long paths at `scripts/tmp_report.py:277` with `tests/test_tmp_report.py:85`; conservative session-identity markers at `scripts/tmp_report.py:305` with `tests/test_tmp_report.py:154`; and unreadable-history coverage propagation at `scripts/tmp_report.py:810` with `tests/test_tmp_report.py:562`. The same comment records one nonblocking consideration about history ordering and marks it informational; the comment does not supply a distinct repository-relative path-and-line anchor for that consideration.

The gate identifies a requested Sol/medium, same-family route, but explicitly says the provider model identity and observed effort are unavailable. No model version is exposed in the durable trail. The writer's full provider-qualified model ID, model version if exposed, and effort are also absent. Requested route labels are not substituted for observed identity facts. The missing writer and reviewer pins/effort prevent a complete fixed-line attribution record.
