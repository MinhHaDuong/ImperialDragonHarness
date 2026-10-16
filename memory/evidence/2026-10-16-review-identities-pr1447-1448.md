# Review identity evidence, PRs 1447 and 1448

Audience: public. Observed identity limits of the review attempts on PRs 1447 and 1448 (ticket 1116, both merged 2026-10-16).
Claude Code `Agent` children are launched with a short model token (`sonnet`, `opus`); the runtime exposes no verbatim provider-qualified model id to the orchestrator.
Headless `codex exec` seats report labels from the session header (`gpt-6.1-sol`, `gpt-6-luna`, "gpt-6 ... exact session model id unavailable"); they are not reconstructed into qualified ids.
Raw panel reports lived in the session scratchpad; they are not committed (decision F2). Durable trail: the PR review and verdict comments.

## PR 1447 (CLI surface; merged head da87721facb280703a338ef0451471d1b8971603)
Writer: Claude Code coder child launched with the `opus` token; model id not exposed.
Writer's /review-pr rounds 1-4: Claude Code Agent children only (no cross-family seat); per-seat anchors not reconstructed.
/gaze round 1 at fba2553893db3a8681318d8dd3ee4a4377a8ffa0 (REROLL) and round 2 at da87721facb280703a338ef0451471d1b8971603 (APPROVED); comments issuecomment-6214876968, issuecomment-6215027538, issuecomment-6215044753 :
- adherence seat with its semantic worker: Claude Code Agent children, ran.
- general review seat (Agent B) and review-pr panel (Agent C): Claude Code Agent children, ran.
- cross-family seat: headless codex, session header `gpt-6.1-sol`, provider openai, medium effort, ran on fba25538 (full) and 21acaba8 (delta).
- simplify seat: Claude Code Agent child, ran; five optional findings, none applied.
- verify-gate seat, rounds 1 and 2: one Claude Code gate session, ran.

## PR 1448 (internals; merged head ddb793af after the ticket close commit on cdd215dbecb53277f2f6787e1a7404c0ed9c5fcb)
Writer: two successive Claude Code coder children launched with the `opus` token; model id not exposed.
Writers' /review-pr rounds 1-6: Claude Code seats plus a headless codex red-team seat (`gpt-6-luna`) in rounds 1-6; per-seat anchors not reconstructed.
/gaze round 1 at 152aebefe26ea58c4cb78cdaff27c5f15dea974c (REROLL) and round 2 at cdd215dbecb53277f2f6787e1a7404c0ed9c5fcb (APPROVED); verdict comment issuecomment-6216680638 :
- adherence seat (Agent A): Claude Code Agent child, ran; PASS.
- general review seat (Agent B): Claude Code Agent child, ran; three consider notes.
- review-pr panel (Agent C, round 7, five seats incl. a red-team seat): Claude Code Agent children, ran.
- cross-family seat: headless codex reporting "gpt-6 (exact session model id unavailable)", read-only, ran on 152aebef and on the fix commits.
- simplify seat: Claude Code Agent child, ran; no must-fix.
- verify-gate seat, rounds 1 and 2: one Claude Code gate session, ran.
