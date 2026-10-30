# Environment: runtimes, models and routing

Single-run observations on named versions. Routing belongs to `skills/route/` and `rules/claude-code.md`; no grid here.

## Current guidance

- Claude Code levers (2026-09-10, v2.1.267, Opus 5): a skill's `model:` never reaches spawned children; `Agent` and `Workflow` `agent()` inherit the session model unless each launch passes a short token. `effort:` in an agent definition pins the child (none: inherits; `max`/`low` honoured; an invalid value is rejected at load); `Workflow` `opts.effort` is per-call. On models with pinned default effort (Opus 4.7/4.8, Fable 5) the key was unreliable before 2.1.267, untested. [levers](../feedback_subagent_model_effort_levers.md)
- Codex `spawn_agent` honours `model` and `reasoning_effort` (child `turn_context`, 2026-10-09); read the session header, not the model's self-report (0.161.0).
- Pi on padme serves padme's own seats, Hugging Face, and (via wrappers) paid doors: `scripts/pi-albert` and `scripts/pi-openrouter` load one key into Pi only and pin provider and model; `pi-albert` serves openweight-code and openweight-large. Author ruling: Albert counts as cleared. [Albert](../journal/2026/2026-10-28-pi-padme-albert-route.md), [OpenRouter](../journal/2026/2026-10-28-pi-openrouter-and-session-close.md)
- Pi 1.4.0 reads skills from `~/.agents/skills`; author decision: no `~/.pi/agent/skills` projection (PR 1690). `idh install` retires undeclared receipt-owned links; run it per machine. [PR 1690](../journal/2026/2026-10-27-pi-skills-standard-root-pr1690.md)
- Headless `vibe -p` (2.26.0) reads files under plan/ask/auto-approve and works as a read-only gaze seat with `--enabled-tools read_file`; it needs `</dev/null`. [1279](../journal/2026/2026-10-27-vibe-headless-seat-1279.md)
- Production local model on padme: Flash-Next IQ3_S under Strata (:8080) since 2026-10-12; pi agents point there. Strata v0.1.43 rejects config `xhigh`, ignores `port`. [switch](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- Codex runs gaze's cross-family seat; a usage-limit failure leaves no other-family reviewer. [1082](../journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md) The headless door pins `model_reasoning_effort="medium"`: inherited `low` made luna seats refuse (4/56 vs 0/81 at medium); a no-report status ends with a stderr excerpt. [1365](../journal/2026/2026-10-30-raid-70b3bc-codex-seat-effort-1365.md)
- `runtime.py wake` must not key on `CLAUDE_CODE_CHILD_SESSION`: a live subagent carries it and wake still fires. [verbs](../journal/2026/2026-10-28-raid-6530fd-runtime-verbs.md)
- Author rulings: design every mechanism for Claude Code, Codex and Pi together, none optional or staged last (2026-10-21, native note). The gaze orchestrator model changes only from arena data (route Update discipline); a faster-orchestrator arm waits for the arena (2026-10-29).

## Hazards

- Pi loads only the first of `AGENTS.override.md`, `AGENTS.md`, `AGENTS.MD`, `CLAUDE.md` per directory; an unknown model gets another model's settings, so declare it (2026-10-07). pi has no Agent tool: raids run inline, DEGRADED.
- `pi-haiku -p` hangs without `</dev/null`; pi defaults drift when the model is missing from enabled lists; `pi-subagent-link` once exited 0 on "nothing to link" (PR #1390).
- Wrappers do not unset a caller-exported OpenRouter key (open, 2026-10-28).
- Vibe cannot report a provider-qualified model id; record it as runtime-masked. A delegate's model id is recorded only as it reported it.
- Hours into a session, `--help` or reload a helper before a mutating call: an interface changed on main (attribution helper, ticket 1307). Never silence its output.
- Gaze run inside a coder returned self-only five of five times; explicit panel briefs fixed it (2026-10-27).

## Open questions

- Does Pi's 195-minute gaze on a local 27B model (2026-10-03, one run, six-seat fan-out as the entry's attribution) recur on the current model? Untested.
- Would a faster gaze orchestrator save 20-30 s of a ~3 min run (40 percent odds)? Hypothesis.

## Retired

- Agent files with `model: standard|strong` failing 404 (2026-10-08): tokens removed then; history ([A0-C](../journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md)).

- Tournament cycles 2-3 medians, Mellum, greedy divergence, routing-rollout launch-line counts: Arena separation (PR #1386) and the route grid own them.
- Earlier padme `qwen3.8-27b` default: superseded by the 2026-10-12 switch.
- Vibe 2.25.8 "headless denies file tools": superseded by 1279.
- Codex 0.159.3 `rules/` note, `gpt-6-luna` accepted and `claude-haiku-5-5` rejected on 0.161.0: stale versions, unverified.

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [First raid on pi](../journal/2026/2026-10-02-first-raid-on-pi-pr1153.md), [raid 0902](../journal/2026/2026-10-03-raid-0902-gaze-risk-band-pr1155.md), [raid 0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [Mistral 4 pi context](../journal/2026/2026-10-07-mistral4-pi-context-correction.md), [routing review](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md), [round two](../journal/2026/2026-10-09-routing-review-round-two.md)
- [PR 1390](../journal/2026/2026-10-14-raids-1080-1089-wrap-up.md), [Arena separation](../journal/2026/2026-10-13-arena-separation-and-force-merge.md)
- [Raid under Vibe](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md), [raid forge-less](../journal/2026/2026-10-27-raid-forge-less-and-guard.md)
