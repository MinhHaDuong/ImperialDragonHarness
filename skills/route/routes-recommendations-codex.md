# Route recommendations: Codex

Read after `SKILL.md`. Defaults for an orchestrator running inside Codex.
Launch forms are in `routes.json` under `launch_doors.codex`.

## What Codex can reach

- Under a ChatGPT-account login only OpenAI models run. `codex exec -m
  claude-haiku-5-5` returns HTTP 400 (ticket 1063, 2026-10-08). Codex has no
  Anthropic door. A custom provider with an Anthropic key was not tested.
- Therefore this runtime has no cross-family door of its own. A review seat
  from another family is a headless CLI that is not Codex (`claude -p`,
  `pi -p`), when one is reachable from bash. Otherwise record `no report`.
- Subagent model selection in Codex is unverified. Until it is checked, name
  the model through `codex exec -m` and read the `model:` line of the session
  header. The model's own answer to "which model are you" is not evidence.

## Which model for which work

- Search, extraction, triage, mechanical checks, bulk reading: Luna
  (`gpt-6-luna`), the default of the cheap cluster. Quality tied with
  Haiku 5.5 on the arena sample (n = 10, not a ranking).
- Real implementation and ordinary review: Sol 6.1 at low or medium effort.
- Judgment-heavy work: Sol 6.1, and say that the reviewer shares the
  producer's family when it does.
