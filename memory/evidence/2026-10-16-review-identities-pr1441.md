# Review identity evidence, PR 1441

Audience: public. Observed identity limits of the review attempts on PR 1441 (merged 2026-10-16, head 61497f94a56c01becd7e7fa66a27d0ca0a91d9a9).
Claude Code `Agent` children are launched with a short model token (`sonnet`, `opus`); the runtime exposes no verbatim provider-qualified model id to the orchestrator.
Headless `codex exec` red-team seats report a bare label (`gpt-6-luna` / "GPT-6"), not a provider-qualified id; bare labels are not reconstructed.
Raw panel reports lived in the session scratchpad and review worktrees; they are not committed (decision F2). Durable trail: the PR review comments.

Writer: three successive Claude Code coder children launched with the `opus` token (local-only rewrite; API-only rework; pyzotero rework), plus orchestrator commits from the same session; model id not exposed.
Hunt review loops by the writers (/review-pr rounds 1-6, posted as PR review comments): correctness, consistency, scope, doc-propagation and regression seats as Claude Code Agent children; red-team seats as headless codex. Per-seat anchors of these rounds are not reconstructed here.
Final /gaze (rounds 1-2), reviewed revisions 8cdbc9791a59e5605769db5857fa9f236ff76fe0 (REROLL) and 68d960f3cf2177b92697dc360835f108986fdd5c (APPROVED); comments https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1441#issuecomment-6212212337 and #issuecomment-6212601135 :
- adherence seat (Agent A): Claude Code Agent child, ran; PASS.
- general review seat (Agent B): Claude Code Agent child, ran; live reproductions on a private Xvfb.
- review-pr panel (Agent C, round 6): Claude Code Agent children, ran.
- red-team seat in the round-6 panel: headless codex reporting GPT-6, ran; three blockers, two kept verifiable by the gate.
- simplify seat: Claude Code Agent child, ran; one must-fix applied in 8cdbc979.
- verify-gate seat, round 1: Claude Code Agent child, ran; REROLL.
- verify-gate seat, round 2: same gate session, ran; APPROVED.
