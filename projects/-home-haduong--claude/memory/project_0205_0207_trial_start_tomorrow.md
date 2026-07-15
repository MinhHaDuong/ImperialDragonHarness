---
name: project-0205-0207-trial-start-tomorrow
description: Author approved (2026-07-15) starting the 0207 advisory trial + 0205 doc criteria on 2026-07-16
metadata: 
  node_type: memory
  type: project
  originSessionId: 0da5dd51-b3fc-49f7-a43f-45a7a7797a74
---

Author decision 2026-07-15: execute on 2026-07-16 the plan for harness tickets 0205/0207 —

1. Enroll the smoke-tested seats in `skills/reviewers/panel.yml`: uncomment `openrouter-frontier` (openai/gpt-5.6-terra, credential-env OPENROUTER_API_KEY_IDH); optionally `openrouter-budget` (openai/deepseek/deepseek-v4-flash) and `local-qwen`. Branch + PR, `Ticket-ref: tickets/0207-...` (do NOT close — criteria 3-4 stay open until the trial completes).
2. Same or second PR: land 0205's two doc criteria — decorrelation rewording in `rules/workflow.md` (replace "Sonnet reviews Opus's work" with the gradient wording in 0205 design rule 3) and the panel-extension contract section in `skills/gaze/SKILL.md` (0205 action 2). `Ticket-ref: tickets/0205-...`.
3. Then the advisory trial fills passively: run `/reviewers request <pr>` on real PRs across ≥3 projects until ≥5 MRs per config are scorecarded in 0207's log; record promote/drop; integration review closes 0205.

Children 0348/0353 stay parked per [[feedback-harness-cooldown-stop-second-order-tooling]]. Delete this memory once step 1-2 PRs are merged.
