# Route recommendations: Vibe

Read after `SKILL.md`. Defaults for an orchestrator running inside Vibe.
Launch forms are in `routes.json` under `launch_doors.vibe`.

## What Vibe can reach

- Vibe is Mistral-served (the `mistral` route). It has no model flag on the
  command line: the model comes from the agent (`--agent <name>`) or the
  configuration; default `mistral-vibe-cli-latest`.
- Headless `vibe -p` reads files and can serve as a detached review seat
  through `gaze_seat.py` (Vibe 2.26.0, ticket 1279): `--enabled-tools
  read_file` only, stdin closed (an inherited stdin hangs it silently), model
  pinned by a seat agent in a disposable `VIBE_HOME`. Its auth is the Le Chat
  plan login in the keyring. A seat that fails is `no report`; never simulate it.
- Run from a trusted folder (`--trust`), or project configuration such as
  `AGENTS.md` is ignored.
- Subagent model selection is unverified.

## Which model for which work

Use the models of the configured agent. For anything the grid ranks above
that, or for a cross-family review, launch another runtime's headless CLI
from bash (`claude -p`, `codex exec`, `pi -p`) as listed in `routes.json`.
