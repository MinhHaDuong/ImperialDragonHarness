# Bounded diagnosis of the temporary report timeout — 2026-10-19

The Codex roar temporary-candidate report had previously timed out at 90
seconds without producing output. The exact report was not rerun during this
diagnosis. Two read-only probes used 25-second bounds and emitted only aggregate
counts and timings.

The first probe measured shallow root enumeration at 0.009 seconds and
candidate scanning at 13.941 seconds. It counted 6,881 candidates, 923 at the
default 1 MiB floor, 14 unreadable entries and 14 truncated candidates. The
second measured enumeration of 11,430 history files at 0.413 seconds; their
total stat-reported size was 5,442,237,290 bytes. Attribution did not finish
within the remaining time in that second probe. After the preceding stages,
about 10.6 seconds remained before the 25-second bound, so this is only a lower
bound on attribution time, not a completion-time measurement. The measured
stages do not account for the observed 90-second timeout.

Code inspection found that report construction does not return until all
stages finish, so it emits no partial output. Later reference collection and
test-source inference were not measured. The report currently enumerates
history across runtimes and builds a global session-parent graph used for
descendant attribution. No cause for the 90-second timeout has been established.

Ticket 1120 records a bounded, read-only profiling and equivalence-check
follow-up under the broader temporary lifecycle work in ticket 1095. The
measurements and code locations were retained in a local diagnostic during
this session; no raw history content, candidate paths or commands were
included in this entry. The full report remains incomplete, and attribution
for merged PR 1456 remains a separate pending capture because required writer
and reviewer identity and adoption facts are not available in its durable
trail (see [the PR 1456 review record](2026-10-19-pr1456-review-and-attribution.md)).

The required roar close-and-clean before-exit phase could not verify close
claims: its forge query returned no result and could not distinguish no merges
from an unavailable query. Its preflight succeeded. The phase was run once;
no clear claim result was recorded.
