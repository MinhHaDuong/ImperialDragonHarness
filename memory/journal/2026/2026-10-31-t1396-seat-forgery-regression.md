# PR 2102: subagent seat forgery reopened by PR 2094, closed again (2026-10-31)

Context: red on main since 2a88d52a (PR 2094, ticket 1388):
`test_subagent_seat_forging_a_headless_header_takes_the_pin` (Blind-Spot 1,
adf4b6ea). Found while isolating 1396; the runner had folded it under 1396.

Events:
- PR 2094 let a `door=headless` worker header win when the plan reason names no
  headless door; a reason of `subagent` names none, so a forged header passed.
- Author chose option A: `identities()` untrusts the header when the reason says
  `subagent`; free text keeps the 1388 behaviour. Robust option B (trust only seats
  with a 1384 launch line) filed as ticket 1399. Revert of 2094 rejected.
- Gaze REVIEWED with a codex red-team seat (gpt-6.1-sol). The seat voted blocking on
  a reason that says `subagent` without `headless <runtime>` for a genuine headless
  seat; gaze downgraded it (plan.md requires the reason to name the door), kept as
  dissent. verify-gate APPROVED round 1. Merged at b9de0b4a.
