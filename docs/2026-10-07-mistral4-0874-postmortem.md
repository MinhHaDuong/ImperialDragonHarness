# Ticket 0874 — native Mistral retry postmortem

Native retry `0874-mr` ended at 2026-10-07 07:05:05 UTC after 2320.7 seconds.
It is an unsuccessful delivery and remains charged to real cumulative accounting.
The original `VOID-EMPTY` record is preserved; a separate diagnostic marks it
as a model failure (quality zero in real accounting), not an infrastructure void.

91 assistant calls: 90 tool-use stops, then one `length` stop. Tools: 15 reads
and 84 bash calls, no write/edit tool calls. All 84 bash commands are distinct.
No recorded provider error. No delivered solution branch. Final assistant response
contains only a thinking block, with no final user-facing answer or executable
request. Recorded totals: input 790435, cached input 10521888, output 134588.
Pi reported USD1.0062; costs in plots use calibrated token-based invoice rates.

The context grew to a recorded peak of 257960 tokens. `length` proves generation
was truncated; context exhaustion is a plausible explanation, not confirmed
without this run's raw HTTP payload. The run was not instrumented at launch.

Despite session thinkingLevel off, thinking blocks total 462979 characters.
Current instrumented native retries omit reasoning_effort and send max_tokens
around 251000 on their first requests. Thus Pi off does not establish native
reasoning_effort none. This finding needs investigation before attributing the
failure exclusively to model quality. Diagnostic retries keep explicit provenance.
