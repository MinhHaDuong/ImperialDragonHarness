# Trace open-coding report — 2026-06 (ticket 0240, trace-doctor phase 2b)

Hypothesis-discovery pass over a stratified random sample of 30 main-session
traces. Child of tracking ticket 0236; consumes the census (0237) sample
frame; the consolidated hypothesis list at the end is the fixed input to
phase 3 (confirmation on the FULL census — this sample is tainted for
confirmation by design).

## Method

- **Sample**: the 30-trace frame from `docs/trace-census-2026-06.md` §(c)
  (project × entry-skill × session-cost-decile, seed 237, cheap deciles
  included). 30/30 traces digested, none dropped.
- **Digest**: `scripts/trace-digest.py` (this PR) — deterministic, zero LLM
  tokens, ≤2K-token budget per digest. Committed under
  `docs/trace-open-coding-2026-06/`. Privacy: tool names, token numbers,
  file paths and structural markers only; no message text, no command
  arguments.
- **Open coding**: 30 read-only Haiku agents (Explore type, one per digest,
  ≤8 concurrent), each returning 3–6 pattern observations plus a one-line
  economic character. Prompts gave decile/project/skill context and the
  digest line format; agents saw ONE digest each and were blind to the
  others.
- **Axial coding**: single stronger-model pass (Fable 5, the session model)
  clustering the 30 narratives, then merging with census seeds H1–H8.
- **Caveat**: readers narrate digests, not raw traces; per-turn causal
  claims ("context never used") are reader inference, treated here as
  hypothesis material only, never as findings.

## Clusters (open → axial)

### C1 — Context monotonically accumulates; compaction comes late or never
Named in 12/27 non-empty narratives (`monotonic-cache-accumulation`,
`context-accumulation-without-recovery`, `cache-creep-on-quiet-turns`, …).
Long sessions climb from ~17K to 250–450K cache_read per turn with no
pruning; where auto-compact fires, the climb resumes immediately
(`3f1f90f2`: post-compact re-climb to 103K "with no evidence that earlier
file context was needed again"; `dd5fd1a6`: 615 turns, ~473K cr/turn peak;
`f72154b3`: 14.8x growth over 183 turns, zero compactions). Strengthens
seed H8 and motivates the phase-2a detector's recoverable-$ statistic.

### C2 — Subagent spawns inherit full parent context; findings poorly consolidated
6 narratives. Spawns at 100–230K parent context replay discovery work per
agent; results return as uniform small payloads that don't visibly change
the parent trajectory (`dd5fd1a6`: 20+ spawn turns each 880B result,
"agents worked in isolation rather than hierarchical delegation";
`a78d6efc`: 5 spawns × ~150K cr inherited; `ad59e972`: 82KB of subagent
output, "parent never fully integrated"). Refines seed H5 from
"duplicate preamble cache_writes" to the broader spawn-boundary cost.

### C3 — Micro-turn churn: trivial turns pay full context price
8 narratives. Runs of tiny turns — `cd`/`git status`/`ls`/idle reasoning
turns with no tool call — each carry the whole cached context
(`03c5e78e`: 40 consecutive Bash(cd) turns; `be60ade1`: 4 of the final 9
turns produced no tool result; `60ffdb7a`: consecutive duplicate `cd`
calls; `467339b6`: 7 idle turns at up to 80K cr). At 100K+ context, a
10-turn navigation loop costs ~$0.50–1.50 of cache_read for near-zero
information. New hypothesis (H11).

### C4 — Post-delivery administrative tail
5 narratives. After the deliverable lands (merge succeeds, audit
completes), sessions drift into housekeeping: memory updates, secondary
ticket discovery, wrap-up skill chains (`822c9c51`: post-merge tail =
"~20% of total cache reads … marginal value post-delivery"; `ff83e53f`:
gaze→roar→lair chain at 200K+ cr/turn; `dd5fd1a6`: merge/lair/dream
re-invocations "added ~600K cumulative cache_read to close one PR").
The work is legitimate; the question is whether it should run at the
session's peak context or in a fresh cheap session. New hypothesis (H10).

### C5 — Same-file re-reads, within session and across worktree paths
5 narratives. The same logical file is read 2–4× — often because a
worktree switch changes its path (`e6212fb6`: slides.tex read at three
different worktree paths; `e23002cf`: MASTERPLAN and STATE re-read after
worktree entry; `822c9c51`: Read→Edit→Read→Read→Edit on one file). New
hypothesis (H12); the census already carries `max_read_repeat` per agent.

### C6 — Verification re-entry loops
3 narratives, top decile only. Verify/gaze machinery re-invoked on the
same object: `a78d6efc` ran /verify 6× at 83–259K cr each; `dd5fd1a6`
re-entered gaze mid-session ("verification loop failed to converge").
Related to seed H4 but distinct: the cost driver is non-convergence, not
diff size. New hypothesis (H13).

### C7 — What frugal looks like (cheap deciles)
Decile-2/3 sessions show the same skills behaving well: single-purpose,
scope-bound, exit fast (`6aec3371`: one turn, schema fetch, done;
`a2f09575`: 5 turns, $0.51, "setup dominance expected"; `f58bf9dc`:
"surgical minimal output … no speculative work"). Frugality is a
*session-shape* property — short bounded arcs — not a per-turn one.

### D1 — Data-quality note: zero-turn traces
All three decile-1 "$0.00" traces are empty (0 turns): aborted or
never-started sessions. The census should flag `turns == 0` rows and the
sample frame should exclude them — they waste reader slots and tell us
nothing about frugality. Feeds back into `trace-stats.py` as a phase-3
chore.

## Consolidated hypothesis list for phase 3

Seeds H1–H8 from the census (see `docs/trace-census-2026-06.md` §(d));
H9–H13 discovered above. Each carries the statistic phase 3 must compute
on the FULL census.

| ID | Hypothesis | Measurable statistic (full census) | Discovery evidence |
|----|-----------|-------------------------------------|--------------------|
| H1 | cache_read dominates $ | $ share by category | seed (63%); every C1 narrative |
| H2 | top-decile agents carry disproportionate context per turn (reframed from cost~turns²) | cr/turn by cost decile; log-log exponent | seed; `dd5fd1a6`, `a78d6efc` |
| H3 | read-only agents drift past budget | $ share of read-only subagents >40 turns | seed (weak, 4.7% of subagents) |
| H4 | gaze cost independent of diff size | $ vs PR diff stats (forge join) | seed (open) |
| H5 | spawn-boundary redundancy: duplicate preamble cache_writes AND full-context inheritance | per-sibling cache_creation overlap; first-turn cr of subagents vs parent context at spawn | seed + C2 (`dd5fd1a6`, `ad59e972`, `a78d6efc`) |
| H6 | main sessions are the cost center | % of $ from `agent_id == main` | seed (76%) |
| H7 | Opus mains sit off the cost curve; right-size long sessions | residuals by model family | seed; `ff83e53f` mid-session model switch |
| H8 | context never shrinks; compaction late or absent | phase-2a detector recoverable-$ over full corpus | seed + C1 (12 narratives) |
| H9 | *(merged into H5 — spawn-boundary redundancy)* | — | — |
| H10 | post-delivery tail is material | $ spent after merge-success marker (PR MERGED / erg-pr-merge OK in trace) as share of session $ | C4 (`822c9c51`, `ff83e53f`, `dd5fd1a6`) |
| H11 | micro-turn churn: trivial turns at full context | $ share of turns with single navigational tool call (cd/ls/git-status) or no tool call, context >50K; length distribution of such runs | C3 (`03c5e78e`, `be60ade1`, `60ffdb7a`) |
| H12 | same-file re-reads, esp. across worktree paths | `max_read_repeat` joined with $; re-reads where paths differ only by worktree prefix | C5 (`e6212fb6`, `e23002cf`) |
| H13 | verification re-entry: non-converging verify/gaze loops | sessions with ≥2 verify/gaze Skill invocations; incremental $ of re-entries | C6 (`a78d6efc`, `dd5fd1a6`) |

Plus chore D1: flag/exclude zero-turn traces in `trace-stats.py`.

Phase-3 discipline (0236): these hypotheses were fixed BEFORE any
confirmatory statistics were computed; confirmation runs on the full
census, never on this 30-trace sample. Discovered-hypothesis statistics
that need new extraction (H10's merge marker, H11's turn classification,
H13's skill-invocation count) extend `trace-stats.py`, keeping the
zero-LLM invariant.
