# Route recommendations: Vibe

Read after `SKILL.md`. Defaults for an orchestrator running inside Vibe.
Launch forms are in `routes.json` under `launch_doors.vibe`.

## What Vibe can reach

- Vibe is Mistral-served (the `mistral` route). It has no model flag on the
  command line: the model comes from the agent (`--agent <name>`) or the
  configuration.
- Headless `vibe -p` denies file tools (ticket 1017), so it cannot serve as a
  detached review seat. Record such a seat as `no report`; never simulate it.
- Run from a trusted folder (`--trust`), or project configuration such as
  `AGENTS.md` is ignored.
- Subagent model selection is unverified.

## Which model for which work

Use the models of the configured agent. For anything the grid ranks above
that, or for a cross-family review, launch another runtime's headless CLI
from bash (`claude -p`, `codex exec`, `pi -p`) as listed in `routes.json`.
