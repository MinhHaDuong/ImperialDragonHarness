# Tournament publication day, 2026-10-08

Context: the reports from the model tournament were being finalized for a blog post while another session (Codex) ran a late Haiku 5.5 arm in the same repository. The two sessions had no inter-agent channel; the author relayed messages and a written coordination prompt, and git was the shared surface.

Ownership split, set by the author: the Codex session owned the run, the results table and `snapshot.json` (PR #1253); the Claude session owned the discussion, figures and the French and English reports, and merged #1252 and #1251 through `/merge`.

Events:
- Haiku 5.5 at medium effort, ten tickets in parallel, native Anthropic routing: mean quality 21.7/30, mean time 366.84 s (median 181.9 s), candidate cost $1.2571 for ten tickets. The headline finding (Luna 6 medium as the best observed compromise) did not change. Judge panel for the arm: Gemini, Grok and MiniMax, no Claude judge.
- Early comparisons given to the author were corrected twice: a seven-ticket Haiku cost was compared against ten-ticket means of other arms (the earlier "$1.09 so far" included in-flight cost), and a derived $0.22 per ticket was replaced by the recorded $0.126.
- The Mistral series were relabelled "last success" and "all attempts" (ids `mi` and `mr` unchanged); "best-of", "full" and "beta" were considered and rejected, "beta" because it collided with the report version name.
- The English edition translates string constants one at a time; the 5 % threshold paragraph had become an f-string with an interpolated comparison count, so the English PDF printed it in French until two fragment keys were added. The same sweep run on the pre-fix ref flagged exactly those two fragments and found none on `main`.
- The extra table row and added sentences pushed text into the footer on pages 1, 2 and 12 of the French report; wording and margins were adjusted and both reports stayed at 12 pages.
- The two Mistral series carry identical scores although the snapshot defines them by different rules (latest versus best). The author's explanation: every ticket was retried on the Mistral API for uniformity, and the one ticket that did not pass (0874) was filled from OpenRouter. On the three tickets with two scored successes the later run was also the higher.
- The worktree isolation guard refused compound shell commands (variable expansion, loops, pipes into `jq` filters) several times; the work was split into plain commands and scripts in the scratchpad.

Outcome: PRs #1251 (ticket 1061, deferred, arena redesign to test orchestrator, coder and reviewer models separately) and #1252 (reports, relabel, Haiku, English edition) merged; #1252 carried a `Ticket-ref` to 1047 so no ticket was closed. The blog post is not published; ticket 1047 remains open pending the author's review and go. Ticket 1046 (PDF report) remains open: its exit criteria (choice guide, message framing, typography and PDF finishing) are not met.

Review attribution: #1251 and #1252 received no reviewer panel; the only gate was the ten CI checks. No attribution record applies. The review trail for #1253 is recorded in `2026-10-08-review-attribution-pr1253.md`.

Sources: [PR #1251](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1251), [PR #1252](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1252), [PR #1253](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1253).
