# 2026-10-28 — OpenRouter through Pi (PR #1894); author decisions at close

Session: Claude Code, claude-opus-5-5, host padme, background job e7e3e853.

- Author chose OPENROUTER_API_KEY_PI to pay for OpenRouter through Pi. Host config `~/.pi/agent/models.json` gained `openrouter-deepseek` (deepseek/deepseek-v4.1-flash-1017) and both minimax providers now name the _PI key (backup `models.json.bak-2026-10-28b`). `scripts/pi-openrouter` loads only that key into Pi and requires a provider and model declared under an openrouter-* provider. Smoke: openrouter-deepseek and openrouter-minimax each served by the requested provider, about $0.0007 per call; openrouter-minimax1p declared, not smoke-tested.
- Review round 1 found the openrouter route entry still naming the IDH key, with a stale date and a smoke claim for an untested provider; fixed before merge. Open consider: the wrapper does not unset an OpenRouter key already exported by the caller.
- Arena ticket 1169 (smoke and spot check of Albert's openweight-code and openweight-large) filed in the arena repository and merged on its main (6637d36); author does not expect the run soon, so gaze seats on Albert are not planned.
- Author decisions at close: keep the raid's trim of rules/workflow.md (commit 868fa580); keep the index raise.
