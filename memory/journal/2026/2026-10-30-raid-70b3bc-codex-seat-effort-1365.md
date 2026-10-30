# Raid 70b3bc: codex seat refusals traced to inherited low effort (1365)

Date: 2026-10-30. Host: padme. PR #2044, merge 033d997a. Ticket 1365 closed.

- Context: gpt-6-luna seats on the codex door intermittently answered
  `NOT-RUN: the review tree cannot be read`; 1363 had closed as not reproduced.
- The failing launch was already captured. Codex writes a rollout of every
  `codex exec` run under `~/.codex/sessions/YYYY/MM/DD/`. The reported seat
  (gaze run gz-20261029T234033056Z-224e) is session
  01a18a09-fb11-79b2-a50b-e4f43dd76f18. It shows cwd = review tree, sandbox
  read-only, approval never and a tool set identical to the seats that did
  read. The model gave its final answer in about 0.2 s, with zero tool calls
  and zero reasoning tokens.
- The headless codex door pinned no effort, so seats ran at whatever
  `~/.codex/config.toml` said. That file was set to
  `model_reasoning_effort = "low"` on 2026-10-29 at 19:33 local time, and the
  refusals all came after that.
- Measured from the recorded seat rollouts: luna at low 3 refusals out of 36,
  luna at medium 0 of 61, gpt-6.1-sol 0 of about 150.
- Measured by a controlled replay of the exact failing prompt on a rebuilt
  review-2026 tree: luna at low 1 of 20 (again zero tool calls), at medium
  0 of 20. That is about 1.07M tokens on the ChatGPT-login quota, about
  26k per launch at either effort; medium took about 4 s longer.
- Pooled luna: 4 of 56 at low against 0 of 81 at medium (Fisher one-sided
  p about 0.026).
- Landed:
  - The codex door pins `-c 'model_reasoning_effort="medium"'` (routes.json
    `effort_status`). A Fable advisor agreed with the pin.
  - Every no-report seat status now ends `; stderr: <excerpt>` (one line, at
    most 600 characters). For codex the excerpt is the settings header:
    workdir, model, sandbox, reasoning effort and session id.
- Gaze REVIEWED with a cross-family codex seat (gpt-6.1-sol) that ran.
  verify-gate APPROVED in round 1.
- Recorded `consider:` items, not adopted:
  - a stderr line containing `: reported in ` would hold wait-roster until
    the deadline;
  - pi's unlisted-model path carries no excerpt;
  - ANSI codes pass through the excerpt;
  - an auth error could put an account identifier on notes.
