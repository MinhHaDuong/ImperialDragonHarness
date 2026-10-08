# Route recommendations: Pi

Read after `SKILL.md`. Defaults for an orchestrator running inside Pi.
Launch forms are in `routes.json` under `launch_doors.pi`.

## Status: syntax known, providers vary by host

Run `pi --list-models` first: Pi only reaches the providers configured on
the host. On padme (2026-10-08, ticket 1063) it lists huggingface and the
local padme seats; `pi auth check` reports `not_ready` for Anthropic, OpenAI
and OpenRouter. That is a configuration fact of that host, not a Pi fault.
No Pi launch was run by the probe.

## What Pi can reach

- Pi names a model by provider and id (`--model <provider>/<id>`, optional
  `:<thinking>` suffix; `--provider` selects the provider). In principle one
  Pi session can reach every family whose credentials are loaded, so it may
  be a native cross-family door. This is the claim to verify.
- A headless worker: `pi --no-session -p --model <provider>/<id> "<prompt>"`.
- How a Pi subagent picks its model is unknown.

## Which model for which work

Follow the general recommendations in `SKILL.md` and the grid. For cheap
work prefer the cluster default, Luna, or Haiku 5.5 when the Anthropic
credentials are loaded. For a review of Claude-produced work, choose a
non-Anthropic model.
