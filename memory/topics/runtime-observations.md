# Runtimes, models and routing

Scope: what was observed about the non-Claude-Code runtimes (pi, Vibe,
Codex), the local model server, the model tournament and the routing rollout
on this repository, 2026-10-02 to 2026-10-13. These are single-run observations
on named versions. Routing decisions live in `skills/route/` and
`skills/route/references/decorrelation.md`, and the profile doctrine in
AGENTS.md, not here.

## Supported observations

pi. pi has no Agent tool: on 2026-10-02 the full raid loop for PR #1153 ran
with every spawn site inline and the panel reported DEGRADED, the decorrelated
evidence coming from external seats. On 2026-10-03 a raid on PR #1155 ran on
pi's named agents with a local 27B model; gaze took 195 minutes against an
1800-second escalate threshold, attributed in the entry to the six-seat
fan-out on that model. A frontmatter-only translation of a Claude agent
definition registered on pi and the live agent read and quoted its
`PROFILE.md` contract (0938). pi loads only the first of `AGENTS.override.md`,
`AGENTS.md`, `AGENTS.MD`, `CLAUDE.md` per directory, which explained the 0918
plant's miss. On 2026-10-07 pi's unknown-model fallback had given
`mistral-large-4` Devstral 2 settings; an explicit model declaration fixed the
context metadata.

pi, 2026-10-08 to 2026-10-12. On padme `pi auth check` was `not_ready` for
anthropic, openai and openrouter, because only Hugging Face and the local seats
are configured there. After API credits arrived, a Haiku-only wrapper
(`scripts/pi-haiku`) ran, and its non-interactive `-p` mode hangs without
`</dev/null`. The pi subagent extension links were dangling once and were
repointed to release 1.1.0. On 2026-10-12 `scripts/pi-subagent-link` printed
"nothing to link" and exited 0 while an npm-global pi existed elsewhere
(ticket 1089, since closed by PR #1390). pi defaults were found resolving away from padme (to
`openrouter/auto` on doudou, to a Hugging Face model on padme) because the
default model was missing from the enabled or provider model lists.

Local server. The earlier standing default (padme `qwen3.8-27b` on
`llama-server`) is superseded. On 2026-10-12 the author switched padme
production to Flash-Next IQ3_S on both GPUs under Strata
(`strata-server.service` on :8080, xhigh default). `llama-server.service` was
disabled, and pi defaults on doudou and padme point to the new model. The roar
sweep repointed six pi agents still pinned to the retired model, and
`adapters/pi/agents/code-reviewer.md` named the new model on 2026-10-13. Strata
v0.1.43 quirks: it rejects `reasoning_effort: "xhigh"` in config (accepts
`high`), and its server ignores the config `port`.

Vibe. Child sessions spawned through Vibe's agent connector do not themselves
expose it; detached `vibe -p` seats were blocked by its approval policy; the
runtime exposed no verbatim provider-qualified model id, so PR #1211's
attribution records the writer as runtime-masked.

Codex. The contradictory-note channel seen in the 0918 trial was closed by a
user-level `AGENTS.md` in `CODEX_HOME`; `rules/` was shown not to be
instruction-bearing on codex-cli 0.159.3 (PR #1147). Detached codex seats
given only a profile contract, a perspective and a diff caught a replayed
defect class (0938). Codex 0.161.0 with a ChatGPT login accepted `-m
gpt-6-luna` and rejected `-m claude-haiku-5-5` (HTTP 400). On 2026-10-10 a
`codex exec` seat failed at once on a usage limit ("try again at Oct 14th"),
so PR #1352 had no other-family reviewer.

Model tournament. Cycle 2 (ticket 1024, closed 2026-10-06): the entry's
opening medians were superseded the same day by two in-entry corrections
(142/160 OK legs; seven VOID-EMPTY results were OpenRouter 403 key-limit
errors). The current figures are the corrected summary
(`docs/2026-10-06-tournament-corrected-summary.json`) and
`skills/route/grid.json`. Haiku 5.5 arm N (PR #1253, 2026-10-08) completed
10/10 with no retry, at a recorded candidate cost of $1.2571. The headline
finding (Luna 6 medium as the best observed compromise) did not change. Cycle 3
(ticket 1048, 2026-10-12) was re-scoped to three speed tickets; its local lane
was announced as running twice while failing (server on the wrong port, then
the launch script refusing the arm's own server), and four attempts were
voided. A Claude Code native note records the author's remark that followed,
"Babysit your takeoffs" (text preserved in the
[third dream](../hoards/2026-10-13-third-dream.md)); it agrees with the entry
and adds no rule here. Mellum 2.1
failed long-context recall and applied 0 of 9 edits on one ticket, and the
author marked it benchmaxxed. Two runs of one ticket on Flash-Next diverged at
the first reply under greedy decoding; the entry notes that the prompt carries
the arm name. Provider limits interrupted runs repeatedly: OpenAI credits, the
OpenRouter monthly cap, a vanished free endpoint, Hugging Face credits
(2026-10-02) and the DashScope free quota (2026-10-12). On 2026-10-12 a
provider 404 was scored OK by the arena runner (1087; subsequently transferred
to the independent Arena repository, where its copy remains open).

Routing rollout (tracker 1052, 2026-10-08/09). The deterministic
`model-level` × `effort` chooser was removed in favour of the orchestrator
choosing from the route grid and per-runtime recommendation files. Haiku 5.5
joined the grid with `family` labels. Risk-scaled decorrelation followed the
author's feedback that many PRs are trivial. Wave C's advisor test (3 arms ×
10 items) caught 0 of 4 recorded board defects in any arm and was recorded as
insufficient evidence to downgrade review seats. The launch line (`worker |
family | effort | risk row | reason`) was written before 4 of 154 traced
launches (2.6%) and 1 of 35 after its introduction. These counts are floors,
because lines written in chat were not counted. About 98% of launches pinned
the model.

## Hypotheses, not facts

That these behaviours hold for later runtime versions, other models or other
prompts is untested. The 195-minute gaze is one run; its cause is the entry's
attribution, not a measurement. That the arm name in the prompt explains the
greedy-decoding divergence is the entry's observation, not a tested cause.

## Refresh: Pi linking and Arena separation (2026-10-13 to 2026-10-15)

[PR #1390](../journal/2026/2026-10-14-raids-1080-1089-wrap-up.md) repaired
Pi linking by resolving the actual launcher and discovering npm-global modules,
while retaining managed-release precedence/fallback. Seven subprocess cases
covered discovery, idempotence, missing/incomplete sources and wrapper
stderr/argv/status. The optional route-cache wording dissent was dismissed
under bounded scope, not repaired; the upstream installer issue was auto-closed
under its contributor policy.

[PR #1386](../journal/2026/2026-10-13-arena-separation-and-force-merge.md)
separated Arena after hash-verifying 96 original files. Eight open tickets,
including 1048 and 1087, retain their IDs there; the historical harness copies
of those two closed as wontdo with transfer reasons. Historical routing numbers
remain evidence, not a current harness-owned tournament. The
[2026-10-15 integration record](../journal/2026/2026-10-15-raid-1101-1103-1104-integration-pending-attribution.md)
records #1423 importing two author-selected provisional local candidates from
pinned Arena evidence. Neither those candidates nor masked review identities
establish a new model-performance finding here.

## Sources

- [First raid on pi](../journal/2026/2026-10-02-first-raid-on-pi-pr1153.md)
- [Raid 0902 on pi](../journal/2026/2026-10-03-raid-0902-gaze-risk-band-pr1155.md)
- [Raid 0938, Pi portability and codex seats](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [Orchestrated raid: #1147, #1150, pi default](../journal/2026/2026-10-02-orchestrated-raid-closes-memory-v8-tracker.md)
- [Raid under Vibe](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md)
- [Detached vibe seats blocked](../journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md)
- [0887 activation, masked model id](../journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md)
- [Tournament cycle 2 with corrections](../journal/2026/2026-10-06-model-tournament-cycle-2-close.md)
- [Mistral Large 4 pi context correction](../journal/2026/2026-10-07-mistral4-pi-context-correction.md)
- [Pi leg interrupted](../journal/2026/2026-10-02-memory-v8-0918-pi-leg-interrupted-credit-depletion.md)
- [Haiku arm N](../journal/2026/2026-10-08-haiku55-arm-n-integration.md) and [publication day](../journal/2026/2026-10-08-tournament-publication-wrapup.md)
- [Routing plan and A1](../journal/2026/2026-10-08-llm-routing-plan-and-wave-a1.md), [A0 to C](../journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md), [review round](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md), [round two](../journal/2026/2026-10-09-routing-review-round-two.md), [launch-line recount](../journal/2026/2026-10-09-1071-launch-line-and-adherence-rerun.md)
- [Raid 1082, Codex usage limit](../journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md)
- [Cycle 3 and production switch](../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md)
- [Arena 1053 close, provider 404 scored OK](../journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md)
- [Raid 1084/1085/1086, pi link no-op](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md)
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
