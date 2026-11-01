# Environment: runtimes, models and routing

Single-run observations on named versions. Routing belongs to `skills/route/`;
no grid here. Rules loading per runtime: `rules/README.md` § Loading per runtime.

## Current guidance
- Claude Code levers (2026-09-10, v2.1.267): a skill's `model:` never reaches children; `Agent`/`Workflow` inherit the session model unless each launch passes a short token; `effort:` pins the child (none inherits; invalid rejected); `Workflow opts.effort` per-call; unreliable on pinned-default-effort models before 2.1.267. [levers](../feedback_subagent_model_effort_levers.md). Codex `spawn_agent` honours `model`/`reasoning_effort` (2026-10-09); read the session header, not the self-report (0.161.0).
- **Rules reach every runtime** (re-probe 2026-11-01, sentinels): resident rules found in generated `~/.codex/AGENTS.md` and `~/.pi/agent/AGENTS.md`; conditional (`paths:`) rules wired for Codex and Pi (1424, measured on read/write/bash). All three runtimes load the project AGENTS.md and session-start hook. [ruleset review](../journal/2026/2026-11-01-ruleset-review-and-diet.md)
- `pi --print` hangs on an open stdin; run with `</dev/null` — looks like a dead model, is not. [ruleset review](../journal/2026/2026-11-01-ruleset-review-and-diet.md)
- Pi 1.4.0 reads skills from `~/.agents/skills` (PR 1690); agents projected to `~/.pi/agent/agents` (PR 2189, ticket 1426) with no `model:` line, so an unpinned Pi child takes the dispatcher's model (`routes.json:100` stale); padme's `code-reviewer.md` there is a FOREIGN file until removed. Pi also serves HF and paid doors via wrappers pinning provider and model (Albert cleared) ([wave 3](../journal/2026/2026-11-01-raid-1f0534-wave3-pi-agents.md), [Albert](../journal/2026/2026-10-28-pi-padme-albert-route.md)).
- Headless `vibe -p` (2.26.0) works as a read-only gaze seat (`--enabled-tools read_file`); needs `</dev/null`. [1279](../journal/2026/2026-10-27-vibe-headless-seat-1279.md)
- padme's local LLM service is configurable and changes within days; never name llama.cpp or one model as "the" padme route (PR 2065; 2026-10-31 default: Qwen 3.8 Flash Next on strata). Strata v0.1.43 rejects `xhigh`, ignores `port`. [xfam](../journal/2026/2026-10-31-cross-family-gate-dropped.md); [switch](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- Codex runs gaze's other-family seat; a usage-limit failure leaves none [1082](../journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md); the headless door pins `model_reasoning_effort="medium"` (inherited `low` made luna seats refuse, 4/56 vs 0/81) [1365](../journal/2026/2026-10-30-raid-70b3bc-codex-seat-effort-1365.md). `runtime.py wake` must not key on `CLAUDE_CODE_CHILD_SESSION` [verbs](../journal/2026/2026-10-28-raid-6530fd-runtime-verbs.md).
- Author rulings: design for all three runtimes, none staged last (2026-10-21); the gaze orchestrator model changes only from arena data (2026-10-29).
## Hazards
- Pi loads only the first of `AGENTS.override.md`/`AGENTS.md`/`AGENTS.MD`/`CLAUDE.md` per directory; an unknown model gets another's settings — declare it (2026-10-07). pi has no Agent tool: raids run inline, DEGRADED. `pi-haiku -p` hangs without `</dev/null`; pi defaults drift when the model is missing from enabled lists (PR #1390).
- Wrappers do not unset a caller-exported OpenRouter key (open, 2026-10-28). Vibe cannot report a provider-qualified model id; record it as runtime-masked, and a delegate's id only as it reported it.
- In a long session, `--help` or reload a helper before a mutating call (1307); never silence its output. Gaze run inside a coder returned self-only 5/5; explicit panel briefs fixed it (2026-10-27).
## Open questions
- Pi's 195-minute gaze on a local 27B (2026-10-03, one run): recur on the current model? Untested. Faster gaze orchestrator saving 20-30 s of ~3 min (40% odds): hypothesis. Padme's default model: the lineup changes within days; treat any named model as dated.
## Retired

- Agent files with `model: standard|strong` 404 (2026-10-08): history ([A0-C](../journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md)).
- Tournament cycles 2-3 medians, Mellum, greedy divergence, launch-line counts: owned by Arena separation (PR #1386) and the route grid.
- Earlier padme `qwen3.8-27b` default: superseded 2026-10-12; any named default model is dated (2026-10-31 ruling).
- "Codex and Pi load none of rules/" (morning 2026-11-01, ticket 1413): superseded same day by the re-probe (generated AGENTS.md files; 1424 conditional rules).
- Vibe 2.25.8 "headless denies file tools": superseded by 1279.
- Codex 0.159.3 `rules/` note, `gpt-6-luna` accepted / `claude-haiku-5-5` rejected on 0.161.0: stale versions, unverified.

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [First raid on pi](../journal/2026/2026-10-02-first-raid-on-pi-pr1153.md), [raid 0902](../journal/2026/2026-10-03-raid-0902-gaze-risk-band-pr1155.md), [raid 0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [Mistral 4 pi context](../journal/2026/2026-10-07-mistral4-pi-context-correction.md), [routing review](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md), [round two](../journal/2026/2026-10-09-routing-review-round-two.md)
- [PR 1390](../journal/2026/2026-10-14-raids-1080-1089-wrap-up.md), [Arena separation](../journal/2026/2026-10-13-arena-separation-and-force-merge.md)
- [Raid under Vibe](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md), [raid forge-less](../journal/2026/2026-10-27-raid-forge-less-and-guard.md)
