# Model tournament on harness work — concept note

Date: 2026-10-03
Status: concept (author-directed, this session) — rules settled in dialogue, awaiting
execution; not yet an approved design
Tracker: tickets/1024 (this note is its rule book)
Related: docs/2026-09-28-essai-pi-backends-souverains.md (Pi backend probing,
silent-reroute finding); tickets/closed/0979 (provider-assertion rule, now in
adapters/pi/README.md); tickets/closed/0977 (Pi + padme smoke evidence)

## 1. Question and the decision it serves

This note defines a **reusable tournament instrument**: a paired, blind, full-crossover
comparison of candidate stacks on harness work, from which routing decisions
follow. The first instantiation decides which stack serves padme's local model
seats — 27B+llama.cpp, Coder+Strata, or 35B-A3B+llama.cpp. The same cycle also
admits the author's hosted workhorses as arms (D: Claude Opus, E: GPT-6 Sol (gpt-6-sol),
F: GLM 5.3), which turns it into a local-vs-hosted value question, not only a
sovereignty one. Future candidates (the Qwen 4 family when
it ships; hosted workhorses such as Sol and Opus, and the tier under them such
as Terra and Sonnet) enter the same instrument — see §8.

## 2. Arms

| | Arm A (incumbent) | Arm B (challenger) | Arm C (challenger) |
|---|---|---|---|
| Model | Qwen3.8-27B Q4_K_M (dense) | Qwen3.8-Flash-Next Coder IQ1_M (MoE, 6B active, experts halved) | Qwen3.6-35B-A3B UD-Q4_K_XL (MoE, 3B active) |
| Engine | llama.cpp (`llama-server`) | Strata v0.1.x | llama.cpp (`llama-server`) |
| Endpoint | `:8080/v1` (OpenAI) | `:8081/v1` (OpenAI + Anthropic) | `:8082/v1` (OpenAI) |
| Context | 131072 | 131072 (reconfigured 2026-10-03; see note) | 131072 |
| Vision | mmproj served; tasks are text-only | off | off |
| Speculative decoding | MTP draft | MTP draft layer (shipped) | none |
| Residency | both GPUs, `--parallel 1` | both GPUs (setup-recommended split) + 35-55 GB RAM | both GPUs, `--parallel 1` |

Arm B notes: the original bring-up at 131072 failed — Strata's prompt-path
device buffers did not fit on 16 GB cards without KV streaming; the model
was first reconfigured to 65536 (KV streaming on: the context's KV cache
lives in RAM, ~0.9 GB at 64K), plus --vram-reserve-mib 2048 (the auto
expert cache otherwise starves the verify phase). Cycle-1 data then
answered the studied question decisively: arm C's session on ticket 0452
peaked at 101,129 tokens — real project tickets run past 64K — so arm B
was reconfigured to 131072 (KV streaming scales in RAM, ~1.8 GB at 128K)
BEFORE any project-cycle arm-B run, keeping within-cycle comparability
clean (the 65K 0188 pilot run is excluded as pilot). Context is now
uniform across the three local arms at 131072.

Arm C notes: the official 35B-A3B is the 3.6-generation model already on
disk at `/data/models/gguf/qwen/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` (21 GB) — no
official Qwen3.8-35B-A3B exists at note time; if one ships, it enters as a
future cycle under §8. Community reports rate the 35B-A3B quants highly on
real-codebase issues; 3B active should decode fast on this hardware.

Hosted arms (§8 rules apply — cost first-class, egress boundary, no
serialization):

| | Arm D (hosted) | Arm E (hosted) | Arm F (hosted) |
|---|---|---|---|
| Model | claude-opus-5-5 (latest Opus, live API id, superseding the 4.x line) | gpt-6-sol (live API id; superseded gpt-5.6-sol at half price) | GLM 5.3 (Mistral Hosted, `zai-glm-5-3`) |
| Provider | Anthropic | OpenAI | Mistral |
| Effort | recommended default, recorded | recommended default, recorded | recommended default (thinking high, temp 1.0), recorded |
| Knob policy | each arm runs at its own recommended default reasoning effort, logged per run — unlike local arms, which are pinned and matched (§4.6) | | |
| Cost | per-token, recorded per run | per-token, recorded per run | published: $1.40/$4.40 per M in/out, $0.26 cached |

Arm F notes: GLM 5.3 via Mistral hosting is the default routing model of the
Mistral Vibe runtime itself — the model family that authors this harness's
workflows (including this note's session), which is exactly why §8's judge
decorrelation must exclude it from the panel when it competes. Text-only (no
images) — the sample's tasks are text-only anyway.

Hosted arms are the author's workhorses; the tier under them (GPT-5.6 Terra,
Claude Sonnet) is reserved for future cycles under §8.

All local arms serialize requests one at a time, so throughput ceilings
differ only by speed — a legitimate part of the measured construct.

Arms are configuration slots, not hardcoded pairings: any OpenAI-compatible
endpoint with a resolvable Pi provider id can fill one. The table above is the
first cycle's instantiation; the arm definition (model id, endpoint, engine,
pinned version) lives in the tournament config, not in the skills.

## 3. Arena and protocol (full crossover)

- **Arena**: Pi configured with both backends in `~/.pi/agent/models.json`,
  driving the IDH harness skills (`hunt`, `raid`) — the same harness, same
  skills, same knobs for both arms.
- **Full crossover**: every ticket in the sample is attempted by **all six**
  arms this cycle — every model works on all tasks. Local arms (A, B, C) run
  serialized on padme's GPUs; hosted arms (D, E, F) run on their providers'
  hardware, in parallel with the local schedule where convenient. Each run
  starts from a fresh historical worktree at the ticket's original base commit.
- **Sample**: closed tickets drawn from the author's repos history so merged
  ground truth exists. Judges fix the strata (project x ticket type x
  difficulty) in advance; the draw is random within strata. Strata must
  deliberately include non-coding tickets (prose, ticket-writing,
  housekeeping) — the deck must not be stacked for the code-specialised arm.
  Target N = 8-12 tickets (48-72 runs at k=6).
- **Task types**: hunt (ticket scoping) and raid (autonomous implementation),
  scored separately; the quality rubric differs by type.
- **No external reviewers in-run — enforced, not requested**: gates during
  the tournament are mechanical only (exit criteria, hygiene tests),
  identical retry/bounce budgets for all arms. The harness's reviewer
  machinery (`/verify-gate` external seats, `/gaze`, `/review-pr` panels)
  is NOT invoked during tournament runs: those seats would be external
  help mid-run, and any family shared with the post-task panel would break
  judge blindness before scoring begins. Enforcement is environmental:
  the runner's environment carries only the arm's own provider
  credentials (no OpenRouter, no cross-provider keys), so external help is
  unreachable — local arms cannot leave the machine, hosted arms can only
  reach their own API. The arm's own self-review — including same-model
  subagents — remains in: it is the stack's capability and part of what is
  measured. Self-declared "done" against mechanical criteria is a measured
  behaviour, caught later by post-task review.
- **Full transcript recording**: every run's complete conversation is
  archived (Pi session storage captured per run into the arena run
  directory), successful runs and hiccups alike. Post-tournament analysis
  reads the transcripts first-class: hiccups — mid-run confusion, retry
  loops, tool-call failures, dead ends — are tuning material for the
  harness, not just noise around the scores.

## 4. Validity rules

1. **Provider assertion per run** (non-negotiable). Pi serves via
   `openrouter/auto` without warning when a model id fails to resolve
   (0977 finding, 0979 rule). Every tournament run logs `--mode json` and asserts
   `provider` matches the declared backend — hosted arms included: a run
   billed as Opus or Sol must prove it ran on Anthropic or OpenAI. Any
   mismatch voids the run.
2. **Strict serialization (local arms).** The local stacks never hold the
   GPUs at the same time. Per ticket and per arm: stop one server, start the
   next, confirm `/health`. With three local arms this is 3N serialized
   server sessions — schedule accordingly. Hosted arms are outside this
   rule (disjoint hardware).
3. **Randomised within-ticket order.** A/B coin flip per ticket (recorded);
   cancels warm-page-cache advantage and thermal drift. Cooldown between runs.
4. **Time-filtered memory.** IDH reads project memory at task start, and
   `tickets/closed/` plus the journal contain the solutions. Expose only
   memory and closed tickets dated before each sampled ticket's creation.
   Unfiltered exposure would make both arms answer-copying, inflating quality.
5. **t0 = `/health` OK** on the serving stack; model load time is excluded
   from time-to-task and logged separately.
6. **Matched knobs for local arms.** Reasoning effort, sampling parameters,
   retry budgets and Pi's max-concurrent-agents cap recorded and fixed
   identically for the local arms (Strata defaults to reasoning high — pin it
   explicitly). Hosted arms run at their recommended default effort instead
   (author decision), recorded per run — the local arms' matched-knob rule
   cannot be imposed across providers, so effort is a declared per-arm
   property of the comparison, logged, not a hidden variable.
7. **Smoke test before the tournament**: 0977-style tool-calling probe (read a file
   via tool) on Strata. llama.cpp tool-calling is proven; if Strata's fails,
   the arm collapses for an infrastructure reason that must not be misread
   as model quality.

## 5. Measurements and pre-registered statistics

- **Speed**: wall-clock from t0 (`/health` OK) to self-declared done
  (mechanical exit criteria checked). Local runs happen only on an unloaded
  padme: the runner asserts no other GPU processes and a load below a
  pre-registered threshold before starting, and records the date and hour
  (UTC and local) with every run — local speed is thermal- and
  history-sensitive, so time-of-day is a recorded covariate, not a footnote.
  Heavy-tailed: analyse paired per-ticket ratios / log-transformed deltas.
- **Cost**: money first, tokens alongside. Hosted arms: provider balance
  checked immediately before and after each run where the provider exposes a
  balance API; where it does not, usage tokens x the pre-registered price
  table (usage metadata from responses). Token counts (input, output, cached)
  recorded per run regardless. Local arms: zero marginal money; an energy
  estimate (draw x time x tariff) may be recorded but never substitutes for
  hosted balance data.
- **Correctness (boxing scoring)**: blind panel, disjoint from the candidate
  families — with Opus, Sol and GLM 5.3 competing, no Anthropic, OpenAI or
  GLM judges; a Gemini / DeepSeek / Kimi class panel. Blindness mechanics:
  each judge invocation is a fresh session by construction (a separate
  `pi --print` process, or a spawned subagent with its own session) — the
  orchestrator's context never enters the judge's context; the only channel
  is the submission package. Therefore the package is the leak surface and
  must be normalized: plain `git diff` output only, no chat templates,
  thinking blocks, tool-call idioms, author names or timestamps; identical
  formatting across arms before judging. Diffs stripped of
  backend identity, arm mapping randomised per ticket, judges see all k
  submissions per ticket in random order. Each judge scores each submission
  from 10 points down, with fixed pre-registered deductions per the common
  vocabulary (~/arena/judge-rubric.md): REROLL −3, CHANGES −2, COMMENTS −1,
  NITS −0.5, floor 0, DNF = 0. Tariffs fixed before the first run and
  identical for every arm, judge and round. Arm score per ticket = sum over
  the panel (boxing style); the merged reference PR is context, not a gold
  standard — a solution better than the author's is not penalised.
- **Role decomposition (analysis dimension)**: a run composes three jobs —
  orchestrator, worker, reviewer. Reviewer is already disentangled by
  construction (blind external panel, mechanical in-run gates; an arm's
  only reviewer role is its self-declared done). Orchestrator vs worker is
  decomposed observationally from the recorded transcripts: time/tokens/
  actions attributed per run phase (plan / execute / verify), plus the
  self-review calibration metric (panel score vs self-declared-done rate
  per arm). A causal split (fixed-conductor worker-only runs on a subset,
  pre-decomposed prompts identical across arms) is a deferred follow-up,
  run only if the primary results are ambiguous — the primary tournament
  measures stacks whole, because the routing question is about the stack.
- **Primary outcome**: paired per-ticket win/loss on the correctness sum;
  secondary: paired time ratio; cost as a first-class reported column, not a
  tiebreaker. Wilcoxon signed-rank over pairs; report magnitudes and the
  deduction composition (counts per category), not just totals. DNF policy:
  equal time cap per run; a DNF scores 0 on correctness and a capped time.
- Failure of a run (crash, provider mismatch) → re-run once, then DNF.
- **Studied question — is arm B's 65K context enough?**: token usage
  (prompt, generation, per turn) is recorded per run against each arm's
  ceiling; the analysis answers with data — overflow rate, per-task-type
  token profiles, and whether the sampled harness work fits 65536 at all.
  The answer either clears arm B's context as sufficient for harness work
  or motivates the patched-engine path back to larger contexts (§2 arm B
  notes).

## 6. Interpretation boundaries

- Stack-level verdict only (model x engine bundled); no attribution to either
  factor alone.
- The Coder is code-specialised by construction (~91% of Flash-Next's
  SWE-bench Verified per its authors, weaker outside code): the balanced
  sample is what keeps the tournament honest.
- Single machine, single week: server versions pinned in the run log; the
  verdict is time-stamped, not eternal.
- If arm B wins on coding tickets only and loses prose/housekeeping, the
  routing outcome may be task-conditional routing, not a replacement.

## 7. Logistics

- Strata install at `~/Strata`; model files at
  `/data/models/gguf/Strata-data/models/coder-IQ1_M/` (download in progress
  at note time; ~65 GB total with the MTP layer).
- Port 8081 keeps the incumbent server untouched at 8080 during setup; arm C
  gets a second llama-server on 8082 (bring-up work).
- Hosted arms D, E and F: API keys per the keystore convention
  (`~/.config/keys/`; arm F rides the Mistral provider Vibe already
  configures), Pi provider entries in `models.json`, model versions pinned at
  cycle start; per-run cost recorded from provider usage metadata.
- Estimated cost: 3N serialized local runs of hunt+raid, hours each — roughly
  1.5 days of machine time for N=10; plus 3N hosted runs at Opus/Sol/GLM
  prices, which is the real budget line — pre-register a spend cap per
  hosted arm.

## 8. Any candidate, any number of arms

The instrument is candidate-agnostic. A candidate is a (model id, endpoint,
engine, pinned version) triple declared in the tournament config; a cycle pairs the
incumbent champion against one or more challengers.

- **K-arm extension**: every candidate in a cycle runs the full crossover over
  the same sample (strata held fixed; the draw may be refreshed per cycle).
  Statistics stay pairwise — Wilcoxon signed-rank per pair over common
  tickets, reported round-robin. A challenger displaces the incumbent's
  routing only by winning on quality at acceptable cost.
- **Local candidates** (Qwen 4 family when it ships — Flash-Next is its
  architecture preview, so Strata/llama.cpp support is expected): the
  serialization and order rules of §4 apply as-is when arms share padme's
  GPUs; disjoint hardware removes them.
- **Hosted candidates** (Sol, Opus; the tier under them, Terra, Sonnet): no
  shared hardware, so hosted arms may run in parallel and order randomisation
  between disjoint arms is unnecessary. Two rules replace it:
  - **Cost is a first-class outcome**: tokens x price per run, recorded next
    to time-to-task; the verdict is a quality/cost/time triple, not a rank.
  - **Egress boundary**: only cleared material (public repo content) may be
    sent to hosted arms — uncleared material never leaves the machine
    (AGENTS.md project-memory boundary; the 0979 lesson is that silent
    rerouting breaks this rule invisibly, hence provider assertion for
    every arm, hosted or local).
- **Judge decorrelation**: the post-task panel must be disjoint from the
  candidate set — a model family cannot judge its own tournament. When Sol and
  Opus are candidates, judges come from other providers; when they are
  workhorses, they may judge local tournaments.
- **Champion ladder**: each cycle's paired results accumulate; the champion
  is whoever the latest cycle failed to displace. This is the same
  offline-ranking posture as the reviewer-attribution board (tickets/1007).

### Cycle-2 candidate slate (author, 2026-10-04 — effort levels are part of the arm definition)

The author's OpenRouter top-of-Python quinté plus frontier anchors; every
arm declares its effort explicitly. Prices at $/1M in/out, pre-registered at
cycle-2 launch (§7 spend caps); ids verified live 2026-10-04.

| Arm | Model | Route | Effort | Price (in/out) |
|---|---|---|---|---|
| D2 | claude-opus-5.5 @ **medium** | Anthropic | one notch BELOW recommended default (high) — the effort axis becomes a measured variable | 4/20 |
| E2 | gpt-6.1-sol | OpenAI | recommended default | pre-register at launch |
| G | claude-sonnet-5-5 | Anthropic | recommended default, recorded | 2/10 |
| H | stealth/space-bunny-alpha | OpenRouter | recommended default — frontier-fast, FREE today | 0/0 (free tier; rate limits replace the spend cap) |
| I | deepseek-flash (V4.1-Flash) | DeepSeek | recommended default | pre-register at launch |
| J | z-ai/glm-5.3-flash | OpenRouter | recommended default | 0.15/0.50 |
| K | xiaomi/mimo-v2.6-flash | OpenRouter | recommended default | 0.14/0.28 |
| L | gpt-6-luna | OpenAI | **medium** (the documented default; effort ladder: none/low/medium/high/xhigh/max) | 0.10/0.50 |

Arm L is the author's designated economic worker — the expected local-killer:
at $0.10/$0.50 per 1M, a typical raid-shaped run (~40K in / 30K out) costs
about $0.019, directly comparable to the free local arms' zero-marginal-cost
plus wall-clock. Its cycle-2 question is whether hosted economics have
crossed the line where local inference stops paying for its electricity.

Panel consequence (§8 decorrelation, binding): with DeepSeek V4.1 Flash as a
candidate, the DeepSeek judge seat is disqualified for cycle 2 — the panel
must be re-seated from the remaining disjoint families (Gemini, Kimi, and a
replacement, e.g. a Grok or Llama-class seat). GLM 5.3 Flash changes nothing:
GLM was already a candidate family in cycle 1 and the panel already excludes
it. Local arms A/B/C carry over unchanged; arm F (zai-glm-5-3) faces its own
Flash sibling as well as the field.

### Cycle-2 local rebalance (author, 2026-10-04 — the quality/speed curve on one engine)

| Arm | Model | Engine | Effort | Notes |
|---|---|---|---|---|
| B2 | Flash-Next FULL, IQ3_S (125B-A6B, all experts) | Strata :8081 | pinned | the quality point of the curve — the unpruned 125B, ~62 GB RAM |
| B3 | Flash-Next FULL, Q2_0 | Strata :8081 | pinned | the speed point — Strata's own table: Q2_0 ≈ 1.8x IQ3_S decode; ~48 GB RAM; download deferred until disk allows (post-cycle-1, when the Coder IQ1_M's 63 GB can free) |
| C2 | Qwen3-Coder-30B-A3B-Instruct, UD-Q4_K_XL ("le bon vieux Qwen-coder-next") | llama.cpp | pinned | the classic coding MoE (30B-A3B) — cycle-1's C showed the 3.6-35B-A3B failing on research work; C2 tests whether the coder-lineage sibling does better on code tasks |

B2/B3 form the within-engine quality/speed pair: same engine, same model,
two quants — the curve is measured, not assumed. B (Coder IQ1_M) stays as
the cycle-1 anchor for continuity. Context 131072 with KV streaming for the
Strata seats, matching arm B's verified configuration.

Deferred experiment (author, 2026-10-04): **engine disentanglement** — when
llama.cpp support for Flash-Next is confirmed workable (community reports
MTP-on-llama.cpp attempts; Unsloth ships llama.cpp-compatible GGUFs), run
the SAME Flash-Next weights on both engines and complete the 2x2 the
bundled-stack design cannot isolate: {engine: Strata vs llama.cpp} x
{quant: IQ3_S vs Q2_0}. Constraint to plan for: Strata's GSQ-RCO quants are
engine-specific — the engine duel needs the Unsloth GGUF copy (~110 GB at
IQ3_S-class), so it lands after cycle 2 frees disk. This closes the
attribution gap stated in §1: stack winners would finally decompose into
model and engine factors.

Deferred experiment (author, 2026-10-05): **harness tournament** — a SEPARATE
series from the model tournament; the manipulated variable is the agent
runtime, model and effort held fixed. Three pairs, same sample, same blind
panel: (1) GLM 5.3 @high — pi vs Vibe (Vibe's catalog default for glm-5-3 IS
high, confirmed from its session runtime-state; so pi-arm F cycle 1 is the
reusable incumbent side, 10 legs already judged); (2) Opus 5.5 @low — pi vs
Claude Code CLI (pi side = arm D2, cycle 2, in flight); (3) Sol 6.1 @low — pi
vs Codex CLI (pi side new: E2 runs @medium, a pi-sol @low arm is needed).
Open items before launch: verify claude-cli and codex expose a pinnable
"low" effort AND record it (as Vibe does in runtime-state), else the pairing
measures two things at once; runner needs a runtime-agnostic path (headless
invocation, per-CLI live-directory isolation in the task prompt, provider
assertion, usage extraction — Vibe path validated 2026-10-05: vibe -p +
VIBE_ACTIVE_MODEL pinned + --auto-approve, usage with cached_input_tokens
extractable from the session journal, Mistral cache billed at 10% of input).
Estimated cost at launch time: ~$25-35 new legs + ~$15 panel.

### Cycle-3 slate (author, 2026-10-05): Flash-Next convergence

The local and hosted copies of the SAME WEIGHTS meet at matched effort. Arm
set (gated on cycle-2 results): the BEST of the THREE local Flash-Next points —
B (Coder pruned variant, IQ1_M), B2 (full IQ3_S), B3 (full Q2_0; the cycle-2
curve spans pruned-vs-full as well as quant level) — run at EXPLICIT @medium, vs
the hosted production sibling `qwen/qwen3.8-flash` (0.15/0.47 $/M, 1M ctx,
served by Alibaba only — MaaS clause of the Qwen Community License) at BOTH
its default (@xhigh — the template default, pi maps high->xhigh) and @medium.
Same sample, same panel, same frozen prompt.

Questions answered: (1) local-vs-hosted at matched effort — does the local
electricity-and-wall-clock still pay when the hosted flash costs ~$0.10-0.30
per leg? (2) the flash's effort axis (xhigh vs medium), including the
documented caveat that lower effort can LENGTHEN multi-turn agent tasks
(insufficient analysis -> failures -> retries) — cycle 1 already priced the
same trade-off for Opus (D @medium vs D2 @low).

Open build items, verified at cycle-3 launch: the local serving must honor
reasoning_effort — llama.cpp has --reasoning-effort server-side (the setting
lives in the 3.8 chat template); Strata's pass-through to verify, else pin
the effort server-side. HOSTED ROUTE UPGRADED (2026-10-05): the author's Ali
account is live — QWEN_API_KEY_AEDIST on dashscope-intl (172 models, qwen3.8-
flash and qwen3.8-27b verified served) — the hosted arm goes DIRECT via a
custom pi provider on the OpenAI-compatible endpoint, bypassing OpenRouter
(no key-cap pressure, direct billing); OR stays the fallback route. Bonus:
the 27B local-vs-hosted duel can use the same direct route (qwen3.8-27b
served there) instead of the rate-limited OR :free tier. Price
pre-registration at launch ($0.15/$0.47 expected per the rate card). Local arms' current label
"no knob" becomes "@template-default (xhigh)" until the effort is pinned.
Estimated cost: hosted 2 arms x 10 legs ~ $3-6 + panel ~$15.

### Extended-context rerun (author, 2026-10-05): the 262K ceiling experiment

Motivated by cycle-1 data: local sessions BUTT against 128K (pi compaction
confirmed on the 4 big tickets; peaks cluster at 112-118K) while hosted arms
expand to 232-236K on the same tickets (Opus/GLM, never compacting). The
local servers run HALF the models' native window (131072 vs 262,144 trained;
Strata's --yarn-orig-ctx default 262144 confirms the card).

Design: rerun the 4 compaction tickets (0333, 0452, 0673, 0874) on the SAME
local arms with the window at the trained 262,144 — no rope scaling (native),
KV int8 AT MOST (the 2026-09-27 bench: int8 indistinguishable from fp16;
q4_0 KV measurably degrades and WORSENS with context — +12% perplexity at
8K — hence KV q4/k8v4 EXCLUDED from quality arms), pi contextWindow raised
to 262144 so compaction moves to ~250K. Paired comparison vs the 128K runs
panel scores + compaction count + wall-clock (KV streams ~2.8 GiB to RAM).

The 524K tier is NOT run (author, 2026-10-05): the observed agent-work
ceiling is ~236K — 262K covers all of it; 524K is a documented capability
(needle bench validated 512K recall, linear and yarn x2), not a tournament
tier. STANDING DESIGN RULE (author): if a runner would saturate more than
256K, it is a MONSTER TICKET and the work must be SPLIT — extend the
decomposition, not the window. Context ceiling as a forcing function for
task decomposition.

## 9. Children (to be opened at hunt time)

- backend bring-up: Strata smoke test in Pi (tool-calling probe + provider
  assertion + models.json entry)
- sample selection: strata definition, random draw, historical worktree
  preparation
- tournament execution: run matrix (ticket x arm), run log
- analysis and verdict: paired statistics, blind review synthesis, routing
  recommendation recorded in STATE/ROADMAP and `models.json`
