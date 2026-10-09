# Route recommendations: Claude Code

Read after `SKILL.md`. These are defaults for an orchestrator running inside
Claude Code; the grid and the task still decide. Launch forms are in
`routes.json` under `launch_doors.claude-code`.

## Launch table

This table suffices for routine choices unless the task is unusual (high risk,
oversize context, uncleared content, or a cross-family need).

| Work type | Token | Family | Note |
|---|---|---|---|
| Search, extraction, triage, bulk reading | `haiku` | Anthropic | under 100K prompt tokens |
| Mechanical checks, smoke runs | `haiku` | Anthropic | cheap to verify |
| Ordinary implementation | `sonnet` | Anthropic | default coder |
| Ordinary review | `sonnet` | Anthropic | same family: replication, not independence |
| Hard implementation, cross-cutting judgment | `opus` | Anthropic | |
| One-shot deep problem, adversarial judgment | `fable` | Anthropic | never orchestration or bulk |
| Independent review of a risky change | `pi -p` / `codex exec -m` | other | headless seat from bash |
| Cheap work, different family wanted | `codex exec -m gpt-6-luna` | OpenAI | headless seat |
| Uncleared content | local model via `pi -p` | local | never a hosted door |
| Context over 256K | none | n/a | split the work |

## Launching

- Pin the model on every launch with the short token `haiku`, `sonnet`,
  `opus` or `fable`. A child never inherits a skill's frontmatter, an unpinned
  `Agent` child inherits the session model; harness agent definitions carry no
  `model:` line.
- Every `Agent` child is Anthropic. A cross-family worker is a headless CLI
  started from bash: `pi -p` with a provider-qualified model, or
  `codex exec -m` for OpenAI.

## Which model for which work

- Search, extraction, triage, mechanical checks, bulk reading: `haiku`
  (Haiku 5.5). Keep each worker under 100K prompt tokens, because the price
  multiplies by 5 above that. Quality tied with Luna on the arena sample
  (10 of 10 tickets, n = 10, not a ranking). If the task exceeds 100K prompt
  tokens, split it, or promote to `sonnet` and state why in the launch line.
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
