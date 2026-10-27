# Trace census — June 2026 (28-day window)

First deterministic census of the Claude Code session-trace corpus, produced by
`scripts/trace-stats.py` (ticket 0237, phase 1 of the trace-doctor study,
tracking ticket 0236). Run date: 2026-06-10. Zero LLM tokens spent.

## Method

- Corpus: every `*.jsonl` under `~/.claude/projects/` — main-session traces
  plus `*/subagents/agent-*.jsonl`. Worktree-suffixed project dirs are folded
  into their parent project.
- Window: in-record timestamps (never file mtime); a file counts when its
  last record is within 28 days of the run.
- **Dedupe rule**: one assistant message spans multiple JSONL rows (one per
  content block), each repeating the same `usage` object. Usage is counted
  once per unique `message.id`. Summing per row overstates ~2.7x — this bug
  inflated the first spot analysis (see 0236) and is now a fixture case in
  `tests/test_trace_stats.py`.
- `<synthetic>` model records (harness-injected, no API cost) are excluded
  from $ and token sums (52 in the window).
- Pricing: each message priced by its own `model` field, $/MTok — Opus 4.x
  5/25, Sonnet 4.x 3/15, Haiku 4.5 1/5, Fable 5 10/50; cache read 0.1×
  input, 5m cache write 1.25×, 1h cache write 2× (the 5m/1h split is taken
  from `usage.cache_creation` when present). Unknown models are flagged, not
  guessed: 0 unknown-model messages in this window.
- Schema tolerance: 0 unparseable lines out of 388,467 (<5% criterion met
  trivially); 0 unreadable files.

## Headline numbers

| Metric | Value |
|---|---|
| Trace files parsed | 2,412 (1,747 in window; 665 older/undated) |
| Sessions | 305 (main agents: 304 with rows) |
| Agents (rows) | 1,747 (304 main + 1,442 subagents + 1 orphan) |
| API turns (unique assistant messages) | 90,362 |
| Total cost | **~$6,544 / 28 days** (~$234/day) |

## $ by category

Token totals are exact (deduped); the $ split uses each row's dominant model
(close approximation — sessions are 90%+ single-family).

| Category | Tokens | ~$ | Share |
|---|---|---|---|
| cache_read | 9.69 B | 4,152 | **63%** |
| cache_write | 231 M | 1,258 | 19% |
| output | 28.5 M | 607 | 9% |
| fresh input | 4.4 M | 22 | <1% |

Re-reading cached context is two-thirds of all spend. Anything that shortens
context or shortens agent lifetimes attacks the dominant category.

## Turns per agent, by role

| Role | n | mean | median | p90 | p99 | max |
|---|---|---|---|---|---|---|
| main | 304 | 156 | 80 | 327 | 882 | 5,255 |
| subagent | 1,442 | 30 | 20 | 63 | 155 | 649 |

| Role | mean $ | median $ | p90 $ | p99 $ | max $ |
|---|---|---|---|---|---|
| main | 16.30 | 4.72 | 36.53 | 177.04 | 368.90 |
| subagent | 1.10 | 0.57 | 2.11 | 7.57 | 75.07 |

Main sessions are 17% of agents but ~76% of spend ($4,955 of $6,544). The
N=1 intuition that subagent fan-outs drive cost is wrong at corpus scale:
long-lived *main* conversations are the cost center.

## cache_read vs turns

Mean total cache_read and mean $ by turns-decile (agents with ≥1 turn):

| Decile | Turns range | cache_read | $ |
|---|---|---|---|
| d1 | 1–5 | 0.1 M | 0.13 |
| d2 | 5–10 | 0.2 M | 0.32 |
| d3 | 10–15 | 0.4 M | 0.41 |
| d4 | 15–18 | 0.6 M | 0.55 |
| d5 | 18–23 | 0.7 M | 0.68 |
| d6 | 23–29 | 1.0 M | 0.87 |
| d7 | 29–38 | 1.4 M | 1.01 |
| d8 | 38–56 | 2.3 M | 1.46 |
| d9 | 56–106 | 5.6 M | 3.99 |
| d10 | 106–5,255 | 42.7 M | 27.72 |

Cost grows mildly superlinearly with turns: the log-log fit is
log($) = −3.86 + **1.134**·log(turns), R² = 0.775. The exponent is ~1.1,
not ~2 — see H2 below. The top decile is qualitatively different: 7.6× the
cache_read of d9 for 1.9× the turns, i.e. *long agents also carry far more
context per turn*.

## Top-20 most expensive agents

`resid` = log-residual from the cost~turns fit (+1.0 ≈ 2.7× the curve).

| $ | resid | turns | agent | project | model |
|---|---|---|---|---|---|
| 368.90 | +1.39 | 1,624 | main | aedist-technical-report | opus |
| 230.13 | +1.77 | 767 | main | git-erg | opus |
| 178.21 | +1.69 | 654 | main | chemin-de-voix | opus |
| 177.04 | −0.68 | 5,255 | main | chemin-de-voix | sonnet |
| 168.98 | +1.61 | 669 | main | aedist-technical-report | opus |
| 130.10 | +1.49 | 594 | main | aedist-technical-report | opus |
| 116.69 | +1.35 | 610 | main | aedist-technical-report | sonnet |
| 112.12 | +1.67 | 441 | main | aedist-technical-report | opus |
| 107.18 | +1.44 | 521 | main | aedist-technical-report | opus |
| 102.42 | +1.82 | 357 | main | aedist-technical-report | opus |
| 97.78 | +1.69 | 384 | main | aedist-technical-report | opus |
| 96.61 | +1.15 | 615 | main | aedist-technical-report | opus |
| 76.53 | +1.23 | 465 | main | IDH | opus |
| 75.76 | +1.46 | 378 | main | IDH | opus |
| 75.07 | +1.29 | 436 | agent-abeb2c87… | aedist-technical-report | opus |
| 68.13 | +0.01 | 1,233 | main | chemin-de-voix | sonnet |
| 67.78 | +1.01 | 509 | main | aedist-technical-report | opus |
| 63.45 | +0.98 | 491 | main | aedist-technical-report | opus |
| 62.42 | +0.65 | 649 | agent-ad937f28… | aedist-technical-report | opus |
| 62.37 | +1.44 | 323 | main | IDH | opus |

18 of 20 are main sessions; 17 of 20 are Opus. The two Sonnet outliers
(5,255 and 1,233 turns) sit *on or below* the curve — model choice moves an
agent off the cost curve as much as turn count does.

By session, the 5 most expensive: raid $404.75 (28 agents), raid $355.23
(24 agents), git-erg "model" session $279.26 (48 agents), gaze-entry
$253.58 (40 agents), chemin-de-voix interactive $181.30 (14 agents).

## Distributions worth knowing

- **Heavy tail, mild bimodality in per-agent cost**: log-histogram of agent
  cost has modes at ~$0.1–1 (subagents, n=971) and ~$1–10 (mains, n=495),
  with 121 agents above $10. Top 5% of agents = **66%** of spend; top 1% =
  34%. The Pareto knife falls between "an agent" and "a long main session".
- **Read-only drift exists but is modest**: 998 of 1,442 subagents are
  read-only (no Edit/Write/NotebookEdit); 68 of them ran past 40 turns.
- **Repeated work signatures**: 172 agents Read the same file ≥5 times;
  20 agents ran the identical Bash command ≥5 times.
- **Final-turn cache_read (context-size proxy)**: median 48K, p90 114K,
  p99 395K, max 982K — a long tail of agents ending life near the 1M
  context ceiling, where every subsequent turn re-reads ~1M tokens.

## Validation (exit criteria of 0237)

- 2,412 files parsed without crashing (>2,000 ✓); 1,747 in window — both
  counts reported because the window filter uses in-record timestamps.
- Skipped lines: 0 of 388,467 (<5% ✓).
- Spot-check on session 96516ff3 (aedist raid wave): the main trace has 278
  usage rows vs 107 unique message ids (review-time measurement was 248→96;
  the session was live and grew) — dedupe demonstrably active. Deduped
  session totals (main + 16 subagents): cache_read 65.2M vs ~57.5M at
  review time (grew, consistent), output 157K vs ~264K claimed at review
  time. The output gap runs the *wrong way* for growth: the review's
  throwaway-prototype figure was itself residually inflated. The committed
  script's numbers are fixture-tested; treat the 0236 spot figures as
  upper bounds.

## Discovery feedstock (input to phase 2, see 0236)

### (a) Cost outliers by residual, not size

Top residual outliers among agents costing >$1 (far *off* the cost~turns
curve, not merely big):

| resid | $ | turns | cache_read | agent | project |
|---|---|---|---|---|---|
| +3.09 | 54.70 | 67 | 12.0 M | main | git-erg |
| +2.54 | 11.65 | 28 | 4.6 M | main | IDH |
| +2.40 | 2.11 | 7 | 0.1 M | agent-aa495618… | git-erg |
| +2.38 | 2.40 | 8 | 0.2 M | agent-aa1f62fc… | git-erg |
| +2.14 | 1.89 | 8 | 0.1 M | agent-a7b1a23d… | git-erg |
| +2.03 | 1.95 | 9 | 0.4 M | main | aedist-technical-report |
| +1.82 | 102.42 | 357 | 127.7 M | main | aedist-technical-report |
| +1.77 | 230.13 | 767 | 356.2 M | main | git-erg |
| +1.69 | 97.78 | 384 | 143.6 M | main | aedist-technical-report |
| +1.69 | 178.21 | 654 | 217.5 M | main | chemin-de-voix |

Two distinct off-curve shapes: (i) short agents (<10 turns) paying $2+ —
huge per-turn context, likely heavy preamble cache_writes; (ii) long mains
whose cache_read per turn dwarfs the norm (300–500K/turn) — context that
never shrinks. Both are open-coding targets.

### (b) Bimodal / heavy-tailed distributions surfaced

1. Per-agent cost (modes ≈ $0.3 and ≈ $3; tail to $369).
2. Final-turn cache_read (median 48K vs p99 395K — most agents stay small,
   a tail rides near the context ceiling).
3. Spend concentration (top 5% of agents = 66% of $).

### (c) Stratified random sample frame for LLM open-coding

Sampled by project × entry-skill × session-cost-decile (decile 1 =
cheapest; cheap deciles included deliberately — frugal sessions show what
good looks like). Seed 237, ≤3 cells per decile. Paths relative to
`~/.claude/projects/`.

| Dec | Project | Entry skill | $ | Agents | Main trace path |
|---|---|---|---|---|---|
| 1 | aedist-technical-report | effort | 0.00 | 1 | `-home-haduong-aedist-technical-report/542e887b-a055-4672-a349-937b5b929ef5.jsonl` |
| 1 | aedist-technical-report-docs | (none) | 0.00 | 1 | `-home-haduong-aedist-technical-report-docs/3274cf36-6a99-4518-b7b0-0f0274444fff.jsonl` |
| 1 | padme | (none) | 0.00 | 1 | `-home-haduong-padme--claude-worktrees-t0028/839f8569-e584-44b8-991c-cc58353c37c4.jsonl` |
| 2 | IDH (~/.claude) | celebrate | 0.51 | 1 | `-home-haduong--claude/a2f09575-dcbe-4eef-879e-d22edd2b88cf.jsonl` |
| 2 | IDH (~/.claude) | verify | 0.19 | 1 | `-home-haduong--claude/6aec3371-ad10-41d2-a8e1-a653c155156c.jsonl` |
| 2 | aedist-technical-report | celebrate | 0.34 | 1 | `-home-haduong-aedist-technical-report--claude-worktrees-explore-t289/65c82411-4937-438a-a742-bb2537397df1.jsonl` |
| 3 | aedist-technical-report | loop | 1.03 | 1 | `-home-haduong-aedist-technical-report/eda10041-f6e3-4a55-89e5-d458235feff3.jsonl` |
| 3 | chemin-de-voix | merge | 0.59 | 1 | `-home-haduong-chemin-de-voix--claude-worktrees-raid-overnight-sweep/63b8501c-7347-487b-9b44-e538085fc625.jsonl` |
| 3 | chemin-de-voix | perch | 1.30 | 1 | `-home-haduong-chemin-de-voix/e4cc6990-d371-41a3-b661-3dc59c037ff7.jsonl` |
| 4 | aedist-technical-report | housekeeping | 3.06 | 1 | `-home-haduong-aedist-technical-report/03c5e78e-c87c-49cd-8100-d561c8699cad.jsonl` |
| 4 | aedist-technical-report | merge | 3.07 | 1 | `-home-haduong-aedist-technical-report/e23002cf-aa34-4dee-beda-f2985d7f7231.jsonl` |
| 4 | chemin-de-voix | celebrate | 1.46 | 1 | `-home-haduong-chemin-de-voix/f58bf9dc-2a2d-4bf2-8f52-d1c99dbb3d89.jsonl` |
| 5 | aedist-technical-report | merge | 5.08 | 1 | `-home-haduong-aedist-technical-report/e6212fb6-ee3d-4868-97f0-3ee0685b2b17.jsonl` |
| 5 | chemin-de-voix | housekeeping | 3.16 | 1 | `-home-haduong-chemin-de-voix/467339b6-956c-4f7b-b351-cb4b5612bde6.jsonl` |
| 5 | git-erg | end-session | 4.38 | 1 | `-home-haduong-git-erg--claude-worktrees-t0202/07745b70-f383-4683-9b2c-9fc0e08496ec.jsonl` |
| 6 | chemin-de-voix | merge | 5.90 | 1 | `-home-haduong-chemin-de-voix/be60ade1-d9f6-4a05-a08e-1874e96670c5.jsonl` |
| 6 | chemin-de-voix | ticket-new | 5.52 | 4 | `-home-haduong-chemin-de-voix/822c9c51-c25f-4231-9efb-cb69dd291453.jsonl` |
| 6 | git-erg | ticket-new | 6.00 | 4 | `-home-haduong-git-erg--claude-worktrees-t0160-followup/d27c1566-c018-4f41-838e-05b153511a28.jsonl` |
| 7 | aedist-technical-report | housekeeping | 13.76 | 3 | `-home-haduong-aedist-technical-report--claude-worktrees-housekeeping/e63dac2c-61c4-4aeb-a18b-37ac8a268c54.jsonl` |
| 7 | chemin-de-voix | healthcheck | 10.78 | 2 | `-home-haduong-chemin-de-voix/e6535bce-fc93-4a50-a534-f5364fd023c4.jsonl` |
| 7 | padme | raid | 10.04 | 4 | `-home-haduong-padme/3f1f90f2-faed-4288-b0cb-9f496e567323.jsonl` |
| 8 | IDH (~) | raid | 22.85 | 1 | `-home-haduong/f72154b3-d66f-438d-a7d5-46b1d1a81931.jsonl` |
| 8 | aedist-technical-report | ticket-new | 16.62 | 2 | `-home-haduong-aedist-technical-report/60ffdb7a-3472-4ce2-b965-eb2267d2e033.jsonl` |
| 8 | git-erg | fang-audit | 23.23 | 2 | `-home-haduong-git-erg/ff83e53f-129c-436d-b421-d6c97d72674d.jsonl` |
| 9 | aedist-technical-report | claude-api | 33.84 | 4 | `-home-haduong-aedist-technical-report--claude-worktrees-explore-anthropic-caching/4ce9fb20-3b79-41a4-90ba-e2b94004e133.jsonl` |
| 9 | aedist-technical-report | perch | 29.21 | 2 | `-home-haduong-aedist-technical-report/a35a77ee-6d22-4e10-a1ba-db903464f65d.jsonl` |
| 9 | aedist-technical-report | ticket-claim | 42.50 | 7 | `-home-haduong-aedist-technical-report/f2d5c6fe-e355-4bbd-a8e7-8cba453c7d7b.jsonl` |
| 10 | IDH (~/.claude) | code-review | 60.76 | 30 | `-home-haduong--claude/ad59e972-efa3-40b6-9fe9-38345f0047ab.jsonl` |
| 10 | IDH (~/.claude) | merge | 102.55 | 33 | `-home-haduong--claude/a78d6efc-7746-40ac-ad23-c854b1fd3641.jsonl` |
| 10 | aedist-technical-report | gaze | 253.58 | 40 | `-home-haduong-aedist-technical-report/dd5fd1a6-54f6-4a9c-8dac-81a5fb68b497.jsonl` |

Reproduce with seed 237 over the census CSV (regenerate via
`uv run python scripts/trace-stats.py --days 28 --output <csv>`).

### (d) H1–H5 seed assessment — seeds from N=1, NOT findings

| Seed | Aggregate signal | Verdict for phase 3 |
|---|---|---|
| H1 cache_read dominates $ | 63% of spend ($4,152 of $6,544) | **Supported** — promote to confirmation |
| H2 cost ~ turns² | log-log exponent **1.13** (R²=0.78), not ~2 | **Not supported** as stated — cost is mildly superlinear in turns; the quadratic intuition came from one extreme session. Reframe: "top-decile agents carry disproportionate context per turn" |
| H3 read-only agents drift past budget | 68 read-only subagents >40 turns (4.7% of subagents) | **Weakly supported** — real but small; quantify $ share in phase 3 before acting |
| H4 gaze cost independent of diff size | Not testable from census alone (needs forge join); only 3 gaze-entry sessions in window, but the single gaze-entry top-5 session cost $253.58 | **Open** — needs the PR-diff join instrument |
| H5 duplicate preamble cache_writes across siblings | cache_write is 19% of spend ($1,258); multi-agent sessions (raid/code-review/merge) dominate the top rollup | **Plausible** — needs per-sibling cache_creation comparison in phase 3 |

New candidate hypotheses the census surfaced (not in the seed list):

- **H6 — main sessions, not subagents, are the cost center** (76% of spend
  from 17% of agents). Interventions targeting subagent budgets address a
  minority of spend.
- **H7 — model mix off-curve**: Opus mains sit ~+1.4 log-residual above the
  curve; comparable-length Sonnet mains sit on it. Model right-sizing of
  long interactive sessions may be the single largest lever.
- **H8 — context never shrinks**: top-decile agents average 43M cache_read
  over their life; final-turn context p99 is 395K. Compaction/context-edit
  timing is a measurable lever on the dominant cost category.
