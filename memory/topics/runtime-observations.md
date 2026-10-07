# Runtime and model observations

Scope: what was observed about the non-Claude-Code runtimes (pi, Vibe,
Codex) and about model routing evidence on this repository, 2026-10-02 to
2026-10-07. Single-run observations on named versions; routing decisions live
in `skills/route/` and the profile doctrine in AGENTS.md, not here.

## Supported observations

pi. pi has no Agent tool: on 2026-10-02 the full raid loop for PR #1153 ran
with every spawn site inline and the panel reported DEGRADED, the decorrelated
evidence coming from external seats. On 2026-10-03 a raid on PR #1155 ran on
pi's named agents with a local 27B model; gaze took 195 minutes against an
1800-second escalate threshold, attributed in the entry to the six-seat
fan-out on that model. A frontmatter-only translation of a Claude agent
definition registered on pi and the live agent read and quoted its
`PROFILE.md` contract (0938). pi's standing default was reconfigured to the
local padme server (qwen3.8-27b), Hugging Face remaining selectable. pi loads
only the first of `AGENTS.override.md`, `AGENTS.md`, `AGENTS.MD`, `CLAUDE.md`
per directory, which explained the 0918 plant's miss. On 2026-10-07 pi's
unknown-model fallback had given `mistral-large-4` Devstral 2 settings
(262144 context, reasoning false); an explicit model declaration fixed the
context metadata; whether reasoning can be turned off natively stays unproven.

Vibe. Child sessions spawned through Vibe's agent connector do not themselves
expose it; detached `vibe -p` seats were blocked by its approval policy; the
runtime exposed no verbatim provider-qualified model id, so PR #1211's
attribution records the writer as runtime-masked.

Codex. The contradictory-note channel seen in the 0918 trial was closed by a
user-level `AGENTS.md` in `CODEX_HOME`; `rules/` was shown not to be
instruction-bearing on codex-cli 0.159.3 (PR #1147). Five detached codex seats
given only a profile contract, a perspective and a diff caught a replayed
defect class and honoured the contract rails unprompted (0938).

Model tournament, cycle 2 (ticket 1024, closed 2026-10-06). The entry's
opening medians, Pareto and dominance claims were superseded the same day by
two in-entry corrections: the final matrix is 142/160 OK legs with 18 non-OK
outcomes, and seven VOID-EMPTY results were identified as OpenRouter 403
monthly key-limit errors, withdrawing the silent-abandonment and heavy-ticket
conclusions. The current figures are the corrected summary
(`docs/2026-10-06-tournament-corrected-summary.json`) and
`skills/route/grid.json`, not the entry's first paragraphs. Provider limits
interrupted runs three times: OpenAI credits, the OpenRouter key's monthly
cap (which stalled the whole judge panel), and a free endpoint that vanished.
Before that, on 2026-10-02, the 0918 pi leg was interrupted by depleted
Hugging Face credits.

## Hypotheses, not facts

That these behaviours hold for later runtime versions, other models or other
prompts is untested. The 195-minute gaze is one run; its cause is the entry's
attribution, not a measurement.

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
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
