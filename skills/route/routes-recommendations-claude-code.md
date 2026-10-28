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
| Ordinary implementation, interactive | `sonnet` @high | Anthropic | default coder; never @medium for code |
| Implementation run unattended | `haiku` @high | Anthropic | provisional (arena 1098): Opus-level, ~1/8 cost, slow |
| Ordinary review | `sonnet` | Anthropic | same family: replication, not independence |
| Hard implementation, cross-cutting judgment | `opus` | Anthropic | |
| One-shot deep problem, adversarial judgment | `fable` | Anthropic | never orchestration or bulk |
| Independent review of a risky change | `codex exec -m` (OpenAI), `vibe` (Mistral) | other | headless seat from bash; on padme `pi -p` serves only the local seats and huggingface |
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
- Ordinary implementation and review: `sonnet` at effort high.
- Unattended implementation (batches, overnight): `haiku` at effort high.
  On the arena 1098 sweep (ten coding tickets, one run per cell) it matched
  `opus` @medium (mean 22.6 vs 24.5/30, paired median difference 0) at
  about one eighth of the cost, but took about 6 minutes per ticket, half of
  it running tests.
- Effort for code: high, not medium. Haiku and Sonnet both lost about 4-5
  points out of 30 at medium (they stop verifying); xhigh added nothing over
  high for Haiku at about 4x the cost. Opus defaults to medium: keep it there.
- Setting effort from Claude Code: the `Agent` call has no effort parameter.
  Use an agent definition whose frontmatter pins `effort:`, or `Workflow`
  `agent()` with `opts.effort`. An unpinned child runs at the model's API
  default (medium for Haiku and Opus, high for Sonnet).
- Hard implementation, cross-cutting judgment: `opus`.
- One-shot deep problems and adversarial judgment: `fable`. Not for
  orchestration or bulk work: as a coding worker at @low it matched `opus`
  @medium at 1.7x the cost (arena 1098).
- Out of Claude Code, Luna (`codex exec -m gpt-6-luna`) is the cheap
  alternative when a different family is wanted.

## Reviews

The reviewer should come from a different family than the producer when the
risk justifies it. From Claude Code that means a headless seat, not an
`Agent` child. If no such seat is reachable, say so in the report.
