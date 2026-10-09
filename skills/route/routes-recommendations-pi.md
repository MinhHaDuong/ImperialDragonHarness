# Route recommendations: Pi

Read after `SKILL.md`. Defaults for an orchestrator running inside Pi.
Launch forms are in `routes.json` under `launch_doors.pi`.

## What Pi can reach

Run `pi --list-models` first: Pi only reaches the providers configured on the host. On padme it lists huggingface and the local padme seats; Anthropic is reachable only through `pi-haiku` (`scripts/pi-haiku`), which fixes Haiku 5.5 and refuses any other model.

- Pi names a model by provider and id: `pi --no-session -p --model <provider>/<id> "<prompt>"`.
- A Pi subagent (the `subagent` extension, relinked by `scripts/pi-subagent-link`) takes its model from the `model:` line of its agent file in `~/.pi/agent/agents/`. Pi agent files therefore carry a model; this is the one sanctioned pin, and the orchestrator picks which agent file to launch. Verified on padme for a Haiku-pinned agent (`haiku-scout`).

## Which model for which work

Follow the general recommendations in `SKILL.md` and the grid. For cheap
work prefer the cluster default, Luna, or Haiku 5.5 when the Anthropic
credentials are loaded. For a review of Claude-produced work, choose a
non-Anthropic model.
