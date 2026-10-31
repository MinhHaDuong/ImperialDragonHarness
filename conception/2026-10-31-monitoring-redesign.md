# Monitoring redesign: stop refusing, keep the transcripts, draw timelines on demand

Status: accepted by the author 2026-10-31 in its short form; this revision
replaces the three-layer design reviewed in rv-20261031-pr-2067-b6f9 (§ 8).

Asked 2026-10-31, after a harness-doctor consultation found that online
attribution capture is the main source of landing friction: rethink what is
recorded, when, how and where; keep every session transcript durably,
headless seats included; record the execution flow with timings and costs of
subagent and test calls, enough to draw timeline bars; keep pointers to the
transcript spans so a detail can be rebuilt quickly. Then asked: is it KISS,
and does it reduce friction? The first revision did not pass that test; this
one is the answer.

Measurements below were taken on padme on 2026-10-31 unless stated; doudou was
unreachable (`ssh: No route to host`), so its side is unmeasured.

## 1. Thesis

Record online only what cannot be reconstructed later, never refuse on a
record, and derive everything else from durable raw transcripts when a
question needs it. Build an index only when two consumers need fast
cross-session queries.

What cannot be reconstructed later: the raw transcripts themselves (they are
deleted by age), and the link between a script and the headless seat it
launched. Everything else (timings, tokens, costs, exit codes, who committed
what) is in the transcripts or in git.

## 2. Current situation

### 2.1 What is recorded, where, for how long

| Source | Where | Retention | Content useful for monitoring |
|---|---|---|---|
| Claude Code sessions and Task subagents | `~/.claude/projects/<cwd>/<session>.jsonl`, subagents in `<session>/subagents/agent-*.jsonl`, large outputs in `<session>/tool-results/`; 5.5 GB, 282 project dirs, 7,735 subagent files | `cleanupPeriodDays: 180` (user and shared settings, the shared file first seen in commit 6193cb37 of 2026-07-22). The oldest transcript is of 2026-06-10, later than the 180-day horizon (2026-05-04): an earlier, shorter period, likely the 30-day default, deleted the rest | timestamp on every message, tool call and tool result; token usage per assistant message; no dollar cost |
| Claude headless seats (`claude -p --restricted`) | same tree | as above, assuming `--restricted` (`skills/route/routes.json:90`) does not change the cleanup period (§ 2.3) | as above |
| Codex | `~/.codex/sessions/YYYY/...`; 3.1 GB | oldest rollout 2026-09-08; no cleanup observed, too young to tell | event stream with cumulative token counts |
| Pi | `~/.pi/agent/sessions`; 12 MB | kept | per-call usage with cost |
| vibe seats | disposable `VIBE_HOME` written per seat by `gaze_seat.py` | **lost** at seat end | none kept |
| aider seats | scratch cwd, `--no-restore-chat-history` | **lost** | none kept |
| `manuscript_review.py` readers | `claude -p ... --no-session-persistence` | **lost** | none kept |
| OpenRouter and Padmé LLM calls made by scripts | not recorded by the harness | — | billed cost per API key, aggregated by `health_checkup.py` |
| Raw command output | the `rtk` hook compacts Bash output before it enters the transcript; `~/.local/share/rtk/tee/` keeps 124 KB | short | compacted form only |
| Seat outcomes | `seat_clock.py` writes `<out>.status` in the panel directory | as long as the panel dir lives | wall time per seat, no parent link |
| Review records | git notes `refs/notes/review` (88 notes), `memory/evidence/attribution/` (206 records) | durable | typed by hand online: the friction |

### 2.2 How it is analysed

Sixteen scripts match `trace-*.py`, `trace_*.py`, `gate_traces.py`,
`mammoth-audit.py` and `health_checkup.py`; about eight read the transcripts
directly, each with its own reader (5,198 lines in the `trace*`,
`gate_traces` and `mammoth` files). A full walk takes about 45 s (mammoth on
4.7 GB). Most read only Claude Code's layout. None of them hurts today.

### 2.3 Observed gaps and open questions

- **Online attribution friction.** Since 2026-10-29, 15 of the 22 sessions
  that executed `attribution_record.py` met at least one refusal; the main one
  (30 of 47 refusal responses) is the missing `writer:` line in interactive
  sessions (ticket 1380).
- **August hole.** No Claude Code transcript on padme has an mtime between
  2026-07-30 and 2026-08-31, while the harness has 215 commits in August.
  Cause not established; the likely discriminator is doudou.
- **Per-host stores.** Transcripts stay on the host that ran the session.
- **Headless cleanup period.** `--restricted` ignores the settings files and
  Claude Code's documented default is 30 days (§ 3). If a seat applied that
  default at start it could delete every transcript older than a month; the
  surviving June files argue against it. One experiment settles it.

### 2.4 Volume (measured, padme)

- October 2026, by mtime: 3.53 GB of Claude Code JSONL, 2.28 GB of Codex.
- Transcript sizes (12,009 files, Claude Code and Codex): median 0.4 MB,
  p90 1.1 MB, p99 5.9 MB, max 63.6 MB.
- zstd on a 163 MB sample: 16× at level 19, 10× at level 3. A 24 MB transcript
  decompresses in 0.01 s.
- Derived, not measured: at October's rate the archive grows by about
  0.4–0.6 GB per month compressed; `/home` has 163 GB free.

## 3. State of the art

Full survey with sources and verification marks:
[2026-10-31-monitoring-redesign-sota.md](2026-10-31-monitoring-redesign-sota.md)
([V] primary doc, [S] secondary, [U] unverified). What bears on this design:

- Claude Code exports OTel natively when `CLAUDE_CODE_ENABLE_TELEMETRY=1`:
  per-request `cost_usd` and `duration_ms`, per-tool `duration_ms`, agent and
  parent-agent ids (v2.1.310+), and, with a beta flag, traces that a `claude -p`
  seat joins through `TRACEPARENT` [V]. Codex exports OTel through `[otel]`
  (no USD) [V]; Pi writes cost in its transcript and has no OTel [V].
- Claude Code's retention defaults to 30 days; large outputs spill to
  `tool-results/` [V].
- Self-hosted observability backends are heavy (Langfuse: Postgres,
  ClickHouse, Redis, S3), source-available (Phoenix) or enterprise-only
  (Logfire) [V/S]. OTel GenAI agent conventions were still "Development" in
  2026-06 [S].
- Chrome Trace Event JSON opens in Perfetto as a local file; overlapping
  spans need one lane (`tid`) each [V].
- Provenance by commit trailer is weak evidence (1 of 39 commits touching an
  agent-notes file carried it, one study) [S]; its critics want capture at
  generation time.

Implication: none of this needs a service. Files, one reader and a Perfetto
export answer the question; OTel stays an option for when transcripts lack
something (cost in dollars is computable from tokens).

## 4. Design

Four pieces, each independent of the others' internals.

### 4.1 No online refusal (friction)

The landing records the writer itself from the session's runtime and model,
and attribution capture warns instead of refusing when a fact is missing.
An attribution check may report "not derivable"; it never stops a landing or
a roar. This is ticket 1380, widened.

### 4.2 Raw archive (retention)

A nightly job (systemd user timer) copies every transcript of the three
runtimes untouched for a day, with Claude Code's `subagents/` and
`tool-results/`, to `~/archive/transcripts/<host>/<runtime>/<original
relative path>.zst`, one plain zstd file each. A source whose size changed
since its last copy is copied again: transcripts only append, so the new copy
supersedes the old one. doudou pushes to padme when online. The archive keeps
the runtime's own file names and contents, unmodified, so any later reader or
index can rebuild from it. Nothing is committed to git.

The coverage holes close at the door: vibe and aider seats get a persistent
home under the archive's spool; `manuscript_review.py` drops
`--no-session-persistence`.

The archive sits on the same disk as the live tree with the same
permissions, so it adds no exposure; uncleared-project material is in the
live transcripts already. Encryption becomes required if the archive is ever
copied off the host.

### 4.3 Launch line (the link that would be lost)

`seat_clock.py run`, which already launches every headless seat, appends one
JSON line per seat to `~/archive/transcripts/<host>/launches.jsonl`:

```
{"ts_start", "ts_end", "host", "parent_runtime", "parent_session",
 "child_runtime", "child_session", "seat", "cwd", "unit", "exit"}
```

`parent_session` comes from the runtime's session id (`runtime.py session
id`); `child_session` is pinned at launch where the CLI allows it (`claude -p
--session-id`) or left empty with the child's start time for a later join.
The write is an append; a failed write prints a warning and the seat runs.

### 4.4 Timeline on demand (execution flow)

`scripts/trace_timeline.py <session>` reads one session, its subagents and
the seats its launch lines name, and writes Chrome Trace Event JSON: one lane
per concurrent agent, one complete event per tool call, test or gate run,
with model, tokens, shadow USD and the pointer `(file, tool_use_id)` in
`args`. It reads the live tree first and falls back to the archive, so a
same-day session works.

The reader is a module apart from the renderer: `scripts/trace_events.py`,
one function per runtime turning a transcript into a stream of events with
the same fields. A later index is that reader run over the archive and
stored; nothing in the timeline script needs to change for it.

## 5. Deferred, and when to pick it up

| Deferred | Pick up when | Kept possible by |
|---|---|---|
| Span index (SQLite/DuckDB) | two consumers need fast cross-session queries (trace-doctor and derived attribution, a per-day raid timeline) | raw archive (§ 4.2), launch lines (§ 4.3), `trace_events.py` as a separate module, pointers by `(file, tool_use_id)` |
| Migrating the eight transcript readers onto `trace_events.py` | a reader is touched for another reason | the same module |
| Native OTel export | a question needs what transcripts lack (exact billed cost, beta trace nesting) | nothing to keep: it is additive |
| Launch lines from adapter hooks, `SubagentStop`, a `Session:` commit trailer | a derivation proves ambiguous without them | the raw transcripts hold the Agent call and the `git commit` result already |
| Seekable compression, byte offsets | a transcript makes whole-file decompression slow (today: p99 5.9 MB, 0.01 s for 24 MB) | plain zstd files can be recompressed |
| Archive encryption | the archive leaves the host | — |

## 6. Phasing and cost

Prices: agent hours, USD at list price for coder and review seats, author
time; odds of meeting the exit on the first pass.

| Step | Ticket content | Exit | Agent | USD | Author | Odds |
|---|---|---|---|---|---|---|
| 1. No online refusal | 1380, widened | an interactive-session landing and its roar capture print no `invalid` and need no hand-typed line | 1–2 h | 5–15 | 0 | 85 % |
| 2. Raw archive | timer, plain zstd, re-copy on growth, both hosts, three holes closed, the headless-cleanup experiment | every transcript untouched for a day is in the archive at its current size; the experiment's result recorded | 2–3 h | 10–20 | 15 min (doudou access) | 85 % |
| 3. Launch line | `seat_clock.py` appends the launch line | every seat of one gaze run appears in `launches.jsonl` with its parent session | 1 h | 5–10 | 0 | 85 % |
| 4. Timeline | `trace_events.py` and `trace_timeline.py` | one raid session of the week renders in Perfetto with its subagents and seats, spot-checked against the transcript | 3–4 h | 20–40 | 15 min (look at one timeline) | 75 % |

Total: about 7–10 agent hours, 40–85 USD, 30 author minutes. Steps 1, 2 and
3 are independent; step 4 needs 3 for seat lanes and 2 for the archive
fallback. Step 2 has a date: the oldest surviving transcript (2026-06-10)
passes the 180-day horizon around 2026-12-07.

## 7. Recommendation

Run the four steps as a ticket train under one tracker; land step 2 before
2026-12-07.

## 8. Review

**First revision** (three layers: archive, span index, derived facts; P0–P3,
175–370 USD). Gaze panel rv-20261031-pr-2067-b6f9 on head 81cde90: FINDINGS,
none blocking. Seats: facts by the orchestrator (Claude Opus), state of the art
by Claude Sonnet, design by GPT-6.1 Sol (OpenAI family, the independent
seat). Findings folded then and kept here: the June cutoff predates the
180-day period; a line number cannot address a compressed frame (moot now:
pointers are `(file, tool_use_id)` over whole-file decompression); resumed
sessions re-copied on growth; same-day landings read the live transcript;
launch lines kept regardless of OTel; survey caveats restated.

**Second revision** (this one), after the author asked whether the design was
KISS. The panel's suggestions had pushed toward completeness (adapter hooks,
`SubagentStop`, commit trailer, a twenty-column index); measured file sizes
showed seekable compression to be unneeded; the friction fix sat in the last
phase. This revision delivers the friction fix first and defers every piece
without a present consumer, each with the condition that brings it back
(§ 5).
