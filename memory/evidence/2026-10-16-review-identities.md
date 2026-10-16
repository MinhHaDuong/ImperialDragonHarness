# Review identity evidence, PRs 1431 and 1440

Audience: public. This file records the observed identity limits of the review attempts on PRs 1431 and 1440 (merged 2026-10-15).
Claude Code `Agent` children are launched with a short model token (`sonnet`, `opus`); the runtime exposes no verbatim provider-qualified model id to the orchestrator.
Headless `codex exec` seats report a bare model label (`gpt-6-luna`), not a provider-qualified id; bare labels are not reconstructed into qualified ids.
Raw attempt reports lived in throwaway review worktrees and the session scratchpad; they are not committed (decision F2). Durable trail: the PR review comments cited below.

## PR 1431
Writer: commits authored in the author's checkout; ticket 1100's log attributes the drafting to ChatGPT notes (tickets/1100-implement-review-orchestration-gaze-single-review.erg log, 2026-10-15T10:12Z to 15:43Z); runtime model id not exposed.
Reviewer attempts, /gaze round 1, reviewed revision 776240ecb5c8bed91b9c0b796d8e6335e438e28f; verdict comment https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1431#issuecomment-6202124547 :
- adherence seat: Claude Code Agent child, `sonnet` token, ran; PASS, no findings.
- general review seat (Agent B): Claude Code Agent child, `sonnet` token, ran; 0 blockers.
- review-pr panel (Agent C: correctness, consistency, scope, doc-propagation): Claude Code Agent children, `sonnet` token, ran; all "comment"; review comment https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1431#issuecomment-6202084848
- simplify seat: Claude Code Agent child, `sonnet` token, ran; 3 should-fix and 4 nits, none applied (author-recorded decision text).
- verify-gate seat: Claude Code Agent child, `sonnet` token, ran; APPROVED.

## PR 1440
Writer: Claude Code coder child launched with the `sonnet` token (commit c5ef2976); fix round by a Claude Code child whose commits carry `Co-Authored-By: Claude Opus 5.5` (1a1c9b54, a1d52899).
Reviewer attempts, /gaze rounds 1-2, reviewed revisions c5ef2976768d09fdd7cf737c0bf35ea622f808e6 (round 1) and a1d52899e59a48d9f6fce124bd64a15c1dec7539 (round 2):
- adherence seat (Agent A): Claude Code Agent child; its semantic review ran as a headless codex seat reporting `gpt-6-luna`, ran.
- general review seat (Agent B): Claude Code Agent child, ran; APPROVE with three consider items.
- review-pr panel (Agent C: correctness, consistency, doc-propagation): Claude Code Agent children, ran; https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1440#issuecomment-6202146672
- external red-team seat: headless `codex exec` reporting `gpt-6-luna`, read-only, ran; request-changes, two blockers.
- simplify seat: Claude Code Agent child, ran; two nice-to-have trims.
- verify-gate seat, round 1: Claude Code Agent child, ran; REROLL https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1440#issuecomment-6202262495
- verify-gate seat, round 2: same gate session, ran; APPROVED https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1440#issuecomment-6202332127
