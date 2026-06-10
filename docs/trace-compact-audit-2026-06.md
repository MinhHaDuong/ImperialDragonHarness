# Missed compact/clear audit — June 2026 (28-day window)

Mechanical detector for missed compaction opportunities in Claude Code
session traces, produced by `scripts/trace-compact-audit.py` (ticket 0239,
trace-doctor phase 2a, tracking ticket 0236). Run date: 2026-06-10. Zero
LLM tokens spent. Tests H8 from the census ("context never shrinks",
`docs/trace-census-2026-06.md`).

## Method

- Per agent, the per-turn cache_read trajectory in unique `message.id`
  order (same dedupe rule as the census), interleaved with compaction
  boundaries (`type: "system"` / `subtype: "compact_boundary"`) and
  `/clear` commands (`<command-name>/clear</command-name>` user records).
- **Missed opportunity** = a run of ≥30 consecutive turns each reading
  ≥300K cache tokens, uninterrupted by any compact or clear
  (`--min-run 30 --threshold 300000`, the ticket's starting parameters).
- **Counterfactual $** — an explicit **upper bound**: had the agent
  compacted at the run's first turn, each later turn in the run would have
  read the post-compact median context instead of its actual cache_read.
  The median is observed from sessions that DID compact: 137 boundaries in
  the window; the first turn after a boundary reads a median of **12,866
  tokens** (boundary `postTokens` metadata gives a similar 12–14K). The
  bound ignores context re-growth after the hypothetical compaction and
  the compaction's own cost (~$0.10–0.30 of cache_write per event), and
  assumes compacted context loses nothing the session later needs —
  all three simplifications inflate it, none deflate it.
- Pricing: per-turn model at the census rates (cache read = 0.1× input).

Reproduce: `python3 scripts/trace-compact-audit.py --days 28 --json`.

## Headline numbers

| Metric | Value |
|---|---|
| Agents in window | 1,749 |
| Compactions observed | 137 |
| `/clear` observed | 124 |
| Missed-opportunity runs | **63** (61 in main sessions, 2 in subagents) |
| Recoverable $ (upper bound) | **≤ $1,035 / 28 days** |

Against the census's $6,544 window total, the upper bound is ~16% of all
spend — and ~25% of main-session spend ($4,955), since 61 of 63 runs are
main sessions. H8 is supported: long main sessions routinely ride 300K+
contexts for dozens of turns without ever compacting.

Run shape: median flagged run is 58 turns at ~414K cache_read/turn; the
worst (a git-erg main session) is 366 consecutive turns averaging 567K,
worth ≤$101 on its own.

## By project (encoded trace-dir names)

| Project | Runs | Recoverable $ ≤ |
|---|---|---|
| aedist-technical-report | 38 | 659.83 |
| git-erg | 7 | 169.92 |
| IDH (~/.claude) | 9 | 118.84 |
| chemin-de-voix | 8 | 78.24 |
| padme | 1 | 8.00 |

## By entry skill

| Entry skill | Runs | Recoverable $ ≤ |
|---|---|---|
| raid | 26 | 419.05 |
| effort | 4 | 173.71 |
| celebrate | 7 | 85.25 |
| perch | 5 | 77.15 |
| (none) | 7 | 68.94 |
| start-ticket | 6 | 64.77 |
| healthcheck | 2 | 57.36 |
| housekeeping | 3 | 33.61 |
| roar | 1 | 29.96 |
| hunt | 1 | 19.86 |
| scry | 1 | 5.18 |

Raid sessions — long-lived multi-wave orchestrators — account for 40% of
the recoverable bound. They are exactly the sessions where the
orchestrator's context accumulates wave after wave of agent reports.

## Top-20 sessions by recoverable $

| Recoverable $ ≤ | Runs | Entry skill | Project | Session |
|---|---|---|---|---|
| 157.57 | 8 | raid | aedist-technical-report | 21e99ac0… |
| 125.14 | 2 | effort | git-erg | 211826a9… |
| 103.83 | 6 | raid | aedist-technical-report | f4537f72… |
| 64.77 | 6 | start-ticket | chemin-de-voix | 207f5efc… |
| 60.15 | 4 | raid | aedist-technical-report | de20a516… |
| 57.36 | 2 | healthcheck | aedist-technical-report | aa731a09… |
| 48.57 | 2 | effort | aedist-technical-report | 1ef5880f… |
| 42.32 | 3 | (none) | aedist-technical-report | 8fe4d2ee… |
| 41.13 | 3 | perch | aedist-technical-report | f6f1d1a2… |
| 38.29 | 2 | roar | aedist-technical-report | dd5fd1a6… |
| 36.54 | 2 | celebrate | aedist-technical-report | eddfaf5e… |
| 32.49 | 2 | raid | IDH | a78d6efc… |
| 24.01 | 1 | raid | aedist-technical-report | e8c40ecf… |
| 22.52 | 1 | perch | IDH | 2e3a435d… |
| 21.44 | 2 | housekeeping | IDH | 617b4df5… |
| 19.86 | 1 | hunt | IDH | dd0eb522… |
| 19.08 | 2 | celebrate | git-erg | 28935cc7… |
| 18.37 | 1 | celebrate | aedist-technical-report | 15b3b196… |
| 14.09 | 1 | raid | git-erg | 01c6929f… |
| 13.51 | 1 | perch | aedist-technical-report | 90650ce6… |

## Caveats

- The $ figure is a **counterfactual upper bound**, not a measured saving.
  A compaction at 300K context drops the *next* turn to ~13K, but real
  context re-grows; the realizable saving over a 58-turn run is smaller.
- The detector measures *opportunity*, not *advisability*: some flagged
  runs may genuinely need their full context (e.g. a manuscript review
  holding a large document). The per-run CSV
  (`--output`) is the open-coding sample frame for phase 3 to separate
  load-bearing context from sediment.
- Auto-compaction triggers near the model context ceiling, so 300K+ runs
  on a 1M-context model sit *below* the auto trigger by design — these are
  missed *manual/policy* opportunities, pointing at skill-level or
  harness-level compaction policy, not at a Claude Code bug.

## Parameter sensitivity

The N=30/T=300K starting point is from the ticket. Re-running at
N=20/T=200K flags 144 runs, ≤$1,668; at N=40/T=400K, 33 runs, ≤$631.
The headline is robust in order of magnitude across a 2× parameter
spread, and concentrated: the top-10 sessions alone carry $0.74K of the
$1.03K baseline bound.
