# Raid 8484af: repository-disabled auto-merge

Ticket 1564, filed from padme 0112 / PR263, was implemented in harness PR2527. The author requested the tool change after the repository checkbox remained unavailable. No repository setting was changed and no live padme merge was attempted.

The narrow GhForge.merge change retries only GitHub's definitive repository-disabled auto-merge refusal, once, as a direct merge. Both calls pin the captured head. Existing lander readback and unknown-outcome handling remain in use. The fix commit is 71b427615bd2c628931785ae2a4e93f52b4f2afa.

New regression tests first produced six failures and one pass on the old adapter. The adapter, lander, and local suites passed 117 tests; lint passed 191 and fast tests passed 1966. Gaze and gate each ran the 14 selected files, 481 tests passing. No source change followed those checks.

The first gaze on 157992846ef7c639a37a76232346badb4f91a374 ended ESCALATE because automatic approval rejected transmission of code, tests, and ticket details to Anthropic for missing trusted user authorization in the child's context. No external seat launched. That result remains on notes. The root selected the expressly permitted safer alternative: an in-process OpenAI reviewer, no external CLI or Anthropic transmission. The new gaze on 7b6a5146b9085e28fdd4810f5c80d19ec726efd4 was REVIEWED with plan PASS; it was same-family, not independent. One consider item on --auto plus --match-head-commit compatibility was settled by installed gh 2.103.3 help and official source at that tag (pkg/cmd/pr/merge/merge.go and http.go).

The served full model IDs and verified efforts were unavailable for the Codex workers. Gaze's subagent attribution generated the requested pin from the manifest despite the worker reporting model not observed. The factual capture records that reviewer as runtime-masked, using the durable execution evidence; the original notes answer was not rewritten. No claim is made that the requested model was observed.

Gate session aa9d70e0-26a1-43bf-9680-3fb7d3992f37 approved round 1 at 3b3364078e08af567f7078daad82124e93f0730f. An initial restricted/offline admission refusal resolved after an authorized live read; admission then matched the bookkeeping ticket closure. Five before checks and the targeted tests passed. PR2527 merged as 1f42d36ac9fa4c59f4797955f82a090c3f11bf7c; readback was MERGED at the ruled head. Main's after-merge record passed: 3923 tests passed, four skipped, and 191 adherence checks passed.

The ref-based sweep found the changed adapter as the only matching merge implementation. Merge and molt instructions already permit direct merge when auto-merge is disabled; no propagation edit was needed. The commissioned attribution backfill returned appended=0, no-match=0, unresolved=355 (missing or malformed historical evidence, and unresolved revision evidence for 2527); no historical coordinates were invented. The bump tally had no row for ticket1564, hence zero categorized bump entries for this ticket.

Timing: first gaze duration 2m26s (its end epoch was not measured); safer gaze duration not measured because setup stdout was unavailable; gate clock 1795682947.032, cleanup completed 1795683159.094; merge row 2527 merge 1795683182 1795683210. Gate duration in verdict: 1m59s. The merge was 28s. The exact gaze-to-merge duration and slowest step cannot be fully measured from those clocks.

No other project, tracker1552, PR2516, explore-session-roles draft, or unregistered t1527 husk was modified. Cleanup is limited to the trees and branches created for this raid.
