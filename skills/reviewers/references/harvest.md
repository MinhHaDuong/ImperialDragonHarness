# `/reviewers harvest <pr>`

Collect every seat's findings and normalize the seat-runner's
`FINDING|severity=…|file=…|rationale=…` output to the 0205 contract shape:

```
verifiable: <file>:<line> — <rationale>  [seat]
consider: <file>:<line> — <rationale>  [seat]
```

A line that does not parse is surfaced as a `WARN` on stderr, never
silently dropped.

**Panel integrity** (ticket 0393). Findings are only half the report. `harvest`
also cross-checks the roster against the run records `request` left, and names
every seat that did not review — on **stdout**, the report stream:

```
SEAT-FAILED: openrouter-frontier — credential OPENROUTER_API_KEY_IDH unresolved  [this seat did NOT review]
SEAT-MISSING: local-qwen — no findings and no run record  [this seat did NOT review]
PANEL-INTEGRITY: 2 seat(s) did not review this merge request — the findings above are NOT a full panel
```

`SEAT-FAILED` comes from the seat's `.status` record; `SEAT-MISSING` is a
roster seat that left neither findings nor a record (`request` never reached
it). A seat that ran and found nothing is not flagged — that silence is a
result. `forge-bot` seats write no local findings by design, so only their
recorded failures surface. Exit stays 0: these are visible lines, not a block,
so one dead seat still never stops a verdict.

This exists because the failure it reports is the one that hid. During a live
`/gaze` the OpenRouter seat failed **open** on a missing credential: the WARN
went to stderr, `harvest` printed nothing, exited 0, and the panel read as
complete. An empty harvest that cannot distinguish "clean" from "nothing ran"
is not a check — the same shape as the merge-request-listing trap recorded in
`tickets/AGENTS.md`, where a scan that could not look returned the same empty
result as a scan that found nothing.
