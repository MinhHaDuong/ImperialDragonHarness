# LLM-chosen routing: waves A0 to C landed (2026-10-08)

Continues [wave A1](2026-10-08-llm-routing-plan-and-wave-a1.md). Tracker 1052; children 1062 to 1070, all closed. PRs #1265 to #1279.

## Observed
- A0 (ticket 1063): in Claude Code, an `Agent` launched with an agent definition carrying `model: standard` or `model: strong` and no per-launch model failed with HTTP 404 `model_not_found`, the token sent verbatim to the API. A per-launch `model=haiku` overrode the frontmatter token and ran as `claude-haiku-5-5`; an unpinned general-purpose launch inherited the session model.
- Codex 0.161.0 with a ChatGPT login: `-m gpt-6-luna` accepted (session header read); `-m claude-haiku-5-5` rejected with HTTP 400. A model's own answer to "which model are you" was wrong on Codex (said gpt-6.1-sol while running gpt-6-luna).
- Pi on padme listed only huggingface and the local padme seats; `pi auth check` was `not_ready` for anthropic, openai, openrouter. Max-plan API credits then arrived; a Haiku-only wrapper `~/.local/bin/pi-haiku` (host-local) ran, the JSON events named `claude-haiku-5-5`. The Pi subagent extension symlinks were dangling and were repointed to the 1.1.0 release.
- Author feedback during B0: decorrelation must scale to risk (many PRs are trivial); the orchestrator should state each launch choice and its reason. Both were applied (#1272, #1273).
- Wave C (1070), advisor Astra via `codex exec -m gpt-6-astra` (header read, effort low): 3 arms x 10 items, 30/30 completed, 0/4 recorded board defects caught by any arm; derived spend at most 2.1 USD; Sonnet-child orchestrator chose Luna as cross-family seat on 6 of 10 items (n=10, titles shown). Verdict recorded: insufficient evidence to downgrade review or gate seats.
- A cross-family Luna seat reviewed PR #1272 and returned "no findings" (attribution record `2026-10-08-review-attribution-pr1272.md`).
- CI: `pytest-guard` failed once on #1270 (`test_check_cross_pr_ticket_collision.sh`), passed on rerun; earlier a `test_attribution_query` failure on #1263 also passed on rerun. Causes not established.

## Outcome
- Merged: Haiku 5.5 in the grid with `family` labels; launch doors and four per-runtime recommendation files; risk-scaled decorrelation doctrine at `skills/route/references/decorrelation.md`; launch-choice floor test; `model-level`/`effort` removed from skills; `model:` tokens removed from agent files; `scripts/model_policy.py` and `tests/test_model_rightsizing.py` deleted; docs marked superseded.
- Ticket line: 0974, 1056, 1057 closed; 1048 kept deferred with its last criterion reworded; 1052 `Blocked-by: 1047` lifted by the author.

## Disclosed gaps
- No `/gaze` ran on any of these PRs; they were verified by `make check` and CI.
- Coder sub-agents wrote #1270, #1271 and #1278; the coordinator read part of their diffs (pin wording in #1270, the AGENTS.md hunk in #1278); #1271 was merged on the coder report and green CI.
- 1070's adherence criterion was met only as a rule-text check on non-board PR 212; spend figures are derived, the Sonnet price is an assumption.
- Pi subagent and Codex `spawn_agent` model pinning were read from code and tool schema, not run.
