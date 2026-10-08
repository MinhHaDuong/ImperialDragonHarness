# Route recommendations: Pi

Read after `SKILL.md`. Defaults for an orchestrator running inside Pi.
Launch forms are in `routes.json` under `launch_doors.pi`.

## Status: unverified

On 2026-10-08 `pi auth check` reported `not_ready` for Anthropic, OpenAI and
OpenRouter in the probing shell, so no Pi launch was run (ticket 1063). The
statements below come from the help text only. Verify with one live call
before relying on them.

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
