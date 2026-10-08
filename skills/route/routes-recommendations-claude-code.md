# Route recommendations: Claude Code

Read after `SKILL.md`. These are defaults for an orchestrator running inside
Claude Code; the grid and the task still decide. Launch forms are in
`routes.json` under `launch_doors.claude-code`.

## Launching

- Pin the model on every launch with the short token `haiku`, `sonnet`,
  `opus` or `fable`. A child never inherits a skill's frontmatter, an unpinned
  `Agent` child inherits the session model, and the `model: standard|strong`
  tokens in agent definitions return HTTP 404 (ticket 1063, 2026-10-08).
- Every `Agent` child is Anthropic. A cross-family worker is a headless CLI
  started from bash: `pi -p` with a provider-qualified model, or
  `codex exec -m` for OpenAI.

## Which model for which work

- Search, extraction, triage, mechanical checks, bulk reading: `haiku`
  (Haiku 5.5). Keep each worker under 100K prompt tokens, because the price
  multiplies by 5 above that. Quality tied with Luna on the arena sample
  (10 of 10 tickets, n = 10, not a ranking).
- Ordinary implementation and review: `sonnet`.
- Hard implementation, cross-cutting judgment: `opus`.
- One-shot deep problems and adversarial judgment: `fable`. Not for
  orchestration or bulk work.
- Out of Claude Code, Luna (`codex exec -m gpt-6-luna`) is the cheap
  alternative when a different family is wanted.

## Reviews

The reviewer should come from a different family than the producer when the
risk justifies it. From Claude Code that means a headless seat, not an
`Agent` child. If no such seat is reachable, say so in the report.
