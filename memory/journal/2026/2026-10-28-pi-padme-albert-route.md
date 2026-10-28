# 2026-10-28 — Pi on padme: local seats, huggingface and Albert (PR #1889)

Session: Claude Code, claude-opus-5-5, host padme, background job e7e3e853.

- Author: Pi on padme is meant to serve padme's LLM service. `pi --list-models` on padme listed huggingface (81 models) and padme, padme-35b, padme-mellum, padme-strata; routes.json still called anthropic, openai, mistral and deepseek through Pi live, and gaze had planned an OpenAI seat through Pi (#1881 round 1, "No API key found for openai").
- Author: Pi can carry Albert's openweight-code (Qwen3 Coder 30B A3B, soon DeepSeek 4) and openweight-large (gpt-oss-120b); ruling: Albert counts as cleared (PRIVÉ) for uncleared content. Albert's /v1/models listed both aliases plus deepseek-v4-flash-0731, mistral-small, ministral, gemma-4-31b.
- Host config: `~/.pi/agent/models.json` gained the `albert` provider (backup `models.json.bak-2026-10-28`); `~/.local/bin/pi-albert` (source `scripts/pi-albert`) loads ALBERT_API_KEY into Pi only and pins `--provider albert` and a declared model; both seats answered, a json run showed turn_end served by albert, and plain `pi` lists no Albert model.
- Review found the egress gap twice: no pinned provider/model (an empty --model reroutes, adapters/pi/README.md), then an allowed but undeclared model id; both closed before merge.
- DeepSeek V4.1 Flash 1017 is reachable on padme through Pi's huggingface provider; OpenRouter (deepseek/deepseek-v4.1-flash-1017 at 0.15/0.60 per M) waits on the author's choice of paying key, and the openrouter-minimax providers are unreachable for the same reason.
