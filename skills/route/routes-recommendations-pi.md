# Route recommendations: Pi

Read after `SKILL.md`. Defaults for an orchestrator running inside Pi.
Launch forms are in `routes.json` under `launch_doors.pi`.

## What Pi can reach

Run `pi --list-models` first: Pi only reaches the providers configured on the host. On padme it lists huggingface and the local padme seats; Albert (`albert/openweight-code`, `albert/openweight-large`) is reachable only through `pi-albert` (`scripts/pi-albert`), which loads its key into the Pi process; OpenRouter (`openrouter-deepseek`, `openrouter-minimax`) only through `pi-openrouter` (`scripts/pi-openrouter`), which requires a declared `--provider` and `--model` and bills `OPENROUTER_API_KEY_PI`; Anthropic is reachable only through `pi-haiku` (`scripts/pi-haiku`), which fixes Haiku 5.5 and refuses any other model.

- Pi names a model by provider and id: `pi --no-session -p --model <provider>/<id> "<prompt>"`.
- A gaze seat on the Pi door also names its thinking level, `<provider>/<id>:<level>`, a level the model supports (grid pins carry none: add it when planning the seat): `gaze_seat.py` refuses a bare id, so the host `defaultThinkingLevel` never sets it.
- A Pi subagent (the `subagent` extension, relinked by `scripts/pi-subagent-link`) takes its model from the `model:` line of its agent file in `~/.pi/agent/agents/`. Pi agent files therefore carry a model; this is the one sanctioned pin, and the orchestrator picks which agent file to launch. Verified on padme for a Haiku-pinned agent (`haiku-scout`).

## Which model for which work

Follow the general recommendations in `SKILL.md` and the grid. For cheap
work prefer the cluster default, Luna, or Haiku 5.5 when the Anthropic
credentials are loaded. When a review of Claude-produced work must be
independent (high risk, `references/decorrelation.md`), choose a non-Anthropic
model.

## Albert seats stay out of the grid

Arena Albert smoke spot check, 2026-10-29 (arena repository,
`docs/2026-10-29-albert-smoke-spot-check.md`, "Readout for the route grid"):
0 of 4 legs OK, no quality or speed observation, so neither Albert identity
enters `grid.json` and the unbenched-identity rule in `SKILL.md` keeps both
off routed agent work.

- `qwen3-coder-30b-a3b-instruct @off · albert` (`albert/openweight-code`):
  not usable as a Pi agent; tool calls do not come back as tool calls when Pi
  omits `tool_choice`. Single-shot text use, without tools, is unaffected.
- `gpt-oss-120b @medium · albert` (`albert/openweight-large`): tool calls
  work, but the experimentation tier's 10 RPM ends a Pi agent leg within a
  minute. Use it for single-shot calls only (judging, probes), never agent
  work.

Re-bench conditions, all outside the arena; any one reopens the question:
Albert parsing Qwen3-Coder tool calls without `tool_choice` (or Pi sending
`tool_choice: "auto"` for the albert provider); a Pi retry policy that waits
out a 60 s rate window; or the Production Limitée tier (declined by the author
on 2026-10-23). Then make a fresh pin and run a smoke leg before any grid row.
